'''
Code related to other sketcher tools interaction.
Exit current tool if another is selected.
'''
import FreeCADGui

from ..gui.qt import QtGui, QtCore
from ..register_commands import CMD_NAME

from typing import Callable

IGNORED = {
    'Part_SelectFilter', 'Sketcher_ViewSketch', 'Sketcher_ViewSection',
    CMD_NAME,
}


class ActionListener(QtCore.QObject):
    '''
    Listen for any action / tool change.
    Triggers `on_action` after the fact (cursor already changed to new tool).
    '''
    def __init__(self, on_action: Callable[[], None]):
        super().__init__()
        self.callback = on_action
        self.actions: list[QtGui.QAction] = []

        # https://github.com/FreeCAD/FreeCAD/blob/main/src/Gui/Workbench.cpp
        # Hopefully including all "Std_" wont do any damage.
        # This also includes "Std_Macro_0" etc.
        filtered = {x for x in available_commands()
                    if not x.startswith('Std_')} - IGNORED

        for action in available_actions():
            if action.objectName() in filtered:
                action.triggered.connect(self.triggered)
                self.actions.append(action)

    def triggered(self, _checked: bool = False) -> None:  # noqa: FBT001 FBT002
        # action: QtGui.QAction = self.sender()  # type: ignore[assignment]
        # from ..helper.notify import Notify
        # Notify.Log.err(f'{action.objectName()}')
        self.callback()

    def stop(self) -> None:
        ''' Cleanup event listener. '''
        for action in self.actions:
            try:
                action.triggered.disconnect(self.triggered)
            except (RuntimeError, TypeError):
                pass

        self.actions.clear()
        del self.actions
        del self.callback


#################################################
# Typed helper
#################################################

def available_actions() -> list[QtGui.QAction]:
    return FreeCADGui.getMainWindow().findChildren(QtGui.QAction)


def available_commands() -> list[str]:
    return FreeCADGui.listCommands()
