from .constraints import Constr
from .geodraw import Draw
from .georef import GeoId, GeoRef, PointPos

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCAD import Vector
    from Part import Geometry

__all__ = ['Constr', 'Draw', 'GeoId', 'GeoRef', 'PointPos']


def moveTo(pos: 'Vector|None', geo: 'Geometry') -> 'Geometry':
    ''' Move geometry and return it (allows chaining). '''
    if pos:
        geo.translate(pos)
    return geo
