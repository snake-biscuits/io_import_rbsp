from typing import List

import bpy
from bpy.types import Material


def base_colours(bsp) -> List[Material]:
    materials = list()
    for i, vmt_name in enumerate(bsp.TEXTURE_DATA_STRING_DATA):
        material = bpy.data.materials.new(vmt_name)
        colour = [
            td.reflectivity
            for td in bsp.TEXTURE_DATA
            if td.name_index == i][0]
        alpha = 1.0 if not vmt_name.startswith("TOOLS") else 0.25
        material.diffuse_color = (*colour, alpha)
        if alpha != 1:
            material.blend_method = "BLEND"
        materials.append(material)
    return materials


# TODO: SourceIO .vmt & .vtf bulk import
