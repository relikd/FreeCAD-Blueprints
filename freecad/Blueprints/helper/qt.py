'''
Code related to Qt simplifications and shared UI componentes.
'''
import sys
from typing import Callable

from PySide import QtCore, QtGui, QtWidgets

from .utils import RES_ROOT
from .settings import Settings

__all__ = ['QtCore', 'QtGui', 'QtWidgets']


class Icon:
    @staticmethod
    def folder() -> QtGui.QIcon:
        return QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DirIcon)

    @staticmethod
    def freecad_file() -> QtGui.QPixmap:
        # return _icon('freecad-document.svg')
        return QtGui.QPixmap(RES_ROOT / 'icons' / 'freecad-document.svg')


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
    def search_bar(
        parent: QtWidgets.QDialog,
        on_search: Callable[[str], None],
        *,
        placeholder: str = 'Search ...',
    ) -> QtWidgets.QLineEdit:
        ''' Create a search bar with hotkey `Ctrl+F`. '''
        rv = QtWidgets.QLineEdit()
        rv.setPlaceholderText(placeholder)
        rv.textChanged.connect(on_search)

        def set_focus() -> None:
            rv.setFocus()
            rv.selectAll()

        shortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+F'), parent)
        shortcut.activated.connect(set_focus)
        return rv

    @staticmethod
    def checkbox(label: str, pref: str) -> QtWidgets.QCheckBox:
        rv = QtWidgets.QCheckBox(label)
        rv.setChecked(Settings.getBool(pref))

        def fn(newState: QtCore.Qt.CheckState) -> None:
            Settings.setBool(pref, newState == QtCore.Qt.CheckState.Checked)

        rv.checkStateChanged.connect(fn)
        return rv
