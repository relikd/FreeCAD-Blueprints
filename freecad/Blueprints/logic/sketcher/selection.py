import FreeCADGui

from .georef import GeoId, GeoRef, PointPos

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator
    from FreeCAD import Vector
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
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) != 1:
            return UserSelection(None, None)

        names = sel[0].SubElementNames
        if len(names) != 1:
            return UserSelection(None, None)

        points = sel[0].PickedPoints
        pt = points[0] if points else None

        return UserSelection(pt, getIdsFromName(names[0], sel[0].Object))

    def from_geometry(self, sketch: 'Sketch') -> 'UserSelection|None':
        ''' Try to determine point by geometry itself (only for start/end). '''
        if self.geo and self.geo.pos != PointPos.none:
            vec = sketch.getPoint(self.geo.geoid, self.geo.pos)
            if vec.x != 0 or vec.y != 0:
                return UserSelection(vec, self.geo)
        return None

    @staticmethod
    def geometries() -> 'Iterator[GeoSelection]':
        ''' Returns filtered geometry (Edge + Vertex) of current selection. '''
        for sel in FreeCADGui.Selection.getSelectionEx()[:1]:
            sketch: Sketch = sel.Object
            if sketch.isDerivedFrom('Sketcher::SketchObject'):
                for name in sel.SubElementNames:
                    if name.startswith(('Edge', 'Vertex', 'ExternalEdge')):
                        if ref := getIdsFromName(name, sketch):
                            yield GeoSelection(sketch, ref)


class GeoSelection(NamedTuple):
    sketch: 'Sketch'
    geo: 'GeoRef'


# see https://github.com/FreeCAD/FreeCAD/blob/d3f4da791daa9e94f340b81770d13f090ec679c6/src/Mod/Sketcher/Gui/Utils.cpp#L223-L242
def getIdsFromName(name: str, sketch: 'Sketch') -> 'GeoRef|None':
    if name.startswith('Edge'):
        return GeoRef(int(name[4:]) - 1)

    if name == 'RootPoint':
        return GeoRef(GeoId.RtPnt, PointPos.start)

    if name == 'H_Axis':
        return GeoRef(GeoId.HAxis)

    if name == 'V_Axis':
        return GeoRef(GeoId.VAxis)

    if name.startswith('ExternalEdge'):
        return GeoRef(GeoId.RefExt + 1 - int(name[12:]))

    if name.startswith('Vertex'):
        g, p = sketch.getGeoVertexIndex(int(name[6:]) - 1)
        return GeoRef(g, p)  # type: ignore[arg-type]

    return None
