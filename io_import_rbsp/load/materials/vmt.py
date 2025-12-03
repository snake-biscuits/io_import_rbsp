from __future__ import annotations
import os
from typing import Dict

import bpy
from bpy.types import ImageTexture

from .utils import search, Slot


# TODO: .vtf -> blender texture
# -- can we load .dds from bytes?
# -- link temporary files?
def load_vtf(asset_dir: str, asset_path: str) -> ImageTexture:
    raise NotImplementedError()
    # texture_path = search(asset_dir, f"{asset_path}.vtf")
    # image = PIL.Image.frombytes(vtf.mipmaps[...])
    # texture = bpy.data.images.new(
    #     texture_path, width=image.width, height=image.height)
    # pixel_array = np.asarray(image.convert("RGBA"), dtype=np.float32)
    # texture.pixels[::] = (pixel_array / 255).ravel()


class VMT:
    """Valve Material w/ some respawn-specific features"""
    vpk_folder: str
    textures: Dict[Slot, ImageTexture]
    # ^ {Slot.ALBEDO: ImageTexture}
    # TODO: shader type -> node maker

    def __init__(self):
        self.vpk_folder = bpy.context.scene.rbsp_prefs.vpk_folder
        self.textures = dict()

    def load_texture(self, slot: Slot, asset_path: str) -> ImageTexture:
        search_folder = os.path.join(self.vpk_folder, "materials")
        texture = load_vtf(search_folder, asset_path)
        if texture is not None:
            self.textures[slot] = texture
        # TODO: error texture w/ asset path

    @classmethod
    def from_path(cls, asset_path: str) -> VMT:
        vpk_folder = bpy.context.scene.rbsp_prefs.vpk_folder
        search_folder = os.path.join(vpk_folder, "materials")
        vmt_path = search(search_folder, f"{asset_path}.vmt")
        if vmt_path is not None:
            return cls.from_file(vmt_path)

    @classmethod
    def from_file(cls, filename: str):
        raise NotImplementedError()
        # vmt = bite.Vmt.from_file(vmt_path)
        # return cls.from_vmt(vmt)

    @classmethod
    def from_vmt(cls, vmt) -> VMT:
        raise NotImplementedError()
        out = cls()
        # $baseTexture -> out.load_texture(Slot.ALBEDO, ...)
        return out
