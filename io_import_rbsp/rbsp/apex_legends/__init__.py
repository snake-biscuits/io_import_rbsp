from ..titanfall import entities
# NOTE: titanfall brush entities differ significantly from r1 & 2
# -- "*coll0" "???????????"
from . import geometry
from . import materials
from ..titanfall import props
# TODO: props (need to use io_import_semodel + Legion)


__all__ = ["entities", "geometry", "materials", "props"]
