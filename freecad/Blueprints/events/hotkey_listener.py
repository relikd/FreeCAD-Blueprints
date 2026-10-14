'''
Code related to single-key (A-Z) hotkey interaction with sketcher tools.
'''
from ..gui.qt import QtCore, QtGui, QtWidgets

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from FreeCADGui import View3DInventorPy


class HotkeyListener(QtCore.QObject):
    ''' Register single-key (A-Z) hotkey listener for the sketcher tools. '''
    def __init__(
        self, view: 'View3DInventorPy', onKey: Callable[[str], bool],
    ) -> None:
        '''
        `onKey` is called with a single letter "A" - "Z".
        Return `True` to consume the event.
        '''
        super().__init__()
        self.view: QtWidgets.QGraphicsView = view.graphicsView()
        self.view.installEventFilter(self)
        self.callback = onKey

    def stop(self) -> None:
        ''' Cleanup event listener. Single use! '''
        self.view.removeEventFilter(self)
        del self.view
        del self.callback

    def eventFilter(self, _obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.KeyPress \
                and isinstance(event, QtGui.QKeyEvent) \
                and not event.isAutoRepeat():
            if 64 < (key := event.key()) < 98:  # A-Z
                if self.callback(chr(key)):
                    return True
        return False
