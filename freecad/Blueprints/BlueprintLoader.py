'''
Code related to loading a Sketch document from disk (with user interaction).
'''
import FreeCAD

from .helper.notify import Notify
from .GuiFileBrowser import open_blueprint_browser
from .GuiSketchChoice import open_sketch_chooser

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from FreeCAD import Document


def chooseBlueprint() -> 'Sketch|None':
    '''
    Open file browser to let user choose which Sketch to load.

    If a sketch is returned, you are responsible for closing the document.
    e.g., `FreeCAD.closeDocument(sketch.Document.Name)`
    '''
    if path := open_blueprint_browser():
        return _loadSketchAtPath(str(path))
    return None


def _loadSketchAtPath(path: str) -> 'Sketch|None':
    '''
    Same as `_loadSketchFromDoc()` but opens Document first.

    If a sketch is returned, you are responsible for closing the document.
    e.g., `FreeCAD.closeDocument(sketch.Document.Name)`
    '''
    curDocName = curDoc.Name if (curDoc := FreeCAD.ActiveDocument) else ''
    if not curDocName:
        Notify.warn('No active document', 'Cannot switch to active document.')
        return None
    # may raise exception and quit
    # hide in open documents tab-bar (hidden) and in model tree (temporary)
    doc = FreeCAD.openDocument(path, hidden=True, temporary=True)  # type: ignore[call-arg]
    # revert focus to original document (prevents a nasty crash in Sketcher)
    FreeCAD.setActiveDocument(curDocName)
    if sk := _loadSketchFromDoc(doc):
        return sk
    # if no sketch found, close doc immediatelly
    FreeCAD.closeDocument(doc.Name)
    return None


def _loadSketchFromDoc(doc: 'Document') -> 'Sketch|None':
    ''' Filter document by Sketch-type and ask user which one to load. '''
    sks: list[Sketch] = [x for x in doc.Objects
                         if x.isDerivedFrom('Sketcher::SketchObject')]
    if not sks:
        return None  # document does not contain any sketches
    if len(sks) == 1:
        return sks[0]  # if there is only one, load it right away
    return open_sketch_chooser(sks)


def reloadSketch(sketch: 'Sketch') -> 'Sketch':
    ''' Reload sketch from disk. '''
    # TODO: replace with `doc.restore()` once #33181 is fixed
    activeDoc = FreeCAD.ActiveDocument
    sketch_id = sketch.ID
    path = sketch.Document.FileName
    FreeCAD.closeDocument(sketch.Document.Name)
    doc = FreeCAD.openDocument(path, hidden=True, temporary=True)  # type: ignore[call-arg]
    if activeDoc:
        FreeCAD.setActiveDocument(activeDoc.Name)  # restore Focus
    return doc.getObject(sketch_id)
