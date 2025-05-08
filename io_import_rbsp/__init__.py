import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

import bsp_tool
from . import rbsp
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
    "category": "Import-Export"
}


class ImportRBSP(Operator, ImportHelper):
    """Load Titanfall Engine rBSP"""
    bl_idname = "io_import_rbsp.rbsp_import"
    bl_label = "Titanfall Engine .bsp"
    filename_ext = ".bsp"
    filter_glob: StringProperty(default="*.bsp", options={"HIDDEN"}, maxlen=255)  # noqa F722
    # TODO: load_materials EnumProperty: None, Names, Base Colours, Nodes
    load_geometry: BoolProperty(name="Geometry", description="Load .bsp Geometry", default=True)  # noqa F722
    # TODO: load_lighting EnumProperty: None, Empties, All, PortalLights
    load_entities: BoolProperty(name="Entities", description="Load .bsp Entities", default=True)  # noqa F722
    load_brushes: EnumProperty(name="Brushes", description="Generate brush geometry",  # noqa F722
                               items=(("None", "No Brushes", "Empties at brush entity origins"),  # noqa F722
                                      ("Brushes", "Generate Brushes", "Generate brushes from planes stored in the entity")),  # noqa F722
                               default="Brushes")  # noqa F722
    # TODO: load_prop_dynamic EnumProperty: None, Empties, Low-Poly, High-Poly
    # TODO: load_prop_static EnumProperty: None, Empties, Low-Poly, High-Poly, Skybox Only
    # -- https://gist.github.com/warmist/c9efdd4d84f8f97aff806fdbb3853ac8
    # -- ^ physics models (rotation yet to be completed)
    # TODO: adapt warmist's .phy converter to tackle the .bsp PHYSICS_COLLIDE lump
    load_props: EnumProperty(name="Props", description="Load smaller models",  # noqa F722
                             items=(("None", "No Props", "Decent performance"),  # noqa F722
                                    ("Empties", "Use Empties", "Place empties at prop origins"),  # noqa F722
                                    ("Instances", "Instanced Collections", "Full props & materials; Very slow")),  # noqa F722
                             default="None")  # noqa F722
    # TODO: cubemap volumes?
    # TODO: Lock out some options if SourceIO is not installed, alert the user
    # TODO: Warnings for missing files
    # TODO: Lightmaps (export to file(s) and append to materials (would require splitting materials up more))

    def execute(self, context):
        """Import selected .bsp"""
        # TODO: loading % indicators
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
        # TODO: locate Legion+ / vmt materials folder and build shaders
        materials = importer.materials.base_colours(bsp)
        # if bsp.branch == bsp_tool.branches.respawn.titanfall2:  # HACK
        #     materials = importer.materials.textured(bsp)
        # geometry
        if self.load_geometry:
            # TODO: rename Model[0] "worldspawn"
            # TODO: skybox collection
            # TODO: load specific model / mesh (e.g. worldspawn only, skip tool brushes etc.)
            importer.geometry.split_meshes(bsp, master_collection, materials)
        # entities
        # TODO: get a user defined palette in here (use a property group?)
        # -- FloatVectorProperty(subtype="COLOR")  # ?
        brush_entity_classnames = ["envmap_volume",
                                   "light_probe_volume",
                                   "light_environment_volume",
                                   "trigger_capture_point",
                                   "trigger_hurt",
                                   "trigger_indoor_area",
                                   "trigger_multiple",
                                   "trigger_once",
                                   "trigger_out_of_bounds",
                                   "trigger_soundscape"]
        if self.load_brushes == "Brushes":
            brushes_entities = {classname: importer.entities.trigger_brushes for classname in brush_entity_classnames}
            importer.entities.ent_object_data.update(brushes_entities)
        if self.load_entities:
            # TODO: link worldspawn to Model[0]
            importer.entities.all_entities(bsp, master_collection)
            # NOTE: includes lights, square info_node* & speakers
            # NOTE: Eevee has limited lighting, try Cycles
        # props
        if self.load_props == "Empties":
            importer.props.as_empties(bsp, master_collection)
        elif self.load_props == "Instances":
            importer.props.static_props(bsp, master_collection)
        # TODO: scale the whole import (Engine Units -> Inches)
        # TODO: override default view / camera (near, far) clipping -> (16, 102400)
        return {"FINISHED"}


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportRBSP.bl_idname, text=ImportRBSP.bl_label)


def register():
    preferences.register()
    bpy.utils.register_submodule_factory(__name__, ("bsp_tool", "rbsp"))
    bpy.utils.register_class(ImportRBSP)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    preferences.unregister()
    bpy.utils.unregister_class(ImportRBSP)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
