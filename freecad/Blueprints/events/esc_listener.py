'''
Code related to triggering ESC hotkey.
'''
from ..gui.qt import QtCore, QtGui, QtWidgets

from typing import Callable


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
            and event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() == QtCore.Qt.Key.Key_Escape
        ):
            if self.callback():
                event.accept()
                return True
        return False
