'''
GUI code for sketch selection (if multiple Sketches per document).
'''
from dataclasses import dataclass
from functools import cached_property

from .helper.properties import Props
from .helper.qt import QtCore, QtWidgets, QuickGui
from .helper.settings import Settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .helper.qt import QtGui
    from Sketcher import SketchObject as Sketch


@dataclass
class DataItem:
    index: int
    title: str
    desc: str
    tooltip: str

    def make_widget(self) -> QtWidgets.QListWidgetItem:
        ''' Widget with self-reference on DataItem. '''
        rv = QtWidgets.QListWidgetItem()
        rv.setData(QtCore.Qt.ItemDataRole.UserRole, self)
        return rv

    @staticmethod
    def of_widget(widget: QtWidgets.QListWidgetItem) -> 'DataItem':
        ''' Helper calls: `widget.data(QtCore.Qt.ItemDataRole.UserRole)` '''
        return widget.data(QtCore.Qt.ItemDataRole.UserRole)

    @cached_property
    def searchable_title(self) -> str:
        ''' Used for search. '''
        return self.title.casefold()

    @cached_property
    def searchable_title_and_desc(self) -> str:
        ''' Used for search. '''
        return self.title.casefold() + '\n' + self.desc.casefold()


class RowWidget(QtWidgets.QWidget):
    def __init__(self, title: str, desc: str) -> None:
        super().__init__()

        l1 = QtWidgets.QLabel(title)
        l1.setStyleSheet('font-weight: bold;')

        l2 = QtWidgets.QLabel(desc)
        l2.setStyleSheet('font-style: italic;')
        l2.setWordWrap(True)
        l2.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.desc = l2

        layout = QtWidgets.QVBoxLayout(self)
        # layout.setContentsMargins(8, 6, 8, 6)
        # layout.setSpacing(2)
        layout.addWidget(l1)
        layout.addWidget(l2)
        self._layout = layout

    def update_width(self, width: int) -> None:
        self.setFixedWidth(width)
        # Clear the previous height before recalculating.
        self.setMinimumHeight(0)
        self.desc.setMinimumHeight(0)
        self.desc.setFixedHeight(self.desc.heightForWidth(max(0, width - 16)))
        self._layout.activate()
        self.setFixedHeight(self._layout.sizeHint().height())


class ListWidget(QtWidgets.QListWidget):
    validated = QtCore.Signal(int)
    returnKeyAccepted = QtCore.Signal()

    def __init__(self, choices: list[DataItem]) -> None:
        super().__init__()
        self.has_valid_selection = False

        self.setUniformItemSizes(False)
        self.setSpacing(1)
        # self.setWordWrap(True)
        # self.setVerticalScrollMode(
        #     QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel,
        # )
        self.currentItemChanged.connect(self.on_selection_changed)

        # populate data
        for choice in choices:
            item = choice.make_widget()
            if choice.tooltip:
                item.setToolTip(choice.tooltip)
            self.addItem(item)
            self.setItemWidget(item, RowWidget(choice.title, choice.desc))

        if self.count():
            self.setCurrentRow(0)

    def on_selection_changed(
        self, current: 'QtWidgets.QListWidgetItem|None', _previous: None,
    ) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        self.has_valid_selection = not (not current or current.isHidden())
        self.validated.emit(self.has_valid_selection)

    def keyPressEvent(self, event: 'QtGui.QKeyEvent') -> None:
        ''' Treat return key as item selection confirm. '''
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            if self.has_valid_selection:
                self.returnKeyAccepted.emit()
                event.accept()
                return
        super().keyPressEvent(event)

    def resizeEvent(self, event: 'QtGui.QResizeEvent') -> None:
        ''' Update row height on window size change. '''
        super().resizeEvent(event)

        width = self.viewport().width()

        for row in range(self.count()):
            list_item = self.item(row)
            widget = self.itemWidget(list_item)

            if isinstance(widget, RowWidget):
                widget.update_width(width)
                list_item.setSizeHint(widget.sizeHint())

        self.doItemsLayout()

    def apply_filter(self, text: str, *, incl_desc: bool) -> None:
        ''' Filter entries on search query change. '''
        query = text.casefold().strip()

        is_first = True
        for row in range(self.count()):
            list_item = self.item(row)
            item = DataItem.of_widget(list_item)

            if incl_desc:
                matches = query in item.searchable_title_and_desc
            else:
                matches = query in item.searchable_title
            list_item.setHidden(not matches)
            if is_first and matches:
                is_first = False
                self.setCurrentItem(list_item)

        if is_first:
            self.setCurrentItem(None)  # type: ignore[call-overload]


class ItemSelectionDialog(QtWidgets.QDialog):
    def __init__(self, choices: list[DataItem]) -> None:
        super().__init__()

        self.setWindowTitle('Select item')
        self.resize(*Settings.getWinSize('SketchChoice', (650, 450)))

        # Search
        search = QtWidgets.QHBoxLayout()
        self.chk = QuickGui.checkbox('incl. desc', 'searchSketchDescription')
        search.addWidget(QuickGui.search_bar(self, self.on_search))
        search.addWidget(self.chk)

        # List
        list_widget = ListWidget(choices)
        list_widget.itemDoubleClicked.connect(self.accept)
        list_widget.returnKeyAccepted.connect(self.accept)
        self.list_widget = list_widget

        # Buttons
        buttons, self.accept_button = QuickGui.buttons(self, abort=True)
        # auto-enable accept button on selection change
        list_widget.validated.connect(self.accept_button.setEnabled)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(search)
        layout.addWidget(list_widget)
        layout.addWidget(buttons)

        self.finished.connect(self.save_settings)

    def save_settings(self, _: int) -> None:
        ''' Persist window size in settings. '''
        Settings.setWinSize('SketchChoice', self)

    def on_search(self, text: str) -> None:
        ''' Filter entries on search query change. '''
        self.list_widget.apply_filter(text, incl_desc=self.chk.isChecked())

    def get_selected(self) -> 'DataItem|None':
        ''' Return selection (if any). '''
        if (row := self.list_widget.currentItem()) and not row.isHidden():
            return DataItem.of_widget(row)
        return None


def open_sketch_chooser(sketches: 'list[Sketch]') -> 'Sketch|None':
    if not sketches:
        return None

    def fn(args: tuple[int, 'Sketch']) -> DataItem:
        i, x = args
        return DataItem(
            i, x.Label, Props.text(x, 'desc'), Props.tooltip(x, 'desc'))

    dialog = ItemSelectionDialog(list(map(fn, enumerate(sketches))))

    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        if selected := dialog.get_selected():
            dialog.deleteLater()
            return sketches[selected.index]
    dialog.deleteLater()
    return None
