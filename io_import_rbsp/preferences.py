import bpy
from bpy.props import StringProperty


class Preferences(bpy.types.PropertyGroup):
    rsx_folder: StringProperty(
        name="RSX folder", subtype="DIR_PATH")  # noqa 722
    # TODO: per-game extracted vpk assets folder (r1 & r2)
    # TODO: game folders for automated extraction

    # TODO: .stbsp (could be a github issue)
    # -- use .stbsp to optimise loaded material mip levels
    # NOTE: would need to target a camera
    # -- could rely on static position
    # -- or match multiple .stbsp columns to an animated camera's route
    # -- tho to get the camera animated, you'd want to load the geo first
    # NOTE: this is why materials was a seperate load stage before
    # -- it lets users re-import materials at a higher quality if they wish
    # -- can't do that without decoupling materials from .all_geometry


class SCENE_PT_LegionFolder(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Titanfall Engine Assets"
    bl_idname = "SCENE_PT_LegionFolder"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.rbsp_prefs, "rsx_folder")


classes = (Preferences, SCENE_PT_LegionFolder)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.rbsp_prefs = bpy.props.PointerProperty(type=Preferences)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.rbsp_prefs
