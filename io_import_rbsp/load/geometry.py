import itertools

import bpy
from bpy.types import Collection
# TODO: see if numpy can speed things up a little

from .materials import placeholder
from .entities import name_of


def get_base_uv(vertices, index):
    u, v = vertices[index].uv0
    return (u, 1 - v)


def get_lightmap_uv(vertices, index):
    vertex = vertices[index]
    if len(vertex.uv) >= 2:
        u, v = vertex.uv1
    else:
        u, v = 0, 0
    return (u, 1 - v)


def all_models(bsp, geometry_collection: Collection):
    for i, model in enumerate(bsp.MODELS):
        model = bsp.model(i)
        vertex_materials = [
            (vertex, mesh.material)
            for mesh in model.meshes
            for polygon in mesh.polygons
            for vertex in polygon.vertices]
        if len(vertex_materials) != 0:
            vertices, materials = zip(*vertex_materials)
        else:  # model w/ no geo
            vertices, materials = list(), list()
        assert len(vertices) % 3 == 0, "not a triangle soup"
        indices = list(itertools.chain([
            (i + 2, i + 1, i + 0)
            for i in range(0, len(vertices), 3)]))

        model_name = name_of(model.entity)
        if model_name is None:
            if i == 0:
                model_name = "worldspawn"
            else:
                model_name = f"model_{i:02d}"

        mesh = bpy.data.meshes.new(model_name)
        mesh.from_pydata(
            [vertex.position for vertex in vertices],
            list(),  # auto-generate edges
            indices,
            shade_flat=False)

        base_uv = mesh.uv_layers.new(name="base")
        base_uv.data.foreach_set(
            "uv",
            list(itertools.chain(*[
                get_base_uv(vertices, index)
                for tri in indices
                for index in tri])))

        lightmap_uv = mesh.uv_layers.new(name="lightmap")
        lightmap_uv.data.foreach_set(
            "uv",
            list(itertools.chain(*[
                get_lightmap_uv(vertices, index)
                for tri in indices
                for index in tri])))

        vertex_colour = mesh.vertex_colors.new(name="Colour")
        vertex_colour.data.foreach_set(
            "color",
            list(itertools.chain(*[
                vertices[index].colour
                for tri in indices
                for index in tri])))

        material_indices = dict()
        for material in {sub_mesh.material for sub_mesh in model.meshes}:
            blender_material = placeholder(material.name, "wld")
            mesh.materials.append(blender_material)
            material_indices[material.name] = len(mesh.materials) - 1

        # assign materials
        mesh.polygons.foreach_set(
            "material_index", [
                material_indices[materials[tri[0]].name]
                for tri in indices])

        # TODO: per-face lightmap index
        # NOTE: bsp_tool doesn't give us this info atm
        # lightmap_index = mesh.attributes.new(
        #     name="Lightmap Index", type="INT", domain="FACE")
        # lightmap_index.data.foreach_set(
        #     "value",
        #     ...)

        # TODO: separate skybox from worldspawn
        # TODO: separate atmospheric effects from worldspawn

        mesh.update()

        # create object and place in geometry collection
        blender_mesh = bpy.data.objects.new(mesh.name, mesh)
        blender_mesh.location = model.origin
        # TODO: model angles?
        geometry_collection.objects.link(blender_mesh)
