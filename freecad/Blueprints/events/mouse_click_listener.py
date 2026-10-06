'''
Code related to geometry selection (or plain sketch clicks without geometry).
'''
import FreeCADGui  # Selection
from FreeCAD import Vector

from ..gui.qt import QtCore
from ..helper.georef import GeoId, GeoRef, PointPos

from typing import TYPE_CHECKING, Callable, NamedTuple

if TYPE_CHECKING:
    from FreeCADGui import SelectionObject, View3DInventorPy
    from Sketcher import SketchObject as Sketch


class UserSelection(NamedTuple):
    ''' `vec` is `None` if clicked point was parallel to sketch plane. '''
    vec: 'Vector|None'
    geo: 'GeoRef|None'


class MouseClickListener:
    ''' Monitor mouse clicks and report selected geometry in `on_click`. '''
    def __init__(
        self,
        view: 'View3DInventorPy',
        sketch: 'Sketch',
        on_click: Callable[[UserSelection], None],
    ):
        self.view = view
        self.sketch = sketch
        self.callback = on_click
        self.callback_id = self.view.addEventCallback(
            'SoMouseButtonEvent', self.on_mouse_event,
        )
        self.prev_pos = (0, 0)
        self.started_with_selection = False

    def stop(self) -> None:
        ''' Stop all events and callbacks. Cleanup attrs. Single use! '''
        self.view.removeEventCallback('SoMouseButtonEvent', self.callback_id)
        del self.callback_id
        del self.callback
        del self.sketch
        del self.view

    def on_mouse_event(self, info: dict) -> None:
        if info.get('Button') != 'BUTTON1':
            return
        pos = info.get('Position')
        if not isinstance(pos, tuple):
            return
        pos = int(pos[0]), int(pos[1])

        if info.get('State') == 'DOWN':
            self.prev_pos = pos
            self.started_with_selection = has_selection()
        elif info.get('State') == 'UP' and self.is_pure_click(pos):
            # delayed because `getSelectionEx` isnt populated yet
            QtCore.QTimer.singleShot(0, lambda: self.did_click(*pos))

    def did_click(self, x: int, y: int) -> None:
        ''' Callback for mouse-UP events. '''
        if self.started_with_selection:
            FreeCADGui.Selection.clearSelection()
        else:
            self.callback(self._selection(x, y))

    def is_pure_click(self, pos: tuple[int, int]) -> bool:
        ''' `False` if user moved cursor during click, e.g., rect select. '''
        prev = self.prev_pos
        return (pos[0] - prev[0]) ** 2 + (pos[1] - prev[1]) ** 2 < 64

    # Internal methods

    def _screen_center(self) -> 'Vector|None':
        ''' Map screen center point to sketch coordinates. '''
        size = self.view.getSize()
        return self._screen_to_sketch(size[0] // 2, size[1] // 2)

    def _screen_to_sketch(self, x: int, y: int) -> 'Vector|None':
        ''' Transform screen point into sketch coordinates. '''
        pt_3d: Vector = self.view.getPoint(x, y)
        cam_dir = self.view.getCameraOrientation().multVec(Vector(0, 0, -1))

        inverse = self.sketch.getGlobalPlacement().inverse()
        inv_pt = inverse.multVec(pt_3d)
        inv_dir = inverse.Rotation.multVec(cam_dir)

        if abs(inv_dir.z) < 1e-12:
            return None  # View is parallel to sketch plane

        pt_2d = inv_pt + inv_dir * (-inv_pt.z / inv_dir.z)
        return Vector(pt_2d.x, pt_2d.y)

    def _selection(self, x: int, y: int) -> UserSelection:
        ''' Try to detect user selected geometry as best as possible. '''
        selected = _current_sketcher_selection()
        # ideally return user-selected geometry (only if geometry was clicked)
        if selected.vec:
            return selected
        # if geometry selected without manual click (no `PickedPoints`),
        # try to determine point by geometry itself (only for start/end pt)
        if selected.geo and selected.geo.pos != PointPos.none:
            vec = self.sketch.getPoint(selected.geo.geoid, selected.geo.pos)
            if vec.x != 0 or vec.y != 0:
                return UserSelection(vec, selected.geo)
        # if that fails, fallback to clicked coordinates
        if clicked_pt := self._screen_to_sketch(x, y):
            return UserSelection(clicked_pt, selected.geo)
        # or screen center point (will likely never trigger)
        if center := self._screen_center():
            return UserSelection(center, None)
        # if everything fails, insert at axis origin
        return UserSelection(None, None)


#################################################
# Helper
#################################################


def has_selection() -> bool:
    ''' Check if there is any geometry selected '''
    rv: list[SelectionObject] = FreeCADGui.Selection.getSelectionEx()
    return len(rv) == 1 and len(rv[0].SubElementNames) > 0


def _current_sketcher_selection() -> UserSelection:
    '''
    Get currently selected Edge or Vertex.
    Nothing else – in all other cases return `None`.
    Assumes UI is already in Sketcher edit mode.
    '''
    selection: list[SelectionObject] = FreeCADGui.Selection.getSelectionEx()
    if len(selection) != 1:
        return UserSelection(None, None)

    names = selection[0].SubElementNames
    if len(names) != 1:
        return UserSelection(None, None)

    points = selection[0].PickedPoints
    pt = points[0] if points else None
    name = names[0]

    if geoid := _name_to_geoid(name, 'Edge'):
        return UserSelection(pt, GeoRef(geoid[0]))

    if geoid := _name_to_geoid(name, 'ExternalEdge'):
        return UserSelection(pt, GeoRef(GeoId.RefExt - geoid[0]))

    if geoid := _name_to_geoid(name, 'Vertex'):
        sketch: Sketch = selection[0].Object
        g, p = sketch.getGeoVertexIndex(geoid[0])
        return UserSelection(pt, GeoRef(g, p))  # type: ignore[arg-type]

    if name == 'H_Axis':
        return UserSelection(pt, GeoRef(GeoId.HAxis))
    if name == 'V_Axis':
        return UserSelection(pt, GeoRef(GeoId.VAxis))
    if name == 'RootPoint':
        return UserSelection(pt, GeoRef(GeoId.HAxis, PointPos.start))

    return UserSelection(pt, None)


def _name_to_geoid(name: str, prefix: str) -> 'tuple[int]|None':
    ''' Helper to reduce boilerplate code. Tuple to allow walrus operator. '''
    if name.startswith(prefix):
        if num := name.removeprefix(prefix).strip():
            return (int(num) - 1,)
    return None
