from __future__ import annotations
from typing import Dict

from bpy.types import ImageTexture, Material

from .utils import Slot
from .matl import MATL
from . import wld


class FixMaterial(wld.WorldMaterial):
    """static prop shader constructor"""
    material: Material
    textures: Dict[Slot, ImageTexture]

    def add_albedo(self, texture, shader):
        # use prop.diffuse_modulation instead of vertex_colour
        diffuse_colour = self.add_node("ShaderNodeObjectInfo")
        texture_node = self.add_texture(texture, "Albedo", True)
        colour_mix = self.add_node("ShaderNodeMix")
        colour_mix.data_type = "RGBA"
        colour_mix.blend_type = "MULTIPLY"
        colour_mix.inputs[0].default_value = 1
        self.link_nodes(diffuse_colour, "Color", colour_mix, "A")
        self.link_nodes(texture_node, "Color", colour_mix, "B")
        self.link_nodes(colour_mix, "Result", shader, "Base Color")
        self.link_nodes(texture_node, "Alpha", shader, "Alpha")
        return texture_node

    # TODO: add_blend
    # -- does diffuse_modulation force a prop-wide alpha for _bm_fix?
    # -- model "levels_terrain/mp_homestead/homestead_ter_road_03_NOCOL.mdl"
    # -- material "world/dirt/dirt_forest_tracks_01_bm_transparent" fix
    # -- material "world/dirt/dirt_forest_water_puddles_dirt_tracks_01_bm" fix

    # TODO: from_matl & from_vmt @classmethods
    # -- change shader node & connection rules based on shader_set
    # -- "Unlit" in shader_set_name or "Emit" in shader_set_name

    @classmethod
    def nodeify(cls, material: Material):
        out = cls()
        out.material = material
        asset_path = material["asset_path"]
        # assert material["shader_type"] == "fix"

        # try for vmt material (r1 & r2 [RARE])
        # vmt = VMT.from_path(asset_path)
        # if vmt is not None:  # .vmt found
        #     out.material["shader"] = vmt.shader
        #     out.textures = vmt.textures
        #     out.make_nodes()
        #     return out.material

        # try for rpak material (r2 & r5)
        matl = MATL.from_path(asset_path, "fix")
        if matl is not None:  # found MATL .json
            out.material["shader_set"] = matl.shader_set_name
            out.textures = matl.textures
            out.make_nodes()
            return out.material

        # file not found, keep placeholder
        return out.material
