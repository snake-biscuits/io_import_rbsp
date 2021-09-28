import bpy

from typing import List


def base_colours(bsp) -> List[bpy.types.Material]:
    materials = list()
    tool_texture_colours = {"TOOLS\\TOOLSBLACK": (0, 0, 0, 1),
                            "TOOLS\\TOOLSENVMAPVOLUME": (0.752, 0.0, 0.972, .25),
                            "TOOLS\\TOOLSFOGVOLUME": (0.752, 0.0, 0.972, .25),
                            "TOOLS\\TOOLSLIGHTPROBEVOLUME": (0.752, 0.0, 0.972, .25),
                            "TOOLS\\TOOLSOUT_OF_BOUNDS": (0.913, 0.39, 0.003, .25),
                            "TOOLS\\TOOLSSKYBOX": (0.441, 0.742, 0.967, .25),
                            "TOOLS\\TOOLSTRIGGER": (0.944, 0.048, 0.004, .25),
                            "TOOLS\\TOOLSTRIGGER_CAPTUREPOINT": (0.273, 0.104, 0.409, .25)}
    for i, vmt_name in enumerate(bsp.SURFACE_NAMES):
        material = bpy.data.materials.new(vmt_name)
        *colour, alpha = tool_texture_colours.get(vmt_name, (0.8, 0.8, 0.8, 1.0))
        alpha = 0.25 if vmt_name.startswith("world\\atmosphere") else alpha
        material.diffuse_color = (*colour, alpha)
        if alpha != 1:
            material.blend_method = "BLEND"
        materials.append(material)
    return materials
