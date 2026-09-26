'''
Code related to geometry references (axes and center point)
'''
from enum import IntEnum
from typing import NamedTuple


# see https://github.com/FreeCAD/FreeCAD/blob/77069de933ab6fd57efa295632f65de1c55e1dd2/src/Mod/Sketcher/App/GeoEnum.h#L39-L42
class GeoId:
    RtPnt = -1  # GeoId of the Root Point
    HAxis = -1  # GeoId of the Horizontal Axis
    VAxis = -2  # GeoId of the Vertical Axis
    # Starting GeoID of external geometry (negative ids starting at this index)
    RefExt = -3
    # GeoId of an undefined Geometry (uninitialised or unused GeoId)
    Undef = -2000

    @staticmethod
    def isAxis(val: int) -> bool:
        ''' `True` if `HAxis` or `VAxis` '''
        return val == GeoId.HAxis or val == GeoId.VAxis

    @staticmethod
    def isExt(val: int) -> bool:
        ''' `True` if `-3 >= val > -2000` '''
        return GeoId.RefExt >= val > GeoId.Undef


# see https://github.com/FreeCAD/FreeCAD/blob/77069de933ab6fd57efa295632f65de1c55e1dd2/src/Mod/Sketcher/App/GeoEnum.h#L86-L92
class PointPos(IntEnum):
    none = 0  # Edge of a geometry
    start = 1  # Starting point of a geometry
    end = 2  # End point of a geometry
    mid = 3  # Mid point of a geometry


class GeoRef(NamedTuple):
    ''' Geometry reference / point on geometry. Default: Edge [X, 0] '''
    geoid: int  # constraint id
    pos: PointPos = PointPos.none  # default: Edge [X, 0]

    @staticmethod
    def S(geoid: int) -> 'GeoRef':
        ''' Start point [X, 1] '''
        return GeoRef(geoid, PointPos.start)

    @staticmethod
    def E(geoid: int) -> 'GeoRef':
        ''' End point [X, 2] '''
        return GeoRef(geoid, PointPos.end)

    @staticmethod
    def M(geoid: int) -> 'GeoRef':
        ''' Mid point [X, 3] '''
        return GeoRef(geoid, PointPos.mid)
