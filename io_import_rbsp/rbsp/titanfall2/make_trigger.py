import collections
import re
from typing import Dict, List, Tuple

import bpy
import bmesh
from mathutils import Vector


Plane = Tuple[Vector, float]
Polygon = List[Vector]


trigger_obj = bpy.data.objects["trigger_multiple.060"]

pattern_plane_key = re.compile(r"\*trigger_brush_([0-9]+)_plane_([0-9]+)")

brushes = collections.defaultdict(lambda: collections.defaultdict(list))
# ^ {brush_index: {plane_index: " ".join(map(str, (*normal, distance)))}}
# ^ Mapping[int, Mapping[int, str]]

# for key in entity
for key in trigger_obj.keys():
    match = pattern_plane_key.match(key)
    if match:
        brush_index, plane_index = map(int, match.groups())
        *normal, distance = map(float, trigger_obj[key].split())  # entity[key]
        normal = Vector(normal)
        brushes[brush_index][plane_index] = (normal, distance)


# adapted from Sledge by LogicAndTrick (archived)
# https://github.com/LogicAndTrick/sledge/blob/master/Sledge.DataStructures/Geometric/Precision/Polygon.cs
def clip(polygon: Polygon, plane: Plane) -> Dict[str, Polygon]:
    normal, distance = plane
    split = {"back": [], "front": []}
    # NOTE: polygon's winding order is preserved
    for i, A in enumerate(polygon):
        B = polygon[(i + 1) % len(polygon)]  # next point
        A_distance = Vector.dot(normal, A) - distance
        B_distance = Vector.dot(normal, B) - distance
        A_behind = round(A_distance, 6) < 0
        B_behind = round(B_distance, 6) < 0
        if A_behind:
            split["back"].append(A)
        else:  # A is in front of the clipping plane
            split["front"].append(A)
        # does the edge AB intersect the clipping plane?
        if (A_behind and not B_behind) or (B_behind and not A_behind):
            t = A_distance / (A_distance - B_distance)
            cut_point = Vector(A).lerp(Vector(B), t)
            split["back"].append(cut_point)
            split["front"].append(cut_point)
            # ^ won't one of these points be added twice?
    return split


mesh_data_name = trigger_obj.get("targetname", trigger_obj["classname"])
mesh_data = bpy.data.meshes.new(mesh_data_name)
bm = bmesh.new()
vertices: Dict[Vector, bmesh.types.BMVert] = dict()
# ^ {(x, y, z): BMVert(...)}

# adapted from vmf_tool.solid.from_namespace by QtPyHammer-devs
# https://github.com/QtPyHammer-devs/vmf_tool/blob/master/vmf_tool/solid.py
for brush_index, brush in brushes.items():
    for plane_index, plane in brush.items():
        normal, distance = plane
        # make base polygon
        non_parallel = Vector((0, 0, -1)) if abs(normal.z) != 1 else Vector((0, -1, 0))
        local_y = Vector.cross(non_parallel, normal).normalized()
        local_x = Vector.cross(local_y, normal).normalized()
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
        # append polygon to bmesh
        polygon = list(map(Vector.freeze, polygon))
        for vertex in polygon:
            if vertex not in vertices:
                vertices[vertex] = bm.verts.new(vertex)
        # try:
        if len(polygon) != 0:  # fix for diagonal planes
            bm.faces.new([vertices[v] for v in polygon])
        # # HACKY BUGFIX
        # except ValueError:
        #     pass  # "face already exists", idk why this happens
bm.to_mesh(mesh_data)
bm.free()
mesh_data.update()

object = bpy.data.objects.new("generated_trigger", mesh_data)
object.location = tuple(map(float, trigger_obj["origin"].split()))
object.data.materials.append(bpy.data.materials["TOOLS\\TOOLSTRIGGER"])
bpy.data.collections["entities"].objects.link(object)
