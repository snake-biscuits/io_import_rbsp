import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator

from . import bsp_tool
from . import rbsp


bl_info = {
    "name": "io_import_rbsp",
    "author": "Jared Ketterer (snake-biscuits / Bikkie)",
    "version": (1, 1, 0),
    "blender": (2, 93, 0),
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
    filter_glob: StringProperty(default="*.bsp", options={"HIDDEN"}, maxlen=255)  # noqa F722
    # TODO: load_materials EnumProperty: None, Names, Base Colours, Nodes
    load_geometry: BoolProperty(name="Geometry", description="Load .bsp Geometry", default=True)  # noqa F722
    load_entities: BoolProperty(name="Entities", description="Load .bsp Entities", default=True)  # noqa F722
    # TODO: cubemap volumes?
    # TODO: load_lighting EnumProperty: None, Empties, All, PortalLights
    # TODO: load_prop_dynamic EnumProperty: None, Empties, Low-Poly, High-Poly
    # TODO: load_prop_static EnumProperty: None, Empties, Low-Poly, High-Poly, Skybox Only
    # TODO: Lock out some options if SourceIO is not installed, alert the user
    # TODO: Warnings for missing files
    # TODO: Lightmaps with Pillow (PIL)

    def execute(self, context):
        bsp = bsp_tool.load_bsp(self.filepath)
        import_script = {bsp_tool.branches.respawn.titanfall: rbsp.titanfall,
                         bsp_tool.branches.respawn.titanfall2: rbsp.titanfall2,
                         bsp_tool.branches.respawn.apex_legends: rbsp.apex_legends}
        importer = import_script[bsp.branch]
        # master_collection
        if bsp.filename not in bpy.data.collections:
            master_collection = bpy.data.collections.new(bsp.filename)
            bpy.context.scene.collection.children.link(master_collection)
        else:
            master_collection = bpy.data.collections[bsp.filename]
        # materials
        materials = importer.materials.base_colours(bsp)
        # geometry
        if self.load_geometry:
            # TODO: rename Model[0] "worldspawn"
            # TODO: skybox collection
            # TODO: load specific model / mesh (e.g. worldspawn only, skip tool brushes etc.)
            importer.geometry(bsp, master_collection, materials)
        # entities
        if self.load_entities:
            # TODO: link worldspawn to Model[0]
            importer.entities.as_empties(bsp, master_collection)
            # NOTE: Eevee has limited lighting, try Cycles
        # props
        # TODO: import scale (Engine Units -> Inches)
        return {"FINISHED"}


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportRBSP.bl_idname, text=ImportRBSP.bl_label)


def register():
    bpy.utils.register_submodule_factory(__name__, ("bsp_tool", "rbsp"))
    bpy.utils.register_class(ImportRBSP)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportRBSP)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
