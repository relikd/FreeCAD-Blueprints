'''
Code related to creating a new blueprint from scratch (or selection).
'''
import FreeCAD
import FreeCADGui

from .helper.settings import Settings
from .logic.sketcher.georef import GeoId
from .logic.sketcher.selection import UserSelection
from .gui.qt import QtCore, QtWidgets

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from .logic.sketcher.selection import GeoSelection


def create_blueprint(*, from_selection: bool = False) -> None:
    '''
    Opens a popup to ask user for a document name (inside of user collection
    dir). Then, creates a new document with an empty or pre-populated sketch.
    Nothing happens if the dialog is aborted.
    '''
    # skip a cycle or else `QFileDialog` will break FreeCAD (issue #33776)
    QtCore.QTimer.singleShot(0,
        create_from_selection if from_selection else create_sketch)


def create_sketch() -> 'Sketch|None':
    ''' Ask user for filename, then create a document with an empty sketch. '''
    # TODO: It'd be nice if we could postpone this dialog after user editing.
    #       But then user wouldn't know where to save the document.
    #       Ideally, provide a root folder for the future save dialog.
    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        FreeCADGui.getMainWindow(),
        caption='Save Blueprint',
        dir=str(Settings.databaseDir() / 'Untitled.FCStd'),
        filter='FreeCAD document (*.FCStd)',
    )
    if not path:
        return None
    if not path.lower().endswith('.fcstd'):
        path += '.FCStd'

    doc = FreeCAD.newDocument()
    doc.saveAs(path)
    sketch = doc.addObject('Sketcher::SketchObject', 'Sketch')
    # bring to front and start Sketcher edit mode
    FreeCAD.setActiveDocument(doc.Name)
    if doc := FreeCADGui.ActiveDocument:
        doc.setEdit(sketch)
    return sketch


def create_from_selection() -> None:
    ''' Get currently selected geometry and copy over to new sketch. '''
    # before `create_sketch` or else, selection will be lost.
    selection = list(UserSelection.geometries())
    if not selection:
        return
    new_sketch = create_sketch()
    if not new_sketch:  # user cancelled save dialog
        return

    # we can reuse `selection[0].sketch` ONLY because:
    # - selection is guaranteed to have at least one item (see above)
    # - `UserSelection.geometries` guarantees a single sketch object
    geo_map = _copy_geometry(selection, new_sketch)
    _copy_constraints(selection[0].sketch, new_sketch, geo_map)
    new_sketch.solve()
    FreeCADGui.runCommand('Std_ViewFitAll')


#################################################
# Helper methods
#################################################

def _copy_geometry(sel: list['GeoSelection'], dst: 'Sketch') -> dict[int, int]:
    ''' Helper method to copy geometry. '''
    uniq = set()
    geo_objs, old_geo_ids = [], []
    for sk, geo in sel:
        gid = geo.geoid
        if gid not in uniq:
            uniq.add(gid)
            old_geo_ids.append(gid)
            if GeoId.isExt(gid):
                geo_objs.append(sk.ExternalGeo[-gid - 1])
            else:
                geo_objs.append(sk.Geometry[gid])
    rv = dict(zip(old_geo_ids, dst.addGeometry(geo_objs)))
    # allow axis refs (+ `Undef` for easier compare in `_copy_constraints`)
    rv.update({x: x for x in
        (GeoId.RtPnt, GeoId.HAxis, GeoId.VAxis, GeoId.Undef)})
    return rv


def _copy_constraints(src: 'Sketch', dst: 'Sketch', g_map: dict[int, int]) \
        -> None:
    ''' Helper method to copy constraints. '''
    con_list = []
    for con in src.Constraints:
        if con.First in g_map and con.Second in g_map and con.Third in g_map:
            con.First = g_map[con.First]
            if con.Second != GeoId.Undef:
                con.Second = g_map[con.Second]
            if con.Third != GeoId.Undef:
                con.Third = g_map[con.Third]
            con_list.append(con)
    dst.addConstraint(con_list)
