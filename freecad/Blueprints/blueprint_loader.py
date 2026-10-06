'''
Code related to loading a Sketch document from disk (with user interaction).
'''
import FreeCAD

from .helper.notify import Notify
from .gui_file_browser import open_blueprint_browser
from .gui.sketch_choice import open_sketch_chooser

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


# fixes: Vanishing expressions after multi-copy insert
#
# After the third copy, expressions from the second copy are forgotten.
# Also, the last copy will forget its expressions as soon as a new constraint
# is added – or the sketch is closed. Restoring the document fixes this issue.
#
# What didn't work:
# - copy geo+constr+expr without modifying the source sketch in any way
# - insert constraints in various ways (also by deleting prev and reinserting)
# - delete and rebuild constr+expr on SOURCE sketch (before & after copying)
# - adding geo+constr as list & individually
# - abortTransaction() and commitTransaction() + undo()
# - recompute() and solve() at various points and for both, source & dest
# - reference map for geo+constr ids instead of start_index + offset
#
# The root cause is likely some modified document state or a FreeCAD bug.
# Hopefully this reload can be omitted at some point.
def reloadSketch(sketch: 'Sketch') -> 'Sketch':
    ''' Reload sketch from disk. '''
    activeDoc = FreeCAD.ActiveDocument
    sketch_id = sketch.ID
    path = sketch.Document.FileName
    # TODO: replace with `doc.restore()` once #33181 is fixed
    FreeCAD.closeDocument(sketch.Document.Name)
    doc = FreeCAD.openDocument(path, hidden=True, temporary=True)  # type: ignore[call-arg]
    if activeDoc:
        FreeCAD.setActiveDocument(activeDoc.Name)  # restore Focus
    return doc.getObject(sketch_id)
