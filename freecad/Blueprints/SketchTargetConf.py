'''
Code related to placing the new Sketch relative to the old selection.
'''
from dataclasses import dataclass

import FreeCADGui

from .helper.georef import GeoId, GeoRef, PointPos

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCAD import Vector
    from FreeCADGui import SelectionObject
    from Sketcher import SketchObject as Sketch


@dataclass
class SketchTargetConf:
    '''
    placement:
        Place blueprint at these coordinates (instead of origin).
    constrainTo:
        If user has selected an Edge or Vertex prior to loading the blueprint,
        add an `PointOnObject` / `Coincident` constraint (respectively).
    allowRotate:
        After import, run `removeAxesAlignment` to allow blueprint rotation.
        This depends heavily on the quality of the source sketch.
        Please avoid `DistanceX` and `DistanceY` constraints.
    '''
    placement: 'Vector|None'
    constrainTo: 'GeoRef|None'
    allowRotate: bool

    def __init__(self, sketch: 'Sketch', *, allowRotate: bool = False):
        # offset = dst.getPoint(selection.geoid, selection.pos)
        pt, geo = _getSketcherSelection()
        # if selection but not manually clicked (no `PickedPoints`),
        # try to determine point by the geometry itself (only for start/end pt)
        if not pt and geo and geo.pos != PointPos.none:
            vec = sketch.getPoint(geo.geoid, geo.pos)
            if vec.x != 0 or vec.y != 0:
                pt = vec
        # if still empty, use current screen center point for insertion
        if not pt:
            pt = getViewCenter()
        # if still empty, give up
        self.placement = pt
        self.constrainTo = geo
        self.allowRotate = allowRotate


def _getSketcherSelection() -> 'tuple[Vector|None, GeoRef|None]':
    '''
    Get currently selected Edge or Vertex.
    Nothing else – in all other cases return `None`.
    Assumes UI is already in Sketcher edit mode.
    '''
    selection: list[SelectionObject] = FreeCADGui.Selection.getSelectionEx()
    if len(selection) != 1:
        return None, None

    names = selection[0].SubElementNames
    if len(names) != 1:
        return None, None

    points = selection[0].PickedPoints
    pt = points[0] if points else None
    name = names[0]

    if name.startswith('Edge'):
        return pt, GeoRef(int(name.removeprefix('Edge')) - 1)

    if name.startswith('Vertex'):
        sketch: Sketch = selection[0].Object
        g, p = sketch.getGeoVertexIndex(int(name.removeprefix('Vertex')) - 1)
        return pt, GeoRef(g, p)  # type: ignore[arg-type]

    if name == 'H_Axis':
        return pt, GeoRef(GeoId.HAxis)
    if name == 'V_Axis':
        return pt, GeoRef(GeoId.VAxis)
    if name == 'RootPoint':
        return pt, GeoRef(GeoId.HAxis, PointPos.start)

    return None, None


def getViewCenter() -> 'Vector|None':
    ''' Current screen center point. '''
    if doc := FreeCADGui.ActiveDocument:
        if view := doc.ActiveView:
            if pos := view.viewPosition():
                return pos.Base
    return None
