from __future__ import annotations
import enum

from .. import shared
from .. import x360
# from . import physics
from . import orange_box
from . import source


FILE_MAGIC = b"PSBV"

BSP_VERSION = 20

GAME_PATHS = {"Half-Life 2": "OrangeBox/hl2",
              "Half-Life 2: Episode 1": "OrangeBox/episodic",
              "Half-Life 2: Episode 2": "OrangeBox/ep2",
              "Left 4 Dead": "Left4Dead/left4dead",
              "Left 4 Dead 2": "Left4Dead2/left4dead2",
              "Portal": "OrangeBox/portal",
              "Team Fortress 2": "OrangeBox/tf"}

GAME_VERSIONS = {GAME_NAME: BSP_VERSION for GAME_NAME in GAME_PATHS}


LUMP = orange_box.LUMP


LumpHeader = x360.make_big_endian(source.LumpHeader)


MIN = source.MIN


class MAX(enum.Enum):
    """#if !defined( BSP_USE_LESS_MEMORY )"""
    ENTITIES = 2
    PLANES = 2
    TEXTURE_DATA = 2
    VERTICES = 2
    VISIBILITY_CLUSTERS = 2
    NODES = 2
    TEXTURE_INFO = 2
    FACES = 2
    LIGHTING_SIZE = 2
    LEAVES = 2
    EDGES = 2
    SURFEDGES = 2
    MODELS = 2
    WORLD_LIGHTS = 2
    LEAF_FACES = 2
    LEAF_BRUSHES = 2
    BRUSHES = 2
    BRUSH_SIDES = 2
    AREAS = 2
    AREA_BYTES = 2
    AREA_PORTALS = 2
    # UNUSED_24 [PORTALVERTS] = 2
    DISPLACEMENT_INFO = 2
    ORIGINAL_FACES = FACES
    VERTEX_NORMALS = 2
    VERTEX_NORMAL_INDICES = 2
    DISPLACEMENT_POWER = 4
    DISPLACEMENT_VERTICES_FOR_ONE = (2 ** DISPLACEMENT_POWER + 1) ** 2
    DISPLACEMENT_VERTICES = DISPLACEMENT_INFO * DISPLACEMENT_VERTICES_FOR_ONE
    LEAF_WATER_DATA = 2
    PRIMITIVES = 2
    PRIMITIVE_VERTICES = 2
    PRIMITIVE_INDICES = 2
    TEXDATA_STRING_DATA = 2
    TEXDATA_STRING_TABLE = 2
    OVERLAYS = 2
    DISPLACEMENT_TRIANGLES_FOR_ONE = 2 ** DISPLACEMENT_POWER * 3
    DISPLACEMENT_TRIANGLES = DISPLACEMENT_INFO * DISPLACEMENT_TRIANGLES_FOR_ONE
    WATER_OVERLAYS = 2
    LIGHTING_HDR_SIZE = LIGHTING_SIZE
    WORLD_LIGHTS_HDR = WORLD_LIGHTS
    FACES_HDR = FACES

# classes for each lump, in alphabetical order:
# TODO: Leaf_x360 bitfields are flipped
# TODO: DisplacementInfo_x360, Primitive_x360
# -- see https://github.com/ValveSoftware/source-sdk-2013/blob/master/sp/src/public/bspfile.h
# "#if !defined( BSP_USE_LESS_MEMORY )" & "#if defined( _X360 )" defines specifically


# special lump classes, in alphabetical order:
# TODO: PakFile_x360
# TODO: PhysicsCollide_x360
# class PhysicsDisplacement_x360(physics.Displacement):
#     _int = UnsignedShort_x360


StaticPropv4_x360 = x360.make_big_endian(source.StaticPropv4)
StaticPropv5_x360 = x360.make_big_endian(source.StaticPropv5)
StaticPropv6_x360 = x360.make_big_endian(source.StaticPropv6)
StaticPropv10_x360 = x360.make_big_endian(orange_box.StaticPropv10)
# NOTE: orange_box.StaticPropv10 overrides source.StaticPropv7 (7*)
# -- Left4Dead (Xbox 360) uses v7, & appears to be a new format...


class GameLump_SPRPv4_x360(source.GameLump_SPRPv4):  # sprp GAME LUMP (LUMP 35) [version 4]
    StaticPropClass = StaticPropv4_x360
    endianness = "big"


class GameLump_SPRPv5_x360(source.GameLump_SPRPv5):  # sprp GAME LUMP (LUMP 35) [version 5]
    StaticPropClass = StaticPropv5_x360
    endianness = "big"


class GameLump_SPRPv6_x360(source.GameLump_SPRPv6):  # sprp GAME LUMP (LUMP 35) [version 6]
    StaticPropClass = StaticPropv6_x360
    endianness = "big"


class GameLump_SPRPv10_x360(orange_box.GameLump_SPRPv10):  # sprp GAME LUMP (LUMP 35) [version 7*/10]
    StaticPropClass = StaticPropv10_x360
    endianness = "big"


# {"LUMP_NAME": {version: LumpClass}}
BASIC_LUMP_CLASSES, LumpClasses = x360.convert_versioned(orange_box.BASIC_LUMP_CLASSES)
# copy used BasicLumpClasses to globals
for LumpClass_name, LumpClass in LumpClasses.items():
    globals()[LumpClass_name] = LumpClass


# pop reimplemented classes first to avoid name collision
LUMP_CLASSES = orange_box.LUMP_CLASSES.copy()
LUMP_CLASSES.pop("DISPLACEMENT_INFO")
LUMP_CLASSES.pop("PRIMITIVES")
LUMP_CLASSES, LumpClasses = x360.convert_versioned(LUMP_CLASSES)
# copy used LumpClasses to globals
for LumpClass_name, LumpClass in LumpClasses.items():
    globals()[LumpClass_name] = LumpClass
del LumpClass_name, LumpClass

SPECIAL_LUMP_CLASSES = {"ENTITIES":                 {0: shared.Entities},
                        "TEXTURE_DATA_STRING_DATA": {0: source.TextureDataStringData}}

GAME_LUMP_HEADER = x360.make_big_endian(orange_box.GAME_LUMP_HEADER)

# {"lump": {version: SpecialLumpClass}}
GAME_LUMP_CLASSES = {"sprp": {4:  GameLump_SPRPv4_x360,
                              5:  GameLump_SPRPv5_x360,
                              6:  GameLump_SPRPv6_x360,
                              7:  GameLump_SPRPv10_x360,  # 7* / Left4Dead v7
                              10: GameLump_SPRPv10_x360}}


methods = [*orange_box.methods]
