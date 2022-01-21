import os

import addon_utils
import bpy
import mathutils


# TODO: break down model paths as collections
# foliage > ...
# auto-hide large collections (> 1000 props)


def as_empties(bsp, master_collection: bpy.types.Collection):
    """Requires all models to be extracted beforehand"""
    prop_collection = bpy.data.collections.new("static props")
    master_collection.children.link(prop_collection)
    for prop in bsp.GAME_LUMP.sprp.props:
        prop_object = bpy.data.objects.new(bsp.GAME_LUMP.sprp.model_names[prop.model_name], None)
        # TODO: link mesh data by model_name
        prop_object.empty_display_type = "SPHERE"
        prop_object.empty_display_size = 64
        prop_object.location = [*prop.origin]
        prop_object.rotation_euler = mathutils.Euler((prop.angles[2], prop.angles[0], 90 + prop.angles[1]))
        prop_collection.objects.link(prop_object)


def all_models(bsp, master_collection: bpy.types.Collection):
    # NOTE: runs post entities, so we should mutate the existing empties (if loaded...)
    raise NotImplementedError()
    static_props(bsp, master_collection)  # <- creates prop collection
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


def static_props(bsp, master_collection: bpy.types.Collection):
    """https://github.com/llennoco22/Apex-mprt-importer-for-Blender/blob/main/ApexMapImporter/panel_op.py"""
    dependencies = {"SourceIO": "https://github.com/REDxEYE/SourceIO/releases"}
    addons = [m.__name__ for m in addon_utils.modules()]
    for addon_name in dependencies:
        assert addon_name in addons, f"Install {addon_name} from {dependencies[addon_name]}"
    models_folder = bpy.context.scene.rbsp_prefs.models_folder
    if not os.path.isdir(models_folder):
        raise FileNotFoundError(f"Models path ({models_folder}) is not a folder")
    for model_name in bsp.GAME_LUMP.model_names:
        bpy.ops.source_io.mdl(filepath=models_folder, files=[{"name": model_name}])
        # NOTE: SourceIO makes collections for each model (use instanced collections?)
        # NOTE: import scale?
        # Collection: body; model(s): body_dmx/{prop_name}_LOD0.dmx (may not match!)
        # but if we delete the bodygroup collections we can always match it's contents
        ...
        # TODO: move collection to a base collection
    for prop in bsp.GAME_LUMP.props:
        # TODO: instance and place
        ...
