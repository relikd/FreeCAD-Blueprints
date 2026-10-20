import FreeCADGui

from .georef import GeoId, GeoRef, PointPos

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from FreeCAD import Vector
    from FreeCADGui import SelectionObject
    from Sketcher import SketchObject as Sketch


class UserSelection(NamedTuple):
    ''' `vec` is `None` if clicked point was parallel to sketch plane. '''
    vec: 'Vector|None'
    geo: 'GeoRef|None'

    @staticmethod
    def get_current() -> 'UserSelection':
        '''
        Get currently selected Edge or Vertex – nothing else.
        In all other cases return `None`.
        Assumes UI is already in Sketcher edit mode.
        '''
        sel: list[SelectionObject] = FreeCADGui.Selection.getSelectionEx()
        if len(sel) != 1:
            return UserSelection(None, None)

        names = sel[0].SubElementNames
        if len(names) != 1:
            return UserSelection(None, None)

        points = sel[0].PickedPoints
        pt = points[0] if points else None
        name = names[0]

        if geoid := _name_to_geoid(name, 'Edge'):
            return UserSelection(pt, GeoRef(geoid[0]))

        if geoid := _name_to_geoid(name, 'ExternalEdge'):
            return UserSelection(pt, GeoRef(GeoId.RefExt - geoid[0]))

        if geoid := _name_to_geoid(name, 'Vertex'):
            sketch: Sketch = sel[0].Object
            g, p = sketch.getGeoVertexIndex(geoid[0])
            return UserSelection(pt, GeoRef(g, p))  # type: ignore[arg-type]

        if name == 'H_Axis':
            return UserSelection(pt, GeoRef(GeoId.HAxis))
        if name == 'V_Axis':
            return UserSelection(pt, GeoRef(GeoId.VAxis))
        if name == 'RootPoint':
            return UserSelection(pt, GeoRef(GeoId.HAxis, PointPos.start))

        return UserSelection(pt, None)

    def from_geometry(self, sketch: 'Sketch') -> 'UserSelection|None':
        ''' Try to determine point by geometry itself (only for start/end). '''
        if self.geo and self.geo.pos != PointPos.none:
            vec = sketch.getPoint(self.geo.geoid, self.geo.pos)
            if vec.x != 0 or vec.y != 0:
                return UserSelection(vec, self.geo)
        return None


def _name_to_geoid(name: str, prefix: str) -> 'tuple[int]|None':
    ''' Helper to reduce boilerplate code. Tuple to allow walrus operator. '''
    if name.startswith(prefix):
        if num := name.removeprefix(prefix).strip():
            return (int(num) - 1,)
    return None
