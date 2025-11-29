import bpy
from bpy.props import StringProperty


class Preferences(bpy.types.PropertyGroup):
    rsx_folder: StringProperty(
        name="RSX folder", subtype="DIR_PATH")  # noqa 722
    vpk_folder: StringProperty(
        name="VPK folder", subtype="DIR_PATH")  # noqa 722
    # TODO: game folders for automated extraction
    # -- need command line extraction tools


class SCENE_PT_ReSourceAssetFolders(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Titanfall Engine Assets"
    bl_idname = "SCENE_PT_ReSourceAssetFolders"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.rbsp_prefs, "rsx_folder")
        layout.prop(context.scene.rbsp_prefs, "vpk_folder")


classes = (
    Preferences,
    SCENE_PT_ReSourceAssetFolders)


def register():
    for class_ in classes:
        bpy.utils.register_class(class_)
    bpy.types.Scene.rbsp_prefs = bpy.props.PointerProperty(type=Preferences)


def unregister():
    for class_ in classes:
        bpy.utils.unregister_class(class_)
    del bpy.types.Scene.rbsp_prefs
