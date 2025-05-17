import collections
import re
from typing import Dict, List, Tuple

import bmesh
import bpy
from bpy.types import Mesh
import mathutils

from ..utils import change_collection
from .entities import Entity
from .entities import editorclass_of, name_of, set_location


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


def all_triggers(bsp):
    entity_blocks = {
        "bsp": bsp.ENTITIES,
        "env": bsp.ENTITIES_env,
        "fx": bsp.ENTITIES_fx,
        "script": bsp.ENTITIES_script,
        "sound": bsp.ENTITIES_snd,
        "spawn": bsp.ENTITIES_spawn}
    for block_name, entities in entity_blocks.items():
        entity_collection = bpy.data.collections[block_name]
        for entity in entities:
            classname = editorclass_of(entity)
            if classname not in trigger_colours:
                continue  # not a trigger, skip
            trigger_object = bpy.data.objects.new(
                name_of(entity), trigger_brushes(entity))
            set_location(trigger_object, entity)
            # NOTE: iirc triggers never have angles
            for field in entity:
                trigger_object[field] = entity[field]
            change_collection(trigger_object, entity_collection)
    # TODO: handle parenting based on entity keyvalues


def trigger_brushes(entity: Entity, palette=trigger_colours) -> Mesh:
    if "*trigger_brush_mins" in entity:  # quick fix for Apex brush entities
        return None  # false positive, no mesh data
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
    bm = bmesh.new()
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
