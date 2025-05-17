import collections
import math
import re
from typing import Dict, List, Tuple

import bmesh
import bpy
from bpy.types import Collection, Mesh, PointLight, Speaker
import mathutils


Entity = Dict[str, str]
# ^ {"key": "value"}

purple = (0.527, 0.006, 1.000)
orange = (0.947, 0.202, 0.004)
mauve = (1.000, 0.026, 0.290)
red = (1.000, 0.007, 0.041)
teal = (0.017, 1.000, 0.246)
lime = (0.224, 1.000, 0.000)
pink = (0.947, 0.010, 0.549)
blue = (0.028, 0.584, 0.947)

trigger_colours = {
    # classnames
    "envmap_volume": purple,
    "light_probe_volume": purple,
    "light_environment_volume": purple,
    "trigger_capture_point": orange,
    "trigger_hurt": red,
    "trigger_indoor_area": purple,
    "trigger_multiple": orange,
    "trigger_once": orange,
    "trigger_out_of_bounds": mauve,
    "trigger_soundscape": purple,
    # editorclasses
    "trigger_checkpoint": teal,
    "trigger_checkpoint_forced": teal,
    "trigger_checkpoint_safe": teal,
    "trigger_checkpoint_silent": teal,
    "trigger_checkpoint_to_safe_spots": teal,
    "trigger_deadly_fog": red,
    "trigger_death_fall": red,
    "trigger_flag_clear": lime,
    "trigger_flag_set": lime,
    "trigger_flag_touching": lime,
    "trigger_friendly": pink,
    "trigger_friendly_follow": pink,
    "trigger_fw_territory": blue,
    "trigger_level_transition": teal,
    "trigger_mp_spawn_zone": blue,
    "trigger_no_grapple": mauve,
    "trigger_quickdeath": red,
    "trigger_quickdeath_checkpoint": red,
    "trigger_spawn": blue,
    "trigger_teleporter": blue}


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


def name_of(entity: Entity) -> str:
    return entity.get("targetname", entity.get("editorclass", entity["classname"]))


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

# TODO: cubemaps, lightprobes, props, areaportals
# TODO: include editorclasses so we can get spectator cams etc.


def all_entities(bsp, bsp_collection: Collection, converters=converters):
    entities_collection = bpy.data.collections.new("entities")
    bsp_collection.children.link(entities_collection)
    entity_blocks = {
        "bsp": bsp.ENTITIES,
        "env": bsp.ENTITIES_env,
        "fx": bsp.ENTITIES_fx,
        "script": bsp.ENTITIES_script,
        "sound": bsp.ENTITIES_snd,
        "spawn": bsp.ENTITIES_spawn}
    for block_name, entities in entity_blocks.items():
        entity_collection = bpy.data.collections.new(block_name)
        entities_collection.children.link(entity_collection)
        for entity in entities:
            classname = entity["classname"]  # TODO: editorclass
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
            position = [*map(float, entity.get("origin", "0 0 0").split())]
            entity_object.location = position
            if entity.get("model", "").startswith("*"):
                model_index = int(entity["model"][1:])
                model_collection = bpy.data.collections.get(f"model #{model_index}")
                if model_collection is not None:
                    if "targetname" in entity:
                        targetname = entity["targetname"]
                        model_collection.name += " " + f"({targetname})"
                    for mesh_object in model_collection.objects:
                        mesh_object.location = position

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
        # TODO: connect paths for keyframe_rope / path_track etc.
        # TODO: handle parenting based on entity keyvalues


# ent_object_data["trigger_*"] = trigger_bounds
def trigger_brushes(entity: Entity, palette=trigger_colours) -> Mesh:
    if "*trigger_brush_mins" in entity:  # quick fix for Apex brush entities
        return None  # false positive, no mesh data
    bm = bmesh.new()
    # get brush planes
    pattern_plane_key = re.compile(r"\*trigger_brush_([0-9]+)_plane_([0-9]+)")
    brushes = collections.defaultdict(lambda: collections.defaultdict(list))
    # ^ {brush_index: {plane_index: " ".join(map(str, (*normal, distance)))}}
    for key in entity.keys():
        match = pattern_plane_key.match(key)
        if match is not None:
            brush_index, plane_index = map(int, match.groups())
            *normal, distance = map(float, entity[key].split())
            normal = mathutils.Vector(normal)
            brushes[brush_index][plane_index] = (normal, distance)

    vertices: Dict[mathutils.Vector, bmesh.types.BMVert] = dict()
    # ^ {(x, y, z): BMVert(...)}

    # adapted from vmf_tool.solid.from_namespace by QtPyHammer-devs
    # https://github.com/QtPyHammer-devs/vmf_tool/blob/master/vmf_tool/solid.py
    for brush_index, brush in brushes.items():
        for plane_index, plane in brush.items():
            normal, distance = plane
            # make base polygon
            non_parallel = mathutils.Vector(
                (0, 0, -1)) if abs(normal.z) != 1 else mathutils.Vector((0, -1, 0))
            local_y = mathutils.Vector.cross(non_parallel, normal).normalized()
            local_x = mathutils.Vector.cross(local_y, normal).normalized()
            center = normal * distance
            radius = 10 ** 6  # may encounter issues if brush is larger than this
            polygon = [
                center + ((-local_x + local_y) * radius),
                center + ((local_x + local_y) * radius),
                center + ((local_x + -local_y) * radius),
                center + ((-local_x + -local_y) * radius)]
            # slice by other planes
            for other_plane_index, other_plane in brushes[brush_index].items():
                if other_plane_index == plane_index:
                    continue  # skip self
                polygon = clip(polygon, other_plane)["back"]
            # slice by other planes
            for other_plane_index, other_plane in brushes[brush_index].items():
                if other_plane_index == plane_index:
                    continue  # skip self
                polygon = clip(polygon, other_plane)["back"]
            # append polygon to bmesh
            polygon = list(map(mathutils.Vector.freeze, polygon))
            # remove duplicate points
            polygon = list(sorted(
                set(polygon),
                key=lambda vertex: polygon.index(vertex)))
            for vertex in polygon:
                if vertex not in vertices:
                    vertices[vertex] = bm.verts.new(vertex)
            if len(polygon) >= 3:
                try:  # HACKY FIX
                    bm.faces.new([
                        vertices[vertex]
                        for vertex in reversed(polygon)])
                except ValueError:
                    pass  # "face already exists"
    mesh_data_name = name_of(entity)
    mesh_data = bpy.data.meshes.new(mesh_data_name)
    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update()
    classname = entity.get("editorclass", entity["classname"])
    if classname not in bpy.data.materials:
        trigger_material = bpy.data.materials.new(classname)
        colour = palette.get(classname, (0.944, 0.048, 0.004))  # default: red
        trigger_material.diffuse_color = (*colour, 0.25)
        trigger_material.blend_method = "BLEND"
    trigger_material = bpy.data.materials[classname]
    mesh_data.materials.append(trigger_material)
    # mesh_data has no faces?
    return mesh_data


Plane = Tuple[mathutils.Vector, float]
Polygon = List[mathutils.Vector]


# adapted from Sledge by LogicAndTrick (archived)
# https://github.com/LogicAndTrick/sledge/blob/master/Sledge.DataStructures/Geometric/Precision/Polygon.cs
def clip(polygon: Polygon, plane: Plane) -> Dict[str, Polygon]:
    normal, distance = plane
    split = {"back": [], "front": []}
    for i, A in enumerate(polygon):  # NOTE: polygon's winding order is preserved
        B = polygon[(i + 1) % len(polygon)]  # next point
        A_distance = mathutils.Vector.dot(normal, A) - distance
        B_distance = mathutils.Vector.dot(normal, B) - distance
        A_behind = round(A_distance, 6) < 0
        B_behind = round(B_distance, 6) < 0
        if A_behind:
            split["back"].append(A)
        else:  # A is in front of the clipping plane
            split["front"].append(A)
        # does the edge AB intersect the clipping plane?
        if (A_behind and not B_behind) or (B_behind and not A_behind):
            t = A_distance / (A_distance - B_distance)
            cut_point = mathutils.Vector(A).lerp(mathutils.Vector(B), t)
            split["back"].append(cut_point)
            split["front"].append(cut_point)
            # ^ won't one of these points be added twice?
    return split
