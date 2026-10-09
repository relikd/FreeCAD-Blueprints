'''
Code related to Qt simplifications and shared UI componentes.
'''
import sys
from pathlib import Path

from ..helper.utils import RES_ROOT, open_in_file_manager
from ..helper.settings import Settings

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:  # switch between "PySide6" (dev) and "PySide" (dist)
    from PySide6 import QtCore, QtGui, QtWidgets
    PathResolvable = Callable[[], Path | str | None] | Path | str | None
else:
    from PySide import QtCore, QtGui, QtWidgets


class Icon:
    # @staticmethod
    # def folder() -> QtGui.QIcon:
    #     ''' Shown in file browser. Regular folder / directory icon. '''
    #     return QtWidgets.QApplication.style().standardIcon(
    #         QtWidgets.QStyle.StandardPixmap.SP_DirIcon)

    # @staticmethod
    # def freecad_file() -> QtGui.QPixmap:
    #     ''' Shown in file browser. FreeCAD app icon for `.FCStd` files. '''
    #     return QtGui.QPixmap(RES_ROOT / 'icons' / 'freecad-document.svg')

    @staticmethod
    def blueprint_toolbar() -> QtGui.QPixmap:
        ''' Shown in Sketcher tool extension box. '''
        return QtGui.QPixmap(RES_ROOT / 'icons' / 'toolbar.svg')

    @staticmethod
    def blueprint_cursor() -> QtGui.QCursor:
        ''' Mouse cursor shown while inserting blueprint. '''
        svg = QtGui.QPixmap(RES_ROOT / 'icons' / 'cursor.svg')
        svg.setDevicePixelRatio(2)
        return QtGui.QCursor(svg, 8, 8)


class OpenFileLocationAction(QtGui.QAction):
    '''`path_fn` takes either static path or function returning path.'''

    def __init__(self, path_fn: 'PathResolvable') -> None:
        if sys.platform == 'darwin':
            super().__init__('Reveal in Finder')
            self.setStatusTip('Reveals the current file location in Finder')
        else:
            super().__init__('Open File Location')
            self.setStatusTip('Opens the current file location')

        self.callback = path_fn
        self.triggered.connect(self._open_in_fm)

    def addTo(self, parent: 'QtWidgets.QWidget') -> None:
        ''' Add action and set parent. '''
        # Sadly, `addAction` alone does not set parent.
        # And without a parent, the action does not trigger.
        parent.addAction(self)
        self.setParent(parent)

    def _open_in_fm(self) -> None:
        ''' Resolve path and open filemanager. '''
        rv = self.callback
        if callable(rv):
            rv = rv()
        if rv:
            if isinstance(rv, str):
                rv = Path(rv)
            open_in_file_manager(rv)


class QuickGui:
    @staticmethod
    def buttons(
        parent: QtWidgets.QDialog,
        *,
        abort: bool = False,
        cancel: bool = False,
    ) -> tuple[QtWidgets.QDialogButtonBox, QtWidgets.QPushButton]:
        '''
        Creates a default buttons box. With at least an "Ok" button.
        Returns: `(box, ok-button)`.
        '''
        flags = QtWidgets.QDialogButtonBox.StandardButton.Ok
        if abort:
            flags |= QtWidgets.QDialogButtonBox.StandardButton.Abort
        if cancel:
            flags |= QtWidgets.QDialogButtonBox.StandardButton.Cancel

        rv = QtWidgets.QDialogButtonBox(flags)
        rv.accepted.connect(parent.accept)
        rv.rejected.connect(parent.reject)
        return rv, rv.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)


class SyncedCheckbox(QtWidgets.QCheckBox):
    ''' Checkbox state is loaded from & synced back to user settings. '''
    on_change = QtCore.Signal(bool)

    def __init__(self, label: str, *, pref: str) -> None:
        super().__init__(label)
        self.setChecked(Settings.getBool(pref))

        def fn(newState: QtCore.Qt.CheckState) -> None:
            flag = newState == QtCore.Qt.CheckState.Checked
            Settings.setBool(pref, flag)
            self.on_change.emit(flag)

        self.checkStateChanged.connect(fn)


class SearchBar(QtWidgets.QLineEdit):
    ''' Create a search bar with hotkey `Ctrl+F` and up/down key-bindings. '''
    on_up_down = QtCore.Signal(bool)

    NO_MODIFIERS = ~(
        QtCore.Qt.KeyboardModifier.ShiftModifier
        | QtCore.Qt.KeyboardModifier.ControlModifier
        | QtCore.Qt.KeyboardModifier.AltModifier
        | QtCore.Qt.KeyboardModifier.MetaModifier
    )

    def __init__(self, parent: 'QtWidgets.QDialog', placeholder: str) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)

        def set_focus() -> None:
            self.setFocus()
            self.selectAll()

        shortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+F'), parent)
        shortcut.activated.connect(set_focus)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.modifiers() & self.NO_MODIFIERS:
            key = event.key()
            if key in (QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down):
                self.on_up_down.emit(key == QtCore.Qt.Key.Key_Up)
                event.accept()
                return
        super().keyPressEvent(event)


class ElidedButton(QtWidgets.QPushButton):
    ''' Button that automatically resizes to trim excessive text. '''
    def __init__(self, text: str, parent: 'QtWidgets.QWidget|None' = None) \
            -> None:
        super().__init__(text, parent)
        self._full_text: str = text
        self._update_elided_text()

    def minimumSizeHint(self) -> QtCore.QSize:
        hint = super().minimumSizeHint()
        return QtCore.QSize(0, hint.height())

    def resizeEvent(self, event: 'QtGui.QResizeEvent') -> None:
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self) -> None:
        # if necessary, calculate margin from current style
        width = max(0, self.contentsRect().width() - 30)
        abbrev = self.fontMetrics().elidedText(
            self._full_text, QtCore.Qt.TextElideMode.ElideRight, width)
        if self.text() != abbrev:
            self.setText(abbrev)
