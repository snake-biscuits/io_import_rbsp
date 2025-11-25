import math
from typing import Any, Dict, List

import bpy
from bpy.types import PointLight
import mathutils

from .utils import change_collection


Entity = Dict[str, str]
# ^ {"key": "value"}


def editorclass_of(entity: Entity) -> str:
    return entity.get("editorclass", entity.get("classname", None))


def name_of(entity: Entity) -> str:
    return entity.get("targetname", editorclass_of(entity))


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


def light_entity(entity: Entity) -> PointLight:
    """Reference objects for entities"""
    if entity["classname"] == "light":
        light = bpy.data.lights.new(name_of(entity), "POINT")

    elif entity["classname"] == "light_spot":
        light = bpy.data.lights.new(name_of(entity), "SPOT")
        outer_angle = math.radians(float(entity["_cone"]))
        inner_angle = math.radians(float(entity["_inner_cone"]))
        light.spot_size = math.radians(outer_angle)
        light.spot_blend = 1 - inner_angle / outer_angle

    elif entity["classname"] == "light_environment":
        light = bpy.data.lights.new(name_of(entity), "SUN")
        light.angle = math.radians(float(entity.get("SunSpreadAngle", "0")))

    light.cycles.use_multiple_importance_sampling = False

    if entity.get("_lightHDR", "-1 -1 -1 1") == "-1 -1 -1 1":
        r, g, b, brightness = map(float, entity["_light"].split())
        light.color = srgb_to_linear(r, g, b)
        light.energy = brightness
    else:
        r, g, b, brightness = map(float, entity["_lightHDR"].split())
        light.color = srgb_to_linear(r, g, b)
        light.energy = brightness * float(entity.get("_lightscaleHDR", "1"))

    if "_zero_percent_distance" in entity:
        light.use_custom_distance = True
        light.cutoff_distance = float(entity["_zero_percent_distance"])

    light.energy = light.energy / 100
    return light


converters = {
    "light": light_entity,
    "light_spot": light_entity,
    "light_environment": light_entity,
    "ambient_generic": lambda entity:
        bpy.data.speakers.new(name_of(entity))}
# ^ {"classname": new_object_data_func}

# TODO: cubemaps
# TODO: lightprobes
# TODO: props
# TODO: areaportals
# TODO: spectator cameras


def set_location(blender_object: Any, entity: Entity):
    location = [
        float(axis)
        for axis in entity.get("origin", "0 0 0").split()]
    blender_object.location = location


def all_entities(bsp, ent_collections, converters=converters):
    entity_blocks = {
        "bsp": bsp.ENTITIES,
        "env": bsp.ENTITIES_env,
        "fx": bsp.ENTITIES_fx,
        "script": bsp.ENTITIES_script,
        "sound": bsp.ENTITIES_snd,
        "spawn": bsp.ENTITIES_spawn}
    for block_name, entities in entity_blocks.items():
        entity_collection = ent_collections[block_name]
        for entity in entities:
            classname = editorclass_of(entity)
            blenderify = converters.get(classname, lambda e: None)
            object_data = blenderify(entity)
            name = name_of(entity)
            entity_object = bpy.data.objects.new(name, object_data)

            # default empty
            if object_data is None:
                entity_object.empty_display_type = "SPHERE"
                entity_object.empty_display_size = 16
                # cubes for ai pathing entities
                if classname.startswith("info_node"):
                    entity_object.empty_display_type = "CUBE"
                    entity_object.empty_display_size = 32
            entity_collection.objects.link(entity_object)

            # location
            set_location(entity_object, entity)
            # update child meshes
            if entity.get("model", "").startswith("*"):
                model_index = int(entity["model"][1:])
                model_collection = bpy.data.collections.get(f"model #{model_index}")
                if model_collection is not None:
                    if "targetname" in entity:
                        targetname = entity["targetname"]
                        model_collection.name += " " + f"({targetname})"
                    for mesh_object in model_collection.objects:
                        mesh_object.location = entity_object.location

            # rotation
            # NOTE: default orientation is facing east (+X)
            # -- some props will get the wrong rotation?
            # TODO: test entity rotation matches in-game
            angles = [
                math.radians(float(axis))
                for axis in entity.get("angles", "0 0 0").split()]
            angles[0] = math.radians(
                -float(entity.get("pitch", -math.degrees(angles[0]))))
            entity_object.rotation_euler = mathutils.Euler(
                    (angles[2], *angles[:2]))  # YZX -> XYZ

            # TODO: optimise
            # -- props with shared worldmodel share mesh data
            # save entity keyvalues as custom properties
            for field in entity:
                entity_object[field] = entity[field]

            change_collection(entity_object, entity_collection)
    # TODO: connect paths for keyframe_rope / path_track etc.
    # TODO: handle parenting based on entity keyvalues
