import os
from typing import List

import bpy


def base_colours(bsp) -> List[bpy.types.Material]:
    materials = list()
    tool_texture_colours = {"tools\\toolsblack": (0, 0, 0, 1),
                            "tools\\toolsblockbullets": (0.914, 0.204, 0.0, .25),
                            "tools\\toolsblocklight": (0.376, 0.582, 0.129, .25),
                            "tools\\toolsclip": (0.665, 0.051, 0.024, .25),
                            "tools\\toolsenvmapvolume": (0.752, 0.0, 0.972, .25),
                            "tools\\toolsfogvolume": (0.752, 0.0, 0.972, .25),
                            "tools\\toolsinvisible": (0.705, 0.0, 0.256, .25),
                            "tools\\toolslightprobevolume": (0.752, 0.0, 0.972, .25),
                            "tools\\toolsnodraw": (0.913, 0.67, 0.012, 1),
                            "tools\\npcclip": (0.29, 0.037, 0.67, .25),
                            "tools\\toolsout_of_bounds": (0.913, 0.39, 0.003, .25),
                            "tools\\toolsplayerclip": (0.629, 0.08, 0.28, .25),
                            "tools\\toolsskybox": (0.441, 0.742, 0.967, .25),
                            "tools\\toolstrigger": (0.944, 0.048, 0.004, .25),
                            "tools\\toolstrigger_capturepoint": (0.273, 0.104, 0.409, .25)}
    # TODO: TOOLS\TOOLSBLOCK_LOS
    # TODO: TOOLS\TOOLSBLOCK_LOS_N_CLIP
    # TODO: TOOLS\TOOLSCLIP
    # TODO: TOOLS\TOOLSCLIP_ALLOW_ABILITIES
    # TODO: TOOLS\TOOLSCLIP_GRATE
    # TODO: TOOLS\TOOLSCLIP_HUMAN
    # TODO: TOOLS\TOOLSCLIP_HUMAN_CLIMBABLE
    # TODO: TOOLS\TOOLSCLIP_HUMAN_SLIP
    # TODO: TOOLS\TOOLSCLIP_METAL
    # TODO: TOOLS\TOOLSCLIP_TITAN
    # TODO: TOOLS\TOOLSCLIP_VEHICLE_BARRIER
    # TODO: TOOLS\TOOLSEXPOSUREVOLUME
    # TODO: TOOLS\TOOLSNOAIRDROP
    # TODO: TOOLS\TOOLSNODRAW_GLASS_FOOTSTEPS
    # TODO: TOOLS\TOOLSSOUNDTRIGGER_CHAINLINK
    # TODO: TOOLS\TOOLSSOUNDTRIGGER_FOLIAGE
    # TODO: TOOLS\TOOLSTRIGGER_NO_ZIPLINE
    # TODO: TOOLS\TOOLS_CLIP_N_BLOCK
    # TODO: use TextureData instead
    for vmt_name in bsp.TEXTURE_DATA_STRING_DATA:
        material = bpy.data.materials.new(vmt_name)
        *colour, alpha = tool_texture_colours.get(vmt_name.lower(), (0.8, 0.8, 0.8, 1.0))
        # TODO: bsp.branch.Flags(td.flags) & bsp.branch.Flags.TRANSLUCENT
        alpha = 0.25 if vmt_name.lower().startswith("world\\atmosphere") else alpha
        material.diffuse_color = (*colour, alpha)
        if alpha != 1:
            material.blend_method = "BLEND"
        materials.append(material)
    return materials


# TODO: source materials direct from the .rpak (bezdna / Legion+)
def textured(bsp) -> List[bpy.types.Material]:
    # TODO: scene properties -> legion folder
    legion_folder = bpy.context.scene.rbsp_prefs.legion_folder
    if not os.path.isdir(legion_folder):
        return base_colours(bsp)  # default to base_colours on fail
    materials_dir = os.path.join(legion_folder, "exported_files/materials")
    materials = list()
    for vmt_name in bsp.TEXTURE_DATA_STRING_DATA:
        material = bpy.data.materials.new(vmt_name)
        material.use_nodes = True
        bsdf_node = material.node_tree.nodes["Principled BSDF"]
        vmt_path = os.path.basename(vmt_name)
        # TODO: make a stack of image textures connected up
        # -- rename each (albedo, metalness, roughness, normal)
        # -- allow extras
        # -- hook each up, but make reconfiguring easy
        i = 0
        material_path = os.path.join(materials_dir, vmt_path)
        if not os.path.isdir(material_path):
            # TODO: log a warning
            continue  # wasn't exported
        for dds in os.listdir(material_path):
            # TODO: identify each image's use
            image_path = os.path.join(material_path, dds)
            if not os.path.isfile(image_path):
                return  # subfolder, can't load that
            try:
                image_texture = bpy.data.images.load(image_path)
            except Exception:
                continue  # idk, stuff breaks sometimes
            image_texture.name = f"{vmt_path}_{i}"
            if image_texture is None:
                # TODO: log a warning
                continue  # some .dds come out broken, ignore them
            i += 1
            image_node = material.node_tree.nodes.new("ShaderNodeTexImage")
            image_node.image = image_texture
            image_node.location.x -= image_node.width * 1.5
            image_node.location.y -= image_node.height * (i * 2 - 3)
            if i == 0:
                image_node.label = "Albedo"
                material.node_tree.links.new(image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                material.node_tree.links.new(image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            elif i == 1:
                image_node.label = "Normal"
                normal_map_node = material.node_tree.nodes.new("ShaderNodeNormalMap")  # intermediary
                normal_map_node.location.x -= normal_map_node.width * 1.5
                normal_map_node.location.y -= normal_map_node.height * (i * 2 - 3)
                material.node_tree.links.new(image_node.outputs["Color"], normal_map_node.inputs["Color"])
                material.node_tree.links.new(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])
            # TODO: bump, metalness, roughness, subsurface, 2nd uv decal?
    return materials
