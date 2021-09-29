import math
import re
from typing import Dict, List

import bpy
import mathutils


def srgb_to_linear(*srgb: List[float]) -> List[float]:
    """colourspace translation for lights"""
    linear = list()
    for s in srgb:
        if s <= 0.0404482362771082:
            lin = s / 12.92
        else:
            lin = ((s + 0.055) / 1.055) ** 2.4
        linear.append(lin)
    return linear


def linear_to_srgb(*linear: List[float]) -> List[float]:
    """colourspace translation for lights"""
    srgb = list()
    for lin in linear:
        if lin > 0.00313066844250063:
            s = 1.055 * (lin ** (1.0 / 2.4)) - 0.055
        else:
            s = 12.92 * lin
        srgb.append(s)
    return srgb


def ent_to_light(entity: Dict[str, str]) -> bpy.types.PointLight:
    """Reference objects for entities"""
    light_name = entity.get("targetname", entity["classname"])
    # IdTech / IW / Source / Titanfall Engine light type
    if entity["classname"] == "light":
        light = bpy.data.lights.new(light_name, "POINT")
    elif entity["classname"] == "light_spot":
        light = bpy.data.lights.new(light_name, "SPOT")
        outer_angle, inner_angle = map(lambda x: math.radians(float(entity[x])), ("_cone", "_inner_cone"))
        light.spot_size = math.radians(outer_angle)
        light.spot_blend = 1 - inner_angle / outer_angle
    elif entity["classname"] == "light_environment":
        light = bpy.data.lights.new(light_name, "SUN")
        light.angle = math.radians(float(entity.get("SunSpreadAngle", "0")))
    # rough light values conversion
    light.cycles.use_multiple_importance_sampling = False
    if entity.get("_lightHDR", "-1 -1 -1 1") == "-1 -1 -1 1":
        r, g, b, brightness = map(float, entity["_light"].split())
        light.color = srgb_to_linear(r, g, b)
        light.energy = brightness
    else:
        r, g, b, brightness = map(float, entity["_lightHDR"].split())
        light.color = srgb_to_linear(r, g, b)
        light.energy = brightness * float(entity.get("_lightscaleHDR", "1"))
    # TODO: use vector math nodes to mimic light curves
    if "_zero_percent_distance" in entity:
        light.use_custom_distance = True
        light.cutoff_distance = float(entity["_zero_percent_distance"])
    light.energy = light.energy / 100
    return light


ent_object_data = {"light": ent_to_light, "light_spot": ent_to_light, "light_environment": ent_to_light,
                   "ambient_generic": lambda e: bpy.data.speakers.new(e.get("targetname", e["classname"]))}
# ^ {"classname": new_object_data_func}
# TODO: cubemaps, lightprobes, props, areaportals
# NOTE: in the Titanfall Engine info_target has a "editorclass" key
# -- this is likely used for script based object classes (weapon pickups, cameras etc.)


def as_empties(bsp, master_collection):
    all_entities = (bsp.ENTITIES, bsp.ENTITIES_env, bsp.ENTITIES_fx,
                    bsp.ENTITIES_script, bsp.ENTITIES_snd, bsp.ENTITIES_spawn)
    block_names = ("bsp", "env", "fx", "script", "sound", "spawn")
    entities_collection = bpy.data.collections.new("entities")
    master_collection.children.link(entities_collection)
    for entity_block, block_name in zip(all_entities, block_names):
        entity_collection = bpy.data.collections.new(block_name)
        entities_collection.children.link(entity_collection)
        for entity in entity_block:
            object_data = ent_object_data.get(entity["classname"], lambda e: None)(entity)
            name = entity.get("targetname", entity["classname"])
            entity_object = bpy.data.objects.new(name, object_data)
            if object_data is None:
                entity_object.empty_display_type = "SPHERE"
                entity_object.empty_display_size = 64
                if entity["classname"].startswith("info_node"):
                    entity_object.empty_display_type = "CUBE"
            entity_collection.objects.link(entity_object)
            # location
            position = [*map(float, entity.get("origin", "0 0 0").split())]
            entity_object.location = position
            if entity.get("model", "").startswith("*"):
                model_collection = bpy.data.collections.get(f"model #{entity['model'][1:]}")
                if model_collection is not None:
                    model_collection.name = entity.get("targetname", model_collection.name)
                    for mesh_object in model_collection.objects:
                        mesh_object.location = position
            # rotation
            angles = [*map(lambda x: math.radians(float(x)), entity.get("angles", "0 0 0").split())]
            angles[0] = math.radians(-float(entity.get("pitch", -math.degrees(angles[0]))))
            entity_object.rotation_euler = mathutils.Euler(angles, "YZX")
            # NOTE: default orientation is facing east (+X), props may appear rotated?
            # TODO: further optimisation (props with shared worldmodel share mesh data) [ent_object_data]
            for field in entity:
                entity_object[field] = entity[field]
        # TODO: once all ents are loaded, connect paths for keyframe_rope / path_track etc.
        # TODO: do a second pass of entities to apply parental relationships (based on targetnames)


# trigger_multiple, trigger_once, trigger_hurt


# ent_object_data["trigger_*"] = trigger_bounds
def trigger_bounds(trigger_ent: Dict[str, str]) -> bpy.types.Mesh:
    # TODO: only for entities with no mesh geometry
    raise NotImplementedError()
    # pattern_vector = re.compile(r"([^\s]+) ([^\s]+) ([^\s]+)")
    # mins = list(map(float, pattern_vector.match(trigger_ent["*trigger_bounds_mins"])))
    # maxs = list(map(float, pattern_vector.match(trigger_ent["*trigger_bounds_maxs"])))
    # TODO: return mesh data for a cube scaled to mins & maxs


# ent_object_data["trigger_*"] = trigger_bounds
def trigger_bmesh(trigger_ent: Dict[str, str]) -> bpy.types.Mesh:
    # TODO: only for entities with no mesh geometry
    pattern_plane_key = re.compile(r"\*trigger_brush([0-9]+)_plane([0-9]+)")  # brush_index, plane_index
    pattern_plane_value = re.compile(r"([^\s]+) ([^\s]+) ([^\s]+) ([^\s]+)")  # *normal, distance
    brushes = dict()
    for key in trigger_ent.keys():
        match = pattern_plane_key.match(key)
        if match:
            brush_index, plane_index = map(int, match.groups())
            *normal, distance = map(float, pattern_plane_value.match(trigger_ent[key]).groups())
            brushes[(brush_index, plane_index)] = (normal, distance)
    raise NotImplementedError()
    # TODO: use Logic&Trick's brush creation code from QtPyHammer here
