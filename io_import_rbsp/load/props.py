import itertools
import os

import bpy
import mathutils

from bpy.types import Collection, Mesh

from ass.scene.valve import Mdl

from .geometry import get_base_uv
from .materials import placeholder, search
# TODO: _fix material node assembler
# -- for now, props will just use placeholders


# TODO: break down model paths as collections
# foliage > ...
# auto-hide large collections (> 1000 props)


def as_empties(bsp, prop_collection: Collection):
    """Requires all models to be extracted beforehand"""
    for prop in bsp.GAME_LUMP.sprp.props:
        prop_object = bpy.data.objects.new(
            bsp.GAME_LUMP.sprp.model_names[prop.model_name], None)
        prop_object.empty_display_type = "SPHERE"
        prop_object.empty_display_size = 64
        prop_object.location = tuple(prop.origin)
        prop_object.rotation_euler = mathutils.Euler(
            (prop.angles[2], prop.angles[0], 90 + prop.angles[1]))
        prop_collection.objects.link(prop_object)


def static_props(bsp, prop_collection: Collection):
    vpk_folder = bpy.context.scene.rbsp_prefs.vpk_folder
    if not os.path.isdir(vpk_folder):
        return
    meshes = [
        load_model(model_path(vpk_folder, model_name))
        for model_name in bsp.GAME_LUMP.sprp.model_names]

    for prop in bsp.GAME_LUMP.sprp.props:
        mesh = meshes[prop.model_name]
        path = bsp.GAME_LUMP.sprp.model_names[prop.model_name]
        name = os.path.basename(path).lower()
        prop_object = bpy.data.objects.new(name, mesh)
        if mesh is None:
            prop_object.empty_display_type = "SPHERE"
            prop_object.empty_display_size = 64
        prop_object.location = tuple(prop.origin)
        prop_object.rotation_euler = mathutils.Euler(
            (prop.angles[2], prop.angles[0], 90 + prop.angles[1]))
        prop_collection.objects.link(prop_object)


def model_path(vpk_folder: str, asset_path: str) -> str:
    filepath = os.path.join(vpk_folder, asset_path)
    if os.path.exists(filepath):
        return filepath  # case-senstive match
    else:  # try for case-insensitive match
        return search(vpk_folder, asset_path)


def load_model(filepath: str) -> Mesh:
    if filepath is None:
        return  # search() FileNotFound
    mdl = Mdl.from_file(filepath)
    mdl.parse()
    base_name = os.path.splitext(mdl.filename)[0]
    model_name = f"{base_name}.lod0"
    model = mdl.models[model_name]
    # ass.Model -> Blender Mesh
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

    mesh = bpy.data.meshes.new(model_name)
    mesh.from_pydata(
        [vertex.position for vertex in vertices],
        list(),  # auto-generate edges
        indices,
        shade_flat=False)

    # NOTE: uv0 only, no vertex colour
    base_uv = mesh.uv_layers.new(name="base")
    base_uv.data.foreach_set(
        "uv",
        list(itertools.chain(*[
            get_base_uv(vertices, index)
            for tri in indices
            for index in tri])))

    material_indices = dict()
    for material in {sub_mesh.material for sub_mesh in model.meshes}:
        blender_material = placeholder(material.name)
        blender_material["shader_type"] = "fix"
        mesh.materials.append(blender_material)
        material_indices[material.name] = len(mesh.materials) - 1

    # assign materials
    mesh.polygons.foreach_set(
        "material_index", [
            material_indices[materials[tri[0]].name]
            for tri in indices])

    mesh.update()
    mesh["asset_path"] = mdl.name
    return mesh
