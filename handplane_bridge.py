# ##### BEGIN GPL LICENSE BLOCK #####
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

maps = ['normal_ts', 'normal_os', 'ao', 'ao_floaters', 'vert_color', 'mat_psd', 'mat_id', 'curve', 'vol_gradient', 'cavity', 'height', 'tsao', 'thickness']                                   

bake_settings_list = ['aoSampleRadius', 'aoSampleCount', 'volumetricGradientCubeFit', 'thicknessSampleRadius', 'thicknessSampleCount', 'heightMapScale', 'heightMapOffset', 'curvatureUseRaySampling', 'curvatureUseRaySampling', 'curvatureSampleRadius', 'curvatureSampleCount', 'curvaturePixelRadius', 'curvatureAutoNormalize', 'curvatureMaxAngle', 'curvatureOutputGamma', 'cavitySensitivity', 'cavityBias', 'cavityPixelRadius', 'cavityOutputGamma', 'cavityKernelType', 'textureSpaceAOPixelRadius', 'textureSpaceAOOutputGamma', 'textureSpaceAOSampleCoveragePercentage', 'tangentSpace', 'isEnabled_tangent_space_normals', 'isEnabled_object_space_normals', 'isEnabled_ambient_occlusion', 'isEnabled_ambient_occlusion_floaters', 'isEnabled_vertex_color', 'isEnabled_material_psd', 'isEnabled_material_id', 'isEnabled_curvature_map', 'isEnabled_volumetric_gradient', 'isEnabled_cavity_map', 'isEnabled_height_map', 'isEnabled_texture_space_ao', 'isEnabled_thickness']

global_settings_list = ['threadCount', 'backRayOffsetScale', 'downsampleInGeneratorSpace', 'buildSmoothedNormalsForHighRes', 'suppressTriangulationWarning', 'checkForMirroredUVs']

output_settings_list = ['outputExtension', 'outputBitDepth', 'texture_format', 'outputWidth', 'outputHeight', 'outputPadding', 'outputSuperSample', 'outputDither']


# report
def report (self, text, type):
    # types: 'INFO', 'WARNING', 'ERROR'
    self.report({type}, text)


def popup (lines, icon, title):
    def draw(self, context):
        for line in lines:
            self.layout.label(line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


# detect mirrored uvs
def detect_mirrored_uvs (bm, uv_index):
    uv_layer = bm.loops.layers.uv[uv_index]
    mirrored_face_count = 0
    for face in bm.faces:
        uvs = [tuple(loop[uv_layer].uv) for loop in face.loops]
        x_coords, y_coords = zip (*uvs)
        result = 0.5 * np.array (np.dot(x_coords, np.roll(y_coords, 1)) - np.dot(y_coords, np.roll(x_coords, 1)))
        if result > 0:
            mirrored_face_count += 1
            break
    if mirrored_face_count > 0:
        return True
    else:
        return False
    
    
def list_to_visual_list (list):
    line = ''
    for index, item in enumerate(list):
        if index > 0:
            line += ', '
        line += str(item)
    return line


def set_folder_name (self, context):
    if context.scene.gyaz_hpb.relative_folder_name.replace (" ", "") == "":
        context.scene.gyaz_hpb.relative_folder_name = ""     

 
import bpy, os, subprocess, bmesh
from bpy.types import Panel, Operator, AddonPreferences, PropertyGroup
from bpy.props import *
import bpy.utils.previews
from mathutils import Matrix
import numpy as np

#popup
def popup (lines, icon, title):
    def draw(self, context):
        for line in lines:
            self.layout.label(line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    
def clear_transformation (object):
    for c in object.constraints:
        c.mute = True
    untransformed_matrix = Matrix (([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]))
    object.matrix_world = untransformed_matrix
        
def select_only_object (object):
    scene = bpy.context.scene
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set (mode='OBJECT')        
    bpy.ops.object.select_all (action='DESELECT')
    object.select = True
    scene.objects.active = object 
    
class Op_GYAZ_HPB_OpenFolderInWindowsFileExplorer (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_open_folder_in_explorer"  
    bl_label = "GYAZ_Handplane Bridg: Open Folder in Explorer"
    bl_description = "Open folder in file explorer"
    
    path = StringProperty (default='', options={'SKIP_SAVE'})
    
    # operator function
    def execute(self, context):  
        scene = bpy.context.scene
        path = os.path.abspath ( bpy.path.abspath (self.path) )
        subprocess.Popen ('explorer "'+path+'"')
          
        return {'FINISHED'}


class GYAZ_HandplaneBridge_Preferences (AddonPreferences):
    # use __name__ with single-file addons
    # use __package__ with multi-file addons
    bl_idname = __package__
    
    def absolute_path__hand_plane_path (self, context):
        prop = getattr (self, "hand_plane_baker_path")
        new_path = os.path.abspath ( bpy.path.abspath (prop) )
        if prop.startswith ('//') == True:
            self.hand_plane_baker_path = new_path
    
    handplane_path = StringProperty (name='Handplane Baker Path', default='', subtype='DIR_PATH', update=absolute_path__hand_plane_path)
    
    #map suffixes
    ts_normals_suffix = StringProperty (name='Tangent Space Normals', default='_n')
    os_normals_suffix = StringProperty (name='Object Space Normals', default='_nws')
    ao_suffix = StringProperty (name='Ambient Occlusion', default='_ao')
    ao_floaters_suffix = StringProperty (name='Ambient Occlusion (Floaters)', default='_aof')
    vert_color_suffix = StringProperty (name='Vertex Color', default='_vcol')
    mat_psd_suffix = StringProperty (name='Material PSD', default='_mat')
    mat_id_suffix = StringProperty (name='Material ID', default='_id')
    curve_suffix = StringProperty (name='Curvature Map', default='_curve')
    vol_gradient_suffix = StringProperty (name='Volumetric Gradient', default='_vg')
    cavity_suffix = StringProperty (name='Cavity Map', default='_cav')
    height_suffix = StringProperty (name='Height Map', default='_h')
    tsao_suffix = StringProperty (name='Texture Space AO', default='_tsao')
    thickness_suffix = StringProperty (name='Thickness', default='_thick')
  
    
    #PRESETS (BakeSettings, OutputSettings, GlobalSettings
    class GYAZ_HandplaneBridge_Preset (PropertyGroup):
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
        checkForMirroredUVs = BoolProperty (default=True)
        
        #output settings
        outputExtension = StringProperty ()
        outputBitDepth = IntProperty ()
        texture_format = StringProperty ()
        outputWidth = StringProperty ()
        outputHeight = StringProperty ()
        outputPadding = IntProperty ()
        outputSuperSample = StringProperty ()
        outputDither = BoolProperty ()
        
    bpy.utils.register_class(GYAZ_HandplaneBridge_Preset)
    
    presets = CollectionProperty (type=GYAZ_HandplaneBridge_Preset)
    
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
                
            #load global settings
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
    bpy.utils.register_class (GYAZ_HandplaneBridge_Preferences)

def unregister():
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_Preferences)

register()


prefs = bpy.context.user_preferences.addons[__package__].preferences


# MAPS
class GYAZ_HPB_TangentSpaceNormalmap (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.ts_normals_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_tangent_space_normals')
    prop_names = ['tangentSpace']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_ObjectSpaceNormalmap (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.os_normals_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_object_space_normals')
    prop_names = []
    has_props = False
    show_props = BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_AmpientOcclusion (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.ao_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_ambient_occlusion')
    prop_names = ['aoSampleRadius', 'aoSampleCount']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)    
    
class GYAZ_HPB_AmpientOcclusionFloaters (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.ao_floaters_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_ambient_occlusion_floaters')
    prop_names = ['aoSampleRadius', 'aoSampleCount']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_VertexColor (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.vert_color_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_vertex_color')
    prop_names = []
    has_props = False
    show_props = BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_MaterialPSD (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.mat_psd_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_material_psd')
    prop_names = []
    has_props = False
    show_props = BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_MaterialID (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.mat_id_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_material_id')
    prop_names = []
    has_props = False
    show_props = BoolProperty (name='Show/hide settings.', default=False)
        
class GYAZ_HPB_Curvature (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.curve_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_curvature_map')
    prop_names = ['curvatureUseRaySampling', 'curvatureSampleRadius', 'curvatureSampleCount', 'curvaturePixelRadius', 'curvatureAutoNormalize', 'curvatureMaxAngle', 'curvatureOutputGamma']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)
    
class GYAZ_HPB_VolumetricGradient (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.vol_gradient_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_volumetric_gradient')
    prop_names = ['volumetricGradientCubeFit']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)    
    
class GYAZ_HPB_Cavity (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.cavity_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_cavity_map')
    prop_names = ['cavitySensitivity', 'cavityBias', 'cavityPixelRadius', 'cavityOutputGamma', 'cavityKernelType']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_Heightmap (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.height_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_height_map')
    prop_names = ['heightMapScale', 'heightMapOffset']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)
    
class GYAZ_HPB_TextureSpaceAO (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.tsao_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_texture_space_ao')
    prop_names = ['textureSpaceAOPixelRadius', 'textureSpaceAOOutputGamma']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)
    
class GYAZ_HPB_Thickness (PropertyGroup):
    filenameSuffix = StringProperty (default=prefs.thickness_suffix)
    is_enabled_prop_name = StringProperty (default='isEnabled_thickness')
    prop_names = ['thicknessSampleRadius', 'thicknessSampleCount']
    has_props = True
    show_props = BoolProperty (name='Show/hide settings.', default=False)


class GYAZ_HandplaneBridge_HighPolyItem (PropertyGroup):
    model = StringProperty (name='', default='')
    overrideMaterial = BoolProperty (name='Override material', default=True)
    material = IntProperty (name='Material ID', default=0, min=0, max=3)
    isFloater = BoolProperty (name='Is Floater', default=False, description='Is Floater?')
    name = StringProperty (name='', default='', description='High poly mesh')


class GYAZ_HandplaneBridge_LowPolyItem (PropertyGroup):
    model = StringProperty (name='', default='')
    cageModel = StringProperty (name='', default='')
    overrideCageOffset = BoolProperty (name='Override Cage Offset', default=False, description='Override Ray Offset')
    autoCageOffset = FloatProperty (name='Cage Offset', default=1)
    name = StringProperty (name='', default='', description='Low poly mesh')
    cage_name = StringProperty (name='', default='', description='Cage mesh')
    
      
class GYAZ_HandplaneBridge_ProjectionGroupItem (PropertyGroup):
    name = StringProperty (name='Name', default='Projection Group')
    active = BoolProperty (default=True, description='Only active groups are exported')
    high_poly = CollectionProperty (type=GYAZ_HandplaneBridge_HighPolyItem)
    low_poly = CollectionProperty (type=GYAZ_HandplaneBridge_LowPolyItem)
    material = IntProperty (default=0)
    isolateAO = BoolProperty (name='Isolate AO', default=False)
    autoCageOffset = FloatProperty (name='Ray Offset', default=1)
    collapsed = BoolProperty (name='', default=False)


def absolute_path__custom_output_folder (self, context):
    scene = bpy.context.scene
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
    checkForMirroredUVs = BoolProperty (name='Check for Mirrored UVs', default=True)

 
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
    
    tangentSpace = EnumProperty (
        name='Tangent Space', 
        items=(
            ('UNREAL_4', 'Unreal Engine 4', ''), 
            ('UNREAL_3', 'Unreal Engine 3', ''), 
            ('UNITY_5_3', 'Unity 5.3', ''), 
            ('UNITY', 'Unity', ''), 
            ('SOURCE', 'Source Engine', ''), 
            ('SOURCE_2', 'Source 2 Engine', ''), 
            ('MAYA_2013_14', 'Autodesk Maya 2013/14', ''), 
            ('MAYA_2012', 'Autodesk Maya 2012', ''), 
            ('3DMAX', 'Autodesk 3DS Max', ''), 
            ('STARCRAFT_II', 'Starcraft II', ''), 
            ('INPUT_TANGENT_AND_BINORMAL', 'Input Tangent and Binormal', ''), 
            ('INPUT_TANGENT_WITH_COMPUTED_BINORMAL', 'Input Tangent with Computed Binormal', '')), 
        default='UNITY_5_3')
    
    isEnabled_tangent_space_normals = BoolProperty (default=False, name='Tangent Space Normals')
    isEnabled_object_space_normals = BoolProperty (default=False, name='Object Space Normals')
    isEnabled_ambient_occlusion = BoolProperty (default=False, name='Ambient Occlusion')
    isEnabled_ambient_occlusion_floaters = BoolProperty (default=False, name='Ambient Occlusion (Floaters)')
    isEnabled_vertex_color = BoolProperty (default=False, name='Vertex Color')
    isEnabled_material_psd = BoolProperty (default=False, name='Material PSD')
    isEnabled_material_id = BoolProperty (default=False, name='Material ID')
    isEnabled_curvature_map = BoolProperty (default=False, name='Curvature Map')
    isEnabled_volumetric_gradient = BoolProperty (default=False, name='Volumetric Gradient')
    isEnabled_cavity_map = BoolProperty (default=False, name='Cavity Map')
    isEnabled_height_map = BoolProperty (default=False, name='Height Map')
    isEnabled_texture_space_ao = BoolProperty (default=False, name='Texture Space AO')
    isEnabled_thickness = BoolProperty (default=False, name='Thickness')


class GYAZ_HandplaneBridge (PropertyGroup):
    projection_groups = CollectionProperty (type=GYAZ_HandplaneBridge_ProjectionGroupItem)
    output_folder_mode = EnumProperty (name='Output Folder', items=(('RELATIVE_FOLDER', 'RELATIVE', ''),('PATH', 'PATH', '')), default='RELATIVE_FOLDER')
    relative_folder_name = StringProperty (name='Folder', default='bake', update=set_folder_name)
    custom_output_folder = StringProperty (name='', default='', subtype='DIR_PATH', update=absolute_path__custom_output_folder)
    file_name = StringProperty (name='Name', default='')
    last_output_path = StringProperty (name='Last Output', default='')
    clear_transforms = BoolProperty (name='Clear Transforms', default=False, description="Clear objects' transformation and mute constraints")
    export_hp = BoolProperty (name='High Poly', default=True, description="Export high poly object(s)")
    export_lp = BoolProperty (name='Low Poly&Cage', default=True, description="Export low poly and cage object(s)")
    global_settings = PointerProperty (type=GYAZ_HandplaneBridge_GlobalSettings)
    output_settings = PointerProperty (type=GYAZ_HandplaneBridge_OutputSettings)
    menu = EnumProperty (name='Menu', items=(('GROUPS', 'GROUPS', ''), ('SETTINGS', 'SETTINGS', ''), ('EXPORT', 'EXPORT', '')), default='GROUPS')
    bake_settings = PointerProperty (type=GYAZ_HandplaneBridge_BakeSettings)
    
    normal_ts = PointerProperty (type=GYAZ_HPB_TangentSpaceNormalmap)
    normal_os = PointerProperty (type=GYAZ_HPB_ObjectSpaceNormalmap)
    ao = PointerProperty (type=GYAZ_HPB_AmpientOcclusion)
    ao_floaters = PointerProperty (type=GYAZ_HPB_AmpientOcclusionFloaters)
    vert_color = PointerProperty (type=GYAZ_HPB_VertexColor)
    mat_psd = PointerProperty (type=GYAZ_HPB_MaterialPSD)
    mat_id = PointerProperty (type=GYAZ_HPB_MaterialID)
    curve = PointerProperty (type=GYAZ_HPB_Curvature)
    vol_gradient = PointerProperty (type=GYAZ_HPB_VolumetricGradient)
    cavity = PointerProperty (type=GYAZ_HPB_Cavity)
    height = PointerProperty (type=GYAZ_HPB_Heightmap)
    tsao = PointerProperty (type=GYAZ_HPB_TextureSpaceAO)
    thickness = PointerProperty (type=GYAZ_HPB_Thickness)


class Op_GYAZ_HandplaneBridge_SavePreset (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_save_preset"  
    bl_label = "GYAZ Handplane Bridge: Save Preset"
    bl_description = "Save preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name = StringProperty (name='preset name', default='')
    
    # popup with properties
    def invoke(self, context, event):
        wm = bpy.context.window_manager
        return wm.invoke_props_dialog(self)
    
    # operator function
    def execute(self, context):
        preset_name = self.preset_name
        scene = bpy.context.scene
        
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        
        # make sure preset name is valid
        if preset_name != '' and preset_name != ' ':
            
            # check for existing preset with the same name
            preset_names = set (preset.name for preset in prefs.presets)
            if preset_name in preset_names:
                preset = prefs.presets[preset_name]
            else:
                # add preset
                preset = prefs.presets.add ()
 
            # add preset name
            preset.name = preset_name
            
            # save bake settings
            # get scene prop value
            for prop_name in bake_settings_list:
                scene_prop_value = getattr (scene.gyaz_hpb.bake_settings, prop_name)
                
                # write scene prop value to preset
                setattr (preset, prop_name, scene_prop_value)
                
            # save global settings
            # get scene prop value
            for prop_name in global_settings_list:
                scene_prop_value = getattr (scene.gyaz_hpb.global_settings, prop_name)
                
                # write scene prop value to preset
                setattr (preset, prop_name, scene_prop_value)
                
            # save output settings
            # get scene prop value
            for prop_name in output_settings_list:
                scene_prop_value = getattr (scene.gyaz_hpb.output_settings, prop_name)
                
                # write scene prop value to preset
                setattr (preset, prop_name, scene_prop_value)
                
            # set new preset active
            setattr (prefs, 'active_preset_name', preset_name)
                
        # save user preferences
        bpy.context.area.type = 'USER_PREFERENCES'
        bpy.ops.wm.save_userpref()
        bpy.context.area.type = 'PROPERTIES'      

        return {'FINISHED'}
    

class Op_GYAZ_HandplaneBridge_RemovePreset (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_remove_preset"  
    bl_label = "GYAZ Handplane Bridge: Remove Preset"
    bl_description = "Remove preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    # operator function
    def execute(self, context):
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        active_preset_name = prefs.active_preset_name
        scene = bpy.context.scene
        
        for index, item in enumerate (prefs.presets):
            if item.name == active_preset_name:
                preset = item
        
        if 'preset' in locals():
            prefs.presets.remove (index)
            
            # set first preset active
            if len (prefs.presets) > 0:
                first_preset_name = prefs.presets[0].name
                setattr (prefs, 'active_preset_name', first_preset_name)
                
        # save user preferences
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
    
    # operator function
    def execute(self, context):
        clear = self.clear  
        scene = bpy.context.scene
        
        if clear == False:
            item = scene.gyaz_hpb.projection_groups.add ()
            item.name += ' ' + str(len(scene.gyaz_hpb.projection_groups))
        else:
            item = scene.gyaz_hpb.projection_groups.clear ()
            
        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_RemoveProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_remove_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Remove Projection Group"
    bl_description = "Remove projection group"
    bl_options = {'REGISTER', 'UNDO'}
    
    projection_group_index = IntProperty (default=0)
    
    # operator function
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
    
    # operator function
    def execute(self, context):
        scene = bpy.context.scene
        
        for pgroup in scene.gyaz_hpb.projection_groups:
            pgroup.active = self.active
            
        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_CollapseAllProjectionGroups (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_collapse_all_projection_groups"  
    bl_label = "GYAZ Handplane Bridge: Collapse All Projection Groups"
    bl_description = "Collapse/expand projection groups"
    bl_options = {'REGISTER', 'UNDO'}
    
    collapse = BoolProperty (default=False)
    
    # operator function
    def execute(self, context):
        scene = bpy.context.scene
        
        for pgroup in scene.gyaz_hpb.projection_groups:
            pgroup.collapsed = self.collapse
            
        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_MoveProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_move_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Move Projection Group"
    bl_description = "Move projection group"
    bl_options = {'REGISTER', 'UNDO'}
    
    index = IntProperty (default=0)
    up = BoolProperty (default=True)
    
    # operator function
    def execute(self, context):
        index = self.index
        up = self.up
        scene = bpy.context.scene
        pgroups = scene.gyaz_hpb.projection_groups
        block = 1 if up else -1
        
        if index < len (pgroups) + block:        
            target_index = index-1 if up else index+1
            #  reorder collection
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
    
    # operator function
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
    
    # operator function
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
    

def start_handplane (self, mode):
    
    def main ():

        scene = bpy.context.scene
        prefs = bpy.context.user_preferences.addons[__package__].preferences
        
        mesh_format = 'fbx'
        
        # FBX EXPORTER SETTINGS:
        # MAIN
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
        # GEOMETRIES
        use_mesh_modifiers = False
        use_mesh_modifiers_render = False
        mesh_smooth_type = 'FACE'
        use_mesh_edges = False
        use_tspace = True
        # ARMATURES
        use_armature_deform_only = False
        add_leaf_bones = False
        primary_bone_axis = '-Y'
        secondary_bone_axis = 'X'
        armature_nodetype = 'NULL'
        # ANIMATION
        bake_anim = False
        bake_anim_use_all_bones = False
        bake_anim_use_nla_strips = False
        bake_anim_use_all_actions = False
        bake_anim_force_startend_keying = False
        bake_anim_step = 1
        bake_anim_simplify_factor = 1
        
        
        # make all layers visible (to make sure that every object gets exported)
        original_visible_layers = []
        for n in range (0, 20):
            if scene.layers[n] == True:
                original_visible_layers.append (n)
            else:
                scene.layers[n] = True
        
        
        # get export folder
        output_folder_mode = scene.gyaz_hpb.output_folder_mode
        relative_folder_name = scene.gyaz_hpb.relative_folder_name if scene.gyaz_hpb.relative_folder_name.replace (" ", "") != "" else ""
        custom_output_folder = scene.gyaz_hpb.custom_output_folder
        file_name = scene.gyaz_hpb.file_name
        
        if output_folder_mode == 'RELATIVE_FOLDER':
            root_folder = '//' + relative_folder_name + '/' + file_name
        else:
            root_folder = custom_output_folder + '/' + file_name
        
        # make sure root folder exists
        root_folder = os.path.abspath ( bpy.path.abspath (root_folder) )
        os.makedirs(root_folder, exist_ok=True)
        # get project-file path    
        project_file_path = root_folder + '/' + file_name + '.HPB'
        project_file_path = os.path.abspath ( bpy.path.abspath (project_file_path) )
        print (project_file_path)
        # save last written project file
        setattr (scene.gyaz_hpb, 'last_output_path', project_file_path)

   
        # export folder
        export_folder = root_folder + '\meshes'
        export_folder = os.path.abspath ( bpy.path.abspath (export_folder) )
        # create export folder
        os.makedirs(export_folder, exist_ok=True) 
        
        # make all layers visible                   
        def export_obj (obj_name, type):
            # type options:'HP', 'LP', 'C'
            if scene.objects.get (obj_name) != None:
                obj = scene.objects[obj_name]
                select_only_object (obj)
                if scene.gyaz_hpb.clear_transforms:
                    # save transform info
                    save__location = obj.location[:]
                    save__rotation_euler = obj.rotation_euler[:]
                    save__rotation_quaternion = obj.rotation_quaternion[:]
                    save__rotation_axis_angle = obj.rotation_axis_angle[:]
                    save__scale = obj.scale[:]
                    save__constraints_mute = []
                    for c in obj.constraints:
                        save__constraints_mute.append (c.mute)
                    # clear transforms
                    clear_transformation (obj)
                # make sure objects are visible and selectable
                obj.hide_select = False
                # select object
                obj.select = True
                # export path
                mesh_filepath = export_folder + '/' + obj.name + '.' + mesh_format
                mesh_filepath = os.path.abspath ( bpy.path.abspath (mesh_filepath) )
                # export
                use_tspace = False if type == 'HP' else True
                
                # apply modifiers and replace
                old_mesh = obj.data
                new_mesh = obj.to_mesh (scene, apply_modifiers=True, settings='RENDER', calc_tessface=True, calc_undeformed=False)
                obj.data = new_mesh
                if type != 'LP':
                    uv_maps = new_mesh.uv_textures
                    for uv_map in reversed(uv_maps):
                        uv_maps.remove (uv_map)
                
                # save modifier states
                mods = obj.modifiers
                mod_states = [(m.show_viewport, m.show_render) for m in mods]
                
                # deactivate mods
                for m in mods:
                    m.show_viewport = False
                    m.show_render = False
                
                bpy.ops.export_scene.fbx ( filepath=mesh_filepath, version=version, use_selection=use_selection, global_scale=global_scale, apply_unit_scale=apply_unit_scale, apply_scale_options=apply_scale_options, axis_forward=axis_forward, axis_up=axis_up, object_types=object_types, bake_space_transform=bake_space_transform, use_custom_props=use_custom_props, path_mode=path_mode, batch_mode=batch_mode, use_mesh_modifiers=use_mesh_modifiers, use_mesh_modifiers_render=use_mesh_modifiers_render, mesh_smooth_type=mesh_smooth_type, use_mesh_edges=use_mesh_edges, use_tspace=use_tspace, use_armature_deform_only=use_armature_deform_only, add_leaf_bones=add_leaf_bones, primary_bone_axis=primary_bone_axis, secondary_bone_axis=secondary_bone_axis, armature_nodetype=armature_nodetype, bake_anim=bake_anim, bake_anim_use_all_bones=bake_anim_use_all_bones, bake_anim_use_nla_strips=bake_anim_use_nla_strips, bake_anim_use_all_actions=bake_anim_use_all_actions, bake_anim_force_startend_keying=bake_anim_force_startend_keying, bake_anim_step=bake_anim_step, bake_anim_simplify_factor=bake_anim_simplify_factor )
                
                # reset mesh and delete the applied mesh
                obj.data = old_mesh
                bpy.data.meshes.remove (new_mesh)
                
                # reactivate mods
                for index, m in enumerate (mods):
                    m.show_viewport = mod_states[index][0]
                    m.show_render = mod_states[index][1]
                    
                # reset object transform and unmute constraints
                if scene.gyaz_hpb.clear_transforms:
                    for index, mute in enumerate (save__constraints_mute):
                        obj.constraints[index].mute = mute
                    obj.location = save__location
                    obj.rotation_euler = save__rotation_euler
                    obj.rotation_quaternion = save__rotation_quaternion
                    obj.rotation_axis_angle = save__rotation_axis_angle
                    obj.scale = save__scale
                
                return mesh_filepath
        
        # export mesh and save filepath (for writing path into .HPB file)
        pgroups = scene.gyaz_hpb.projection_groups
        for pgroup in pgroups:
            
            if pgroup.active == True:
            
                # high poly
                if scene.gyaz_hpb.export_hp == True:
                    for item in pgroup.high_poly:
                        setattr ( item, 'model', '""' )
                        if scene.objects.get (item.name) != None:
                            path = '"' + export_obj (item.name, 'HP') + '"'
                            setattr ( item, 'model', path )
                
                # low poly, cage
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
        
        
        # set extention and bit depth
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
        # set output props
        setattr (scene.gyaz_hpb.output_settings, 'outputFolder', '"' + path + '"')
        setattr (scene.gyaz_hpb.output_settings, 'outputFilename', scene.gyaz_hpb.file_name)
        setattr (scene.gyaz_hpb.output_settings, 'outputExtension', texture_format)
        setattr (scene.gyaz_hpb.output_settings, 'outputBitDepth', bit_depth)


        #########################################################################
        # write Handplane project file (.HPB)
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
        
        
        # mesh props       
        def high_poly_props (prop_owner):
            return write_prop_group (prop_owner=prop_owner, props = [['model', 'Filename'], ['overrideMaterial', 'bool'], ['material', 'int32'], ['isFloater', 'bool']], tabs = 4)
        
        def low_poly_props (prop_owner):
            return write_prop_group (prop_owner=prop_owner, props = [['model', 'Filename'], ['cageModel', 'Filename'], ['overrideCageOffset', 'bool'], ['autoCageOffset', 'float']], tabs = 4)
        
        def misc_props (prop_owner):    
            return write_prop_group (prop_owner=prop_owner, props = [['material', 'int32'], ['isolateAO', 'bool'], ['autoCageOffset', 'float']], tabs = 2)


        # global settings
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
        
        # material library
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

        # output settings
        def output_settings (prop_owner):
            return write_prop_group (prop_owner=prop_owner, props = [['outputFolder', 'Filename'], ['outputFilename', 'String'], ['outputExtension', 'String'], ['outputBitDepth', 'ImageBitDepth'], ['outputWidth', 'int32'], ['outputHeight', 'int32'], ['outputPadding', 'int32'], ['outputSuperSample', 'int32'], ['outputDither', 'bool']], tabs=0)
        
        
        # image output
        def image_outputs ():
            start = '\tImageOutput outputs\n'+'\t[\n'
            l = ''
            for map_name in maps:
                l += '\t\t{\n'
                
                map = getattr (scene.gyaz_hpb, map_name)
                prop_name = map.is_enabled_prop_name
                l += write_prop (owner=scene.gyaz_hpb.bake_settings, name=prop_name, tabs=3, type='bool', name_override='isEnabled')
                
                l += write_prop (owner=map, name='filenameSuffix', tabs=3, type='String', name_override=None)
                l += '\t\t}\n'
            end = '\t]\n'
            return start + l + end


        # Write data out (2 integers)
        with open (project_file_path, "w") as file:
            file.write (p1)
            
            # projection groups
            file.write (open_groups)
            
            for pgroup in pgroups:
                if pgroup.active == True:
                    file.write (group_start)
                    file.write (group_name (pgroup.name))
                    # high poly
                    file.write (high_poly_title)
                    file.write (models_start)
                    
                    models = pgroup.high_poly
                    for model in models:
                        file.write (item_start)
                        file.write (high_poly_props (model) )
                        file.write (item_end)
                    file.write (models_end)
     
                    # low poly               
                    file.write (low_poly_title)
                    file.write (models_start)
                    
                    models = pgroup.low_poly
                    for model in models:
                        file.write (item_start)
                        file.write (low_poly_props (model) )
                        file.write (item_end)
                    file.write (models_end)
                    
                    # misc
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
            
            
        # restore original visible layers
        for n in range (0, 20):
            if n in original_visible_layers:
                scene.layers[n] = True
            else:
                scene.layers[n] = False
                

        # start/bake with handplane
        handplane_path = prefs.handplane_path
        
        if mode == 'GO_TO':
            # start handplane
            handplane_user = os.path.abspath ( bpy.path.abspath (handplane_path+"handplane.exe") )
            subprocess.Popen (handplane_user)
            # open explorer and select handplane file 
            subprocess.Popen (r'explorer /select,' + project_file_path)
            
        elif mode == 'BAKE':
            # bake with handplane
            handplane_cmd = os.path.abspath ( bpy.path.abspath (handplane_path+"handplaneCmd.exe") )
            subprocess.run (handplane_cmd + ' /project ' + project_file_path)
            # open explorer at baked textures
            textures_folder = os.path.abspath ( bpy.path.abspath (root_folder + '/textures') )
            subprocess.Popen('explorer ' + textures_folder)
                        
    ##############################################
    # SAFETY CHECKS
    ##############################################
    prefs = bpy.context.user_preferences.addons[__package__].preferences
    scene = bpy.context.scene
    
    
    # check if file has ever been saved
    blend_data = bpy.context.blend_data
    if blend_data.is_saved == False:      
        report (self, 'File has never been saved.', 'WARNING')
        
    else:
        
        # check file name
        fn = scene.gyaz_hpb.file_name
        if  fn == '' or fn == ' ' or ',' in fn:
            report (self, 'Invalid export file name.', 'WARNING')
            
        else:
                         
    
            # handplane path
            handplane_path = prefs.handplane_path
            if handplane_path == '' or handplane_path == ' ':
                report (self, 'Handplane path is not set in user preferences.', 'WARNING')
            
            else:
                
                # no active projection group warning
                active_pgroups = [pgroup for pgroup in scene.gyaz_hpb.projection_groups if pgroup.active]
                if len (active_pgroups) == 0:
                    report (self, 'No active projection groups.', 'INFO')
                
                else:
                    
                    # check for groups with no high/low poly items
                    # check for missing and unset objects:
                    groups_with_no_high_poly_item = []
                    groups_with_no_low_poly_item = []
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
                            group_info = pgroup.name+'('+str(pgroup_index)+')'
                            if len (pgroup.high_poly) == 0:
                                groups_with_no_high_poly_item.append (group_info)
                            if len (pgroup.low_poly) == 0:
                                groups_with_no_low_poly_item.append (group_info)
                            if len (unset_objects) > 0:
                                groups_with_unset_objects.append (group_info)
                            if len (missing_objects) > 0:
                                groups_with_missing_objects.append (group_info)
                                
                    if len(groups_with_no_high_poly_item)>0 or len(groups_with_no_low_poly_item)>0 or len(groups_with_unset_objects)>0 or len(groups_with_missing_objects)>0:
                        warning_lines = []
                        if len (groups_with_no_high_poly_item) > 0:
                            warning_lines.append ("Groups with no high poly item: "+list_to_visual_list(groups_with_no_high_poly_item))
                        if len (groups_with_no_low_poly_item) > 0:
                            warning_lines.append ("Groups with no low poly item: "+list_to_visual_list(groups_with_no_low_poly_item))
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
                        # get lists of objects to export
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
                                    
                        # low poly, cage
                        quads_allowed = scene.gyaz_hpb.global_settings.suppressTriangulationWarning
                        max_verts_per_face = 4 if quads_allowed == True else 3
                        lp_c_objs_with_bad_polygons = []     
                        lp_objs_with_no_uvs = []
                        lp_objs_with_mirrored_uvs = []
                        
                        # face check
                        for obj_name in lp_objs + c_objs:
                            obj = scene.objects[obj_name]
                            bm = bmesh.new ()
                            bm.from_object (obj, scene=bpy.context.scene, deform=False, render=True, cage=False, face_normals=False)
                            faces = bm.faces
                            bad_polygons = [face for face in faces if len(face.verts)>max_verts_per_face]
                            bad_polygon_count = len (bad_polygons)
                            if bad_polygon_count > 0:
                                lp_c_objs_with_bad_polygons.append (obj_name)
                            bm.free ()
                           
                        for obj_name in lp_objs:
                            obj = scene.objects[obj_name]
                            uv_maps = obj.data.uv_textures
                            if len (uv_maps) < 1:
                                # no uvs
                                if obj_name in lp_objs:
                                    lp_objs_with_no_uvs.append (obj.name)  
                            else:
                                bm = bmesh.new ()
                                bm.from_mesh (obj.data)
                                faces = bm.faces                    
                                has_mirrored_uvs = detect_mirrored_uvs (bm, uv_index=0)
                                if has_mirrored_uvs:
                                    lp_objs_with_mirrored_uvs.append (obj.name)               
                                bm.free ()
                                    
                        # high poly
                        hp_objs_wo_vert_color = []
                        if scene.gyaz_hpb.bake_settings.isEnabled_vertex_color:
                            for obj_name in hp_objs:
                                obj = scene.objects[obj_name]
                                if len (obj.data.vertex_colors) == 0:
                                    hp_objs_wo_vert_color.append (obj_name)
                                
                        
                        if len (lp_c_objs_with_bad_polygons) == 0 and len (lp_objs_with_no_uvs) == 0:
                            good_to_go = True
                        else:
                            good_to_go = False
                            
                        if good_to_go == False:
                            
                            warning_lines = []
                            
                            # warnings
                            lp_no_uv_map_warning = 'No UV Maps: '
                            
                            if quads_allowed == False:
                                lp_c_polygon_warning = 'Quads or Ngons: '
                            else:
                                lp_c_polygon_warning = 'Ngons: '
                            hp_no_vert_color_warning = 'No Vertex Color: '
                            mirrored_uv_warning = 'Mirrored UVs: '

                                
                            if len (lp_c_objs_with_bad_polygons) > 0:
                                line = lp_c_polygon_warning + list_to_visual_list (lp_c_objs_with_bad_polygons)
                                warning_lines.append (line)
                                
                            if len (lp_objs_with_no_uvs) > 0:
                                line = lp_no_uv_map_warning + list_to_visual_list (lp_objs_with_no_uvs)
                                warning_lines.append (line)
                                
                            if len (hp_objs_wo_vert_color) > 0:
                                line = hp_no_vert_color_warning + list_to_visual_list (hp_objs_wo_vert_color)
                                warning_lines.append (line)
                            
                            if len (lp_objs_with_mirrored_uvs):        
                                warning_lines.append ( mirrored_uv_warning + list_to_visual_list (lp_objs_with_mirrored_uvs) )
                                
                            # print warning
                            popup (lines=warning_lines, icon='INFO', title='Mesh Warning')
                            for line in warning_lines:
                                print (line)
                        
                        else:

                            main ()
    

class Op_GYAZ_HandplaneBridge_GoToHandPlane (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_go_to_handplane"  
    bl_label = "GYAZ Handplane Bridge: Go To"
    bl_description = "Export to Handplane"
    bl_options = {'REGISTER', 'UNDO'}

    # operator function
    def execute(self, context):
        
        start_handplane (self, mode = 'GO_TO')

        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_BakeWithHandPlane (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_bake_with_handplane"  
    bl_label = "GYAZ Handplane Bridge: Bake"
    bl_description = "Export to Handplane and start baking"
    bl_options = {'REGISTER', 'UNDO'}
    
    # confirm popup
    def invoke (self, context, event):
        wm = bpy.context.window_manager
        return  wm.invoke_props_dialog (self)
    
    def draw (self, context):
        lay = self.layout
        lay.label ('')
        lay.label ('Open System Console before start to see progress report.')
        lay.label ('') 

    # operator function
    def execute(self, context):
        
        start_handplane (self, mode = 'BAKE')

        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_OpenLastOutput (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_open_last_output"  
    bl_label = "GYAZ Handplane Bridge: Open Last Output"
    bl_description = ""
    
    info = BoolProperty (default=False)
    
    # operator function
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


class Pa_GYAZ_HandplaneBridge (Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_label = 'Handplane Bridge'    
    
    # add ui elements here
    def draw (self, context):
        
        scene = bpy.context.scene
        prefs = bpy.context.user_preferences.addons[__package__].preferences        
        lay = self.layout
        lay.row ().prop (scene.gyaz_hpb, 'menu', expand=True)
        
        if scene.gyaz_hpb.menu == 'GROUPS':
            lay.label ('Projection Groups:')
            row = lay.row (align=True)
            row.scale_x = 2
            row.separator ()
            row.operator (Op_GYAZ_HandplaneBridge_AddProjectionGroup.bl_idname, text='', icon='ZOOMIN').clear=False
            row.operator (Op_GYAZ_HandplaneBridge_AddProjectionGroup.bl_idname, text='', icon='X').clear=True
            row.separator ()
            row.operator (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive.bl_idname, text='', icon='CHECKBOX_HLT').active=True
            row.operator (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive.bl_idname, text='', icon='CHECKBOX_DEHLT').active=False
            row.separator ()
            row.operator (Op_GYAZ_HandplaneBridge_CollapseAllProjectionGroups.bl_idname, text='', icon='TRIA_DOWN').collapse=False
            row.operator (Op_GYAZ_HandplaneBridge_CollapseAllProjectionGroups.bl_idname, text='', icon='TRIA_UP').collapse=True
            
            lay.separator ()
                
            for group_index, group_item in enumerate(scene.gyaz_hpb.projection_groups):
                
                enabled = True if group_item.active == True else False
                collapsed = True if group_item.collapsed else False
                
                if enabled and not collapsed:
                    box = lay.box ()
                    element = box
                else:
                    element = lay
                    
                row = element.row (align=True)
                row.prop (group_item, 'active', text='')
                if collapsed and enabled:
                    row.prop (group_item, 'collapsed', icon='TRIA_DOWN' if collapsed else 'TRIA_UP', emboss=False)
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
                
                if not collapsed:               
                
                    if enabled == True:
                        
                        row = element.row (align=True)
                        row.prop (group_item, 'autoCageOffset')
                        row.prop (group_item, 'isolateAO', toggle=True)
                        
                        row = element.row ()
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ZOOMIN')
                        operator_props.type = 'HIGH_POLY'
                        operator_props.projection_group_index = group_index
                        operator_props.remove = False
                        
                        row.label ('High Poly Models:')
                        
                        for hp_index, hp_item in enumerate(group_item.high_poly):
                            row = element.row (align=True)
                            row.prop_search (hp_item, 'name', scene, "objects", icon='SOLID')
                            
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
                            
                            row = element.row (align=True)
                            row.label (icon='BLANK1')
                            row.prop (hp_item, 'isFloater', toggle=True)
                            row.prop (hp_item, 'material')


                        row = element.row ()
                        
                        operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ZOOMIN')
                        operator_props.type = 'LOW_POLY'
                        operator_props.projection_group_index = group_index
                        operator_props.remove = False
                        
                        row.label ('Low Poly Models:')
                        for lp_index, lp_item in enumerate(group_item.low_poly):
                            row = element.row (align=True)
                            
                            row.prop_search (lp_item, 'name', scene, "objects", icon='MESH_ICOSPHERE')
                            
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
                            
                            row = element.row (align=True)
                            row.label (icon='BLANK1')
                            row.prop_search (lp_item, 'cage_name', scene, "objects", icon='LATTICE_DATA')
                            
                            operator_props = row.operator (Op_GYAZ_HandplaneBridge_AssignActiveObject.bl_idname, text='', icon='EYEDROPPER')
                            operator_props.type = 'CAGE'
                            operator_props.projection_group_index = group_index
                            operator_props.model_index = lp_index
                            
                            row.prop (lp_item, 'overrideCageOffset', text='', icon='LINE_DATA')             
                            
                            if lp_item.overrideCageOffset == True:
                                row = element.row ()
                                row.label (icon='BLANK1')
                                row.prop (lp_item, 'autoCageOffset')
                
                        element.prop (group_item, 'collapsed', icon='TRIA_DOWN' if collapsed else 'TRIA_UP', emboss=False)
         
        
        elif scene.gyaz_hpb.menu == 'SETTINGS':

            row = lay.row (align=True)
            row.prop (prefs, 'active_preset_name')
            row.operator (Op_GYAZ_HandplaneBridge_SavePreset.bl_idname, text='', icon='ZOOMIN')
            row.operator (Op_GYAZ_HandplaneBridge_RemovePreset.bl_idname, text='', icon='ZOOMOUT')
            
            col = lay.column (align=True)
            col.label ('Output:')
            row = col.row (align=True)
            row.prop (scene.gyaz_hpb.output_settings, 'outputWidth', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'outputHeight', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'texture_format', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'outputSuperSample', text='')
            row = lay.row ()
            row.prop (scene.gyaz_hpb.output_settings, 'outputPadding')
            row.prop (scene.gyaz_hpb.output_settings, 'outputDither')
            
            col = lay.column (align=True)
            col.label ('Maps:')
            bake_settings = scene.gyaz_hpb.bake_settings
            
            for map_name in maps:
                row = col.row (align=True)
                map = getattr (scene.gyaz_hpb, map_name)
                row.prop (bake_settings, map.is_enabled_prop_name, toggle=True)
                if map.has_props:
                    icon='TRIA_UP' if map.show_props == True else 'TRIA_DOWN'
                    row.prop (map, 'show_props', text='', icon=icon) 
                    if map.show_props:
                        col.separator ()
                        for prop_name in map.prop_names:
                            row = col.row (align=True)
                            row.label (icon='BLANK1')
                            row.prop (bake_settings, prop_name)
                        col.separator ()
            
            col = lay.column (align=True)
            col.label ('Global Settings:')
            col.prop (scene.gyaz_hpb.global_settings, 'threadCount')    
            col.prop (scene.gyaz_hpb.global_settings, 'backRayOffsetScale')    
            col.prop (scene.gyaz_hpb.global_settings, 'downsampleInGeneratorSpace')    
            col.prop (scene.gyaz_hpb.global_settings, 'buildSmoothedNormalsForHighRes')    
            col.prop (scene.gyaz_hpb.global_settings, 'suppressTriangulationWarning')    
            col.prop (scene.gyaz_hpb.global_settings, 'checkForMirroredUVs')    

                       
        elif scene.gyaz_hpb.menu == 'EXPORT':
            
            col = lay.column (align=True)
            col.label ('Destination:')
            row = col.row (align=True)
            row.prop(scene.gyaz_hpb, 'output_folder_mode', expand=True)
            path = '//' + scene.gyaz_hpb.relative_folder_name if scene.gyaz_hpb.output_folder_mode == 'RELATIVE_FOLDER' else scene.gyaz_hpb.custom_output_folder
            row.operator (Op_GYAZ_HPB_OpenFolderInWindowsFileExplorer.bl_idname, text='', icon='VIEWZOOM').path=path
            if scene.gyaz_hpb.output_folder_mode == 'RELATIVE_FOLDER':
                lay.prop (scene.gyaz_hpb, 'relative_folder_name')
            else:
                lay.prop (scene.gyaz_hpb, 'custom_output_folder')
            lay.prop (scene.gyaz_hpb, 'file_name')                               
            
            lay.prop (scene.gyaz_hpb, 'clear_transforms')
            row = lay.row ()
            row.prop (scene.gyaz_hpb, 'export_hp')
            row.prop (scene.gyaz_hpb, 'export_lp')
            col = lay.column (align=True)
            col.scale_y = 2       
            col.operator (Op_GYAZ_HandplaneBridge_GoToHandPlane.bl_idname, text='GO TO HANDPLANE', icon_value=custom_icons['handplane'].icon_id)
            col.operator (Op_GYAZ_HandplaneBridge_BakeWithHandPlane.bl_idname, text='BAKE WITH HANDPLANE', icon_value=custom_icons['handplane'].icon_id)
            row = lay.row (align=True)
            row.operator (Op_GYAZ_HandplaneBridge_OpenLastOutput.bl_idname, text='Open Last Export', icon='VIEWZOOM').info=False
            row.operator (Op_GYAZ_HandplaneBridge_OpenLastOutput.bl_idname, text='', icon='INFO').info=True


#######################################################
#######################################################

#REGISTER

def register():
    
    # custom icons
    custom_icon_names = ['handplane']
    
    global custom_icons
    custom_icons = bpy.utils.previews.new ()
    icons_dir = os.path.join ( os.path.dirname (__file__), "icons" )
    for icon_name in custom_icon_names:
        custom_icons.load ( icon_name, os.path.join (icons_dir, icon_name+'.png'), 'IMAGE' )
    # referencing icons:
    # icon_value = custom_icons["custom_icon"].icon_id
    
    bpy.utils.register_class (GYAZ_HPB_TangentSpaceNormalmap)
    bpy.utils.register_class (GYAZ_HPB_ObjectSpaceNormalmap)
    bpy.utils.register_class (GYAZ_HPB_AmpientOcclusion)
    bpy.utils.register_class (GYAZ_HPB_AmpientOcclusionFloaters)
    bpy.utils.register_class (GYAZ_HPB_VertexColor)
    bpy.utils.register_class (GYAZ_HPB_MaterialPSD)
    bpy.utils.register_class (GYAZ_HPB_MaterialID)
    bpy.utils.register_class (GYAZ_HPB_Curvature)
    bpy.utils.register_class (GYAZ_HPB_VolumetricGradient)
    bpy.utils.register_class (GYAZ_HPB_Cavity)
    bpy.utils.register_class (GYAZ_HPB_Heightmap)
    bpy.utils.register_class (GYAZ_HPB_TextureSpaceAO)
    bpy.utils.register_class (GYAZ_HPB_Thickness)
    
    bpy.utils.register_class (GYAZ_HandplaneBridge_HighPolyItem)
    bpy.utils.register_class (GYAZ_HandplaneBridge_LowPolyItem)
    bpy.utils.register_class (GYAZ_HandplaneBridge_ProjectionGroupItem)
    bpy.utils.register_class (GYAZ_HandplaneBridge_GlobalSettings)
    bpy.utils.register_class (GYAZ_HandplaneBridge_OutputSettings)
    bpy.utils.register_class (GYAZ_HandplaneBridge_BakeSettings)
    bpy.utils.register_class (GYAZ_HandplaneBridge)
    bpy.types.Scene.gyaz_hpb = PointerProperty (type=GYAZ_HandplaneBridge)

    
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_SavePreset)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_RemovePreset)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AddProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_RemoveProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_CollapseAllProjectionGroups)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_MoveProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AddModelItem)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AssignActiveObject)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_GoToHandPlane)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_BakeWithHandPlane)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_OpenLastOutput)
    bpy.utils.register_class (Op_GYAZ_HPB_OpenFolderInWindowsFileExplorer)
    
    bpy.utils.register_class (Pa_GYAZ_HandplaneBridge)
   

def unregister ():
    
    # custom icons
    global custom_icons
    bpy.utils.previews.remove (custom_icons)
    
    bpy.utils.unregister_class (GYAZ_HPB_TangentSpaceNormalmap)
    bpy.utils.unregister_class (GYAZ_HPB_ObjectSpaceNormalmap)
    bpy.utils.unregister_class (GYAZ_HPB_AmpientOcclusion)
    bpy.utils.unregister_class (GYAZ_HPB_AmpientOcclusionFloaters)
    bpy.utils.unregister_class (GYAZ_HPB_VertexColor)
    bpy.utils.unregister_class (GYAZ_HPB_MaterialPSD)
    bpy.utils.unregister_class (GYAZ_HPB_MaterialID)
    bpy.utils.unregister_class (GYAZ_HPB_Curvature)
    bpy.utils.unregister_class (GYAZ_HPB_VolumetricGradient)
    bpy.utils.unregister_class (GYAZ_HPB_Cavity)
    bpy.utils.unregister_class (GYAZ_HPB_Heightmap)
    bpy.utils.unregister_class (GYAZ_HPB_TextureSpaceAO)
    bpy.utils.unregister_class (GYAZ_HPB_Thickness)
    
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_HighPolyItem)
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_LowPolyItem)
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_ProjectionGroupItem)
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_GlobalSettings)
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_OutputSettings)
    bpy.utils.unregister_class (GYAZ_HandplaneBridge_BakeSettings)
    bpy.utils.unregister_class (GYAZ_HandplaneBridge)
    del bpy.types.Scene.gyaz_hpb
    
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_SavePreset)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_RemovePreset)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AddProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_RemoveProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_CollapseAllProjectionGroups)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_MoveProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AddModelItem)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AssignActiveObject)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_GoToHandPlane)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_BakeWithHandPlane)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_OpenLastOutput)
    bpy.utils.unregister_class (Op_GYAZ_HPB_OpenFolderInWindowsFileExplorer)
    
    bpy.utils.unregister_class (Pa_GYAZ_HandplaneBridge)

  
if __name__ == "__main__":   
    register()              