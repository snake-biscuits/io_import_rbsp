import bpy
import mathutils


def as_empties(bsp, master_collection):
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


def as_models(bsp, master_collection):
    raise NotImplementedError()
    # model_dir = os.path.join(game_dir, "models")
    # TODO: hook into SourceIO to import .mdl files
    # TODO: make a collection for static props
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
