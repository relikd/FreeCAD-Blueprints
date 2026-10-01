import FreeCADGui

from .events.ActionListener import ActionListener
from .events.EscListener import EscListener
from .events.MouseClickListener import MouseClickListener, UserSelection
from .events.MouseCursorListener import MouseCursorListener
from .BlueprintDuplicator import BlueprintDuplicator

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from PartDesignGui import ViewProvider
    from Sketcher import SketchObject as Sketch


_SESSIONS: list['BlueprintInserter'] = []


class BlueprintInserter:
    @staticmethod
    def cancel_previous() -> None:
        ''' Cancel any previous insert session. '''
        for prev in _SESSIONS:
            prev.close()

    def __init__(self, current: 'Sketch', blueprint: 'Sketch', *,
                 on_close: Callable[[], None]) -> None:
        doc = FreeCADGui.ActiveDocument
        if not doc:
            raise RuntimeError('No active document')
        view = doc.ActiveView
        if not view:
            raise RuntimeError('No active view')

        _SESSIONS.append(self)

        self.current = current
        self.blueprint = blueprint
        self.callback = on_close

        # indicate insertion mode by showing cursor icon
        self.cursor_monitor = MouseCursorListener(view)
        # listen for mouse click events
        self.click_monitor = MouseClickListener(view, current, self.did_click)
        # exit if user performs another action (e.g. other geometry tool)
        self.action_monitor = ActionListener(self.on_other_action)
        # user pressed esc to exit insertion mode
        self.esc_monitor = EscListener(self.on_esc)
        # self-close on exiting Sketcher Edit Mode
        FreeCADGui.addDocumentObserver(self)

    def close(self, *, postponeCursorCleanup: bool = False) -> None:
        _SESSIONS.remove(self)
        FreeCADGui.removeDocumentObserver(self)
        self.cursor_monitor.stop(cleanupLater=postponeCursorCleanup)
        self.click_monitor.stop()
        self.action_monitor.stop()
        self.esc_monitor.stop()
        del self.cursor_monitor
        del self.click_monitor
        del self.action_monitor
        del self.esc_monitor
        self.callback()
        del self.callback
        del self.blueprint
        del self.current

    def on_other_action(self) -> None:
        # keep cursor icon because by now, the new tool is already loaded
        self.close(postponeCursorCleanup=True)

    def on_esc(self) -> bool:
        ''' Dialog exited by pressing ESC key. '''
        self.close()
        return True

    def slotResetEdit(self, _obj: 'ViewProvider') -> None:  # DocumentObserver
        ''' Called when exiting sketcher edit mode. '''
        self.close()

    def did_click(self, sel: UserSelection) -> None:
        duplicator = BlueprintDuplicator(sel.vec, sel.geo, allowRotate=False)
        thisDoc = self.current.Document
        thisDoc.openTransaction('Insert Blueprint (Sketch)')
        try:
            duplicator.copyTo(self.current, src=self.blueprint)
            thisDoc.commitTransaction()
            FreeCADGui.Selection.clearSelection()
        except Exception:
            thisDoc.abortTransaction()
            self.close()
            raise
