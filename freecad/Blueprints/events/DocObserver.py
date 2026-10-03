from dataclasses import dataclass

import FreeCADGui

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from PartDesignGui import ViewProvider


# see https://github.com/FreeCAD/FreeCAD/blob/e7ee55e0264d80ec002c3e72ba78a22f53a944c9/src/Gui/DocumentModel.h#L61-L72
@dataclass
class DocObserver:
    '''
    Listen for document changes (`FreeCADGui.addDocumentObserver`).
    Currently constrained on sketch objects.
    '''

    onEditStart: Callable[[], None] | None = None
    onEditEnd: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        FreeCADGui.addDocumentObserver(self)

    def stop(self) -> None:
        FreeCADGui.removeDocumentObserver(self)

    def slotInEdit(self, vp: 'ViewProvider') -> None:
        ''' New editing session has started. '''
        if self.onEditStart:
            if_sketch(vp, self.onEditStart)

    def slotResetEdit(self, vp: 'ViewProvider') -> None:
        ''' Editing session has ended. '''
        if self.onEditEnd:
            if_sketch(vp, self.onEditEnd)


def if_sketch(vp: 'ViewProvider', callback: Callable[[], None]) -> None:
    if vp.Object.isDerivedFrom('Sketcher::SketchObject'):
        callback()
