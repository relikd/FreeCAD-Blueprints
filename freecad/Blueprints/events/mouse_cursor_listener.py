'''
Code related to changing the current cursor icon in the 3D navigation view.
'''
from ..gui.qt import QtCore, Icon

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCADGui import View3DInventorPy
    from ..gui.qt import QtWidgets


class MouseCursorListener(QtCore.QObject):
    ''' Temporarily change mouse cursor to blueprint insert mode. '''
    def __init__(self, view: 'View3DInventorPy') -> None:
        super().__init__()
        _DelayedCursorReset.clear()
        self.view: QtWidgets.QGraphicsView = view.graphicsView()
        self.view.installEventFilter(self)
        self.cursor = Icon.blueprint_cursor()
        self._reApplyCursor()

    def stop(self, *, cleanupLater: bool) -> None:
        ''' Cleanup event listener. Single use! '''
        self.view.removeEventFilter(self)

        if self.is_my_cursor:
            self.view.unsetCursor()
        elif cleanupLater:
            _DelayedCursorReset(self.view, self.cursor.pixmap().cacheKey())

    @property
    def is_my_cursor(self) -> bool:
        return self.view.cursor().pixmap().cacheKey() \
            == self.cursor.pixmap().cacheKey()

    @property
    def is_default_cursor(self) -> bool:
        return self.view.cursor().shape() == QtCore.Qt.CursorShape.ArrowCursor

    def eventFilter(self, _obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.CursorChange \
                and self.is_default_cursor:
            QtCore.QTimer.singleShot(0, self._reApplyCursor)
        return False

    def _reApplyCursor(self) -> None:
        self.view.setCursor(self.cursor)


#################################################
# Hopefully we can get rid of this soon
#################################################

_DELAYED_CURSOR_RESETTER: 'list[_DelayedCursorReset]' = []


class _DelayedCursorReset(QtCore.QObject):
    '''
    Auto-managed delayed executor for removing our custom cursor icon.
    Only instantiated when user switches to another tool because the
    `.triggered` event happens after the cursor icon is already changed
    to the new tool icon. This class listens for `CursorChange` events until a
    change with our original icon occurs. Afterwards this class self-destructs.
    '''
    def __init__(self, view: 'QtWidgets.QGraphicsView', cache_key: int):
        super().__init__()
        self.view = view
        self.view.installEventFilter(self)
        self.needle = cache_key
        _DELAYED_CURSOR_RESETTER.append(self)

    def eventFilter(self, _obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.CursorChange:
            if self.view.cursor().pixmap().cacheKey() == self.needle:
                self.view.unsetCursor()
                self.stop()
        return False

    def stop(self) -> None:
        _DELAYED_CURSOR_RESETTER.pop(0)
        self.view.removeEventFilter(self)
        del self.view
        del self.needle

    @staticmethod
    def clear() -> None:
        while _DELAYED_CURSOR_RESETTER:
            _DELAYED_CURSOR_RESETTER[0].stop()
