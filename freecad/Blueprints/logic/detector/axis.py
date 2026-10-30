'''
Detect if any axis or origin point was referenced.
'''
from ..sketcher.georef import GeoId, PointPos

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


class ReferencedAxis(NamedTuple):
    v: bool
    h: bool
    origin: bool


def detect_axis(sketch: 'Sketch') -> ReferencedAxis:
    ''' Check whether sketch references `(VAxis, HAxis, RtPnt)`. '''
    v, h, origin = False, False, False
    for con in sketch.Constraints:
        for geo, pos in (
            (con.First, con.FirstPos),
            (con.Second, con.SecondPos),
            (con.Third, con.ThirdPos),
        ):
            if geo == GeoId.VAxis:
                v = True
            elif geo == GeoId.HAxis:
                if pos == PointPos.start:
                    origin = True
                else:
                    h = True
        if v and h:  # origin not relevant. h is used as origin
            return ReferencedAxis(True, True, True)  # break early
    return ReferencedAxis(v, h, origin)
