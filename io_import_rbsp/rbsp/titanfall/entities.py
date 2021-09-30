import collections
import math
import re
from typing import Dict, List, Tuple

import bmesh
import bpy
import mathutils


Entity = Dict[str, str]
# ^ {"key": "value"}


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


def ent_to_light(entity: Entity) -> bpy.types.PointLight:
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


def name_of(entity: Entity) -> str:
    return entity.get("targetname", entity.get("editorclass", entity["classname"]))


ent_object_data = {"light": ent_to_light, "light_spot": ent_to_light, "light_environment": ent_to_light,
                   "ambient_generic": lambda e: bpy.data.speakers.new(e.get("targetname", e["classname"]))}
# ^ {"classname": new_object_data_func}
# TODO: cubemaps, lightprobes, props, areaportals
# NOTE: in the Titanfall Engine info_target has a "editorclass" key
# -- this is likely used for script based object classes (weapon pickups, cameras etc.)


def all_entities(bsp, master_collection: bpy.types.Collection):
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
            name = name_of(entity)
            entity_object = bpy.data.objects.new(name, object_data)
            if object_data is None:
                entity_object.empty_display_type = "SPHERE"
                entity_object.empty_display_size = 64
                # cubes for ai pathing entities
                if entity["classname"].startswith("info_node"):
                    entity_object.empty_display_type = "CUBE"
            entity_collection.objects.link(entity_object)
            # location
            position = [*map(float, entity.get("origin", "0 0 0").split())]
            entity_object.location = position
            if entity.get("model", "").startswith("*"):
                model_collection = bpy.data.collections.get(f"model #{entity['model'][1:]}")
                if model_collection is not None:
                    if "targetname" in entity:
                        model_collection.name = f"{model_collection.name} ({entity['targetname']})"
                    for mesh_object in model_collection.objects:
                        mesh_object.location = position
            # rotation
            angles = [*map(lambda x: math.radians(float(x)), entity.get("angles", "0 0 0").split())]
            angles[0] = math.radians(-float(entity.get("pitch", -math.degrees(angles[0]))))
            entity_object.rotation_euler = mathutils.Euler(angles, "YZX")
            # NOTE: default orientation is facing east (+X), props may appear rotated?
            # TODO: further optimisation (props with shared worldmodel share mesh data) [ent_object_data]
            # set all key values as custom properties
            for field in entity:
                entity_object[field] = entity[field]
        # TODO: once all ents are loaded, connect paths for keyframe_rope / path_track etc.
        # TODO: do a second pass of entities to apply parental relationships (based on targetnames)


# ent_object_data["trigger_*"] = trigger_bounds
def trigger_brushes(entity: Entity) -> bpy.types.Mesh:
    bm = bmesh.new()
    # get brush planes
    pattern_plane_key = re.compile(r"\*trigger_brush_([0-9]+)_plane_([0-9]+)")
    brushes = collections.defaultdict(lambda: collections.defaultdict(list))
    # ^ {brush_index: {plane_index: " ".join(map(str, (*normal, distance)))}}
    for key in entity.keys():
        match = pattern_plane_key.match(key)
        if match:
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
            non_parallel = mathutils.Vector((0, 0, -1)) if abs(normal.z) != 1 else mathutils.Vector((0, -1, 0))
            local_y = mathutils.Vector.cross(non_parallel, normal).normalized()
            local_x = mathutils.Vector.cross(local_y, normal).normalized()
            center = normal * distance
            radius = 10 ** 6  # may encounter issues if brush is larger than this
            polygon = [center + ((-local_x + local_y) * radius),
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
            polygon = list(sorted(set(polygon), key=lambda v: polygon.index(v)))  # remove doubles
            for vertex in polygon:
                if vertex not in vertices:
                    vertices[vertex] = bm.verts.new(vertex)
            if len(polygon) >= 3:
                try:  # HACKY FIX
                    bm.faces.new([vertices[v] for v in polygon])
                except ValueError:
                    pass  # "face already exists"
    mesh_data_name = name_of(entity)
    mesh_data = bpy.data.meshes.new(mesh_data_name)
    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update()
    # HACK: apply trigger material
    if "TOOLS\\TOOLSTRIGGER" not in bpy.data.materials:
        trigger_material = bpy.data.materials.new("TOOLS\\TOOLSTRIGGER")
        trigger_material.diffuse_color = (0.944, 0.048, 0.004, 0.25)
        trigger_material.blend_method = "BLEND"
    trigger_material = bpy.data.materials["TOOLS\\TOOLSTRIGGER"]
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
