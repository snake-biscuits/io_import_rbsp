__all__ = ["entities", "geometry", "materials", "props"]

from ..titanfall import entities
# NOTE: titanfall brush entities differ significantly from r1 & 2
# -- "*coll0" "???????????"
# -- use bsp_tool.respawn.starcoll
from . import geometry
from . import materials
from ..titanfall import props
# TODO: props (need to use io_import_semodel + Legion)
