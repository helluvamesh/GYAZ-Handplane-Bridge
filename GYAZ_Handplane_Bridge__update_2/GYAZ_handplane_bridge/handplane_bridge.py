﻿# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any laTter version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


##########################################################################################################
##########################################################################################################
 
 
bake_settings_list = ['aoSampleRadius', 'aoSampleCount', 'volumetricGradientCubeFit', 'thicknessSampleRadius', 'thicknessSampleCount', 'heightMapScale', 'heightMapOffset', 'curvatureUseRaySampling', 'curvatureUseRaySampling', 'curvatureSampleRadius', 'curvatureSampleCount', 'curvaturePixelRadius', 'curvatureAutoNormalize', 'curvatureMaxAngle', 'curvatureOutputGamma', 'cavitySensitivity', 'cavityBias', 'cavityPixelRadius', 'cavityOutputGamma', 'cavityKernelType', 'textureSpaceAOPixelRadius', 'textureSpaceAOOutputGamma', 'textureSpaceAOSampleCoveragePercentage', 'tangentSpace', 'isEnabled_tangent_space_normals', 'isEnabled_object_space_normals', 'isEnabled_ambient_occlusion', 'isEnabled_ambient_occlusion_floaters', 'isEnabled_vertex_color', 'isEnabled_material_psd', 'isEnabled_material_id', 'isEnabled_curvature_map', 'isEnabled_volumetric_gradient', 'isEnabled_cavity_map', 'isEnabled_height_map', 'isEnabled_texture_space_ao', 'isEnabled_thickness']

global_settings_list = ['threadCount', 'backRayOffsetScale', 'downsampleInGeneratorSpace', 'buildSmoothedNormalsForHighRes', 'suppressTriangulationWarning']

output_settings_list = ['outputExtension', 'outputBitDepth', 'texture_format', 'outputWidth', 'outputHeight', 'outputPadding', 'outputSuperSample', 'outputDither']
 

def popup (lines, icon, title):
    def draw(self, context):
        for line in lines:
            self.layout.label(line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

    
def list_to_visual_list (list):
    line = ''
    for index, item in enumerate(list):
        if index > 0:
            line += ', '
        line += str(item)
    return line

 
import bpy
import os
import subprocess
from bpy.types import Panel, Operator, AddonPreferences, PropertyGroup
from bpy.props import *
import bpy.utils.previews

#popup
def popup (lines, icon, title):
    def draw(self, context):
        for line in lines:
            self.layout.label(line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    
def clear_transformation (obj, loc, rot, scale):
    if loc == True:
        setattr (obj, 'location', [0, 0, 0])
    if scale == True:
        setattr (obj, 'scale', [1, 1, 1])
    if rot == True:
        setattr (obj, 'rotation_euler', [0, 0, 0])
        setattr (obj, 'rotation_quaternion', [1, 0, 0, 0])
        setattr (obj, 'rotation_axis_angle', [0, 0, 0, 0])
        
def select_only_object (object):
    scene = bpy.context.scene
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set (mode='OBJECT')        
    bpy.ops.object.select_all (action='DESELECT')
    object.select = True
    scene.objects.active = object 


class GYAZ_HandplaneBridge_Preferences(AddonPreferences):
    # use __name__ with single-file addons
    # use __package__ with multi-file addons
    bl_idname = __package__
    
    def absolute_path__hand_plane_path (self, context):
        prop = getattr (self, "hand_plane_baker_path")
        new_path = os.path.abspath ( bpy.path.abspath (prop) )
        if prop.startswith ('//') == True:
            self.hand_plane_baker_path = new_path
    
    handplane_path = StringProperty (name='Handplane Baker Path', default='', subtype='FILE_PATH', update=absolute_path__hand_plane_path)
    
    #map suffixes
    ts_normals_suffix = StringProperty (name='Tangent Space Normals', default='_ts')
    os_normals_suffix = StringProperty (name='Object Space Normals', default='_os')
    ao_suffix = StringProperty (name='Ambient Occlusion', default='_ao')
    ao_floaters_suffix = StringProperty (name='Ambient Occlusion (Floaters)', default='_aof')
    vert_color_suffix = StringProperty (name='Vertex Color', default='_color')
    mat_psd_suffix = StringProperty (name='Material PSD', default='_mat')
    mat_id_suffix = StringProperty (name='Material ID', default='_matid')
    curve_suffix = StringProperty (name='Curvature Map', default='_curve')
    vol_gradient_suffix = StringProperty (name='Volumetric Gradient', default='_vg')
    cavity_suffix = StringProperty (name='Cavity Map', default='_cav')
    height_suffix = StringProperty (name='Height Map', default='_hm')
    tsao_suffix = StringProperty (name='Texture Space AO', default='_tsao')
    thickness_suffix = StringProperty (name='Thickness', default='_thick')
  
    
    #PRESETS (BakeSettings, OutputSettings, GlobalSettings
    class Op_GYAZ_HandplaneBridge_Preset (PropertyGroup):
        #preset name
        name = StringProperty ()
        
        #bake settings
        aoSampleRadius = FloatProperty ()
        aoSampleCount = IntProperty ()
        volumetricGradientCubeFit = BoolProperty ()
        thicknessSampleRadius = FloatProperty ()
        thicknessSampleCount = IntProperty ()
        heightMapScale = FloatProperty ()
        heightMapOffset = FloatProperty ()
        curvatureUseRaySampling = BoolProperty ()
        curvatureSampleRadius = FloatProperty ()
        curvatureSampleCount  = IntProperty ()
        curvaturePixelRadius = IntProperty ()
        curvatureAutoNormalize  = BoolProperty ()
        curvatureMaxAngle = FloatProperty ()
        curvatureOutputGamma = FloatProperty ()
        cavitySensitivity = FloatProperty ()
        cavityBias = FloatProperty ()
        cavityPixelRadius = IntProperty ()
        cavityOutputGamma  = FloatProperty ()
        cavityKernelType = StringProperty ()
        textureSpaceAOPixelRadius = IntProperty ()
        textureSpaceAOOutputGamma = FloatProperty ()
        textureSpaceAOSampleCoveragePercentage = FloatProperty ()
        
        tangentSpace = StringProperty ()
        
        isEnabled_tangent_space_normals = BoolProperty ()
        isEnabled_object_space_normals = BoolProperty ()
        isEnabled_ambient_occlusion = BoolProperty ()
        isEnabled_ambient_occlusion_floaters = BoolProperty ()
        isEnabled_vertex_color = BoolProperty ()
        isEnabled_material_psd = BoolProperty ()
        isEnabled_material_id = BoolProperty ()
        isEnabled_curvature_map = BoolProperty ()
        isEnabled_volumetric_gradient = BoolProperty ()
        isEnabled_cavity_map = BoolProperty ()
        isEnabled_height_map = BoolProperty ()
        isEnabled_texture_space_ao = BoolProperty ()
        isEnabled_thickness = BoolProperty ()
        
        #global settings
        threadCount = IntProperty ()
        backRayOffsetScale = FloatProperty ()
        downsampleInGeneratorSpace = BoolProperty ()
        buildSmoothedNormalsForHighRes = BoolProperty ()
        suppressTriangulationWarning = BoolProperty ()
        
        #output settings
        outputExtension = StringProperty ()
        outputBitDepth = IntProperty ()
        texture_format = StringProperty ()
        outputWidth = StringProperty ()
        outputHeight = StringProperty ()
        outputPadding = IntProperty ()
        outputSuperSample = StringProperty ()
        outputDither = BoolProperty ()
        
    bpy.utils.register_class(Op_GYAZ_HandplaneBridge_Preset)
    
    presets = CollectionProperty (type=Op_GYAZ_HandplaneBridge_Preset)
    
    #preset name selection menu:
    #preset names
    def get_preset_name_items (self, context):
        names = []
        for preset in self.presets:
            preset_name = preset.name
            names.append ( (preset_name, preset_name, '') )
        return names
    
    #load preset
    def load_preset (self, context):
        active_preset_name = self.active_preset_name
        scene = bpy.context.scene
        
        for item in self.presets:
            if item.name == active_preset_name:
                preset = item
        
        if 'preset' in locals():
            #load bake settings
            #get scene prop value
            for prop_name in bake_settings_list:
                preset_prop_value = getattr (preset, prop_name)
                
                #write scene prop value to preset
                setattr (scene.gyaz_hpb.bake_settings, prop_name, preset_prop_value)
                
            #load globaé settings
            #get scene prop value
            for prop_name in global_settings_list:
                preset_prop_value = getattr (preset, prop_name)
                
                #write scene prop value to preset
                setattr (scene.gyaz_hpb.global_settings, prop_name, preset_prop_value)
                
            #load output settings
            #get scene prop value
            for prop_name in output_settings_list:
                preset_prop_value = getattr (preset, prop_name)
                
                #write scene prop value to preset
                setattr (scene.gyaz_hpb.output_settings, prop_name, preset_prop_value)            
            
    
    active_preset_name = EnumProperty (name='Presets', items=get_preset_name_items, default=None, update=load_preset)
    
    
    
    def draw (self, context):
        layout = self.layout
        layout.prop (self, 'handplane_path')
        
        layout.label ('Map Suffixes:')
        layout.prop (self, 'ts_normals_suffix')
        layout.prop (self, 'os_normals_suffix')
        layout.prop (self, 'ao_suffix')
        layout.prop (self, 'ao_floaters_suffix')
        layout.prop (self, 'vert_color_suffix')
        layout.prop (self, 'mat_psd_suffix')
        layout.prop (self, 'mat_id_suffix')
        layout.prop (self, 'curve_suffix')
        layout.prop (self, 'vol_gradient_suffix')
        layout.prop (self, 'cavity_suffix')
        layout.prop (self, 'height_suffix')
        layout.prop (self, 'tsao_suffix')
        layout.prop (self, 'thickness_suffix')
        
#        #debug
#        col = layout.column ()
#        col = layout.column ()
#        col = layout.column ()
#        layout.label ('Presets:')
#        layout.prop (self, 'presets')
#        for preset in self.presets:
#            layout.prop (preset, 'name', text='preset_name')
#            for prop_name in bake_settings_list+global_settings_list+output_settings_list:
#                layout.prop (preset, prop_name)
#            col = layout.column ()
#            col = layout.column ()
#            col = layout.column ()
            


# Registration
def register():
    bpy.utils.register_class(GYAZ_HandplaneBridge_Preferences)


def unregister():
    bpy.utils.unregister_class(GYAZ_HandplaneBridge_Preferences)


register()


#INIT OPERATOR
#for creating global properties
class Op_GYAZ_HandplaneBridge_InitGlobalProps (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_init"  
    bl_label = "GYAZ Handplane Bridge: Init"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    #operator function
    def execute(self, context):
             
        scene = bpy.context.scene
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        
        class GYAZ_HandplaneBridge_HighPolyItem (PropertyGroup):
            model = StringProperty (name='', default='')
            overrideMaterial = BoolProperty (name='Override material', default=True)
            material = IntProperty (name='Material ID', default=0, min=0, max=3)
            isFloater = BoolProperty (name='Is Floater', default=False, description='Is Floater?')
            name = StringProperty (name='', default='')
        bpy.utils.register_class (GYAZ_HandplaneBridge_HighPolyItem)
        
        class GYAZ_HandplaneBridge_LowPolyItem (PropertyGroup):
            model = StringProperty (name='', default='')
            cageModel = StringProperty (name='', default='')
            overrideCageOffset = BoolProperty (name='Override Cage Offset', default=False, description='Override Ray Offset.')
            autoCageOffset = FloatProperty (name='Cage Offset', default=1)
            name = StringProperty (name='', default='')
            cage_name = StringProperty (name='', default='')
        bpy.utils.register_class (GYAZ_HandplaneBridge_LowPolyItem)
              
        class GYAZ_HandplaneBridge_ProjectionGroupItem (PropertyGroup):
            name = StringProperty (name='Name', default='Projection Group')
            active = BoolProperty (default=True, description='Only active groups are exported')
            high_poly = CollectionProperty (type=GYAZ_HandplaneBridge_HighPolyItem)
            low_poly = CollectionProperty (type=GYAZ_HandplaneBridge_LowPolyItem)
            material = IntProperty (default=0)
            isolateAO = BoolProperty (name='Isolate AO', default=False)
            autoCageOffset = FloatProperty (name='Ray Offset', default=1)
              
        bpy.utils.register_class (GYAZ_HandplaneBridge_ProjectionGroupItem)
        
        
        def absolute_path__custom_output_folder (self, context):
            prop = getattr (scene.gyaz_hpb, "custom_output_folder")
            new_path = os.path.abspath ( bpy.path.abspath (prop) )
            if prop.startswith ('//') == True:
                scene.gyaz_hpb.custom_output_folder = new_path


        class GYAZ_HandplaneBridge_GlobalSettings (PropertyGroup):
            threadCount = IntProperty (name='Baker Thread Count', default=0, min=0)
            backRayOffsetScale = FloatProperty (name='Back Ray Offset Scale', default=5.0)
            downsampleInGeneratorSpace = BoolProperty (name='Generator Space Downsampling', default=True)
            buildSmoothedNormalsForHighRes = BoolProperty (name='Smooth High Res Normals (If None Found)', default=False)
            suppressTriangulationWarning = BoolProperty (name='Suppress Triangulation Warnings', default=False)
            
        bpy.utils.register_class (GYAZ_HandplaneBridge_GlobalSettings)


        class GYAZ_HandplaneBridge_BakeSettings (PropertyGroup):
            aoSampleRadius = FloatProperty (name='Sample Radius', default=1.0)
            aoSampleCount = IntProperty (name='Sample Count', default=20, min=0)
            volumetricGradientCubeFit = BoolProperty (name='Cube Fit', default=False)
            thicknessSampleRadius = FloatProperty (name='Sample Radius', default=1.0)
            thicknessSampleCount = IntProperty (name='Sample Count', default=20, min=0)
            heightMapScale = FloatProperty (name='Scale', default=1.0)
            heightMapOffset = FloatProperty (name='Offset', default=0.0)
            curvatureUseRaySampling = BoolProperty (name='Use Ray Sampling', default=False)
            curvatureSampleRadius = FloatProperty (name='Sample Radius', default=0.05)
            curvatureSampleCount  = IntProperty (name='Sample Count', default=20, min=0)
            curvaturePixelRadius = IntProperty (name='Pixel Sample Radius', default=4, min=0)
            curvatureAutoNormalize  = BoolProperty (name='Auto Normalize', default=True)
            curvatureMaxAngle = FloatProperty (name='Max Curvature', default=100.0)
            curvatureOutputGamma = FloatProperty (name='Output Gamma', default=1.0)
            cavitySensitivity = FloatProperty (name='Sensitivity', default=0.75)
            cavityBias = FloatProperty (name='Bias', default=0.015)
            cavityPixelRadius = IntProperty (name='PixelSampleRadius', default=4, min=0)
            cavityOutputGamma  = FloatProperty (name='Output Gamma', default=1.0)
            cavityKernelType = EnumProperty (name='Kernel Type', items=(('ConstantBox', 'Constant Box', ''), ('ConstantDisk', 'Constant Disk', ''), ('LinearBox', 'Linear Box', ''), ('LinearDisk', 'Linear Disk', ''), ('Gaussian', 'Gaussian', '')), default='ConstantDisk')
            textureSpaceAOPixelRadius = IntProperty (name='Pixel Sample Radius', default=10, min=0)
            textureSpaceAOOutputGamma = FloatProperty (name='Output Gamma', default=1.0)
            textureSpaceAOSampleCoveragePercentage = FloatProperty (name='Sample Coverage Percentage', default=100.0)
            
            tangentSpace = EnumProperty (name='Tangent Space', items=(('UNREAL_4', 'Unreal Engine 4', ''), ('UNREAL_3', 'Unreal Engine 3', ''), ('UNITY_5_3', 'Unity 5.3', ''), ('UNITY', 'Unity', ''), ('SOURCE', 'Source Engine', ''), ('SOURCE_2', 'Source 2 Engine', ''), ('MAYA_2013_14', 'Autodesk Maya 2013/14', ''), ('MAYA_2012', 'Autodesk Maya 2012', ''), ('3DMAX', 'Autodesk 3DS Max', ''), ('STARCRAFT_II', 'Starcraft II', ''), ('INPUT_TANGENT_AND_BINORMAL', 'Input Tangent and Binormal', ''), ('INPUT_TANGENT_WITH_COMPUTED_BINORMAL', 'Input Tangent with Computed Binormal', '')), default='UNREAL_4')
            
            isEnabled_tangent_space_normals = BoolProperty (default=False)
            isEnabled_object_space_normals = BoolProperty (default=False)
            isEnabled_ambient_occlusion = BoolProperty (default=False)
            isEnabled_ambient_occlusion_floaters = BoolProperty (default=False)
            isEnabled_vertex_color = BoolProperty (default=False)
            isEnabled_material_psd = BoolProperty (default=False)
            isEnabled_material_id = BoolProperty (default=False)
            isEnabled_curvature_map = BoolProperty (default=False)
            isEnabled_volumetric_gradient = BoolProperty (default=False)
            isEnabled_cavity_map = BoolProperty (default=False)
            isEnabled_height_map = BoolProperty (default=False)
            isEnabled_texture_space_ao = BoolProperty (default=False)
            isEnabled_thickness = BoolProperty (default=False)

        bpy.utils.register_class (GYAZ_HandplaneBridge_BakeSettings)

 
        class GYAZ_HandplaneBridge_OutputSettings (PropertyGroup):
            outputFolder = StringProperty (name='Folder', default='')
            outputFilename = StringProperty (name='Name', default='')
            outputExtension = StringProperty (default='TGA')
            outputBitDepth = IntProperty (default=8)
            texture_format = EnumProperty (name='Format', items=(('TIF_8', 'TIF 8', ''), ('TIF_16', 'TIF 16', ''), ('PNG_8', 'PNG 8', ''), ('PNG_16', 'PNG 16', ''), ('PSD_8', 'PSD 8', ''), ('PSD_16', 'PSD 16', ''), ('TGA_8', 'TGA 8', '')), default='PNG_8')
            outputWidth = EnumProperty (name='Width', items=(('256', '256', ''), ('512', '512', ''), ('1024', '1024', ''), ('2048', '2048', ''), ('4096', '4096', ''), ('8192', '8192', ''), ('16384', '16384', '')), default='2048')
            outputHeight = EnumProperty (name='Height', items=(('256', '256', ''), ('512', '512', ''), ('1024', '1024', ''), ('2048', '2048', ''), ('4096', '4096', ''), ('8192', '8192', ''), ('16384', '16384', '')), default='2048')
            outputPadding = IntProperty (name='Padding', default=64, min=0)
            outputSuperSample = EnumProperty (name='Super Sample', items=(('1', '1', ''), ('2', '2', ''), ('4', '4', ''), ('8', '8', ''), ('16', '16', '')), default='1')
            outputDither = BoolProperty (name='Dither', default=True)
            
        bpy.utils.register_class (GYAZ_HandplaneBridge_OutputSettings)
        
        
        class GYAZ_HandplaneBridge_MapSettingsItem (PropertyGroup):
            name = StringProperty ()
            
        bpy.utils.register_class (GYAZ_HandplaneBridge_MapSettingsItem)
        
        class GYAZ_HandplaneBridge_MapItem (PropertyGroup):
            name = StringProperty (default='')
            is_enabled_prop_name = StringProperty (default='')
            filenameSuffix = StringProperty (default='')
            has_props = BoolProperty (default=True)
            show_props = BoolProperty (name='Show/hide settings.', default=False)
            props = CollectionProperty (type=GYAZ_HandplaneBridge_MapSettingsItem)
            
        bpy.utils.register_class (GYAZ_HandplaneBridge_MapItem)   
            
        
        class GYAZ_HandplaneBridge (PropertyGroup):
            projection_groups = CollectionProperty (type=GYAZ_HandplaneBridge_ProjectionGroupItem)
            output_folder_mode = EnumProperty (name='Output Folder', items=(('RELATIVE_FOLDER', 'RELATIVE', ''),('PATH', 'PATH', '')), default='RELATIVE_FOLDER')
            relative_folder_name = StringProperty (name='Folder', default='bake')
            custom_output_folder = StringProperty (name='', default='', subtype='DIR_PATH', update=absolute_path__custom_output_folder)
            file_name = StringProperty (name='Name', default='')
            last_output_path = StringProperty (name='Last Output', default='')
            clear_transforms = BoolProperty (name='Clear Transforms', default=False, description="Clear objects' transformation")
            export_hp = BoolProperty (name='High Poly', default=True, description="Export high poly object(s)")
            export_lp = BoolProperty (name='Low Poly&Cage', default=True, description="Export low poly and cage object(s)")
            bake_settings = PointerProperty (type=GYAZ_HandplaneBridge_BakeSettings)
            global_settings = PointerProperty (type=GYAZ_HandplaneBridge_GlobalSettings)
            output_settings = PointerProperty (type=GYAZ_HandplaneBridge_OutputSettings)
            maps = CollectionProperty (type=GYAZ_HandplaneBridge_MapItem)
            menu = EnumProperty (name='Menu', items=(('GROUPS', 'GROUPS', ''), ('SETTINGS', 'SETTINGS', ''), ('EXPORT', 'EXPORT', '')), default='GROUPS')
        
        bpy.utils.register_class (GYAZ_HandplaneBridge)
    
    
        bpy.types.Scene.gyaz_hpb = PointerProperty (type=GYAZ_HandplaneBridge)
        
        
        #maps
        bpy.context.scene.gyaz_hpb.maps.clear ()
        
        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Tangent Space Normals'
        item.filenameSuffix = prefs.ts_normals_suffix
        item.is_enabled_prop_name = 'isEnabled_tangent_space_normals'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'tangentSpace'
        
        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Object Space Normals'
        item.filenameSuffix = prefs.os_normals_suffix
        item.is_enabled_prop_name = 'isEnabled_object_space_normals'
        item.has_props = False
        
        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Ambient Occlusion'
        item.filenameSuffix = prefs.ao_suffix
        item.is_enabled_prop_name = 'isEnabled_ambient_occlusion'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'aoSampleRadius'
        prop = item.props.add ()
        prop.name = 'aoSampleCount'
        
        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Ambient Occlusion (Floaters)'
        item.filenameSuffix = prefs.ao_floaters_suffix
        item.is_enabled_prop_name = 'isEnabled_ambient_occlusion_floaters'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'aoSampleRadius'
        prop = item.props.add ()
        prop.name = 'aoSampleCount'

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Vertex Color'
        item.filenameSuffix = prefs.vert_color_suffix
        item.is_enabled_prop_name = 'isEnabled_vertex_color'
        item.has_props = False

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Material PSD'
        item.filenameSuffix = prefs.mat_psd_suffix
        item.is_enabled_prop_name = 'isEnabled_material_psd'
        item.has_props = False

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Material ID'
        item.filenameSuffix = prefs.mat_id_suffix
        item.is_enabled_prop_name = 'isEnabled_material_id'
        item.has_props = False

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Curvature Map'
        item.filenameSuffix = prefs.curve_suffix
        item.is_enabled_prop_name = 'isEnabled_curvature_map'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'curvatureUseRaySampling'
        prop = item.props.add ()
        prop.name = 'curvatureSampleRadius'
        prop = item.props.add ()
        prop.name = 'curvatureSampleCount'
        prop = item.props.add ()
        prop.name = 'curvaturePixelRadius'
        prop = item.props.add ()
        prop.name = 'curvatureAutoNormalize'
        prop = item.props.add ()
        prop.name = 'curvatureMaxAngle'
        prop = item.props.add ()
        prop.name = 'curvatureOutputGamma'

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Volumetric Gradient'
        item.filenameSuffix = prefs.vol_gradient_suffix
        item.is_enabled_prop_name = 'isEnabled_volumetric_gradient'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'volumetricGradientCubeFit'

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Cavity Map'
        item.filenameSuffix = prefs.cavity_suffix
        item.is_enabled_prop_name = 'isEnabled_cavity_map'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'cavitySensitivity'
        prop = item.props.add ()
        prop.name = 'cavityBias'
        prop = item.props.add ()
        prop.name = 'cavityPixelRadius'
        prop = item.props.add ()
        prop.name = 'cavityOutputGamma'
        prop = item.props.add ()
        prop.name = 'cavityKernelType'

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Height Map'
        item.filenameSuffix = prefs.height_suffix
        item.is_enabled_prop_name = 'isEnabled_height_map'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'heightMapScale'
        prop = item.props.add ()
        prop.name = 'heightMapOffset'

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Texture Space AO'
        item.filenameSuffix = prefs.tsao_suffix
        item.is_enabled_prop_name = 'isEnabled_texture_space_ao'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'textureSpaceAOPixelRadius'
        prop = item.props.add ()
        prop.name = 'textureSpaceAOOutputGamma'

        item = scene.gyaz_hpb.maps.add ()
        item.name = 'Thickness'
        item.filenameSuffix = prefs.thickness_suffix
        item.is_enabled_prop_name = 'isEnabled_thickness'
        item.has_props = True
        prop = item.props.add ()
        prop.name = 'thicknessSampleRadius'
        prop = item.props.add ()
        prop.name = 'thicknessSampleCount'
            
        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_SavePreset (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_save_preset"  
    bl_label = "GYAZ Handplane Bridge: Save Preset"
    bl_description = "Save preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name = StringProperty (name='preset name', default='')
    
    #popup with properties
    def invoke(self, context, event):
        wm = bpy.context.window_manager
        return wm.invoke_props_dialog(self)
    
    #operator function
    def execute(self, context):
        preset_name = self.preset_name
        scene = bpy.context.scene
        
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        
        #make sure preset name is valid
        if preset_name != '' and preset_name != ' ':
        
            #add preset
            preset = prefs.presets.add ()
            
            #add preset name
            preset.name = preset_name
            
            #save bake settings
            #get scene prop value
            for prop_name in bake_settings_list:
                scene_prop_value = getattr (scene.gyaz_hpb.bake_settings, prop_name)
                
                #write scene prop value to preset
                setattr (preset, prop_name, scene_prop_value)
                
            #save global settings
            #get scene prop value
            for prop_name in global_settings_list:
                scene_prop_value = getattr (scene.gyaz_hpb.global_settings, prop_name)
                
                #write scene prop value to preset
                setattr (preset, prop_name, scene_prop_value)
                
            #save output settings
            #get scene prop value
            for prop_name in output_settings_list:
                scene_prop_value = getattr (scene.gyaz_hpb.output_settings, prop_name)
                
                #write scene prop value to preset
                setattr (preset, prop_name, scene_prop_value)
                
            #set new preset active
            setattr (prefs, 'active_preset_name', preset_name)
                
        #save user preferences
        bpy.context.area.type = 'USER_PREFERENCES'
        bpy.ops.wm.save_userpref()
        bpy.context.area.type = 'PROPERTIES'      

        return {'FINISHED'}
    

class Op_GYAZ_HandplaneBridge_RemovePreset (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_remove_preset"  
    bl_label = "GYAZ Handplane Bridge: Remove Preset"
    bl_description = "Remove preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    #operator function
    def execute(self, context):
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        active_preset_name = prefs.active_preset_name
        scene = bpy.context.scene
        
        for index, item in enumerate (prefs.presets):
            if item.name == active_preset_name:
                preset = item
        
        if 'preset' in locals():
            prefs.presets.remove (index)
            
            #set first preset active
            if len (prefs.presets) > 0:
                first_preset_name = prefs.presets[0].name
                setattr (prefs, 'active_preset_name', first_preset_name)
                
        #save user preferences
        bpy.context.area.type = 'USER_PREFERENCES'
        bpy.ops.wm.save_userpref()
        bpy.context.area.type = 'PROPERTIES'      

        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_AddProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_add_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Add Projection Group"
    bl_description = "Add projection group / Clear projection groups"
    bl_options = {'REGISTER', 'UNDO'}
    
    clear = BoolProperty (default=False)
    
    #operator function
    def execute(self, context):
        clear = self.clear  
        scene = bpy.context.scene
        
        if clear == False:
            item = scene.gyaz_hpb.projection_groups.add ()
        else:
            item = scene.gyaz_hpb.projection_groups.clear ()
            
        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_RemoveProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_remove_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Remove Projection Group"
    bl_description = "Remove projection group"
    bl_options = {'REGISTER', 'UNDO'}
    
    projection_group_index = IntProperty (default=0)
    
    #operator function
    def execute(self, context):
        index = self.projection_group_index  
        scene = bpy.context.scene
        scene.gyaz_hpb.projection_groups.remove (index)
            
        return {'FINISHED'}
 
    
class Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_set_all_projection_groups_active"  
    bl_label = "GYAZ Handplane Bridge: Set All Projection Groups Active"
    bl_description = "Set all projection groups active/inactive. Only active groups are exported"
    bl_options = {'REGISTER', 'UNDO'}
    
    active = BoolProperty (default=False)
    
    #operator function
    def execute(self, context):
        scene = bpy.context.scene
        
        for pgroup in scene.gyaz_hpb.projection_groups:
            pgroup.active = self.active
            
        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_MoveProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_move_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Move Projection Group"
    bl_description = "Move projection group"
    bl_options = {'REGISTER', 'UNDO'}
    
    index = IntProperty (default=0)
    up = BoolProperty (default=True)
    
    #operator function
    def execute(self, context):
        index = self.index
        up = self.up
        scene = bpy.context.scene
        pgroups = scene.gyaz_hpb.projection_groups
        block = 1 if up else -1
        
        if index < len (pgroups) + block:        
            target_index = index-1 if up else index+1
            # reorder collection
            pgroups.move (index, target_index)
            
        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_AddModelItem (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_add_model_item"  
    bl_label = "GYAZ Handplane Bridge: Add High Poly Item"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    type = EnumProperty ( items= ( ('HIGH_POLY', '', ''), ('LOW_POLY', '', '') ) )
    projection_group_index = IntProperty (default=0)
    remove = BoolProperty (default=False)
    model_index = IntProperty (default=0)
    
    #operator function
    def execute(self, context):
        type = self.type
        projection_group_index = self.projection_group_index
        remove = self.remove
        model_index = self.model_index     
        scene = bpy.context.scene
        
        if remove == False:
            if type == 'HIGH_POLY':
                item = scene.gyaz_hpb.projection_groups[projection_group_index].high_poly.add ()
            elif type == 'LOW_POLY':
                item = scene.gyaz_hpb.projection_groups[projection_group_index].low_poly.add ()
                
        else:
            if type == 'HIGH_POLY':
                scene.gyaz_hpb.projection_groups[projection_group_index].high_poly.remove (model_index)
            elif type == 'LOW_POLY':
                scene.gyaz_hpb.projection_groups[projection_group_index].low_poly.remove (model_index)
            
        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_AssignActiveObject (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_assign_active_object"  
    bl_label = "GYAZ Handplane Bridge: Assign Active Object"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    type = EnumProperty ( items=( ('HIGH_POLY', '', ''), ('LOW_POLY', '', ''), ('CAGE', '', '') ) )
    projection_group_index = IntProperty (default=0)
    model_index = IntProperty (default=0)
    
    #operator function
    def execute(self, context):
        import bpy
        if bpy.context.active_object != None:
            type = self.type
            projection_group_index = self.projection_group_index
            model_index = self.model_index   
            scene = bpy.context.scene
            ao = bpy.context.active_object.name
            
            if type == 'HIGH_POLY':
                scene.gyaz_hpb.projection_groups[projection_group_index].high_poly[model_index].name = ao
            elif type == 'LOW_POLY':
                scene.gyaz_hpb.projection_groups[projection_group_index].low_poly[model_index].name = ao
            elif type == 'CAGE':
                scene.gyaz_hpb.projection_groups[projection_group_index].low_poly[model_index].cage_name = ao
            
        return {'FINISHED'}
    

class Op_GYAZ_HandplaneBridge_ExportToHandPlane (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_export_to_handplane"  
    bl_label = "GYAZ Handplane Bridge: Export To Hand Plane Baker"
    bl_description = "Export to Handplane Baker"
    bl_options = {'REGISTER', 'UNDO'}
    
    #operator function
    def execute(self, context):
        
        #report
        def report (self, text, type):
            #types: 'INFO', 'WARNING', 'ERROR'
            self.report({type}, text)
        
        def main ():
        
            import os
            scene = bpy.context.scene
            prefs = bpy.context.user_preferences.addons[__package__].preferences
            
            mesh_format = 'fbx'
            
            
            #FBX EXPORTER SETTINGS:
            #MAIN
            version = 'BIN7400'
            use_selection = True
            global_scale = 1
            apply_unit_scale = False
            apply_scale_options = 'FBX_SCALE_NONE'
            axis_forward = '-Z'
            axis_up = 'Y'
            object_types = {'EMPTY', 'MESH', 'OTHER', 'ARMATURE'}
            bake_space_transform = False
            use_custom_props = False
            path_mode = 'ABSOLUTE'
            batch_mode = 'OFF'
            #GEOMETRIES
            use_mesh_modifiers = True
            use_mesh_modifiers_render = True
            mesh_smooth_type = 'FACE'
            use_mesh_edges = False
            use_tspace = True
            #ARMATURES
            use_armature_deform_only = False
            add_leaf_bones = False
            primary_bone_axis = '-Y'
            secondary_bone_axis = 'X'
            armature_nodetype = 'NULL'
            #ANIMATION
            bake_anim = False
            bake_anim_use_all_bones = False
            bake_anim_use_nla_strips = False
            bake_anim_use_all_actions = False
            bake_anim_force_startend_keying = False
            bake_anim_step = 1
            bake_anim_simplify_factor = 1
            
            
            #make all layers visible (to make sure that every object gets exported)
            original_visible_layers = []
            for n in range (0, 20):
                if scene.layers[n] == True:
                    original_visible_layers.append (n)
                else:
                    scene.layers[n] = True
            
            
            #get export folder
            output_folder_mode = scene.gyaz_hpb.output_folder_mode
            relative_folder_name = scene.gyaz_hpb.relative_folder_name
            custom_output_folder = scene.gyaz_hpb.custom_output_folder
            file_name = scene.gyaz_hpb.file_name
            
            if output_folder_mode == 'RELATIVE_FOLDER':
                root_folder = '//' + relative_folder_name + '/' + file_name
            else:
                root_folder = custom_output_folder + '/' + file_name
            
            #make sure root folder exists
            root_folder = os.path.abspath ( bpy.path.abspath (root_folder) )
            os.makedirs(root_folder, exist_ok=True)
            #get project-file path    
            project_file_path = root_folder + '/' + file_name + '.HPB'
            project_file_path = os.path.abspath ( bpy.path.abspath (project_file_path) )
            #save last written project file
            setattr (scene.gyaz_hpb, 'last_output_path', project_file_path)

       
            #export folder
            export_folder = root_folder + '\meshes'
            export_folder = os.path.abspath ( bpy.path.abspath (export_folder) )
            #create export folder
            os.makedirs(export_folder, exist_ok=True) 
            
            #make all layers visible                   
            def export_obj (obj_name, type):
                #type options:'HP', 'LP', 'C'
                if scene.objects.get (obj_name) != None:
                    obj = scene.objects[obj_name]
                    select_only_object (obj)
                    #clear transforms
                    if scene.gyaz_hpb.clear_transforms == True:
                        clear_transformation (obj, loc=True, rot=True, scale=True)
                    #make sure objects are visible and selectable
                    obj.hide_select = False
                    #select object
                    obj.select = True
                    #export path
                    mesh_filepath = export_folder + '/' + obj.name + '.' + mesh_format
                    mesh_filepath = os.path.abspath ( bpy.path.abspath (mesh_filepath) )
                    #export
                    use_tspace = False if type == 'HP' else True
                    
                    bpy.ops.export_scene.fbx ( filepath=mesh_filepath, version=version, use_selection=use_selection, global_scale=global_scale, apply_unit_scale=apply_unit_scale, apply_scale_options=apply_scale_options, axis_forward=axis_forward, axis_up=axis_up, object_types=object_types, bake_space_transform=bake_space_transform, use_custom_props=use_custom_props, path_mode=path_mode, batch_mode=batch_mode, use_mesh_modifiers=use_mesh_modifiers, use_mesh_modifiers_render=use_mesh_modifiers_render, mesh_smooth_type=mesh_smooth_type, use_mesh_edges=use_mesh_edges, use_tspace=use_tspace, use_armature_deform_only=use_armature_deform_only, add_leaf_bones=add_leaf_bones, primary_bone_axis=primary_bone_axis, secondary_bone_axis=secondary_bone_axis, armature_nodetype=armature_nodetype, bake_anim=bake_anim, bake_anim_use_all_bones=bake_anim_use_all_bones, bake_anim_use_nla_strips=bake_anim_use_nla_strips, bake_anim_use_all_actions=bake_anim_use_all_actions, bake_anim_force_startend_keying=bake_anim_force_startend_keying, bake_anim_step=bake_anim_step, bake_anim_simplify_factor=bake_anim_simplify_factor )
                    return mesh_filepath
            
            #export mesh and save filepath (for writing path into .HPB file)
            pgroups = scene.gyaz_hpb.projection_groups
            for pgroup in pgroups:
                
                if pgroup.active == True:
                
                    #high poly
                    if scene.gyaz_hpb.export_hp == True:
                        for item in pgroup.high_poly:
                            setattr ( item, 'model', '""' )
                            if scene.objects.get (item.name) != None:
                                path = '"' + export_obj (item.name, 'HP') + '"'
                                setattr ( item, 'model', path )
                    
                    #low poly, cage
                    if scene.gyaz_hpb.export_lp == True:
                        for item in pgroup.low_poly:
                            setattr ( item, 'model', '""')
                            if scene.objects.get (item.name) != None:
                                path =  '"' + export_obj (item.name, 'LP') + '"'
                                setattr ( item, 'model', path)
                            setattr ( item, 'cageModel', '""')
                            if scene.objects.get (item.cage_name) != None:
                                path = '"' + export_obj (item.cage_name, 'C') + '"'
                                setattr ( item, 'cageModel', path )
            
            
            #set extention and bit depth
            prop = scene.gyaz_hpb.output_settings.texture_format
            if prop.startswith ('TIF'):
                texture_format = 'tif'
            elif prop.startswith ('PNG'):
                texture_format = 'png'
            elif prop.startswith ('PSD'):
                texture_format = 'psd'
            elif prop.startswith ('TGA'):
                texture_format = 'tga'
                
            if prop.endswith ('8'):
                bit_depth = 8
            elif prop.endswith ('16'):
                bit_depth = 16
            
            
            path = os.path.abspath ( bpy.path.abspath (root_folder + '/textures') )
            os.makedirs(path, exist_ok=True)     
            #set output props
            setattr (scene.gyaz_hpb.output_settings, 'outputFolder', '"' + path + '"')
            setattr (scene.gyaz_hpb.output_settings, 'outputFilename', scene.gyaz_hpb.file_name)
            setattr (scene.gyaz_hpb.output_settings, 'outputExtension', texture_format)
            setattr (scene.gyaz_hpb.output_settings, 'outputBitDepth', bit_depth)


            #########################################################################
            #write Handplane project file (.HPB)
            #########################################################################

            
            p1 = 'BakerConfiguration bakeConfig'+'\n{'+'\n\t'+'int32 version = 1;'+'\n\t'+'ProjectionGroup groups'+'\n'
            
            open_groups = '\t'+'['+'\n'
            close_groups = '\t'+']'+'\n'

            group_start = '\t\t'+'{'+'\n'
            group_end = '\t\t'+'}'+'\n'
            
            def group_name (name):
                return '\t\t\t'+'String name = "'+name+'";'+'\n'

            high_poly_title = '\t\t\t'+'HighPolyModelConfiguration highModels'+'\n'
            low_poly_title = '\t\t\t'+'LowPolyModelConfiguration lowModels'+'\n'

            models_start = '\t\t\t'+'['+'\n'
            models_end = '\t\t\t'+']'+'\n'

            item_start = '\t\t\t\t'+'{'+'\n'
            item_end = '\t\t\t\t'+'}'+'\n'
            
            end = '}'


            def write_prop (owner, name, tabs, type, name_override):
                value = getattr (owner, name)
                               
                l = ''
                for n in range (0, tabs+1):
                    l += '\t'
                l += type + ' '
                if name_override == False or name_override == None or name_override == '':
                    l += name + ' = '
                else:
                    l += name_override + ' = '
                
                if type == 'bool':
                    l += str.lower ( str(value) )
                elif type == 'String':
                    l += '"'+str(value)+'"'
                else:
                    l += str (value)
                
                l += ';' + '\n'
                return l
            
            
            def write_tangent_space_enum (tabs):
                type = 'String'
                name = 'tangentSpace'
                value = getattr (scene.gyaz_hpb.bake_settings, 'tangentSpace')
                
                if value == 'UNREAL_4':
                    string = '"Unreal Engine 4"'
                elif value == 'UNREAL_3':
                    string = '"Unreal Engine 3"'
                elif value == 'UNITY_5_3':
                    string = '"Unity 5.3"'
                elif value == 'UNITY':
                    string = '"Unity"'
                elif value == 'Source_2':
                    string = '"Source 2 Engine"'
                elif value == 'Source':
                    string = '"Source Engine"'
                elif value == 'MAYA_2013_2014':
                    string = '"Autodesk Maya 2013/2014"'
                elif value == 'MAYA_2012':
                    string = '"Maya 2012"'
                elif value == '3DMAX':
                    string = '"Autodesk 3DS MAX"'
                elif value == 'STARCRAFT_II':
                    string = '"Starcraft II"'
                elif value == 'INPUT_TANGENT_AND_BINORMAL':
                    string = '"Input Tangent and Binormal"'
                elif value == 'INPUT_TANGENT_WITH_COMPUTED_BINORMAL':
                    string = '"Input Tangent with Computed Binormal"'
                    
                l = ''
                for n in range (0, tabs+1):
                    l += '\t'
                l += type + ' '
                l += name + ' = '
                l += string
                l += ';' + '\n'
                return l
                    

            def write_prop_group (prop_owner, props, tabs):
                l = ''
                for prop in props:
                    prop_name = prop[0]
                    type = prop[1]
                    l += write_prop (owner=prop_owner, name=prop_name, tabs=tabs, type=type, name_override=None)
                return l
            
            
            #mesh props       
            def high_poly_props (prop_owner):
                return write_prop_group (prop_owner=prop_owner, props = [['model', 'Filename'], ['overrideMaterial', 'bool'], ['material', 'int32'], ['isFloater', 'bool']], tabs = 4)
            
            def low_poly_props (prop_owner):
                return write_prop_group (prop_owner=prop_owner, props = [['model', 'Filename'], ['cageModel', 'Filename'], ['overrideCageOffset', 'bool'], ['autoCageOffset', 'float']], tabs = 4)
            
            def misc_props (prop_owner):    
                return write_prop_group (prop_owner=prop_owner, props = [['material', 'int32'], ['isolateAO', 'bool'], ['autoCageOffset', 'float']], tabs = 2)


            #global settings
            def gloabal_settings (prop_owner):
                return write_prop_group (prop_owner=prop_owner, props = [['threadCount', 'int32'], ['backRayOffsetScale', 'float'], ['downsampleInGeneratorSpace', 'bool'], ['buildSmoothedNormalsForHighRes', 'bool'], ['suppressTriangulationWarning', 'bool']], tabs=0)
            
            def bake_settings (prop_owner):
                props = [
                    ['aoSampleRadius', 'float'], 
                    ['aoSampleCount', 'int32'],
                    ['thicknessSampleRadius', 'float'], 
                    ['thicknessSampleCount', 'int32'],
                    ['volumetricGradientCubeFit', 'bool'],
                    ['heightMapScale', 'float'],
                    ['heightMapOffset', 'float'],
                    ['curvatureUseRaySampling', 'bool'],
                    ['curvatureSampleRadius', 'float'],
                    ['curvatureSampleCount', 'int32'],
                    ['curvaturePixelRadius', 'int32'],
                    ['curvatureAutoNormalize', 'bool'],
                    ['curvatureMaxAngle', 'float'],
                    ['curvatureOutputGamma', 'float'],
                    ['cavitySensitivity', 'float'],
                    ['cavityBias', 'float'],
                    ['cavityPixelRadius', 'int32'],
                    ['cavityOutputGamma', 'float'],
                    ['cavityKernelType', 'KernelType'],
                    ['textureSpaceAOPixelRadius', 'int32'],
                    ['textureSpaceAOOutputGamma', 'float'],
                    ['textureSpaceAOSampleCoveragePercentage', 'float'],
                    ]
                
                return write_prop_group (prop_owner=prop_owner, props=props, tabs=0)
            
            #material library
            def material_library ():
                matlib_title = '\tMaterialLibrary materialLibrary\n'
                matlib_start = '\t{\n'
                mat_channels = '\t\tString channelNames\n'+'\t\t[\n'+'\t\t\t"_",\n'+'\t\t\t"_",\n'+'\t\t\t"_"\n'+'\t\t]\n'
                mat_config_title = '\t\tMaterialConfiguration materials\n'
                mat_config_start = '\t\t[\n'
                def mat (color, name):
                    return '\t\t\t{\n'+'\t\t\t\tString name = "'+name+'";\n'+'\t\t\t\tColor matIDColor = '+color+';\n'+'\t\t\t\tColor channelColors\n'+'\t\t\t\t[\n'+'\t\t\t\t\t0xFF000000, \n'+'\t\t\t\t\t0xFF000000, \n'+'\t\t\t\t\t0xFF000000\n'+'\t\t\t\t]\n'+'\t\t\t}\n'
                materials = mat ('0xFF000000', '0') + mat ('0xFFFF0000', '1') + mat ('0xFF00FF00', '2') + mat ('0xFF0000FF', '3')
                mat_config_end = '\t\t]\n'
                matlib_end = '\t}\n'
                
                return matlib_title + matlib_start + mat_channels + mat_config_title + mat_config_start + materials + mat_config_end + matlib_end

            #output settings
            def output_settings (prop_owner):
                return write_prop_group (prop_owner=prop_owner, props = [['outputFolder', 'Filename'], ['outputFilename', 'String'], ['outputExtension', 'String'], ['outputBitDepth', 'ImageBitDepth'], ['outputWidth', 'int32'], ['outputHeight', 'int32'], ['outputPadding', 'int32'], ['outputSuperSample', 'int32'], ['outputDither', 'bool']], tabs=0)
            
            #image output
            def image_outputs ():
                start = '\tImageOutput outputs\n'+'\t[\n'
                l = ''
                for item in scene.gyaz_hpb.maps:
                    l += '\t\t{\n'
                    
                    prop_name = item.is_enabled_prop_name
                    l += write_prop (owner=scene.gyaz_hpb.bake_settings, name=prop_name, tabs=3, type='bool', name_override='isEnabled')
                    
                    l += write_prop (owner=item, name='filenameSuffix', tabs=3, type='String', name_override=None)
                    l += '\t\t}\n'
                end = '\t]\n'
                return start + l + end

                
            import os

            # Write data out (2 integers)
            with open (project_file_path, "w") as file:
                file.write (p1)
                
                #projection groups
                file.write (open_groups)
                
                for pgroup in pgroups:
                    if pgroup.active == True:
                        file.write (group_start)
                        file.write (group_name (pgroup.name))
                        #high poly
                        file.write (high_poly_title)
                        file.write (models_start)
                        
                        models = pgroup.high_poly
                        for model in models:
                            file.write (item_start)
                            file.write (high_poly_props (model) )
                            file.write (item_end)
                        file.write (models_end)
         
                        #low poly               
                        file.write (low_poly_title)
                        file.write (models_start)
                        
                        models = pgroup.low_poly
                        for model in models:
                            file.write (item_start)
                            file.write (low_poly_props (model) )
                            file.write (item_end)
                        file.write (models_end)
                        
                        #misc
                        file.write (misc_props (pgroup))
                        
                        file.write (group_end)
                    
                file.write (close_groups)
                
                file.write (bake_settings (scene.gyaz_hpb.bake_settings))
                file.write (gloabal_settings (scene.gyaz_hpb.global_settings))
                
                file.write (material_library ())
                
                file.write (output_settings (scene.gyaz_hpb.output_settings))
                
                file.write (image_outputs ())
                
                file.write (write_tangent_space_enum (tabs=0))
                 
                file.write (end)
                
                
            #restore original visible layers
            for n in range (0, 20):
                if n in original_visible_layers:
                    scene.layers[n] = True
                else:
                    scene.layers[n] = False
                    

            #start handplane
            handplane_path = prefs.handplane_path
            handplane_path = os.path.abspath ( bpy.path.abspath (handplane_path) )
            subprocess.Popen (handplane_path)
            
            #open explorer and select handplane file 
            subprocess.Popen (r'explorer /select,' + project_file_path)
            
        ##############################################
        #SAFETY CHECKS
        ##############################################
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        scene = bpy.context.scene
        
        
        #check if file has ever been saved
        blend_data = bpy.context.blend_data
        if blend_data.is_saved == False:      
            report (self, 'File has never been saved.', 'WARNING')
            
        else:
            
            #check file name
            fn = scene.gyaz_hpb.file_name
            if  fn == '' or fn == ' ' or ',' in fn:
                report (self, 'Invalid export file name.', 'WARNING')
                
            else:
                             
        
                #handplane path
                handplane_path = prefs.handplane_path
                if handplane_path == '' or handplane_path == ' ':
                    report (self, 'Handplane path is not set in user preferences.', 'WARNING')
                
                else:
                    
                    # no active projection group warning
                    active_pgroups = list( filter( lambda pgroup: pgroup.active, scene.gyaz_hpb.projection_groups) )
                    if len (active_pgroups) == 0:
                        report (self, 'No active projection groups.', 'INFO')
                    
                    else:
                        
                        # check for missing and unset objects:
                        groups_with_unset_objects = []
                        groups_with_missing_objects = []
                        for pgroup_index, pgroup in enumerate (scene.gyaz_hpb.projection_groups):
                            if pgroup.active == True:
                                high_poly_names = [high_poly_item.name for high_poly_item in pgroup.high_poly]
                                low_poly_names = [low_poly_item.name for low_poly_item in pgroup.low_poly]
                                cage_names = [low_poly_item.cage_name for low_poly_item in pgroup.low_poly]
                                
                                # get unset objects (cage can be unset, high and low can't)
                                unset_objects = []
                                missing_objects = []
                                for obj_name in high_poly_names + low_poly_names:
                                    if obj_name == '':
                                        unset_objects.append (True)
                                    elif scene.objects.get (obj_name) == None:
                                        missing_objects.append (obj_name)
                                for obj_name in cage_names:
                                    if obj_name != '':
                                        if scene.objects.get (obj_name) == None:
                                            missing_objects.append (obj_name)
                                        
                                # result
                                if len (unset_objects) > 0:
                                    groups_with_unset_objects.append (pgroup.name+'('+str(pgroup_index)+')')
                                if len (missing_objects) > 0:
                                    groups_with_missing_objects.append (pgroup.name+'('+str(pgroup_index)+')')
                                    
                        if len (groups_with_unset_objects) > 0 or len (groups_with_missing_objects) > 0:
                            warning_lines = []
                            if len (groups_with_unset_objects) > 0:
                                warning_lines.append ("Groups with unset objects: "+list_to_visual_list(groups_with_unset_objects))
                            if len (groups_with_missing_objects) > 0:
                                warning_lines.append ("Groups with missing objects: "+list_to_visual_list(groups_with_missing_objects))
                            
                            # print warning
                            popup (lines=warning_lines, icon='INFO', title='Projection Group Warning')
                            for line in warning_lines:
                                print (line)
                    
                        else:
                            
                            # mesh checks
                            #get lists of objects to export
                            hp_objs = []
                            lp_objs = []
                            c_objs = []
                            projection_groups = scene.gyaz_hpb.projection_groups
                            for group in projection_groups:
                                for item in group.high_poly:
                                    if scene.objects.get (item.name) != None:
                                        hp_objs.append (item.name)
                                for item in group.low_poly:
                                    if scene.objects.get (item.name) != None:
                                        lp_objs.append (item.name)
                                    if scene.objects.get (item.cage_name) != None:
                                        c_objs.append (item.cage_name)
                                        
                            
                            #low poly, cage
                            quads_allowed = scene.gyaz_hpb.global_settings.suppressTriangulationWarning
                            max_verts_per_face = 4 if quads_allowed == True else 3
                            lp_c_objs_with_bad_polygons = []     
                            lp_objs_with_no_uvs = []
                            for obj_name in lp_objs + c_objs:
                                #face check
                                obj = scene.objects[obj_name]
                                faces = obj.data.polygons
                                bad_polygons = list ( filter ( lambda x: len(x.vertices)>max_verts_per_face, faces ) )
                                bad_polygon_count = len (bad_polygons)
                                if bad_polygon_count > 0:
                                    lp_c_objs_with_bad_polygons.append (obj_name)
                                #uv check
                                uv_maps = obj.data.uv_textures
                                if len (uv_maps) < 1:
                                    if obj_name in lp_objs:
                                        lp_objs_with_no_uvs.append (obj.name)
                                    
                            
                            if len (lp_c_objs_with_bad_polygons) == 0 and len (lp_objs_with_no_uvs) == 0:
                                good_to_go = True
                            else:
                                good_to_go = False
                                
                            if good_to_go == False:
                                
                                warning_lines = []
                                
                                #warnings
                                lp_no_uv_map_warning = 'no uv maps in: '
                                
                                if quads_allowed == False:
                                    lp_c_polygon_warning = 'quads or ngons found in: '
                                else:
                                    lp_c_polygon_warning = 'ngons found in: '
                                
                                    
                                if len (lp_c_objs_with_bad_polygons) > 0:
                                    line = lp_c_polygon_warning + list_to_visual_list (lp_c_objs_with_bad_polygons)
                                    warning_lines.append (line)
                                    
                                if len (lp_objs_with_no_uvs) > 0:
                                    line = lp_no_uv_map_warning + list_to_visual_list (lp_objs_with_no_uvs)
                                    warning_lines.append (line)
                                    
                                # print warning
                                popup (lines=warning_lines, icon='INFO', title='Mesh Warning')
                                for line in warning_lines:
                                    print (line)
                            
                            else:

                                main ()
                    
                
            
        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_OpenLastOutput (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_open_last_output"  
    bl_label = "GYAZ Handplane Bridge: Open Last Output"
    bl_description = ""
    
    info = BoolProperty (default=False)
    
    #operator function
    def execute(self, context):
        info = self.info
        scene = bpy.context.scene
        last_output = scene.gyaz_hpb.last_output_path
        last_output = os.path.abspath ( bpy.path.abspath (last_output) )
        
        if info == False:
            subprocess.Popen (r'explorer /select,' + last_output)
        else:
            popup (lines=[last_output], icon='INFO', title='Last export:')

        return {'FINISHED'}


class UI_GYAZ_HandplaneBridge_InitGlobalProps (Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_label = 'Handplane Bridge'  
    
    #add ui elements here
    def draw (self, context):
        
        scene = bpy.context.scene        
        layout = self.layout
        layout.operator (Op_GYAZ_HandplaneBridge_InitGlobalProps.bl_idname, 'Initialize')
        

    #when the buttons should show up    
    @classmethod
    def poll(cls, context):
        scene = bpy.context.scene
        return hasattr (scene, 'gyaz_hpb') == False


class UI_GYAZ_HandplaneBridge (Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_label = 'Handplane Bridge'    
    
    #add ui elements here
    def draw (self, context):
        
        scene = bpy.context.scene
        prefs = bpy.context.user_preferences.addons[__package__].preferences        
        layout = self.layout
        layout.row ().prop (scene.gyaz_hpb, 'menu', expand=True)
        
        if scene.gyaz_hpb.menu == 'GROUPS':
            layout.label ('Projection Groups:')
            row = layout.row (align=True)
            row.scale_x = 2
            row.separator ()
            row.operator (Op_GYAZ_HandplaneBridge_AddProjectionGroup.bl_idname, text='', icon='ZOOMIN').clear=False
            row.operator (Op_GYAZ_HandplaneBridge_AddProjectionGroup.bl_idname, text='', icon='X').clear=True
            row.separator ()
            row.operator (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive.bl_idname, text='All Active').active=True
            row.operator (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive.bl_idname, text='All Inactive').active=False
                
            for group_index, group_item in enumerate(scene.gyaz_hpb.projection_groups):
                enabled = True if group_item.active == True else False
                box = layout.box()  
                row = box.row (align=True)
                row.prop (group_item, 'active', text='')
                row.separator ()
                row.prop (group_item, 'name', text='')
                row.separator ()
                move = row.operator (Op_GYAZ_HandplaneBridge_MoveProjectionGroup.bl_idname, text='', icon='TRIA_UP')
                move.up = True
                move.index = group_index
                move = row.operator (Op_GYAZ_HandplaneBridge_MoveProjectionGroup.bl_idname, text='', icon='TRIA_DOWN')
                move.up = False
                move.index = group_index
                row.separator ()               
                row.operator (Op_GYAZ_HandplaneBridge_RemoveProjectionGroup.bl_idname, text='', icon='X').projection_group_index=group_index                
                
                if enabled == True:
                    
                    row = box.row (align=True)
                    row.prop (group_item, 'autoCageOffset')
                    row.prop (group_item, 'isolateAO', toggle=True)
                    
                    row = box.row ()
                    
                    operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ZOOMIN')
                    operator_props.type = 'HIGH_POLY'
                    operator_props.projection_group_index = group_index
                    operator_props.remove = False
                    
                    row.label ('High Poly Models:')
                    
                    for hp_index, hp_item in enumerate(group_item.high_poly):
                        row = box.row (align=True)
                        row.prop_search (hp_item, 'name', scene, "objects", icon='MESH_CUBE')
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AssignActiveObject.bl_idname, text='', icon='EYEDROPPER')
                        operator_props.type = 'HIGH_POLY'
                        operator_props.projection_group_index = group_index
                        operator_props.model_index = hp_index
                        
                        row.separator ()
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ZOOMOUT')
                        operator_props.type = 'HIGH_POLY'
                        operator_props.projection_group_index = group_index
                        operator_props.remove = True
                        operator_props.model_index = hp_index
                        
                        row = box.row (align=True)
                        row.label (icon='BLANK1')
                        row.prop (hp_item, 'isFloater', toggle=True)
                        row.prop (hp_item, 'material')


                    row = box.row ()
                    
                    operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ZOOMIN')
                    operator_props.type = 'LOW_POLY'
                    operator_props.projection_group_index = group_index
                    operator_props.remove = False
                    
                    row.label ('Low Poly Models:')
                    for lp_index, lp_item in enumerate(group_item.low_poly):
                        row = box.row (align=True)
                        
                        row.prop_search (lp_item, 'name', scene, "objects")
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AssignActiveObject.bl_idname, text='', icon='EYEDROPPER')
                        operator_props.type = 'LOW_POLY'
                        operator_props.projection_group_index = group_index
                        operator_props.model_index = lp_index
                        
                        row.separator ()
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ZOOMOUT')
                        operator_props.type = 'LOW_POLY'
                        operator_props.projection_group_index = group_index
                        operator_props.remove = True
                        operator_props.model_index = lp_index
                        
                        row = box.row (align=True)
                        row.label (icon='BLANK1')
                        row.prop_search (lp_item, 'cage_name', scene, "objects", icon='LATTICE_DATA')
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AssignActiveObject.bl_idname, text='', icon='EYEDROPPER')
                        operator_props.type = 'CAGE'
                        operator_props.projection_group_index = group_index
                        operator_props.model_index = lp_index
                        
                        row.prop (lp_item, 'overrideCageOffset', text='', icon='LINE_DATA')             
                        
                        if lp_item.overrideCageOffset == True:
                            row = box.row ()
                            row.label (icon='BLANK1')
                            row.prop (lp_item, 'autoCageOffset')
                            
                    col = layout.column ()
                    col = layout.column ()
                    col = layout.column ()
         
        
        elif scene.gyaz_hpb.menu == 'SETTINGS':

            row = layout.row (align=True)
            row.prop (prefs, 'active_preset_name')
            row.operator (Op_GYAZ_HandplaneBridge_SavePreset.bl_idname, text='', icon='ZOOMIN')
            row.operator (Op_GYAZ_HandplaneBridge_RemovePreset.bl_idname, text='', icon='ZOOMOUT')
            
            box = layout.box ()
            box.label ('Output:')
            row = box.row (align=True)
            row.prop (scene.gyaz_hpb.output_settings, 'outputWidth', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'outputHeight', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'texture_format', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'outputSuperSample', text='')
            row = box.row ()
            row.prop (scene.gyaz_hpb.output_settings, 'outputPadding')
            row.prop (scene.gyaz_hpb.output_settings, 'outputDither')
            
            box = layout.box ()
            box.label ('Maps:')
            for index, item in enumerate (scene.gyaz_hpb.maps):
                row = box.row ()
                row.prop (scene.gyaz_hpb.bake_settings, item.is_enabled_prop_name, text=item.name, toggle=True)
                if item.has_props == True:
                    icon='TRIA_UP' if item.show_props == True else 'TRIA_DOWN'        
                    row.prop (item, 'show_props', text='', icon=icon)
                    
                    if item.show_props == True:
                        for prop in item.props:
                            row = box.row ()
                            row.label (icon='BLANK1')
                            row.prop (scene.gyaz_hpb.bake_settings, prop.name) if index != 0 else row.prop (scene.gyaz_hpb.bake_settings, prop.name, text='')     
                
            box = layout.box ()
            box.label ('Global Settings:')
            box.prop (scene.gyaz_hpb.global_settings, 'threadCount')    
            box.prop (scene.gyaz_hpb.global_settings, 'backRayOffsetScale')    
            box.prop (scene.gyaz_hpb.global_settings, 'downsampleInGeneratorSpace')    
            box.prop (scene.gyaz_hpb.global_settings, 'buildSmoothedNormalsForHighRes')    
            box.prop (scene.gyaz_hpb.global_settings, 'suppressTriangulationWarning')    

                       
        elif scene.gyaz_hpb.menu == 'EXPORT':
            
            box = layout.box ()
            box.label ('Destination:')
            row = box.row ().prop (scene.gyaz_hpb, 'output_folder_mode', expand=True)
            if scene.gyaz_hpb.output_folder_mode == 'RELATIVE_FOLDER':
                box.prop (scene.gyaz_hpb, 'relative_folder_name')
            else:
                box.prop (scene.gyaz_hpb, 'custom_output_folder')
            box.prop (scene.gyaz_hpb, 'file_name')                               
            
            box = layout.box ()
            box.prop (scene.gyaz_hpb, 'clear_transforms')
            row = box.row ()
            row.prop (scene.gyaz_hpb, 'export_hp')
            row.prop (scene.gyaz_hpb, 'export_lp')
            row = box.row (align=True)
            row.scale_y = 2       
            row.operator (Op_GYAZ_HandplaneBridge_ExportToHandPlane.bl_idname, text='GO TO HANDPLANE', icon_value=custom_icons['handplane'].icon_id)
            row = box.row (align=True)
            row.operator (Op_GYAZ_HandplaneBridge_OpenLastOutput.bl_idname, text='Open Last Export', icon='VIEWZOOM').info=False
            row.operator (Op_GYAZ_HandplaneBridge_OpenLastOutput.bl_idname, text='', icon='INFO').info=True
        
                    

    #when the buttons should show up    
    @classmethod
    def poll(cls, context):
        scene = bpy.context.scene
        return hasattr (scene, 'gyaz_hpb') == True


#######################################################
#######################################################

#REGISTER

def register():
    
    # custom icons
    custom_icon_names = ['handplane', 'highpoly']
    
    global custom_icons
    custom_icons = bpy.utils.previews.new ()
    icons_dir = os.path.join ( os.path.dirname (__file__), "icons" )
    for icon_name in custom_icon_names:
        custom_icons.load ( icon_name, os.path.join (icons_dir, icon_name+'.png'), 'IMAGE' )
    # referencing icons:
    # icon_value = custom_icons["custom_icon"].icon_id    
    
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_InitGlobalProps)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_SavePreset)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_RemovePreset)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AddProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_RemoveProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_MoveProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AddModelItem)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AssignActiveObject)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_ExportToHandPlane)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_OpenLastOutput)
    bpy.utils.register_class (UI_GYAZ_HandplaneBridge_InitGlobalProps)
    bpy.utils.register_class (UI_GYAZ_HandplaneBridge)
   

def unregister ():
    
    # custom icons
    global custom_icons
    bpy.utils.previews.remove (custom_icons)
    
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_InitGlobalProps)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_SavePreset)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_RemovePreset)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AddProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_RemoveProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_MoveProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AddModelItem)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AssignActiveObject)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_ExportToHandPlane)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_OpenLastOutput)
    bpy.utils.unregister_class (UI_GYAZ_HandplaneBridge_InitGlobalProps)
    bpy.utils.unregister_class (UI_GYAZ_HandplaneBridge)

  
if __name__ == "__main__":   
    register()              