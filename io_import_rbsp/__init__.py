import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

import bsp_tool

from . import load
from . import preferences


bl_info = {
    "name": "io_import_rbsp",
    "author": "Jared Ketterer (snake-biscuits / Bikkie)",
    "version": (1, 3, 0),
    "blender": (4, 2, 0),
    "location": "File > Import > Titanfall Engine .bsp",
    "description": "Import maps from Titanfall, Titanfall 2 & Apex Legends",
    "doc_url": "https://github.com/snake-biscuits/io_import_rbsp",
    "tracker_url": "https://github.com/snake-biscuits/io_import_rbsp/issues",
    "category": "Import-Export"}


class ImportRBSP(Operator, ImportHelper):
    """Load Titanfall Engine rBSP"""
    bl_idname = "io_import_rbsp.rbsp_import"
    bl_label = "Titanfall Engine .bsp"
    filename_ext = ".bsp"
    filter_glob: StringProperty(
        default="*.bsp", options={"HIDDEN"}, maxlen=255)  # noqa F722
    # importer settings
    load_geometry: BoolProperty(
        name="Geometry", description="Load geometry", default=True)  # noqa F722
    load_triggers: BoolProperty(
        name="Triggers", description="Load triggers", default=True)  # noqa F722
    load_entities: BoolProperty(
        name="Entities", description="Load entities", default=True)  # noqa F722
    # TODO: separate entities into more sub-categories
    # -- lights
    # -- sound
    # -- cameras
    load_props: EnumProperty(
        name="Props", description="Load smaller models",  # noqa F722
        items=(
            ("None", "No Props",  # noqa F722
             "Decent performance"),  # noqa F722
            ("Empties", "Use Empties",  # noqa F722
             "Place empties at prop origins"),  # noqa F722
            ("Instances", "Instanced Collections",  # noqa F722
             "Full props & materials; Very slow")),  # noqa F722
        default="None")  # noqa F722

    # TODO: loading % indicators
    # TODO: error handling
    def execute(self, context):
        bsp = bsp_tool.load_bsp(self.filepath)
        if not is_titanfall_engine(bsp):
            self.report(
                {"ERROR_INVALID_INPUT"},
                "Not a Titanfall Engine .bsp!")
            return {"CANCELLED"}
        # TODO: self.report({"INFO"}, <timestamps>)
        # bsp_collection
        if bsp.filename not in bpy.data.collections:
            bsp_collection = bpy.data.collections.new(bsp.filename)
            context.scene.collection.children.link(bsp_collection)
        else:
            bsp_collection = bpy.data.collections[bsp.filename]
        # load based on chosen options
        # TODO: pre-check extracted assets folders in prefs
        # -- can do a bunch of skips if they're empty
        if self.load_geometry:
            # NOTE: also loads materials
            # TODO: pass down preferences for asset folders
            load.geometry.all_models(bsp, bsp_collection)
        if self.load_triggers or self.load_entities:
            make_entities_collection()
            if self.load_triggers:
                load.triggers.all_triggers(bsp)
            if self.load_entities:
                load.entities.all_entities(bsp)
        # props
        if self.load_props == "Empties":
            load.props.as_empties(bsp, bsp_collection)
        elif self.load_props == "Instances":
            # TODO: pass down preferences for asset folders
            load.props.static_props(bsp, bsp_collection)
        # TODO: scale the whole import (Engine Units -> Inches)
        # TODO: override default view clipping (16 near, 102400 far)
        del bsp  # don't cache!
        return {"FINISHED"}


def is_titanfall_engine(bsp) -> bool:
    valid_bspclass = isinstance(bsp, bsp_tool.RespawnBsp)
    valid_branch = bsp.branch in (
        bsp_tool.branches.respawn.titanfall,
        bsp_tool.branches.respawn.titanfall2,
        bsp_tool.branches.respawn.apex_legends,
        bsp_tool.branches.respawn.apex_legends50,
        bsp_tool.branches.respawn.apex_legends51,
        bsp_tool.branches.respawn.apex_legends52)
    return valid_bspclass and valid_branch


def make_entities_collection(bsp_collection):
    entities_collection = bpy.data.collections.new("entities")
    bsp_collection.children.link(entities_collection)
    entity_blocks = ("bsp", "env", "fx", "script", "sound", "spawn")
    for block_name in entity_blocks:
        entity_collection = bpy.data.collections.new(block_name)
        entities_collection.children.link(entity_collection)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportRBSP.bl_idname, text=ImportRBSP.bl_label)


def register():
    preferences.register()
    bpy.utils.register_submodule_factory(__name__, ("bsp_tool", "load"))
    bpy.utils.register_class(ImportRBSP)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    preferences.unregister()
    bpy.utils.unregister_class(ImportRBSP)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
