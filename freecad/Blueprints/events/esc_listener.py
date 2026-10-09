'''
Code related to triggering ESC hotkey.
'''
import FreeCADGui
from ..gui.qt import QtCore, QtGui, QtWidgets

from typing import Callable


# the correct way would be to use:
#   ViewProviderSketch::activateHandler + ViewProviderSketch::keyPressed
# but that isnt exposed to python
# see https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Sketcher/Gui/ViewProviderSketch.cpp

class EscListener(QtCore.QObject):
    '''
    Intercept ESC key and forward to `on_esc` callback.
    Return `True` to stop event propagation (aka. prevent other ESC triggers).
    '''
    def __init__(self, on_esc: Callable[[], bool]) -> None:
        super().__init__()
        app = QtWidgets.QApplication.instance()
        if not app:
            raise RuntimeError('Missing Qt application.')
        self.app = app
        self.callback = on_esc
        app.installEventFilter(self)

    def stop(self) -> None:
        ''' Cleanup event listener. Single use! '''
        self.app.removeEventFilter(self)
        del self.callback
        del self.app

    def eventFilter(self, _obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if (
            isinstance(event, QtGui.QKeyEvent)
            # Dialogs react to KeyPress, sketcher tools react to KeyRelease.
            # We cannot fix both. Escaping a dialog will exit sketcher tool.
            and event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() == QtCore.Qt.Key.Key_Escape
        ):
            # only close if main window == active window. Allows ESC on dialogs
            if focus_on_main_window() and self.callback():
                event.accept()
                return True
        return False


def focus_on_main_window() -> bool:
    return QtWidgets.QApplication.activeWindow() == FreeCADGui.getMainWindow()
