from __future__ import annotations

import enum
import json
import os
from typing import Any, Dict

import bpy
from bpy.types import ImageTexture, Material, Node
import numpy as np


# TODO: pass failed asset loads up to be reported


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


# TODO: values should line up with matl "$textures" keys
class Slot(enum.Enum):
    ALBEDO = 0
    NORMAL = 1
    # TODO:
    # -- SPECULAR
    # -- CAVITY
    # -- GLOSS
    # -- OPACITY
    # -- duplicates for blendmodulate


def make_material(material_name, palette=tool_colours) -> Material:
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]
    # viewport colour & transparency
    material = bpy.data.materials.new(material_name)
    *colour, alpha = palette.get(
        material_name, (0.8, 0.8, 0.8, 1.0))
    if material_name.startswith("world/atmosphere"):
        alpha = 0.25
    # apply
    if alpha != 1:
        material.blend_method = "BLEND"
    material.diffuse_color = (*colour, alpha)
    # full nodes
    make_nodes(material)


def make_nodes(material: Material):
    material.use_nodes = True
    vmt = Vmt.from_material(material)
    matl = Matl.from_material(material)
    # TODO: metadata
    # -- shader node type
    # -- material type (blendmodulate etc.)
    # load textures
    textures = {
        **vmt.textures,
        **matl.textures}
    # make & use nodes for textures
    shader_node = material.node_tree.nodes["Principled BSDF"]
    for slot, texture in textures.items():
        add_node[slot](material, texture, shader_node)
    # TODO: vertex colour nodes if shader requires it
    # -- blendmodule blend factor


# textures
def add_texture(material, texture, label="") -> Node:
    """basic texture node"""
    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = texture
    node.label = label
    return node


def link_nodes(material, out_node, out_slot, in_node, in_slot):
    material.node_tree.links.new(
        out_node.outputs[out_slot],
        in_node.inputs[in_slot])


def add_albedo(material, texture, shader_node):
    texture_node = add_texture(material, texture, "Albedo")
    texture_node.location.x -= texture_node.width * 1.5
    texture_node.location.y += texture_node.height * 3
    link_nodes(texture_node, "Color", shader_node, "Base Color")
    link_nodes(texture_node, "Alpha", shader_node, "Alpha")


def add_normal(material, texture, shader_node):
    texture_node = add_texture(material, texture, "Normal Map")
    texture_node.image.colorspace_settings.name = "Non-Color"
    texture_node.location.x -= texture_node.width * 1.5
    texture_node.location.y += texture_node.height
    normal_map_node = material.node_tree.nodes.new("ShaderNodeNormalMap")
    normal_map_node.location.x -= normal_map_node.width * 1.5
    normal_map_node.location.y += normal_map_node.height
    link_nodes(texture_node, "Color", normal_map_node, "Color")
    link_nodes(normal_map_node, "Normal", shader_node, "Normal")


# defaults (load texture, but don't link)
add_node = {
    slot: lambda m, t, x: add_texture(m, t, slot.name)
    for slot in Slot}
# full integration
add_node.update({
    Slot.ALBEDO: add_albedo,
    Slot.NORMAL: add_normal})
# TODO: more slots


# material formats
class MaterialFormat:
    assets_folder: str
    textures: Dict[Slot, Any]
    # ^ {Slot.ALBEDO: ImageTexture}

    def __init__(self):
        self.textures = dict()


# TODO: guide users on what RSX settings to use when exporting
class Matl(MaterialFormat):
    """Titanfall 2 & Apex Legends .rpak material"""
    assets_folder = bpy.context.scene.rbsp_prefs.rsx_folder
    # TODO: confirm the assets folder is real
    # NOTE: assets_folder should contain rsx.exe
    # -- we go down into exported_files/
    # -- could potentially run rsx w/ some command line args in future

    @classmethod
    def load_texture(cls, texture_path: str) -> ImageTexture:
        raise NotImplementedError()
        # texture/material_col.rpak -> ImageTexture
        # texture_folder = ...
        # texture_base_name = os.path.split_ext(texture_path)[0]
        # TODO: will this catch .dds w/ 1 file per mip level?
        # fnmatch.filter(os.listdir(texture_folder), f"{texture_base_name}.*")
        # texture_path = ...
        # TODO: return None if FileNotFound
        full_texture_path = os.path.join(cls.assets_folder, texture_path)
        # TODO: check to see if texture is already loaded
        # -- return if found
        texture = bpy.data.images.load(full_texture_path)
        assert texture.name == full_texture_path
        # NOTE: if true, checking it's already been loaded will be easy
        return texture

    @classmethod
    def from_material(cls, material: Material) -> Matl:
        json_filename = os.path.join(
            cls.assets_folder,
            "exported_files/material",
            f"{material.name}.json")
        if not os.path.exists(json_filename):
            return cls()
        else:
            return cls.from_filename(json_filename)

    @classmethod
    def from_filename(cls, filename: str) -> Matl:
        with open(filename) as json_file:
            return cls.from_json(json.load(json_file))

    @classmethod
    def from_json(cls, json_: Dict) -> Matl:
        out = cls()
        matl_textures = json_.get("$textures", dict())
        raise NotImplementedError()
        out.textures = {
            Slot(i): cls.load_texture(texture_path)
            for i, texture_path in matl_textures.items()}
        # TODO: out.shader_type = lookup_table[json_["shaderSet"]]
        # -- shaderSet
        return out


class Vmt:
    """Valve Material w/ some respawn-specific features"""
    assets_folder = bpy.context.scene.rbsp_prefs.vpk_folder

    @classmethod
    def load_texture(cls, texture_path: str) -> ImageTexture:
        full_texture_path = os.path.join(cls.assets_folder, texture_path)
        if not os.path.exists(full_texture_path):
            return None
        # TODO: check to see if texture is already loaded
        # -- return if found
        # TODO: .vtf -> PIL.Image (@ target miplevel)
        # -- MRVN-VMT & respawn_cubemap_tool should be good references
        # -- or maybe SourceIO
        # NOTE: Pillow should be available as a dependency of bsp_tool
        image = ...
        raise NotImplementedError()
        texture = bpy.data.images.new(
            texture_path, width=image.width, height=image.height)
        pixel_array = np.asarray(image.convert("RGBA"), dtype=np.float32)
        texture.pixels[::] = (pixel_array / 255).ravel()
        return texture

    @classmethod
    def from_material(cls, material) -> Vmt:
        out = cls()
        raise NotImplementedError()
        # TODO: parse .vmt (see MRVN-VMT)
        # -- shader type
        vtfs: Dict[Slot, str] = ...
        out.textures = {
            slot: cls.load_texture(texture_path)
            for slot, texture_path in vtfs}
        return out
