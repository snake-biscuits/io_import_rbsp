from __future__ import annotations
import json
import os
from typing import Dict

import bpy
from bpy.types import ImageTexture

from .utils import search, Slot


# NOTE: if RSX does not export all mips, filenames might not match
def load_dds(asset_dir: str, asset_path: str) -> ImageTexture:
    textures = [
        texture.get("asset_path", None)
        for texture in bpy.data.images]
    if asset_path in textures:
        texture_index = textures.index(asset_path)
        return bpy.data.images[texture_index]

    full_path = search(asset_dir, asset_path)
    if full_path is None:
        return None  # file not found

    texture = bpy.data.images.load(full_path)
    texture["asset_path"] = asset_path
    return texture


class MATL:
    """Titanfall 2 & Apex Legends .rpak material"""
    rsx_folder: str
    textures: Dict[Slot, ImageTexture]
    # ^ {Slot.ALBEDO: ImageTexture}

    def __init__(self):
        self.rsx_folder = bpy.context.scene.rbsp_prefs.rsx_folder
        self.textures = dict()

    def load_texture(self, slot: Slot, asset_path: str):
        search_folder = os.path.join(self.rsx_folder, "exported_files")
        assert asset_path.endswith(".rpak")
        asset_path = f"{asset_path[:-5]}.dds"
        texture = load_dds(search_folder, asset_path)
        if texture is not None:
            self.textures[slot] = texture
        # TODO: error texture w/ asset path

    @classmethod
    def from_path(cls, asset_path: str, type_: str) -> MATL:
        rsx_folder = bpy.context.scene.rbsp_prefs.rsx_folder
        search_folder = os.path.join(rsx_folder, "exported_files/material")
        json_path = search(search_folder, f"{asset_path}_{type_}.json")
        if json_path is not None:
            return cls.from_file(json_path)

    @classmethod
    def from_file(cls, filename: str) -> MATL:
        with open(filename) as json_file:
            return cls.from_json(json.load(json_file))

    @classmethod
    def from_json(cls, json_: Dict) -> MATL:
        out = cls()
        matl_textures = json_.get("$textures", dict())
        matl_slot_names = json_.get("$textureTypes")
        for key, asset_path in matl_textures.items():
            try:
                slot = Slot(int(key))
            except ValueError:
                slot = (int(key), matl_slot_names.get(key, None))
            if not asset_path.startswith("0x"):  # not a GUID
                out.load_texture(slot, asset_path)
        return out
