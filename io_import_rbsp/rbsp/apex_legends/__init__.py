__all__ = ["entities", "geometry", "materials", "props"]
from typing import List

import bmesh
import bpy

from ..titanfall import entities, props
# NOTE: titanfall brush entities differ significantly from r1 & 2
# -- "*coll0" "???????????"
from . import materials
# TODO: props (need to use io_import_semodel + Legion)


def geometry(bsp, master_collection: bpy.types.Collection, materials: List[bpy.types.Material]):
    geometry_collection = bpy.data.collections.new("geometry")
    master_collection.children.link(geometry_collection)
    # load_model
    for model_index, model in enumerate(bsp.MODELS):
        model_collection = bpy.data.collections.new(f"model #{model_index}")
        geometry_collection.children.link(model_collection)
        # load_mesh
        for mesh_index in range(model.first_mesh, model.first_mesh + model.num_meshes):
            blender_mesh = bpy.data.meshes.new(f"mesh #{mesh_index}")  # mesh object
            blender_bmesh = bmesh.new()  # mesh data
            mesh_vertices = bsp.vertices_of_mesh(mesh_index)
            bmesh_vertices = dict()
            # ^ {bsp_vertex.position_index: BMVert}
            face_uvs = list()
            # ^ [{vertex_position_index: (u, v)}]
            for triangle_index in range(0, len(mesh_vertices), 3):
                face_indices = list()
                uvs = dict()
                for vert_index in reversed(range(3)):  # inverted winding order
                    bsp_vertex = mesh_vertices[triangle_index + vert_index]
                    vertex = bsp.VERTICES[bsp_vertex.position_index]
                    if bsp_vertex.position_index not in bmesh_vertices:
                        bmesh_vertices[bsp_vertex.position_index] = blender_bmesh.verts.new(vertex)
                    face_indices.append(bsp_vertex.position_index)
                    uvs[tuple(vertex)] = (bsp_vertex.uv.u, -bsp_vertex.uv.v)  # inverted V-axis
                try:
                    blender_bmesh.faces.new([bmesh_vertices[vpi] for vpi in face_indices])
                    face_uvs.append(uvs)  # index must match bmesh.faces index
                # HACKY BUGFIX
                except ValueError:
                    pass  # "face already exists", idk why this happens
            del bmesh_vertices
            # apply uv
            uv_layer = blender_bmesh.loops.layers.uv.new()
            blender_bmesh.faces.ensure_lookup_table()
            for face, uv_dict in zip(blender_bmesh.faces, face_uvs):
                for loop in face.loops:  # loops correspond to verts
                    loop[uv_layer].uv = uv_dict[tuple(loop.vert.co)]
            blender_bmesh.to_mesh(blender_mesh)
            blender_bmesh.free()
            # apply material
            material_index = bsp.SURFACE_NAMES.index(bsp.get_Mesh_SurfaceName(mesh_index))
            blender_mesh.materials.append(materials[material_index])
            # push to collection
            blender_mesh.update()
            blender_object = bpy.data.objects.new(blender_mesh.name, blender_mesh)
            model_collection.objects.link(blender_object)
        if len(model_collection.objects) == 0:
            bpy.data.collections.remove(model_collection)
