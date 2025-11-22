import os

import addon_utils
import bpy
import mathutils

from bpy.types import Collection


# TODO: break down model paths as collections
# foliage > ...
# auto-hide large collections (> 1000 props)

# NOTE: SourceIO doesn't support v53 .mdl
# -- will have to roll our own model loader


def as_empties(bsp, bsp_collection: Collection):
    """Requires all models to be extracted beforehand"""
    prop_collection = bpy.data.collections.new("static props")
    bsp_collection.children.link(prop_collection)
    for prop in bsp.GAME_LUMP.sprp.props:
        prop_object = bpy.data.objects.new(bsp.GAME_LUMP.sprp.model_names[prop.model_name], None)
        # TODO: link mesh data by model_name
        prop_object.empty_display_type = "SPHERE"
        prop_object.empty_display_size = 64
        prop_object.location = [*prop.origin]
        prop_object.rotation_euler = mathutils.Euler((prop.angles[2], prop.angles[0], 90 + prop.angles[1]))
        prop_collection.objects.link(prop_object)


def all_models(bsp, bsp_collection: Collection):
    # NOTE: runs post entities, so we should mutate the existing empties (if loaded...)
    raise NotImplementedError()
    static_props(bsp, bsp_collection)  # <- creates prop collection
    # TODO: non-static prop entities:
    # -- prop_control_panel
    # -- prop_dynamic
    # -- prop_physics
    # -- prop_exfil_panel
    # -- prop_refuel_pump
    # -- prop_bigbrother_panel
    # ENTITIES_script "classname" .match("prop_\w+")
    # ENTITIES_script only?

    # try:
    #     bpy.ops.source_io.mdl(filepath=model_dir, files=[{"name": "error.mdl"}])
    # except Exception as exc:
    #     print("Source IO not installed!", exc)
    # else:
    #     for mdl_name in bsp.GAME_LUMP.sprp.mdl_names:
    #         bpy.ops.source_io.mdl(filepath=model_dir, files=[{"name": mdl_name}])
    # now find it..., each model creates a collection...
    # this is gonna be real memory intensive...
    # TODO: instance each prop at listed location & rotation etc. (preserve object data)


def static_props(bsp, bsp_collection: Collection):
    # check we have SourceIO installed for loading .mdl
    dependencies = {"SourceIO": "https://github.com/REDxEYE/SourceIO/releases"}
    addons = [m.__name__ for m in addon_utils.modules()]
    for addon, url in dependencies.items():
        assert addon in addons, f"Install {addon} from {url}"

    # load models [WIP]
    models_folder = bpy.context.scene.rbsp_prefs.models_folder
    if not os.path.isdir(models_folder):
        return
    for model_name in bsp.GAME_LUMP.model_names:
        # NOTE: SourceIO makes collections for each model (use instanced collections?)
        # NOTE: does SourceIO force an import scale?
        # Collection: body; model(s): body_dmx/{prop_name}_LOD0.dmx (may not match!)
        # but if we delete the bodygroup collections we can always match it's contents
        # TODO: relocate mdl collection
        bpy.ops.source_io.mdl(
            filepath=models_folder,
            files=[{"name": model_name}])
        ...

    # place models [WIP]
    for prop in bsp.GAME_LUMP.props:
        # TODO:
        # -- select model
        # -- instance w/ position, rotation & scale
        # -- diffuse colour custom attribute?
        ...
