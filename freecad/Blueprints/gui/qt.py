'''
Code related to Qt simplifications and shared UI componentes.
'''
import sys
from pathlib import Path

from ..helper.utils import RES_ROOT, open_in_file_manager
from ..helper.settings import Settings

from typing import TYPE_CHECKING, Callable, Literal, overload

if TYPE_CHECKING:  # switch between "PySide6" (dev) and "PySide" (dist)
    from PySide6 import QtCore, QtGui, QtWidgets
    PathResolvable = Callable[[], Path | str | None] | Path | str | None
else:
    from PySide import QtCore, QtGui, QtWidgets


class Icon:
    @staticmethod
    def freecad(name: str) -> QtGui.QIcon:
        '''
        Icons already bundled with FreeCAD (`:/icons/<name>`).
        See: https://github.com/search?q=repo:FreeCAD/FreeCAD+path:*.qrc
        '''
        return QtGui.QIcon(':/icons/' + name)

    @staticmethod
    def res(name: str) -> QtGui.QPixmap:
        ''' Load addon provided icon and set device pixel ration to 2. '''
        rv = QtGui.QPixmap(RES_ROOT / 'icons' / name)
        rv.setDevicePixelRatio(2)
        return rv

    @staticmethod
    def blueprint_cursor() -> QtGui.QCursor:
        ''' Mouse cursor shown while inserting blueprint. '''
        return QtGui.QCursor(Icon.res('cursor.svg'), 8, 8)


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


# see https://github.com/FreeCAD/FreeCAD/blob/4a1904f8db57d4a31e44cdb1dd984d4c98447c10/src/Tools/plugins/widget/customwidgets.cpp#L136-L189
class DirChooser(QtWidgets.QWidget):
    ''' `QLineEdit` with button to choose a filesystem directory. '''
    changed = QtCore.Signal()

    def __init__(self, initial: str = '', *, btnReveal: bool = False) -> None:
        super().__init__()

        txt = QtWidgets.QLineEdit(initial)
        self.txt = txt

        # original uses `QPushButton`, but I haven't found a way to min-size it
        btn = QtWidgets.QToolButton()
        btn.setText('...')
        btn.setFixedWidth(2 * btn.fontMetrics().horizontalAdvance(' ... '))
        btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Preferred)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)  # QToolButton: 2, QPushButton: 6
        layout.addWidget(txt)
        layout.addWidget(btn)

        self.setFocusProxy(txt)

        txt.textEdited.connect(self.install_path_completer)
        txt.editingFinished.connect(self.changed)
        btn.clicked.connect(self._selectDirectory)

        if btnReveal:
            btn_open = QtWidgets.QToolButton()
            btn_open.setIcon(QtGui.QIcon(':/icons/document-open.svg'))
            btn_open.setToolTip('Open in filemanager.')
            layout.addWidget(btn_open)
            btn_open.clicked.connect(self.on_open_in_fm)

    @property
    def value(self) -> str:
        return self.txt.text()

    def setValue(self, value: str) -> None:
        self.txt.setText(value)

    def on_open_in_fm(self) -> None:
        open_in_file_manager(Path(self.value))

    def _selectDirectory(self) -> None:
        ans = QtWidgets.QFileDialog.getExistingDirectory(self, dir=self.value)
        if ans:
            self.txt.setText(ans)
            self.changed.emit()

    def install_path_completer(self, _text: str) -> None:
        ''' Install postponed until first typing. '''
        self.txt.textEdited.disconnect(self.install_path_completer)  # once

        model = QtWidgets.QFileSystemModel(self.txt)
        model.setRootPath(self.txt.text())
        completer = QtWidgets.QCompleter(model, self.txt)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.txt.setCompleter(completer)


@overload
def FCWidget(name: Literal['Gui::ExpLineEdit']) -> QtWidgets.QLineEdit: ...
@overload
def FCWidget(name: Literal['Gui::IntSpinBox']) -> QtWidgets.QSpinBox: ...
@overload
def FCWidget(name: Literal['Gui::DoubleSpinBox']) -> QtWidgets.QDoubleSpinBox: ...  # noqa: E501
@overload
def FCWidget(name: str) -> QtWidgets.QWidget: ...
def FCWidget(name: str) -> 'QtWidgets.QWidget':
    ''' Load FreeCAD internal widget. '''
    import FreeCADGui  # noqa: PLC0415
    return FreeCADGui.UiLoader().createWidget(name)  # type: ignore[return-value]
