from __future__ import annotations

import enum
import os

import bpy
from bpy.types import Material


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


# NOTE: entries marked w/ "*" aren't implemented
class Slot(enum.Enum):
    ALBEDO = 0
    NORMAL = 1
    GLOSS = 2
    SPECULAR = 3
    ILLUMINATION = 4
    AMBIENT_OCCLUSION = 11  # *
    CAVITY = 12  # *
    OPACITY = 13
    DETAIL_ALBEDO = 14  # *
    DETAIL_NORMAL = 15
    UV_DISTORTION = 18  # *
    UV_DISTORTION_2 = 19  # *
    BLEND = 22
    ALBEDO_2 = 23
    NORMAL_2 = 24
    GLOSS_2 = 25
    SPECULAR_2 = 26


# NOTE: assumes "/" path separator in filename
def search(folder: str, filename: str) -> str:
    if not os.path.isdir(folder):
        return None  # dead end
    steps = filename.split("/")
    target = steps[0].lower()
    for filename in os.listdir(folder):
        if filename.lower() == target:
            if len(steps) > 1:  # 1 layer searched
                next_folder = "/".join([folder, filename])
                next_filename = "/".join(steps[1:])
                return search(next_folder, next_filename)
            else:
                return os.path.join(folder, filename)  # full match!
    return None  # file not found


def placeholder(asset_path: str, palette=tool_colours) -> Material:
    """make a placeholder material to be loaded later"""
    materials = [
        material.get("asset_path", None)
        for material in bpy.data.materials]
    if asset_path in materials:
        material_index = materials.index(asset_path)
        return bpy.data.materials[material_index]

    folder, filename = os.path.split(asset_path)
    material = bpy.data.materials.new(filename)
    material["asset_path"] = asset_path

    # asset_path -> viewport colour & alpha
    *colour, alpha = palette.get(
        asset_path, (0.8, 0.8, 0.8, 1.0))
    if asset_path.startswith("world/atmosphere"):
        alpha = 0.25

    # apply viewport colour & alpha
    if alpha != 1:
        material.blend_method = "BLEND"
    material.diffuse_color = (*colour, alpha)
    return material
