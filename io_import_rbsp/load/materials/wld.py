from __future__ import annotations
from typing import Dict

from bpy.types import ImageTexture, Material, Node

from .utils import Slot
from .matl import MATL


class WorldMaterial:
    """generic level geometry shader constructor"""
    material: Material
    textures: Dict[Slot, ImageTexture]

    def __init__(self):
        self.material = None
        self.textures = dict()

    def add_albedo(self, texture, shader):
        vertex_colour = self.add_node("ShaderNodeVertexColor")
        texture_node = self.add_texture(texture, "Albedo", True)
        colour_mix = self.add_node("ShaderNodeMix")
        colour_mix.data_type = "RGBA"
        colour_mix.blend_type = "MULTIPLY"
        colour_mix.inputs[0].default_value = 1
        self.link_nodes(vertex_colour, "Color", colour_mix, "A")
        self.link_nodes(texture_node, "Color", colour_mix, "B")
        self.link_nodes(colour_mix, "Result", shader, "Base Color")
        self.link_nodes(texture_node, "Alpha", shader, "Alpha")
        return texture_node

    def add_blend(self, texture, mix_shader):
        """quick & dirty blend modulate approximation"""
        vertex_colour = self.add_node("ShaderNodeVertexColor")
        texture_node = self.add_texture(texture, "Blend Mask")
        # quick & dirty blend math that looks good enough
        mix_node = self.add_mixer("MIX")
        add_node = self.add_mixer("ADD")
        sub_node = self.add_mixer("SUBTRACT")
        self.link_nodes(vertex_colour, "Alpha", add_node, "A")
        self.link_nodes(texture_node, "Color", add_node, "B")
        self.link_nodes(vertex_colour, "Alpha", sub_node, "A")
        self.link_nodes(texture_node, "Color", sub_node, "B")
        self.link_nodes(vertex_colour, "Alpha", mix_node, "Factor")
        self.link_nodes(sub_node, "Result", mix_node, "A")
        self.link_nodes(add_node, "Result", mix_node, "B")
        self.link_nodes(mix_node, "Result", mix_shader, "Fac")

    def add_mixer(self, mode, fac=1):
        mix_node = self.add_node("ShaderNodeMix")
        mix_node.data_type = "RGBA"
        mix_node.blend_type = mode
        mix_node.inputs[0].default_value = fac
        return mix_node

    def add_gloss(self, texture, shader):
        """inverse of roughness"""
        texture_node = self.add_texture(texture, "Gloss", True)
        invert = self.add_node("ShaderNodeInvert")
        self.link_nodes(texture_node, "Color", invert, "Color")
        self.link_nodes(invert, "Color", shader, "Roughness")

    def add_illumination(self, texture, shader):
        texture_node = self.add_texture(texture, "Illumination", True)
        self.link_nodes(texture_node, "Color", shader, "Emission Color")
        self.link_nodes(texture_node, "Alpha", shader, "Emission Strength")

    def add_node(self, name):
        return self.material.node_tree.nodes.new(name)

    def add_normal(self, texture):
        """assumes blue normal"""
        texture_node = self.add_texture(texture, "Normal Map")
        map_node = self.add_node("ShaderNodeNormalMap")
        self.link_nodes(texture_node, "Color", map_node, "Color")
        return map_node  # link to Shader.Normal / MaterialOutput.Displacement

    def add_opacity(self, texture, shader):
        texture_node = self.add_texture(texture, "Opacity")
        self.link_nodes(texture_node, "Color", shader, "Alpha")
        self.material.blend_method = "BLEND"

    def add_specular(self, texture, shader):
        texture_node = self.add_texture(texture, "Specular", True)
        self.link_nodes(texture_node, "Color", shader, "Specular Tint")

    def add_texture(self, texture, label="", albedo=False) -> Node:
        """basic texture node"""
        node = self.add_node("ShaderNodeTexImage")
        node.image = texture
        colourspace = "sRGB" if albedo else "Non-Color"
        node.image.colorspace_settings.name = colourspace
        node.label = label
        return node

    def link_nodes(self, out_node, out_slot, in_node, in_slot):
        self.material.node_tree.links.new(
            out_node.outputs[out_slot],
            in_node.inputs[in_slot])

    def setup_shader_a(self):
        shader_a = self.material.node_tree.nodes["Principled BSDF"]
        frame_a = self.add_node("NodeFrame")
        frame_a.label = "Shader A"
        frame_a.use_custom_color = True
        frame_a.color = (0.85, 0.65, 0.25)
        frame_a.location = (-880, 460)
        shader_a.parent = frame_a
        return shader_a, frame_a

    def setup_shader_b(self):
        shader_b = self.add_node("ShaderNodeBsdfPrincipled")
        frame_b = self.add_node("NodeFrame")
        frame_b.label = "Shader B"
        frame_b.use_custom_color = True
        frame_b.color = (0.15, 0.70, 0.40)
        frame_b.location = (-880, 460)
        shader_b.parent = frame_b
        return shader_b, frame_b

    def setup_mix_shader(self, shader_a, shader_b):
        mix_shader = self.add_node("ShaderNodeMixShader")
        mix_shader.location = (1000, 50)
        self.link_nodes(shader_a, 0, mix_shader, 1)
        self.link_nodes(shader_b, 0, mix_shader, 2)
        output = self.material.node_tree.nodes["Material Output"]
        output.location = (1300, 100)
        self.link_nodes(mix_shader, 0, output, "Surface")
        return mix_shader

    def make_nodes(self):
        self.material.use_nodes = True
        shader_a, frame_a = self.setup_shader_a()
        if Slot.BLEND in self.textures:  # _bm_wld
            shader_b, frame_b = self.setup_shader_b()
            mix_shader = self.setup_mix_shader(shader_a, shader_b)
        # textures
        for slot, texture in self.textures.items():
            if slot == Slot.ALBEDO:
                self.add_albedo(texture, shader_a)
            elif slot == Slot.ALBEDO_2:
                self.add_albedo(texture, shader_b)
            elif slot == Slot.SPECULAR:
                self.add_specular(texture, shader_a)
            elif slot == Slot.SPECULAR_2:
                self.add_specular(texture, shader_b)
            elif slot == Slot.GLOSS:
                self.add_gloss(texture, shader_a)
            elif slot == Slot.GLOSS_2:
                self.add_gloss(texture, shader_b)
            elif slot == Slot.NORMAL:
                map_node = self.add_normal(texture)
                self.link_nodes(map_node, "Normal", shader_a, "Normal")
            elif slot == Slot.NORMAL_2:
                map_node = self.add_normal(texture)
                self.link_nodes(map_node, "Normal", shader_b, "Normal")
            elif slot == Slot.BLEND:
                self.add_blend(texture, mix_shader)
            elif slot == Slot.DETAIL_NORMAL:
                map_node = self.add_normal(texture)
                output = self.material.node_tree.nodes["Material Output"]
                self.link_nodes(map_node, "Normal", output, "Displacement")
            elif slot == Slot.ILLUMINATION:
                self.add_illumination(texture, shader_a)
            elif slot == Slot.OPACITY:
                self.add_opacity(texture, shader_a)
            # NOTE: skipping unimplemented slots
        # TODO: organisation pass (set node locations)
        # TODO: make locations relative to links

    @classmethod
    def nodeify(cls, material: Material):
        out = cls()
        out.material = material
        asset_path = material["asset_path"]
        # NOTE: shader_type is not set in placeholder
        # -- the caller handles it instead
        # -- "wld" for .bsp geo; "fix" for .mdl geo

        # try for vmt material (r1 & r2 [RARE])
        # vmt = VMT.from_path(asset_path)
        # if vmt is not None:  # .vmt found
        #     out.textures = vmt.textures
        #     out.make_nodes()
        #     return out.material

        # try for rpak material (r2 & r5)
        matl = MATL.from_path(asset_path, "wld")
        if matl is not None:  # found MATL .json
            out.textures = matl.textures
            out.make_nodes()
            return out.material

        return out.material
