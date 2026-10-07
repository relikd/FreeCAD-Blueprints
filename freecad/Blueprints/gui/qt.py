'''
Code related to Qt simplifications and shared UI componentes.
'''
import sys
from typing import Callable, TYPE_CHECKING

from ..helper.utils import RES_ROOT
from ..helper.settings import Settings

if TYPE_CHECKING:  # switch between "PySide6" (dev) and "PySide" (dist)
    from PySide6 import QtCore, QtGui, QtWidgets
else:
    from PySide import QtCore, QtGui, QtWidgets


class Icon:
    @staticmethod
    def folder() -> QtGui.QIcon:
        ''' Shown in file browser. Regular folder / directory icon. '''
        return QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DirIcon)

    @staticmethod
    def freecad_file() -> QtGui.QPixmap:
        ''' Shown in file browser. FreeCAD app icon for `.FCStd` files. '''
        return QtGui.QPixmap(RES_ROOT / 'icons' / 'freecad-document.svg')

    @staticmethod
    def blueprint_cursor() -> QtGui.QCursor:
        ''' Mouse cursor shown while inserting blueprint. '''
        svg = QtGui.QPixmap(RES_ROOT / 'icons' / 'cursor.svg')
        svg.setDevicePixelRatio(2)
        return QtGui.QCursor(svg, 8, 8)


class MenuAction:
    @staticmethod
    def open_file_location(parent: QtWidgets.QWidget, func: object) \
            -> QtGui.QAction:
        ''' Create action and attach it to `parent` via `addAction()`. '''
        if sys.platform == 'darwin':
            act = QtGui.QAction('Reveal in Finder', parent)
            act.setStatusTip('Reveals the current file location in Finder')
        else:
            act = QtGui.QAction('Open File Location', parent)
            act.setStatusTip('Opens the current file location')
        act.triggered.connect(func)
        parent.addAction(act)
        return act


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

    @staticmethod
    def search_bar(parent: QtWidgets.QDialog, placeholder: str = 'Search ...')\
            -> 'NavigatableLineEdit':
        ''' Create a search bar with hotkey `Ctrl+F`. '''
        rv = NavigatableLineEdit()
        rv.setPlaceholderText(placeholder)

        def set_focus() -> None:
            rv.setFocus()
            rv.selectAll()

        shortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+F'), parent)
        shortcut.activated.connect(set_focus)
        return rv


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


class NavigatableLineEdit(QtWidgets.QLineEdit):
    ''' Create key-bindings for up- down keys. '''
    on_up_down = QtCore.Signal(bool)

    NO_MODIFIERS = ~(
        QtCore.Qt.KeyboardModifier.ShiftModifier
        | QtCore.Qt.KeyboardModifier.ControlModifier
        | QtCore.Qt.KeyboardModifier.AltModifier
        | QtCore.Qt.KeyboardModifier.MetaModifier
    )

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.modifiers() & self.NO_MODIFIERS:
            key = event.key()
            if key in (QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down):
                self.on_up_down.emit(key == QtCore.Qt.Key.Key_Up)
                event.accept()
                return
        super().keyPressEvent(event)
