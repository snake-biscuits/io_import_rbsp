from typing import List

from bsp_tool.branches.respawn import titanfall as r1


def sanitise(path: str) -> str:
    return path.lower().replace("\\", "/")


# faster mesh construction
def vertex_lump_and_indices_of_mesh(bsp, mesh_index: int) -> (str, List[int]):
    mesh = bsp.MESHES[mesh_index]
    vertex_lump_name = (mesh.flags & r1.MeshFlags.MASK_VERTEX).name
    material_sort = bsp.MATERIAL_SORTS[mesh.material_sort]
    start = mesh.first_mesh_index
    finish = start + mesh.num_triangles * 3
    indices = [
        i + material_sort.vertex_offset
        for i in bsp.MESH_INDICES[start:finish]]
    return vertex_lump_name, indices


def remap_indices(indices: List[int]) -> (List[int], List[int]):
    subset = list(set(indices))
    new_indices = [subset.index(i) for i in indices]
    return new_indices, subset
    # new_index -> subset -> VertexLump


def bsp_model_to_blender_mesh(bsp, model_index: int) -> str:
    lumps = {
        "LIT_BUMP": bsp.VERTEX_LIT_BUMP,
        "LIT_FLAT": bsp.VERTEX_LIT_FLAT,
        "UNLIT": bsp.VERTEX_UNLIT,
        "UNLIT_TS": bsp.VERTEX_UNLIT_TS}

    all_position_indices = list()
    for mesh_index in range(bsp.MODELS[0].num_meshes):
        vertex_lump_name, indices = vertex_lump_and_indices_of_mesh(bsp, mesh_index)
        # TODO: generate uvs per vertex per face
        # -- same with surface normals
        vertex_lump = lumps[vertex_lump_name[7:]]
        position_indices = [vertex_lump[i].position for i in indices]
        all_position_indices.extend(position_indices)

    indices, positions = remap_indices(position_indices)
    vertices = [bsp.VERTICES[i].as_tuple() for i in positions]
    assert len(indices) % 3 == 0, "everything should be triangles"
    triangles = [
        (indices[i], indices[i+1], indices[i+2])
        for i in range(0, len(indices), 3)]
    # TODO: can we pass vertices & triangles as generators? memory savings

    mesh_name = f"BspModel.{model_index:04d}"
    mesh = bsp.data.meshes.new(mesh_name)
    mesh.from_pydata(vertices, list(), triangles)
    # TODO: vertex: normal, colour, uv, lightmap_uv
    # -- attributes: bsp.mesh->lightmap_index, bsp.material_sort->cubemap_index
    # -- bsp.mesh -> material
    # -- bsp.mesh.flags->VertexReservedX->transparency flags
    # --- split into worldspawn opaque, decal & transparent
    return mesh_name
    # model = bpy.data.models.new(mesh_name, mesh)
    # bpy.context.scene.collection.children.add(model)
