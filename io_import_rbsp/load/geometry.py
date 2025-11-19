import itertools

import bpy
from bpy.types import Collection
# TODO: see if numpy can speed things up a little

from .materials import make_material
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
        vertices, materials = zip(*[
            (vertex, mesh.material)
            for mesh in model.meshes
            for polygon in mesh.polygons
            for vertex in polygon.vertices])
        assert len(vertices) % 3 == 0, "not a triangle soup"
        indices = list(itertools.chain([
            (i + 2, i + 1, i + 0)
            for i in range(0, len(vertices), 3)]))
        # TODO: map index ranges for each material

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
                blender_uv(*vertices[index].uv0)
                for tri in indices
                for index in tri])))

        lightmap_uv = mesh.uv_layers.new(name="lightmap")
        lightmap_uv.data.foreach_set(
            "uv",
            list(itertools.chain(*[
                blender_uv(*vertices[index].uv1) if len(vertices[index].uv) >= 2 else (0, 0)
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
            blender_material = make_material(material.name)
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

        mesh.update()

        # create object and place in geometry collection
        blender_mesh = bpy.data.objects.new(mesh.name, mesh)
        blender_mesh.location = model.origin
        # TODO: model angles?
        geometry_collection.objects.link(blender_mesh)
