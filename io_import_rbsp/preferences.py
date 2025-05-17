import bpy
from bpy.props import StringProperty


class Preferences(bpy.types.PropertyGroup):
    materials_folder: StringProperty(
        name="Materials folder", subtype="DIR_PATH")  # noqa 722
    models_folder: StringProperty(
        name="Models folder", subtype="DIR_PATH")  # noqa F722


class SCENE_PT_LegionFolder(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Titanfall Engine Assets"
    bl_idname = "SCENE_PT_LegionFolder"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.rbsp_prefs, "materials_folder")
        layout.prop(context.scene.rbsp_prefs, "models_folder")


classes = (Preferences, SCENE_PT_LegionFolder)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.rbsp_prefs = bpy.props.PointerProperty(type=Preferences)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.rbsp_prefs
