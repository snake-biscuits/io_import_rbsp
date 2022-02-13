# https://wiki.zeroy.com/index.php?title=Call_of_Duty_2:_d3dbsp
# https://github.com/mauserzjeh/PyD3DBSP/blob/master/pyd3dbsp/read_d3dbsp.py
# TODO: see modding tools: cod2map.exe -info
import enum
from typing import List

from .. import base
from ..id_software import quake
from ..id_software import quake3
from . import call_of_duty1


FILE_MAGIC = b"IBSP"

BSP_VERSION = 4

GAME_PATHS = {"Call of Duty 2": "Call of Duty 2"}

GAME_VERSIONS = {GAME_NAME: BSP_VERSION for GAME_NAME in GAME_PATHS}


class LUMP(enum.Enum):
    SHADERS = 0
    LIGHTMAPS = 1
    LIGHT_GRID_HASHES = 2
    LIGHT_GRID_VALUES = 3  # MODEL_LIGHTING
    PLANES = 4
    BRUSH_SIDES = 5
    BRUSHES = 6
    TRIANGLE_SOUPS = 7
    VERTICES = 8
    TRIANGLES = 9
    CULL_GROUPS = 10
    CULL_GROUP_INDICES = 11
    SHADOW_VERTICES = 12
    SHADOW_INDICES = 13
    SHADOW_CLUSTERS = 14
    SHADOW_AABB_TREES = 15
    SHADOW_SOURCES = 16
    PORTAL_VERTICES = 17
    OCCLUDERS = 18
    OCCLUDER_PLANES = 19
    OCCLUDER_EDGES = 20
    OCCLUDER_INDICES = 21
    AABB_TREE = 22
    CELLS = 23
    PORTALS = 24
    NODES = 25
    LEAVES = 26
    LEAF_BRUSHES = 27
    LEAF_SURFACES = 28
    COLLISION_VERTICES = 29
    COLLISION_EDGES = 30
    COLLISION_TRIANGLES = 31
    COLLISION_BORDERS = 32
    COLLISION_PARTS = 33
    COLLISION_AABBS = 34
    MODELS = 35
    VISIBILITY = 36
    ENTITIES = 37
    PATHS = 38  # singleplayer only, for AI?
    LIGHTS = 39


LumpHeader = call_of_duty1.LumpHeader

# Known lump changes from Call of Duty -> Call of Duty 2:
# New:
#   LIGHT_GRID_HASH
#   LIGHT_GRID_VALUES
#   DRAW_VERTICES -> VERTICES
#   DRAW_INDICES -> TRIANGLES ?
#   SHADOW_VERTICES
#   SHADOW_INDICES
#   SHADOW_CLUSTERS
#   SHADOW_AABB_TREES
#   SHADOW_SOURCES
#   COLLISION_EDGES
#   COLLISION_TRIANGLES
#   COLLISION_BORDERS
#   COLLISION_PARTS
#   COLLISION_AABBS
#   PATHS
# Deprecated:
#   LIGHT_INDICES
#   COLLISION_INDICES

# TODO: a rough map of the relationships between lumps:


# flag enums
class Surface(enum.IntFlag):
    """wiki.zeroy.com/index.php?title=Call_of_Duty_2:_d3dbsp#Lump.5B0.5D_-_Materials"""
    # NOTE: zeroy's detailing of Contents is confusing, but most of these are paired with: Contents = 0x01;
    BARK = 0x001 << 20
    BRICK = 0x002 << 20
    CARPET = 0x003 << 20
    CLOTH = 0x004 << 20
    CONCRETE = 0x005 << 20
    DIRT = 0x006 << 20
    FLESH = 0x007 << 20
    FOLIAGE = 0x008 << 20  # Contents = 0x02
    GLASS = 0x009 << 20  # Contents = 0x10
    GRASS = 0x00A << 20
    GRAVEL = 0x00B << 20
    ICE = 0x00C << 20
    METAL = 0x00D << 20
    MUD = 0x00E << 20
    PAPER = 0x00F << 20
    PLASTER = 0x01 << 200
    ROCK = 0x011 << 20
    SAND = 0x012 << 20
    SNOW = 0x013 << 20
    WATER = 0x014 << 20  # Contents = 0x20
    WOOD = 0x015 << 20
    ASPHALT = 0x016 << 20
    PORTAL = 0x8 << 28  # Contents = 0x00


# TODO: Contents enum.IntFlag

# classes for lumps, in alphabetical order:
class CollisionEdge(base.Struct):  # LUMP 30
    unknown: int  # an index?
    position: List[float]
    normal: List[List[float]]
    distance: float
    __slots__ = ["unknown", "position", "normal", "distance"]
    _format = "I13f"
    _arrays = {"position": [*"xyz"],
               "normal": {"A": [*"xyz"], "B": [*"xyz"], "C": [*"xyz"]}}
    # NOTE: {"normal": {3: [*"xyz"]}} doesn't work /; (yet)


class CollisionTriangle(base.Struct):  # LUMP 31
    normal: List[float]
    distance: float
    unknown_1: List[float]
    unknown_2: List[int]
    __slots__ = ["normal", "distance", "unknown_1", "unknown_2"]
    _format = "12f6"
    _arrays = {"normal": [*"xyz"], "unknown": 8, "id": 6}


class Model(base.Struct):  # LUMP 35
    mins: List[float]
    maxs: List[float]
    first_triangle_soup: int
    num_triangle_soups: int
    first_mesh: int  # "Patches" (Quake3+ displacements / q3map2 geo)
    num_meshes: int  # indexes Collision* lumps? brush geo physics is brush based
    first_brush: int
    num_brushes: int
    __slots__ = ["mins", "maxs", "first_triangle_soup", "num_triangle_soups",
                 "first_mesh", "num_meshes", "first_brush", "num_brushes"]
    _format = "6f6i"
    _arrays = {"mins": [*"xyz"], "maxs": [*"xyz"]}


class Triangle(list):  # LUMP 9
    _format = "3H"  # List[int]

    def flat(self):
        return self  # HACK


class TriangleSoup(base.MappedArray):  # LUMP 7
    material: int
    draw_order: int  # ?
    first_vertex: int
    num_vertices: int
    first_triangle: int
    num_triangles: int
    _mapping = ["material", "draw_order", "first_vertex", "num_vertices",
                "first_triangle", "num_triangles"]
    _format = "2HI2HI"


class Vertex(base.Struct):  # LUMP 8
    position: List[float]
    normal: List[float]
    colour: List[int]  # RGBA32
    uv0: List[float]  # albedo / normal ?
    uv1: List[float]  # lightmap ?
    unknown: List[float]  # texture vectors? too short... additional uvs?
    __slots__ = ["position", "normal", "colour", "uv0", "uv1", "unknown"]
    _format = "6f4B10f"
    _arrays = {"position": [*"xyz"], "normal": [*"xyz"], "colour": [*"rgba"],
               "uv0": [*"uv"], "uv1": [*"uv"], "unknown": 6}


# {"LUMP_NAME": LumpClass}
BASIC_LUMP_CLASSES = call_of_duty1.BASIC_LUMP_CLASSES.copy()

LUMP_CLASSES = call_of_duty1.LUMP_CLASSES.copy()
LUMP_CLASSES.pop("LIGHTMAPS")  # 4 MB per lightmap?
LUMP_CLASSES.update({"LIGHT_GRID_HASH": quake3.LightVolume,
                     "PORTAL_VERTICES": quake.Vertex,
                     "TRIANGLES":       Triangle,
                     "TRIANGLE_SOUPS":  TriangleSoup,
                     "VERTICES":        Vertex})

SPECIAL_LUMP_CLASSES = call_of_duty1.SPECIAL_LUMP_CLASSES.copy()


methods = [*call_of_duty1.methods]