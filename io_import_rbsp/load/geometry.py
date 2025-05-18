# import itertools

# import bmesh
import bpy
from bpy.types import Collection
# TODO: see if numpy can speed things up a little

from bsp_tool.utils.geometry import triangle_soup

from .entities import name_of


def blender_uv(u, v):
    return (u, 1 - v)


def all_models(bsp, bsp_collection: Collection):
    geometry_collection = bpy.data.collections.new("geometry")
    bsp_collection.children.link(geometry_collection)
    # TODO: sort sub-meshes by material (see bsp_tool.scene)
    # -- combine if same material
    # -- separate skybox from worldspawn
    for i, model in enumerate(bsp.MODELS):
        model = bsp.model(i)
        vertices = [
            vertex
            for mesh in model
            for polygon in mesh
            for vertex in polygon]
        indices = list(reversed(triangle_soup(vertices)))  # invert winding
        # TODO: map index ranges for each material

        mesh = bpy.data.meshes.new(name_of(model.entity))
        mesh.from_pydata([
            [vertex.position for vertex in vertices],
            list(),  # auto-generate edges
            indices])

        # NOTE: these next bits might break
        # -- commenting them out for now

        # bmesh_ = bmesh.new()  # mesh data
        # base_uv = bmesh_.loops.layers.uv.new("base")
        # base_uv.uv.foreach_set("vector", itertools.chain(*[
        #     blender_uv(*vertices[index].uv0)
        #     for index in indices]))

        # lightmap_uv = bmesh_.loops.layers.uv.new("lightmap")
        # lightmap_uv.uv.foreach_set("vector", itertools.chain(*[
        #     blender_uv(*vertices[index].uv1)
        #     for index in indices]))
        # bmesh_.to_mesh(mesh)
        # bmesh_.free()

        # vertex_colour = bmesh_.color_attributes.new("Colour")
        # vertex_colour.foreach_set("color", itertools.chain(*[
        #     vertices[index].colour
        #     for index in indices]))

        # # TODO: assign materials
        # for material in {sub_mesh.material for sub_mesh in model.meshes}:
        #     blender_material = load.materials.make_material(material.name)
        #     mesh.materials.append(blender_material)
        # mesh.update()

        blender_mesh = bpy.data.objects.new(mesh.name, mesh)
        blender_mesh.location = model.origin
        # TODO: model angles?
        # TODO: try to get smooth shading from vertex normals instead
        blender_mesh.data.use_auto_smooth()
        blender_mesh.link(geometry_collection)
