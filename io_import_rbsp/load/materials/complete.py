import bpy

from .wld import WorldMaterial
# from .fix import FixMaterial


def all_materials():
    for material in bpy.data.materials:
        if "is_placeholder" not in material:
            continue  # already loaded
        if "asset_path" not in material:
            continue  # not one of our placeholders
        shader_type = material.get("shader_type", None)
        if shader_type == "wld":
            WorldMaterial.nodeify(material)
            del material["is_placeholder"]
        # elif shader_type == "fix":
        #     FixMaterial.nodeify(material)
