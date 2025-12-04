from typing import Dict

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Collection, Operator

import bsp_tool

from . import load
from . import preferences


bl_info = {
    "name": "io_import_rbsp",
    "author": "Jared Ketterer (snake-biscuits / Bikkie)",
    "version": (1, 4, 0),
    "blender": (4, 5, 0),
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
    load_materials: BoolProperty(
        name="Materials", description="Load materials", default=True)  # noqa F722
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
            ("Models", "Textured Models",  # noqa F722
             "Full props & materials; Very slow")),  # noqa F722
        default="None")  # noqa F722

    def execute(self, context):
        bsp = bsp_tool.load_bsp(self.filepath)
        if not is_titanfall_engine(bsp):
            self.report(
                {"ERROR_INVALID_INPUT"}, "Not a Titanfall Engine .bsp!")
            del bsp  # cleanup
            return {"CANCELLED"}

        # main collection
        if bsp.filename not in bpy.data.collections:
            bsp_collection = bpy.data.collections.new(bsp.filename)
            context.scene.collection.children.link(bsp_collection)
        else:
            bsp_collection = bpy.data.collections[bsp.filename]

        # level geometry & materials
        if self.load_geometry:
            geo_collection = make_collection(bsp_collection, "geometry")
            load.geometry.all_models(bsp, geo_collection)

        # solid & point entities
        if self.load_triggers or self.load_entities:
            ent_collections = make_entity_collections(bsp_collection)
            if self.load_triggers:
                load.triggers.all_triggers(bsp, ent_collections)
            if self.load_entities:
                load.entities.all_entities(bsp, ent_collections)

        # props
        if self.load_props != "None":
            prop_collection = make_collection(bsp_collection, "static props")
        if self.load_props == "Empties":
            load.props.as_empties(bsp, prop_collection)
        elif self.load_props == "Models":
            load.props.static_props(bsp, prop_collection)

        if self.load_materials:
            load.materials.all_materials()  # update all placeholders
        # TODO: report how many materials were loaded from files
        # -- self.report({"INFO"}, "{x} / {total} materials loaded")

        # TODO: scale the whole import (Engine Units -> Inches)
        # TODO: override default view clipping (16 near, 102400 far)
        # TODO: self.report({"INFO"}, "took <X> seconds to import <mapname>")
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


# BUG: makes a new collection if map is already loaded?
def make_collection(parent: Collection, name: str) -> Collection:
    for child in parent.children:  # doesn't work?
        if child.name.startswith(name):
            return child
    child = bpy.data.collections.new(name)
    parent.children.link(child)
    return child


def make_entity_collections(bsp_collection) -> Dict[str, Collection]:
    out = dict()
    entities_collection = bpy.data.collections.new("entities")
    bsp_collection.children.link(entities_collection)
    entity_blocks = ("bsp", "env", "fx", "script", "sound", "spawn")
    for block_name in entity_blocks:
        entity_collection = bpy.data.collections.new(block_name)
        entities_collection.children.link(entity_collection)
        out[block_name] = entity_collection
    return out


class ImportMATL(Operator, ImportHelper):
    """Load .rpak MATL asset"""
    bl_idname = "io_import_rbsp.matl_import"
    bl_label = "Titanfall Engine MATL"
    filename_ext = ".json"
    filter_glob: StringProperty(
        default="*.json", options={"HIDDEN"}, maxlen=255)  # noqa F722

    def execute(self, context):
        matl = load.materials.MATL.from_file(self.filepath)
        # TODO: choose maker for MATL type ("fix", "wld" etc.)
        maker = load.materials.WorldMaterial()
        maker.textures = matl.textures
        maker.make_nodes()
        del maker, matl
        return {"FINISHED"}


class ImportMDL(Operator, ImportHelper):
    """Load Titanfall 2 v53 .mdl"""
    bl_idname = "io_import_rbsp.mdl_import"
    bl_label = "Titanfall 2 v53 .mdl"
    filename_ext = ".mdl"
    filter_glob: StringProperty(
        default="*.mdl", options={"HIDDEN"}, maxlen=255)  # noqa F722

    # TODO: importer settings
    # -- IntProperty  target body group
    # -- IntProperty  target lod
    # -- BoolProperty load materials

    def execute(self, context):
        # TODO: error msg on unsupported .mdl format:
        # -- self.report({"ERROR_INVALID_INPUT"}, "Not a Titanfall v53 .mdl")
        # -- return {"CANCELLED"}
        mesh = load.props.load_model(self.filepath)
        name = mesh.name.partition(".")[0]
        mdl_object = bpy.data.objects.new(name, mesh)
        # link to view layer
        view_collection = context.view_layer.active_layer_collection.collection
        view_collection.objects.link(mdl_object)
        context.view_layer.objects.active = mdl_object
        return {"FINISHED"}


# NOTE: not yet implemented
# class ImportVMT(Operator, ImportHelper):
#     """Load Titanfall Engine .vmt"""
#     bl_idname = "io_import_rbsp.vmt_import"
#     bl_label = "Titanfall Engine .vmt"
#     filename_ext = ".vmt"
#     filter_glob: StringProperty(
#         default="*.vmt", options={"HIDDEN"}, maxlen=255)  # noqa F722
#
#     def execute(self, context):
#         maker = load.materials.NodeMaker()
#         vmt = load.materials.VMT.from_file(self.filepath)
#         maker.textures = vmt.textures
#         maker.make_nodes()
#         del maker, vmt
#         return {"FINISHED"}


def add_operators(self, context):
    """for adding to a dynamic menu"""
    self.layout.operator(ImportRBSP.bl_idname, text=ImportRBSP.bl_label)
    self.layout.operator(ImportMDL.bl_idname, text=ImportMDL.bl_label)
    self.layout.operator(ImportMATL.bl_idname, text=ImportMATL.bl_label)
    # self.layout.operator(ImportVMT.bl_idname, text=ImportVMT.bl_label)


def register():
    preferences.register()
    bpy.utils.register_submodule_factory(__name__, (
        "ass", "breki", "bsp_tool", "load"))
    bpy.utils.register_class(ImportMATL)
    bpy.utils.register_class(ImportMDL)
    bpy.utils.register_class(ImportRBSP)
    # bpy.utils.register_class(ImportVMT)
    bpy.types.TOPBAR_MT_file_import.append(add_operators)


def unregister():
    preferences.unregister()
    bpy.utils.unregister_class(ImportMATL)
    bpy.utils.unregister_class(ImportMDL)
    bpy.utils.unregister_class(ImportRBSP)
    # bpy.utils.unregister_class(ImportVMT)
    bpy.types.TOPBAR_MT_file_import.remove(add_operators)


if __name__ == "__main__":
    register()
