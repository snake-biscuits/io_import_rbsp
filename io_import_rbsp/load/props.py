import os

import bpy
import mathutils

from bpy.types import Collection

from ass.scene.valve import Mdl


# TODO: break down model paths as collections
# foliage > ...
# auto-hide large collections (> 1000 props)


def as_empties(bsp, prop_collection: Collection):
    """Requires all models to be extracted beforehand"""
    for prop in bsp.GAME_LUMP.sprp.props:
        prop_object = bpy.data.objects.new(
            bsp.GAME_LUMP.sprp.model_names[prop.model_name], None)
        # TODO: link mesh data by model_name
        prop_object.empty_display_type = "SPHERE"
        prop_object.empty_display_size = 64
        prop_object.location = [*prop.origin]
        prop_object.rotation_euler = mathutils.Euler(
            (prop.angles[2], prop.angles[0], 90 + prop.angles[1]))
        prop_collection.objects.link(prop_object)


def static_props(bsp, prop_collection: Collection):
    # load models [WIP]
    vpk_folder = bpy.context.scene.rbsp_prefs.vpk_folder
    if not os.path.isdir(vpk_folder):
        return
    # TODO: instance model data
    for model_name in bsp.GAME_LUMP.model_names:
        load_model(vpk_folder, )

    # place models [WIP]
    for prop in bsp.GAME_LUMP.props:
        # TODO:
        # -- select model
        # -- instance w/ position, rotation & scale
        # -- diffuse colour custom attribute?
        ...


# TODO: expose to blender for easier testing
def load_model(vpk_folder: str, model_name: str):
    # TODO: case insensitive search for model_name in vpk_folder
    # -- see load.materials
    mdl = Mdl.from_file(os.path.join(vpk_folder, f"{model_name}.mdl"))
    mdl.parse()
    base_name = os.path.basename(model_name)
    model = mdl.models[f"{base_name}.lod0"]
    ...
    # TODO: model -> Blender Model
    # -- see load.geometry.all_model
    # TODO: model.meshes[...].material -> Blender Material
    # -- see load.materials.NodeMaker.material_from_name
    # -- "{material.name}_fix.json", not `wld`!
