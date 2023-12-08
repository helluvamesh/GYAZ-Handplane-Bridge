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

global_settings_list = ['threadCount', 'backRayOffsetScale', 'downsampleInGeneratorSpace', 'buildSmoothedNormalsForHighRes', 'suppressTriangulationWarning', 'checkForMirroredUVs', 'isDecal']

output_settings_list = ['outputExtension', 'outputBitDepth', 'texture_format', 'outputWidth', 'outputHeight', 'outputPadding', 'outputSuperSample', 'outputDither']



import bpy, os, subprocess, bmesh
from bpy.types import Panel, Operator, AddonPreferences, PropertyGroup, UIList, Menu
from bpy.props import *
import bpy.utils.previews
from mathutils import Matrix
import numpy as np


def report (self, text, type):
    # types: 'INFO', 'WARNING', 'ERROR'
    self.report({type}, text)


def popup (lines, icon, title):
    def draw(self, context):
        for line in lines:
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def deselect_all_uvs (bm, uv_index):
    uv_layer = bm.loops.layers.uv[uv_index]
    for face in bm.faces:
        for loop in face.loops:
            loop[uv_layer].select = False


def detect_mirrored_uvs (bm, uv_index):
    uv_layer = bm.loops.layers.uv[uv_index]
    mirrored_face_count = 0
    for face in bm.faces:
        uvs = [tuple(loop[uv_layer].uv) for loop in face.loops]
        x_coords, y_coords = zip (*uvs)
        if 0.5 * np.array (np.dot(x_coords, np.roll(y_coords, 1)) - np.dot(y_coords, np.roll(x_coords, 1))) > 0:
            mirrored_face_count += 1
            break      
    if mirrored_face_count > 0:
        return True
    else:
        return False
    

def select_mirrored_uvs (bm, uv_index):
    uv_layer = bm.loops.layers.uv[uv_index]
    mirrored_face_count = 0
    for face in bm.faces:
        uvs = [tuple(loop[uv_layer].uv) for loop in face.loops]
        x_coords, y_coords = zip (*uvs)
        if 0.5 * np.array (np.dot(x_coords, np.roll(y_coords, 1)) - np.dot(y_coords, np.roll(x_coords, 1))) > 0:
            mirrored_face_count += 1
            uvs_ = [loop[uv_layer] for loop in face.loops]
            for uv in uvs_:
                uv.select = True  
    
    
def list_to_visual_list (list):
    line = ''
    for index, item in enumerate(list):
        if index > 0:
            line += ', '
        line += str(item)
    return line

        
def baked_mesh (object):
    object_eval = object.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh_from_eval = bpy.data.meshes.new_from_object (object_eval)
    object_eval.to_mesh_clear ()
    return mesh_from_eval
    

def clear_transformation (object):
    for c in object.constraints:
        c.mute = True
    object.matrix_world = Matrix (([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]))


def apply_transforms (obj, co):
    co = co[:]
    # get vert coords in world space
    m = np.array (obj.matrix_world)    
    mat = m[:3, :3].T # rotates backwards without T
    loc = m[:3, 3]
    return co @ mat + loc


class GYAZ_HandplaneBridge_Preferences (AddonPreferences):
    # use __name__ with single-file addons
    # use __package__ with multi-file addons
    bl_idname = __package__
    
    def absolute_path__hand_plane_path (self, context):
        prop = getattr (self, "handplane_path")
        new_path = os.path.abspath ( bpy.path.abspath (prop) )
        if prop.startswith ('//') == True:
            self.handplane_path = new_path
    
    handplane_path: StringProperty (name='Handplane Baker Path', default='', subtype='DIR_PATH', update=absolute_path__hand_plane_path)
    
    #map suffixes
    ts_normals_suffix: StringProperty (name='TS Normals', default='_N')
    os_normals_suffix: StringProperty (name='OS Normals', default='_NW')
    ao_suffix: StringProperty (name='AO', default='_AO')
    ao_floaters_suffix: StringProperty (name='AO (Floaters)', default='_AOFLOAT')
    vert_color_suffix: StringProperty (name='Vert Color', default='_VERTCOL')
    mat_psd_suffix: StringProperty (name='Material PSD', default='_MAT')
    mat_id_suffix: StringProperty (name='Material', default='_ID')
    curve_suffix: StringProperty (name='Curvature', default='_CURVE')
    vol_gradient_suffix: StringProperty (name='Volumetric Gradient', default='_VOLGRAD')
    cavity_suffix: StringProperty (name='Cavity', default='_CAVITY')
    height_suffix: StringProperty (name='Height', default='_H')
    tsao_suffix: StringProperty (name='TS AO', default='_TSAO')
    thickness_suffix: StringProperty (name='Thickness', default='_THICK')
  
    
    #PRESETS (BakeSettings, OutputSettings, GlobalSettings
    class GYAZ_HandplaneBridge_Preset (PropertyGroup):
        #preset name
        name: StringProperty ()
        
        #bake settings
        aoSampleRadius: FloatProperty (min=0.0)
        aoSampleCount: IntProperty (min=0)
        volumetricGradientCubeFit: BoolProperty ()
        thicknessSampleRadius: FloatProperty (min=0.0)
        thicknessSampleCount: IntProperty (min=0)
        heightMapScale: FloatProperty (min=0.0)
        heightMapOffset: FloatProperty (min=0.0)
        curvatureUseRaySampling: BoolProperty ()
        curvatureSampleRadius: FloatProperty (min=0.0)
        curvatureSampleCount: IntProperty (min=0)
        curvaturePixelRadius: IntProperty (min=0)
        curvatureAutoNormalize: BoolProperty ()
        curvatureMaxAngle: FloatProperty (min=0.0)
        curvatureOutputGamma: FloatProperty (min=0.0)
        cavitySensitivity: FloatProperty (min=0.0)
        cavityBias: FloatProperty (min=0.0)
        cavityPixelRadius: IntProperty (min=0)
        cavityOutputGamma: FloatProperty (min=0.0)
        cavityKernelType: StringProperty ()
        textureSpaceAOPixelRadius: IntProperty (min=0)
        textureSpaceAOOutputGamma: FloatProperty (min=0.0)
        textureSpaceAOSampleCoveragePercentage: FloatProperty (min=0.0)
        
        tangentSpace: StringProperty ()
        
        isEnabled_tangent_space_normals: BoolProperty ()
        isEnabled_object_space_normals: BoolProperty ()
        isEnabled_ambient_occlusion: BoolProperty ()
        isEnabled_ambient_occlusion_floaters: BoolProperty ()
        isEnabled_vertex_color: BoolProperty ()
        isEnabled_material_psd: BoolProperty ()
        isEnabled_material_id: BoolProperty ()
        isEnabled_curvature_map: BoolProperty ()
        isEnabled_volumetric_gradient: BoolProperty ()
        isEnabled_cavity_map: BoolProperty ()
        isEnabled_height_map: BoolProperty ()
        isEnabled_texture_space_ao: BoolProperty ()
        isEnabled_thickness: BoolProperty ()
        
        #global settings
        threadCount: IntProperty (min=0)
        backRayOffsetScale: FloatProperty (min=0.0)
        downsampleInGeneratorSpace: BoolProperty ()
        buildSmoothedNormalsForHighRes: BoolProperty ()
        suppressTriangulationWarning: BoolProperty ()
        checkForMirroredUVs: BoolProperty (default=True)
        isDecal: BoolProperty ()
        
        #output settings
        outputExtension: StringProperty ()
        outputBitDepth: IntProperty (min=0)
        texture_format: StringProperty ()
        outputWidth: StringProperty ()
        outputHeight: StringProperty ()
        outputPadding: IntProperty (min=0)
        outputSuperSample: StringProperty ()
        outputDither: BoolProperty ()
        
    bpy.utils.register_class(GYAZ_HandplaneBridge_Preset)
    
    presets: CollectionProperty (type=GYAZ_HandplaneBridge_Preset)
    
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
            
    
    active_preset_name: EnumProperty (name='Preset', items=get_preset_name_items, default=None, update=load_preset)
    
    
    
    def draw (self, context):
        layout = self.layout
        layout.prop (self, 'handplane_path')
        
        layout.label (text='Map Suffixes:')
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
#        layout.label (text='Presets:')
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


prefs = bpy.context.preferences.addons[__package__].preferences


# MAPS
class GYAZ_HPB_TangentSpaceNormalmap (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.ts_normals_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_tangent_space_normals')
    prop_names = ['tangentSpace']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_ObjectSpaceNormalmap (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.os_normals_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_object_space_normals')
    prop_names = []
    has_props = False
    show_props: BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_AmpientOcclusion (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.ao_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_ambient_occlusion')
    prop_names = ['aoSampleRadius', 'aoSampleCount']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)    
    
class GYAZ_HPB_AmpientOcclusionFloaters (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.ao_floaters_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_ambient_occlusion_floaters')
    prop_names = ['aoSampleRadius', 'aoSampleCount']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_VertexColor (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.vert_color_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_vertex_color')
    prop_names = []
    has_props = False
    show_props: BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_MaterialPSD (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.mat_psd_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_material_psd')
    prop_names = []
    has_props = False
    show_props: BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_MaterialID (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.mat_id_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_material_id')
    prop_names = []
    has_props = False
    show_props: BoolProperty (name='Show/hide settings.', default=False)
        
class GYAZ_HPB_Curvature (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.curve_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_curvature_map')
    prop_names = ['curvatureUseRaySampling', 'curvatureSampleRadius', 'curvatureSampleCount', 'curvaturePixelRadius', 'curvatureAutoNormalize', 'curvatureMaxAngle', 'curvatureOutputGamma']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)
    
class GYAZ_HPB_VolumetricGradient (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.vol_gradient_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_volumetric_gradient')
    prop_names = ['volumetricGradientCubeFit']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)    
    
class GYAZ_HPB_Cavity (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.cavity_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_cavity_map')
    prop_names = ['cavitySensitivity', 'cavityBias', 'cavityPixelRadius', 'cavityOutputGamma', 'cavityKernelType']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)

class GYAZ_HPB_Heightmap (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.height_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_height_map')
    prop_names = ['heightMapScale', 'heightMapOffset']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)
    
class GYAZ_HPB_TextureSpaceAO (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.tsao_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_texture_space_ao')
    prop_names = ['textureSpaceAOPixelRadius', 'textureSpaceAOOutputGamma']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)
    
class GYAZ_HPB_Thickness (PropertyGroup):
    filenameSuffix: StringProperty (default=prefs.thickness_suffix)
    is_enabled_prop_name: StringProperty (default='isEnabled_thickness')
    prop_names = ['thicknessSampleRadius', 'thicknessSampleCount']
    has_props = True
    show_props: BoolProperty (name='Show/hide settings.', default=False)


def set_object (self, object):
    return object.type in ['MESH', 'CURVE', 'META', 'SURFACE', 'FONT']


class GYAZ_HandplaneBridge_HighPolyItem (PropertyGroup):
    model: StringProperty (name='', default='')
    overrideMaterial: BoolProperty (name='Override material', default=True)
    material: IntProperty (name='Material ID', default=0, min=0, max=3)
    isFloater: BoolProperty (name='Is Floater', default=False, description='Is Floater?')
    object: PointerProperty (name='', type=bpy.types.Object, description='High poly mesh', poll=set_object)


class GYAZ_HandplaneBridge_LowPolyItem (PropertyGroup):
    model: StringProperty (name='', default='')
    cageModel: StringProperty (name='', default='')
    overrideCageOffset: BoolProperty (name='Override Cage Offset', default=False, description='Override Ray Offset')
    autoCageOffset: FloatProperty (name='Cage Offset', default=1.0, min=0.0)
    object: PointerProperty (name='', type=bpy.types.Object, description='Low poly mesh', poll=set_object)
    cage_object: PointerProperty (name='', type=bpy.types.Object, description='Cage mesh', poll=set_object)
    
      
class GYAZ_HandplaneBridge_ProjectionGroupItem (PropertyGroup):
    name: StringProperty (name='Name', default='Projection Group')
    active: BoolProperty (default=True, description='Only active groups are exported')
    high_poly: CollectionProperty (type=GYAZ_HandplaneBridge_HighPolyItem)
    low_poly: CollectionProperty (type=GYAZ_HandplaneBridge_LowPolyItem)
    material: IntProperty (default=0, min=0)
    isolateAO: BoolProperty (name='Isolate AO', default=False, description='Projection groups are baked separately except for AO unless Isolate AO is True')
    autoCageOffset: FloatProperty (name='Ray Offset', default=1, min=0.0)


class GYAZ_HandplaneBridge_GlobalSettings (PropertyGroup):
    threadCount: IntProperty (name='Baker Thread Count', default=0, min=0)
    backRayOffsetScale: FloatProperty (name='Back Ray Offset Scale', default=5.0, min=0.0)
    downsampleInGeneratorSpace: BoolProperty (name='Generator Space Downsampling', default=True)
    buildSmoothedNormalsForHighRes: BoolProperty (name='Smooth High Res Normals (If None Found)', default=False)
    suppressTriangulationWarning: BoolProperty (name='Suppress Triangulation Warnings', default=False)
    checkForMirroredUVs: BoolProperty (name='Check for Mirrored UVs', default=True)
    isDecal: BoolProperty (name='Is Decal', description='Calculate values for Heightmap.Scale, Heightmap.Offset, AmbientOcclusion.SampleRadius automaically based on the vertex depths of the first high-poly mesh compared to the first-low_poly mesh')

 
class GYAZ_HandplaneBridge_OutputSettings (PropertyGroup):
    outputFolder: StringProperty (name='Folder', default='')
    outputFilename: StringProperty (name='Name', default='')
    outputExtension: StringProperty (default='TGA')
    outputBitDepth: IntProperty (default=8, min=0)
    texture_format: EnumProperty (name='Format', items=(('TIF_8', 'TIF 8', ''), ('TIF_16', 'TIF 16', ''), ('PNG_8', 'PNG 8', ''), ('PNG_16', 'PNG 16', ''), ('PSD_8', 'PSD 8', ''), ('PSD_16', 'PSD 16', ''), ('TGA_8', 'TGA 8', '')), default='PNG_8')
    outputWidth: EnumProperty (name='Width', items=(('256', '256', ''), ('512', '512', ''), ('1024', '1024', ''), ('2048', '2048', ''), ('4096', '4096', ''), ('8192', '8192', ''), ('16384', '16384', '')), default='2048')
    outputHeight: EnumProperty (name='Height', items=(('256', '256', ''), ('512', '512', ''), ('1024', '1024', ''), ('2048', '2048', ''), ('4096', '4096', ''), ('8192', '8192', ''), ('16384', '16384', '')), default='2048')
    outputPadding: IntProperty (name='Padding', default=64, min=0)
    outputSuperSample: EnumProperty (name='Super Sample', items=(('1', '1', ''), ('2', '2', ''), ('4', '4', ''), ('8', '8', ''), ('16', '16', '')), default='1')
    outputDither: BoolProperty (name='Dither', default=True)

class GYAZ_HandplaneBridge_BakeSettings (PropertyGroup):
    aoSampleRadius: FloatProperty (name='Sample Radius', default=1.0, min=0.0)
    aoSampleCount: IntProperty (name='Sample Count', default=20, min=0)
    volumetricGradientCubeFit: BoolProperty (name='Cube Fit', default=False)
    thicknessSampleRadius: FloatProperty (name='Sample Radius', default=1.0, min=0.0)
    thicknessSampleCount: IntProperty (name='Sample Count', default=20, min=0)
    heightMapScale: FloatProperty (name='Scale', default=1.0, min=0.0)
    heightMapOffset: FloatProperty (name='Offset', default=0.0)
    curvatureUseRaySampling: BoolProperty (name='Use Ray Sampling', default=False)
    curvatureSampleRadius: FloatProperty (name='Sample Radius', default=0.05, min=0.0)
    curvatureSampleCount: IntProperty (name='Sample Count', default=20, min=0)
    curvaturePixelRadius: IntProperty (name='Pixel Sample Radius', default=4, min=0)
    curvatureAutoNormalize: BoolProperty (name='Auto Normalize', default=True)
    curvatureMaxAngle: FloatProperty (name='Max Curvature', default=100.0, min=0.0)
    curvatureOutputGamma: FloatProperty (name='Output Gamma', default=1.0, min=0.0)
    cavitySensitivity: FloatProperty (name='Sensitivity', default=0.75, min=0.0)
    cavityBias: FloatProperty (name='Bias', default=0.015)
    cavityPixelRadius: IntProperty (name='PixelSampleRadius', default=4, min=0)
    cavityOutputGamma: FloatProperty (name='Output Gamma', default=1.0, min=0.0)
    cavityKernelType: EnumProperty (name='Kernel Type', items=(('ConstantBox', 'Constant Box', ''), ('ConstantDisk', 'Constant Disk', ''), ('LinearBox', 'Linear Box', ''), ('LinearDisk', 'Linear Disk', ''), ('Gaussian', 'Gaussian', '')), default='ConstantDisk')
    textureSpaceAOPixelRadius: IntProperty (name='Pixel Sample Radius', default=10, min=0)
    textureSpaceAOOutputGamma: FloatProperty (name='Output Gamma', default=1.0, min=0.0)
    textureSpaceAOSampleCoveragePercentage: FloatProperty (name='Sample Coverage Percentage', default=100.0, min=0.0)
    
    tangentSpace: EnumProperty (
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
    
    isEnabled_tangent_space_normals: BoolProperty (default=False, name='Tangent Space Normals')
    isEnabled_object_space_normals: BoolProperty (default=False, name='Object Space Normals')
    isEnabled_ambient_occlusion: BoolProperty (default=False, name='Ambient Occlusion')
    isEnabled_ambient_occlusion_floaters: BoolProperty (default=False, name='Ambient Occlusion (Floaters)')
    isEnabled_vertex_color: BoolProperty (default=False, name='Vertex Color')
    isEnabled_material_psd: BoolProperty (default=False, name='Material PSD')
    isEnabled_material_id: BoolProperty (default=False, name='Material ID')
    isEnabled_curvature_map: BoolProperty (default=False, name='Curvature Map')
    isEnabled_volumetric_gradient: BoolProperty (default=False, name='Volumetric Gradient')
    isEnabled_cavity_map: BoolProperty (default=False, name='Cavity Map')
    isEnabled_height_map: BoolProperty (default=False, name='Height Map')
    isEnabled_texture_space_ao: BoolProperty (default=False, name='Texture Space AO')
    isEnabled_thickness: BoolProperty (default=False, name='Thickness')


class GYAZ_HandplaneBridge (PropertyGroup):
    projection_groups: CollectionProperty (type=GYAZ_HandplaneBridge_ProjectionGroupItem)
    active_projection_group: IntProperty (min=0)
    output_folder: StringProperty (name='', default='', subtype='DIR_PATH')
    file_name: StringProperty (name='Name', default='')
    last_output_path: StringProperty (name='Last Output', default='')
    clear_transforms_hp: BoolProperty (name='HP to Origo', default=False, description="Clear objects' transformation and mute constraints")
    clear_transforms_lp: BoolProperty (name='LP to Origo', default=False, description="Clear objects' transformation and mute constraints")
    export_hp: BoolProperty (name='Update HP', default=True, description="Export high poly object(s)")
    export_lp: BoolProperty (name='Update LP', default=True, description="Export low poly and cage object(s)")
    global_settings: PointerProperty (type=GYAZ_HandplaneBridge_GlobalSettings)
    output_settings: PointerProperty (type=GYAZ_HandplaneBridge_OutputSettings)
    menu: EnumProperty (name='Menu', items=(('GROUPS', 'GROUPS', ''), ('SETTINGS', 'SETTINGS', ''), ('EXPORT', 'EXPORT', '')), default='GROUPS')
    bake_settings: PointerProperty (type=GYAZ_HandplaneBridge_BakeSettings)
    
    normal_ts: PointerProperty (type=GYAZ_HPB_TangentSpaceNormalmap)
    normal_os: PointerProperty (type=GYAZ_HPB_ObjectSpaceNormalmap)
    ao: PointerProperty (type=GYAZ_HPB_AmpientOcclusion)
    ao_floaters: PointerProperty (type=GYAZ_HPB_AmpientOcclusionFloaters)
    vert_color: PointerProperty (type=GYAZ_HPB_VertexColor)
    mat_psd: PointerProperty (type=GYAZ_HPB_MaterialPSD)
    mat_id: PointerProperty (type=GYAZ_HPB_MaterialID)
    curve: PointerProperty (type=GYAZ_HPB_Curvature)
    vol_gradient: PointerProperty (type=GYAZ_HPB_VolumetricGradient)
    cavity: PointerProperty (type=GYAZ_HPB_Cavity)
    height: PointerProperty (type=GYAZ_HPB_Heightmap)
    tsao: PointerProperty (type=GYAZ_HPB_TextureSpaceAO)
    thickness: PointerProperty (type=GYAZ_HPB_Thickness)


class Op_GYAZ_HandplaneBridge_SavePreset (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_save_preset"  
    bl_label = "GYAZ Handplane Bridge: Save Preset"
    bl_description = "Save preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty (name='preset name', default='')
    
    # popup with properties
    def invoke(self, context, event):
        wm = bpy.context.window_manager
        return wm.invoke_props_dialog(self)
    
    # operator function
    def execute(self, context):
        preset_name = self.preset_name
        scene = bpy.context.scene
        
        prefs = bpy.context.preferences.addons[__package__].preferences
        
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
        bpy.context.area.type = 'PREFERENCES'
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
        prefs = bpy.context.preferences.addons[__package__].preferences
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
        bpy.context.area.type = 'PREFERENCES'
        bpy.ops.wm.save_userpref()
        bpy.context.area.type = 'PROPERTIES'      

        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_AddProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_add_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Add Projection Group"
    bl_description = "Add projection group / Clear projection groups"
    bl_options = {'REGISTER', 'UNDO'}
    
    clear: BoolProperty (default=False)
    
    # operator function
    def execute(self, context):
        clear = self.clear  
        scene = bpy.context.scene
        
        if not clear:
            item = scene.gyaz_hpb.projection_groups.add ()
            item.name += ' ' + str(len(scene.gyaz_hpb.projection_groups))
            item.high_poly.add ()
            item.low_poly.add ()
            scene.gyaz_hpb.active_projection_group = len(scene.gyaz_hpb.projection_groups) - 1
        else:
            item = scene.gyaz_hpb.projection_groups.clear ()
            
        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_RemoveProjectionGroup (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_remove_projection_group"  
    bl_label = "GYAZ Handplane Bridge: Remove Projection Group"
    bl_description = "Remove projection group"
    bl_options = {'REGISTER', 'UNDO'}
    
    projection_group_index: IntProperty (default=0, min=0)
    
    # operator function
    def execute(self, context):
        index = self.projection_group_index  
        scene = bpy.context.scene
        scene.gyaz_hpb.projection_groups.remove (index)
        scene.gyaz_hpb.active_projection_group = max (index - 1, 0)
            
        return {'FINISHED'}
 

class Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_set_all_projection_groups_active"  
    bl_label = "GYAZ Handplane Bridge: Set All Projection Groups Active"
    bl_description = "Set all projection groups active/inactive. Only active groups are exported"
    bl_options = {'REGISTER', 'UNDO'}    
    
    active: BoolProperty (default=False)
    
    # operator function
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
    
    index: IntProperty (default=0, min=0)
    up: BoolProperty (default=True)
    
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
            scene.gyaz_hpb.active_projection_group = min(max(target_index, 0), len(scene.gyaz_hpb.projection_groups) - 1)
            
        return {'FINISHED'}

    
class Op_GYAZ_HandplaneBridge_AddModelItem (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_add_model_item"  
    bl_label = "GYAZ Handplane Bridge: Add High Poly Item"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    type: EnumProperty ( items= ( ('HIGH_POLY', '', ''), ('LOW_POLY', '', '') ) )
    projection_group_index: IntProperty (default=0, min=0)
    remove: BoolProperty (default=False)
    model_index: IntProperty (default=0, min=0)
    
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


def start_handplane (self, mode):
    
    def main ():
        
        # if all materials are 0, material library is [white]
        # else: material library is [black, red, green, blue]
        all_materials_0 = True

        scene = bpy.context.scene
        prefs = bpy.context.preferences.addons[__package__].preferences
        
        mesh_format = 'fbx'
        
        # FBX EXPORTER SETTINGS:
        # MAIN
        use_selection = True
        use_active_collection = False
        global_scale = 1
        apply_unit_scale = False
        apply_scale_options = 'FBX_SCALE_NONE'
        axis_forward = '-Z'
        axis_up = 'Y'
        object_types = {'EMPTY', 'MESH', 'OTHER', 'ARMATURE'}
        bake_space_transform = False
        use_custom_props = False
        path_mode = 'STRIP'
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
        

        # get export folder
        output_folder = scene.gyaz_hpb.output_folder
        file_name = scene.gyaz_hpb.file_name
        
        if output_folder.startswith ('//'):
            output_folder = os.path.abspath ( bpy.path.abspath (output_folder) )
        if not os.path.isdir(output_folder):
            report (self, "Export folder (Destination) doesn't exist.", "WARNING")
            return {"CANCELLED"} 

        root_folder = os.path.join(output_folder, file_name) 
        os.makedirs(root_folder, exist_ok=True)

        # get project-file path    
        project_file_path = os.path.join(root_folder, file_name + '.HPB')
        # save last written project file
        scene.gyaz_hpb.last_output_path = project_file_path

   
        # export folder
        export_folder = os.path.join(root_folder, 'Meshes')
        # create export folder
        os.makedirs(export_folder, exist_ok=True)
        
        
        #_______________________________________________________________
        
        # Is Decal - modify some settings based on vertex depths
        
        if scene.gyaz_hpb.global_settings.isDecal:
        
            pgroups = scene.gyaz_hpb.projection_groups
            
            first_pgroup = None
            for pgroup in pgroups:
                if pgroup.active:
                    first_pgroup = pgroup
                    break
            
            if first_pgroup is not None:
                first_hp = None
                for item in first_pgroup.high_poly:
                    if item.object is not None:
                        first_hp = item.object
                        break
                    
                if first_hp is not None:
                    first_lp = None
                    for item in first_pgroup.low_poly:
                        if item.object is not None:
                            first_lp = item.object
                            break
                        
                    if first_lp is not None:
            
                        hp = first_hp
                        lp = first_lp
                        
                        lp_vert_zpos = apply_transforms(lp, lp.data.vertices[0].co)[2]

                        # mesh with modifiers applied
                        baked_hp_mesh = baked_mesh(hp)

                        vert_depths = [apply_transforms(hp, v.co)[2] for v in baked_hp_mesh.vertices]
                        deepest_vert_zpos = min(vert_depths)
                        heighest_vert_zpos = max(vert_depths)

                        lower_height = lp_vert_zpos - deepest_vert_zpos
                        upper_height = heighest_vert_zpos - lp_vert_zpos

                        interval = max(lower_height, upper_height)

                        #  blender: 1 = 1m, handplane: 1 = 1cm
                        interval *= 100
                        
                        scene.gyaz_hpb.bake_settings.heightMapOffset = interval
                        scene.gyaz_hpb.bake_settings.heightMapScale = interval * 2
                        scene.gyaz_hpb.bake_settings.aoSampleRadius = interval
        
        #_______________________________________________________________
        
        
		# export func               
        def export_obj (obj, type):
            # type options:'HP', 'LP', 'C'
            transform_was_cleared = False
            if (type == 'HP' and scene.gyaz_hpb.clear_transforms_hp) or ((type == 'LP' or type == 'C') and scene.gyaz_hpb.clear_transforms_lp):
                transform_was_cleared = True
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
            # export path
            mesh_filepath = os.path.join(export_folder, obj.name + '.' + mesh_format)
            # export
            use_tspace = False if type == 'HP' else True
            
            # apply modifiers and replace
            old_mesh = obj.data
            new_mesh = baked_mesh (obj)
            obj.data = new_mesh
            if type != 'LP':
                uv_maps = new_mesh.uv_layers
                for uv_map in reversed(uv_maps):
                    uv_maps.remove (uv_map)
            
            # save modifier states
            mods = obj.modifiers
            mod_states = [(m.show_viewport, m.show_render) for m in mods]
            
            # deactivate mods
            for m in mods:
                m.show_viewport = False
                m.show_render = False
            
            with bpy.context.temp_override(selected_objects=[obj]):
                bpy.ops.export_scene.fbx (
                    filepath=mesh_filepath, 
                    use_selection=use_selection,
                    use_active_collection=use_active_collection, 
                    global_scale=global_scale, 
                    apply_unit_scale=apply_unit_scale, 
                    apply_scale_options=apply_scale_options, 
                    axis_forward=axis_forward, 
                    axis_up=axis_up, 
                    object_types=object_types, 
                    bake_space_transform=bake_space_transform, 
                    use_custom_props=use_custom_props, 
                    path_mode=path_mode, 
                    batch_mode=batch_mode, 
                    use_mesh_modifiers=use_mesh_modifiers, 
                    use_mesh_modifiers_render=use_mesh_modifiers_render, 
                    mesh_smooth_type=mesh_smooth_type, 
                    use_mesh_edges=use_mesh_edges, 
                    use_tspace=use_tspace, 
                    use_armature_deform_only=use_armature_deform_only, 
                    add_leaf_bones=add_leaf_bones, 
                    primary_bone_axis=primary_bone_axis, 
                    secondary_bone_axis=secondary_bone_axis, 
                    armature_nodetype=armature_nodetype, 
                    bake_anim=bake_anim, 
                    bake_anim_use_all_bones=bake_anim_use_all_bones, 
                    bake_anim_use_nla_strips=bake_anim_use_nla_strips, 
                    bake_anim_use_all_actions=bake_anim_use_all_actions, 
                    bake_anim_force_startend_keying=bake_anim_force_startend_keying, 
                    bake_anim_step=bake_anim_step, 
                    bake_anim_simplify_factor=bake_anim_simplify_factor
                    )
            
            # reset mesh and delete the applied mesh
            obj.data = old_mesh
            bpy.data.meshes.remove (new_mesh)
            
            # reactivate mods
            for index, m in enumerate (mods):
                m.show_viewport = mod_states[index][0]
                m.show_render = mod_states[index][1]
                
            # reset object transform and unmute constraints
            if transform_was_cleared:
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
                if scene.gyaz_hpb.export_hp:
                    for item in pgroup.high_poly:
                        setattr ( item, 'model', '""' )
                        if item.object is not None:
                            path = '"' + export_obj (item.object, 'HP') + '"'
                            setattr ( item, 'model', path )
                            if item.material != 0:
                                all_materials_0 = False
                
                # low poly, cage
                if scene.gyaz_hpb.export_lp:
                    for item in pgroup.low_poly:
                        setattr ( item, 'model', '""')
                        if item.object is not None:
                            path =  '"' + export_obj (item.object, 'LP') + '"'
                            setattr ( item, 'model', path)
                        setattr ( item, 'cageModel', '""')
                        if item.cage_object is not None:
                            path = '"' + export_obj (item.cage_object, 'C') + '"'
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
        
        
        path = os.path.join(root_folder, 'Textures')
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
            if all_materials_0:
                materials = mat ('0xFFFFFFFF', '0')
            else:
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
 

        # start/bake with handplane
        handplane_path = prefs.handplane_path
        
        if mode == 'GO_TO':
            # start handplane
            handplane_user = os.path.abspath ( bpy.path.abspath (handplane_path+"handplane.exe") )
            subprocess.Popen (handplane_user)
            # open explorer and select handplane file 
            subprocess.Popen (r'explorer /select,' + os.path.abspath ( bpy.path.abspath (project_file_path) ))
            
        elif mode == 'BAKE':
            # bake with handplane
            handplane_cmd = os.path.abspath ( bpy.path.abspath (handplane_path+"handplaneCmd.exe") )
            subprocess.run (handplane_cmd + ' /project ' + project_file_path)
                        
    ##############################################
    # SAFETY CHECKS
    ##############################################
    prefs = bpy.context.preferences.addons[__package__].preferences
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
                    # check for missing objects:
                    groups_with_no_high_poly_item = []
                    groups_with_no_low_poly_item = []
                    groups_with_missing_objects = []
                    for pgroup_index, pgroup in enumerate (active_pgroups):
                        high_poly_objs = [item.object for item in pgroup.high_poly]
                        low_poly_objs = [item.object for item in pgroup.low_poly]
                        cage_objs = [item.cage_object for item in pgroup.low_poly]
                        
                        # cage object can be None, hp and lp can't
                        missing_objects = []
                        for obj in high_poly_objs + low_poly_objs:
                            if obj is None:
                                missing_objects.append (obj)
                            elif obj.name not in scene.objects:
                                missing_objects.append (obj)
                                
                        for obj in cage_objs:
                            if obj is not None:
                                if obj.name not in scene.objects:
                                    missing_objects.append (obj)
                                
                        # result
                        group_info = pgroup.name+'('+str(pgroup_index)+')'
                        if len (pgroup.high_poly) == 0:
                            groups_with_no_high_poly_item.append (group_info)
                        if len (pgroup.low_poly) == 0:
                            groups_with_no_low_poly_item.append (group_info)
                        if len (missing_objects) > 0:
                            groups_with_missing_objects.append (group_info)
                            
                    if len(groups_with_no_high_poly_item)>0 or len(groups_with_no_low_poly_item)>0 or len(groups_with_missing_objects)>0:
                        warning_lines = []
                        if len (groups_with_no_high_poly_item) > 0:
                            warning_lines.append ("Groups with no high poly item: "+list_to_visual_list(groups_with_no_high_poly_item))
                        if len (groups_with_no_low_poly_item) > 0:
                            warning_lines.append ("Groups with no low poly item: "+list_to_visual_list(groups_with_no_low_poly_item))
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
                        for group in active_pgroups:
                            for item in group.high_poly:
                                if item.object is not None:
                                    hp_objs.append (item.object)
                            for item in group.low_poly:
                                if item.object is not None:
                                    lp_objs.append (item.object)
                                if item.cage_object is not None:
                                    c_objs.append (item.cage_object)
                                    
                        # low poly, cage
                        quads_allowed = scene.gyaz_hpb.global_settings.suppressTriangulationWarning
                        max_verts_per_face = 4 if quads_allowed == True else 3
                        lp_c_objs_with_bad_polygons = []     
                        lp_objs_with_no_uvs = []
                        lp_objs_with_mirrored_uvs = []
                        
                        # face check
                        for obj in lp_objs + c_objs:
                            bm = bmesh.new ()
                            bm.from_object (obj, bpy.context.evaluated_depsgraph_get(), cage=False, face_normals=False, vertex_normals=False)
                            faces = bm.faces
                            bad_polygons = [face for face in faces if len(face.verts)>max_verts_per_face]
                            bad_polygon_count = len (bad_polygons)
                            if bad_polygon_count > 0:
                                lp_c_objs_with_bad_polygons.append (obj.name)
                            bm.free ()
                           
                        for obj in lp_objs:
                            uv_maps = obj.data.uv_layers
                            if len (uv_maps) < 1:
                                # no uvs
                                if obj in lp_objs:
                                    lp_objs_with_no_uvs.append (obj.name)  
                            else:
                                # select mirored uvs
                                bm = bmesh.new ()
                                bm.from_mesh (obj.data)                               
                                has_mirrored_uvs = detect_mirrored_uvs (bm, uv_index=0)
                                if has_mirrored_uvs:
                                    deselect_all_uvs (bm, uv_index=0)
                                    select_mirrored_uvs (bm, uv_index=0)
                                    lp_objs_with_mirrored_uvs.append (obj.name)
                                    bm.to_mesh (obj.data)               
                                else:    
                                    bm.free ()
                                    
                        # high poly
                        hp_objs_wo_vert_color = []
                        if scene.gyaz_hpb.bake_settings.isEnabled_vertex_color:
                            for obj in hp_objs:
                                if len (obj.data.color_attributes) == 0:
                                    hp_objs_wo_vert_color.append (obj.name)
                                
                        
                        if len (lp_c_objs_with_bad_polygons) == 0 and len (lp_objs_with_no_uvs) == 0 and len (hp_objs_wo_vert_color) == 0 and len (lp_objs_with_mirrored_uvs) == 0:
                            good_to_go = True
                        else:
                            good_to_go = False
                            
                        if not good_to_go:
                            
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
                            
                            if len (lp_objs_with_mirrored_uvs) > 0:        
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
        lay.label (text='')
        lay.label (text='Open System Console before start to see progress report.')
        lay.label (text='') 

    # operator function
    def execute(self, context):
        
        start_handplane (self, mode = 'BAKE')

        return {'FINISHED'}


class Op_GYAZ_HandplaneBridge_OpenLastOutput (bpy.types.Operator):
       
    bl_idname = "object.gyaz_hpb_open_last_output"  
    bl_label = "GYAZ Handplane Bridge: Open Last Output"
    bl_description = ""
    
    info: BoolProperty (default=False)
    
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
    

class UI_UL_GYAZ_ProjectionGroupItem (UIList):
    def draw_item (self, context, layout, data, set, icon, active_data, active_propname, index):
        row = layout.row (align=True)
        row.prop (set, 'active', text='')
        row.prop (set, 'name', text='', emboss=False, expand=True)
        

class RENDER_MT_GYAZ_HPB_ProjectionGroup (Menu):
    bl_label = 'Projection Group'
    
    def draw (self, context):   
        lay = self.layout
        lay.operator (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive.bl_idname, text='All Active', icon='CHECKBOX_HLT').active=True
        lay.operator (Op_GYAZ_HandplaneBridge_SetAllProjectionGroupsActive.bl_idname, text='All Inactive', icon='CHECKBOX_DEHLT').active=False
        lay.separator ()
        lay.operator (Op_GYAZ_HandplaneBridge_AddProjectionGroup.bl_idname, text='Remove All', icon='X').clear=True


class RENDER_PT_GYAZ_HandplaneBridge (Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Handplane Baker'    
    bl_category = 'Bake'
    
    # add ui elements here
    def draw (self, context):
        
        scene = bpy.context.scene
        prefs = bpy.context.preferences.addons[__package__].preferences        
        lay = self.layout
        lay.column ().prop (scene.gyaz_hpb, 'menu', expand=True)
        
        col = lay.column ().scale_y = .5
        
        if scene.gyaz_hpb.menu == 'GROUPS':
            
            row = lay.row ()
            row.template_list ("UI_UL_GYAZ_ProjectionGroupItem", "",  # type and unique id
                               scene.gyaz_hpb, "projection_groups",  # pointer to the CollectionProperty
                               scene.gyaz_hpb, "active_projection_group",  # pointer to the active identifier
                               rows=4, maxrows=4
                               ) 
            col = row.column (align=True)
            
            group_index = scene.gyaz_hpb.active_projection_group
            
            col.operator (Op_GYAZ_HandplaneBridge_AddProjectionGroup.bl_idname, text='', icon='ADD').clear=False
            col.operator (Op_GYAZ_HandplaneBridge_RemoveProjectionGroup.bl_idname, text='', icon='REMOVE').projection_group_index=group_index
            if len (scene.gyaz_hpb.projection_groups) > 1:
                col.separator ()
                col.menu ('RENDER_MT_GYAZ_HPB_ProjectionGroup', text='', icon='DOWNARROW_HLT')
                col.separator ()
                move = col.operator (Op_GYAZ_HandplaneBridge_MoveProjectionGroup.bl_idname, text='', icon='TRIA_UP')
                move.up = True
                move.index = group_index
                move = col.operator (Op_GYAZ_HandplaneBridge_MoveProjectionGroup.bl_idname, text='', icon='TRIA_DOWN')
                move.up = False
                move.index = group_index
            
            col = lay.column ()  
                    
            col.separator ()
            
            if group_index < len (scene.gyaz_hpb.projection_groups):
                group_item = scene.gyaz_hpb.projection_groups[group_index]
                
                col = col.column ()
                
                sub_col = col.column (align=True)
                sub_col.prop (group_item, 'autoCageOffset')
                sub_col.prop (group_item, 'isolateAO')
                                        
                col.separator ()
                row = col.row ()
                operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ADD')
                operator_props.type = 'HIGH_POLY'
                operator_props.projection_group_index = group_index
                operator_props.remove = False
                row.label (text='High Poly:')
                col.separator ()
                
                for hp_index, hp_item in enumerate(group_item.high_poly):
                    row = col.row (align=True)
                    row.prop (hp_item, 'object', icon='SHADING_SOLID')
                    
                    row.separator ()
                    
                    operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='REMOVE')
                    operator_props.type = 'HIGH_POLY'
                    operator_props.projection_group_index = group_index
                    operator_props.remove = True
                    operator_props.model_index = hp_index
                    
                    row = col.row (align=True)
                    row.label (icon='BLANK1')
                    row.prop (hp_item, 'isFloater', toggle=True)
                    row.prop (hp_item, 'material')

                
                col.separator ()
                row = col.row ()
                operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='ADD')
                operator_props.type = 'LOW_POLY'
                operator_props.projection_group_index = group_index
                operator_props.remove = False
                row.label (text='Low Poly:')
                col.separator ()
                
                for lp_index, lp_item in enumerate(group_item.low_poly):
                    row = col.row (align=True)

                    row.prop (lp_item, 'object', icon='MESH_ICOSPHERE')
                    
                    row.separator ()
                    
                    operator_props = row.operator (Op_GYAZ_HandplaneBridge_AddModelItem.bl_idname, text='', icon='REMOVE')
                    operator_props.type = 'LOW_POLY'
                    operator_props.projection_group_index = group_index
                    operator_props.remove = True
                    operator_props.model_index = lp_index
                    
                    row = col.row (align=True)
                    row.label (icon='BLANK1')
                    
                    row.prop (lp_item, 'cage_object', text='', icon='LATTICE_DATA')
                   
                    row.prop (lp_item, 'overrideCageOffset', text='', icon='LINE_DATA')             
                    
                    if lp_item.overrideCageOffset == True:
                        row = col.row ()
                        row.label (icon='BLANK1')
                        row.prop (lp_item, 'autoCageOffset')
                        
                col.separator ()
     
        
        elif scene.gyaz_hpb.menu == 'SETTINGS':

            col = lay.column (align=True)
            col.label (text='Preset:')
            row = col.row (align=True)
            row.prop (prefs, 'active_preset_name', text="")
            row.operator (Op_GYAZ_HandplaneBridge_SavePreset.bl_idname, text='', icon='ADD')
            row.operator (Op_GYAZ_HandplaneBridge_RemovePreset.bl_idname, text='', icon='REMOVE')
            
            col = lay.column (align=True)
            col.label (text='Output:')
            row = col.row (align=True)
            row.prop (scene.gyaz_hpb.output_settings, 'outputWidth', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'outputHeight', text='')
            row = col.row (align=True)
            row.prop (scene.gyaz_hpb.output_settings, 'texture_format', text='')
            row.prop (scene.gyaz_hpb.output_settings, 'outputSuperSample', text='')
            
            col = lay.column (align=True)
            col.prop (scene.gyaz_hpb.output_settings, 'outputPadding')
            col.prop (scene.gyaz_hpb.output_settings, 'outputDither')
            
            col = lay.column (align=True)
            col.label (text='Maps:')
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
            col.label (text='Global Settings:')
            col.prop (scene.gyaz_hpb.global_settings, 'threadCount')    
            col.prop (scene.gyaz_hpb.global_settings, 'backRayOffsetScale')    
            col.prop (scene.gyaz_hpb.global_settings, 'downsampleInGeneratorSpace')    
            col.prop (scene.gyaz_hpb.global_settings, 'buildSmoothedNormalsForHighRes')    
            col.prop (scene.gyaz_hpb.global_settings, 'suppressTriangulationWarning')    
            col.prop (scene.gyaz_hpb.global_settings, 'checkForMirroredUVs')    
            col.prop (scene.gyaz_hpb.global_settings, 'isDecal')    

                       
        elif scene.gyaz_hpb.menu == 'EXPORT':
            
            col = lay.column (align=True)
            col.label (text='Destination:')
            col.prop (scene.gyaz_hpb, 'output_folder')
            col = lay.column (align=True)
            col.label (text='Name:')
            col.prop (scene.gyaz_hpb, 'file_name', text="")                               
            
            col = lay.column ()
            col.prop (scene.gyaz_hpb, 'clear_transforms_hp')
            col.prop (scene.gyaz_hpb, 'clear_transforms_lp')
            col.prop (scene.gyaz_hpb, 'export_hp')
            col.prop (scene.gyaz_hpb, 'export_lp')
            row = lay.row (align=True)
            col = row.column (align=True)
            col.scale_y = 2
            col.operator (Op_GYAZ_HandplaneBridge_GoToHandPlane.bl_idname, text='GO TO HANDPLANE', icon_value=custom_icons['handplane'].icon_id)
            col.operator (Op_GYAZ_HandplaneBridge_BakeWithHandPlane.bl_idname, text='BAKE', icon_value=custom_icons['handplane'].icon_id)
            col = row.column (align=True)
            col.scale_y = 4
            col.operator (Op_GYAZ_HandplaneBridge_OpenLastOutput.bl_idname, text='', icon='VIEWZOOM').info=False


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
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_MoveProjectionGroup)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_AddModelItem)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_GoToHandPlane)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_BakeWithHandPlane)
    bpy.utils.register_class (Op_GYAZ_HandplaneBridge_OpenLastOutput)
    
    bpy.utils.register_class (UI_UL_GYAZ_ProjectionGroupItem)
    bpy.utils.register_class (RENDER_MT_GYAZ_HPB_ProjectionGroup)
    bpy.utils.register_class (RENDER_PT_GYAZ_HandplaneBridge)
   

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
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_MoveProjectionGroup)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_AddModelItem)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_GoToHandPlane)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_BakeWithHandPlane)
    bpy.utils.unregister_class (Op_GYAZ_HandplaneBridge_OpenLastOutput)
    
    bpy.utils.unregister_class (RENDER_PT_GYAZ_HandplaneBridge)
    bpy.utils.unregister_class (UI_UL_GYAZ_ProjectionGroupItem)
    bpy.utils.unregister_class (RENDER_MT_GYAZ_HPB_ProjectionGroup)

  
if __name__ == "__main__":   
    register()              