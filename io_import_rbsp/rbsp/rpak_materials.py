# by MySteyk & Dogecore
# TODO: extraction instructions & testing
import json
import os.path
from typing import List

import bpy


loaded_materials = {}

MATERIAL_LOAD_PATH = ""  # put your path here

# normal has special logic
MATERIAL_INPUT_LINKING = {
    "color": "Base Color",
    "rough": "Roughness",
    "spec": "Specular",
    "illumm": "Emission",
}


def load_material_data_from_name(subpath):
    full_path = MATERIAL_LOAD_PATH + subpath + ".json"
    if not os.path.isfile(full_path):
        return False
    return json.load(open(full_path, "rb"))


def load_image_from_subpath(subpath):
    full_path = MATERIAL_LOAD_PATH + subpath
    if not os.path.isfile(full_path):
        return False
    return bpy.data.images.load(full_path)


def load_materials(bsp) -> List[bpy.types.Material]:
    materials = []
    for material_name in bsp.TEXTURE_DATA_STRING_DATA:
        if material_name in loaded_materials:
            materials.append(loaded_materials[material_name])
            continue
        mat_data = load_material_data_from_name(material_name)
        material = bpy.data.materials.new("materials/" + material_name)
        if not mat_data:
            loaded_materials[material_name] = material
            materials.append(material)
            # raise ValueError(f"Material data for material {material_name} does not exist!")
            continue
        # print(material_name, mat_data)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        # data link
        for mat_data_entry in MATERIAL_INPUT_LINKING.keys():
            texture_file = mat_data[mat_data_entry]
            if texture_file == "":
                print(f"Texture type {mat_data_entry} doesn't exist in {material_name}'s material data, skipping.")
                continue
            img = load_image_from_subpath(texture_file)
            if not img:
                raise ValueError(f"{material_name}'s texture {texture_file} ({mat_data_entry}) doesn't exist!")
                continue
            tex = material.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = img
            material.node_tree.links.new(bsdf.inputs[MATERIAL_INPUT_LINKING[mat_data_entry]], tex.outputs["Color"])
            if mat_data_entry == "color":
                material.node_tree.links.new(bsdf.inputs["Alpha"], tex.outputs["Alpha"])
        # normal link
        if mat_data["normal"] != "":
            texture_file = mat_data["normal"]
            normalmap = material.node_tree.nodes.new("ShaderNodeNormalMap")
            img = load_image_from_subpath(texture_file)
            if not img:
                raise ValueError(f"Texture {texture_file} for material {material_name} (normal) doesn't exist!")
                continue
            tex = material.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = img
            material.node_tree.links.new(normalmap.inputs["Color"], tex.outputs["Color"])
            material.node_tree.links.new(bsdf.inputs["Normal"], normalmap.outputs["Normal"])
        loaded_materials[material_name] = material
        materials.append(material)
    return materials
