from typing import List

import bpy
from bsp.types import Material


tool_colours = {
    "tools/toolsblack": (0, 0, 0, 1),
    "tools/toolsblockbullets": (0.914, 0.204, 0.0, .25),
    "tools/toolsblocklight": (0.376, 0.582, 0.129, .25),
    "tools/toolsclip": (0.665, 0.051, 0.024, .25),
    "tools/toolsenvmapvolume": (0.752, 0.0, 0.972, .25),
    "tools/toolsfogvolume": (0.752, 0.0, 0.972, .25),
    "tools/toolsinvisible": (0.705, 0.0, 0.256, .25),
    "tools/toolslightprobevolume": (0.752, 0.0, 0.972, .25),
    "tools/toolsnodraw": (0.913, 0.67, 0.012, 1),
    "tools/npcclip": (0.29, 0.037, 0.67, .25),
    "tools/toolsout_of_bounds": (0.913, 0.39, 0.003, .25),
    "tools/toolsplayerclip": (0.629, 0.08, 0.28, .25),
    "tools/toolsskybox": (0.441, 0.742, 0.967, .25),
    "tools/toolstrigger": (0.944, 0.048, 0.004, .25),
    "tools/toolstrigger_capturepoint": (0.273, 0.104, 0.409, .25)}


def base_colours(bsp, palette=tool_colours) -> List[Material]:
    materials = list()
    for i, vmt_name in enumerate(bsp.SURFACE_NAMES):
        material = bpy.data.materials.new(vmt_name)
        *colour, alpha = palette.get(vmt_name.lower(), (0.8, 0.8, 0.8, 1.0))
        # TODO: bsp.branch.Flags(td.flags) & bsp.branch.Flags.TRANSLUCENT
        alpha = 0.25 if vmt_name.startswith("world/atmosphere") else alpha
        material.diffuse_color = (*colour, alpha)
        if alpha != 1:
            material.blend_method = "BLEND"
        materials.append(material)
    return materials
