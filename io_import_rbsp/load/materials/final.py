# from .wld import WorldMaterial


# NOTE: all_materials would be nice
# -- but we need to determine MaterialClass after loading MATL / VMT
# -- also need to search for _wld.json, _fix.json & .vmt
def complete(mesh, MaterialClass):
    for material in mesh.materials:
        if material.use_nodes:
            continue  # already loaded
        if "asset_path" not in material:
            continue  # not one of our placeholders
        # TODO: try to load VMT / MATL
        # -- shader type -> node assembler
        MaterialClass.nodeify(material)
