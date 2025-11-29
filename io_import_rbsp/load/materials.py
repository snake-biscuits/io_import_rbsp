from __future__ import annotations

import enum
import json
import os
from typing import Any, Dict

import bpy
from bpy.types import ImageTexture, Material, Node
import numpy as np


# TODO:
# -- don't load textures more than once each
# -- store metadata in material custom properties


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
    """wld matl texture slots"""
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


# TODO: shaderset -> preset (_bm_wld) etc.
# -- base shader node type
class NodeMaker:
    material: Material
    textures: Dict[Slot, str]

    def __init__(self):
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

    # TODO: blend modulate group node
    # -- 6x math nodes
    # --- - vc.a bm.c
    # --- + +0.5 ^ (clamp) [blend_factor]
    # --- * -2.0 ^
    # --- + +3.0 ^
    # --- * vc.a ^ [curve]
    # --- * vc.a [blend_factor]
    def add_blend(self, texture, mix_shader):
        """quick & dirty blend modulate approximation"""
        vertex_colour = self.add_node("ShaderNodeVertexColor")
        texture_node = self.add_texture(texture, "Blend Mask")
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
    def material_from_name(cls, name: str, palette=tool_colours):
        folder, filename = os.path.split(name)

        # return early if material already exists
        # NOTE: checking for filenames isn't ideal
        if filename in bpy.data.materials:
            return bpy.data.materials[filename]

        out = cls()
        out.material = bpy.data.materials.new(filename)
        # viewport colour & alpha from name
        *colour, alpha = palette.get(
            name, (0.8, 0.8, 0.8, 1.0))
        if name.startswith("world/atmosphere"):
            alpha = 0.25
        # set colour & alpha
        if alpha != 1:
            out.material.blend_method = "BLEND"
        out.material.diffuse_color = (*colour, alpha)

        # try for vmt material (r1 & r2 [RARE])
        # vmt = VMT.from_name(name)
        # if vmt is not None:  # .vmt found
        #     out.textures = vmt.textures
        #     out.make_nodes()
        #     return out.material

        # try for rpak material (r2 & r5)
        matl = MATL.from_name(name)
        if matl is not None:  # _wld.json found
            out.textures = matl.textures
            out.make_nodes()
            return out.material

        return out.material


class MATL:
    """Titanfall 2 & Apex Legends .rpak material"""
    rsx_folder: str
    textures: Dict[Slot, Any]
    # ^ {Slot.ALBEDO: ImageTexture}

    def __init__(self):
        self.rsx_folder = bpy.context.scene.rbsp_prefs.rsx_folder
        self.textures = dict()

    def load_texture(self, slot: Slot, texture_path: str) -> ImageTexture:
        if texture_path.startswith("0x"):
            return  # GUID, no filename
        # NOTE: .dds w/ all mips only
        # TODO: skip search if texture is already loaded
        folder, filename = os.path.split(texture_path)
        base_name = os.path.splitext(filename)[0]
        search_folder = os.path.join(
            self.rsx_folder, "exported_files", folder)
        if not os.path.isdir(search_folder):
            return
        # case insensitive file search
        search_filename = f"{base_name.lower()}.dds"
        for dds_filename in os.listdir(search_folder):
            if dds_filename.lower() == search_filename:
                dds_path = os.path.join(search_folder, dds_filename)
                texture = bpy.data.images.load(dds_path)
                self.textures[slot] = texture

    @classmethod
    def from_name(cls, name: str) -> MATL:
        rsx_folder = bpy.context.scene.rbsp_prefs.rsx_folder
        folder, filename = os.path.split(name)
        search_folder = os.path.join(
            rsx_folder, "exported_files/material", folder)
        if not os.path.isdir(search_folder):
            return
        # case insensitive file search
        search_filename = f"{filename.lower()}_wld.json"
        for json_filename in os.listdir(search_folder):
            if json_filename.lower() == search_filename:
                json_path = os.path.join(search_folder, json_filename)
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
        for key, texture_path in matl_textures.items():
            try:
                slot = Slot(int(key))
            except ValueError:
                slot = (int(key), matl_slot_names.get(key, None))
            out.load_texture(slot, texture_path)
        return out


class VMT:
    """Valve Material w/ some respawn-specific features"""
    vpk_folder: str
    textures: Dict[Slot, Any]
    # ^ {Slot.ALBEDO: ImageTexture}

    def __init__(self):
        self.vpk_folder = bpy.context.scene.rbsp_prefs.vpk_folder
        self.textures = dict()

    def load_texture(self, slot: Slot, texture_path: str) -> ImageTexture:
        full_texture_path = os.path.join(self.vpk_folder, texture_path)
        if not os.path.exists(full_texture_path):
            return None
        # TODO: check to see if texture is already loaded
        # -- return if found
        # TODO: .vtf -> PIL.Image (@ target miplevel)
        # -- MRVN-VMT & respawn_cubemap_tool should be good references
        # -- can we feed Blender the .vtf as a .dds? (convert w/ bite)
        # NOTE: Pillow should be available as a dependency of bsp_tool
        image = ...
        raise NotImplementedError()
        texture = bpy.data.images.new(
            texture_path, width=image.width, height=image.height)
        pixel_array = np.asarray(image.convert("RGBA"), dtype=np.float32)
        texture.pixels[::] = (pixel_array / 255).ravel()
        self.textures[slot] = texture

    @classmethod
    def from_name(cls, name) -> VMT:
        vpk_folder = bpy.context.scene.rbsp_prefs.vpk_folder
        out = cls()
        raise NotImplementedError()
        # TODO: parse .vmt (w/ `bite`)
        # -- shader type
        vtfs: Dict[Slot, str] = ...
        out.textures = {
            slot: cls.load_texture(texture_path)
            for slot, texture_path in vtfs}
        return out
