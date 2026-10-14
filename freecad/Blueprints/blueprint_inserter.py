'''
Code related to the workflow of inserting a sketch (key-, mouse-events, etc.).
'''
import FreeCAD
import FreeCADGui

from .events.action_listener import ActionListener
from .events.doc_observer import DocObserver
from .events.esc_listener import EscListener
from .events.hotkey_listener import HotkeyListener
from .events.mouse_click_listener import MouseClickListener, UserSelection
from .events.mouse_cursor_listener import MouseCursorListener
from .gui.sketcher_tool import BlueprintSketcherTool
from .blueprint_duplicator import BlueprintDuplicator
from .blueprint_loader import reloadSketch

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


_SESSIONS: list['BlueprintInserter'] = []


class BlueprintInserter:
    @staticmethod
    def cancel_previous(*, keepOpen: 'Sketch') -> None:
        ''' Cancel any previous insert session. '''
        for prev in _SESSIONS:
            same_doc = prev.blueprint.Document.Name == keepOpen.Document.Name
            prev.close(keepOpen=same_doc)

    def __init__(self, current: 'Sketch', blueprint: 'Sketch') -> None:
        doc = FreeCADGui.ActiveDocument
        if not doc:
            raise RuntimeError('No active document')
        view = doc.ActiveView
        if not view:
            raise RuntimeError('No active view')

        # Required for `.DoF` access in `sketcher_tool` later.
        # Not necessary for `.FullyConstrained` (if performance need arises).
        # ... but also nice to enforce properly defined blueprints.
        if (err := blueprint.solve()) != 0:
            raise RuntimeError(
                f'Sketch solver error: {err}. '
                'This is an issue with the blueprint template file.')

        _SESSIONS.append(self)

        self.current = current
        self.blueprint = blueprint
        self.prev_state = {}

        # indicate insertion mode by showing cursor icon
        self.cursor_monitor = MouseCursorListener(view)
        # listen for mouse click events
        self.click_monitor = MouseClickListener(view, current, self.did_click)
        # exit if user performs another action (e.g. other geometry tool)
        self.action_monitor = ActionListener(self.on_other_action)
        # user pressed esc to exit insertion mode
        self.esc_monitor = EscListener(self.on_esc)
        # self-close on exiting Sketcher Edit Mode
        self.doc_monitor = DocObserver(onEditEnd=self.on_end_editing)
        # add option buttons to sketcher task panel
        self.sketcher_tool = BlueprintSketcherTool(self)
        # allow user to toggle sketcher tool options with single-key hotkeys
        self.hotkeyd = HotkeyListener(view, self.sketcher_tool.on_hotkey)

    def close(
        self,
        *,
        postponeCursorCleanup: bool = False,
        reopenInEditMode: bool = False,
        keepOpen: bool = False,
    ) -> None:
        _SESSIONS.remove(self)
        self.cursor_monitor.stop(cleanupLater=postponeCursorCleanup)
        self.click_monitor.stop()
        self.action_monitor.stop()
        self.esc_monitor.stop()
        self.doc_monitor.stop()
        self.hotkeyd.stop()
        self.sketcher_tool.stop()
        del self.cursor_monitor
        del self.click_monitor
        del self.action_monitor
        del self.esc_monitor
        del self.doc_monitor
        del self.hotkeyd
        del self.sketcher_tool
        if reopenInEditMode:
            new_sketch = reloadSketch(self.blueprint, hidden=False)
            if doc := FreeCADGui.ActiveDocument:
                doc.setEdit(new_sketch)
        elif not keepOpen:
            FreeCAD.closeDocument(self.blueprint.Document.Name)
        del self.blueprint
        del self.current

    def on_other_action(self) -> None:
        # keep cursor icon because by now, the new tool is already loaded
        self.close(postponeCursorCleanup=True)

    def on_esc(self) -> bool:
        ''' Dialog exited by pressing ESC key. '''
        self.close()
        return True

    def on_end_editing(self) -> None:
        ''' Sketch editing ended via close dialog. '''
        self.close(postponeCursorCleanup=True)

    def did_click(self, sel: UserSelection) -> None:
        options = self.sketcher_tool.get_state()
        duplicator = BlueprintDuplicator(
            sel.vec, sel.geo,
            allowRotate=options.rotation,
            hideUnnamed=options.hide_unnamed,
            # `prev_state` is updated (and reused) only if the checkbox is set.
            # Else, a new dict is created and discarded in the same run.
            # If toggled multiple times during insert, `prev_state` will reuse
            # the first copy instead of some in-between copy.
            # Starting a new blueprint session, will also reset the first copy.
            namedEquals=self.prev_state if options.equal_named else {},
        )
        thisDoc = self.current.Document
        thisDoc.openTransaction('Insert Blueprint (Sketch)')
        try:
            duplicator.copyTo(self.current, src=self.blueprint)
            thisDoc.commitTransaction()
        except Exception:
            thisDoc.abortTransaction()
            self.close()
            raise

        FreeCADGui.Selection.clearSelection()
        # TODO: Try to get rid of this. See note in definition.
        self.blueprint = reloadSketch(self.blueprint)
