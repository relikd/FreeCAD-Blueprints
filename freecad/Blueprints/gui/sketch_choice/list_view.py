from ..qt import QtCore, QtWidgets
from .entry_view import EntryView

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry import DataItem
    QIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class ListView(QtWidgets.QListView):
    validated = QtCore.Signal(int)

    def __init__(self, items: list['DataItem']) -> None:
        super().__init__()

        proxy = ListFilter(ListModel(items))
        proxy.filtered.connect(self._on_filtered)
        self.setModel(proxy)
        self.setItemDelegate(EntryView(self))

        self.setWordWrap(True)
        self.setUniformItemSizes(False)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.setSpacing(2)
        self.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.selectionModel().currentChanged.connect(self.on_selection_changed)
        self._on_filtered()

    @property
    def filter(self) -> 'ListFilter':
        return self.model()  # type: ignore[return-value]

    def _on_filtered(self) -> None:
        if (first := self.filter.index(0, 0)) and first.isValid():
            self.setCurrentIndex(first)
            self.selectionModel().select(
                first,
                QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect,
            )
            return
        self.clearSelection()

    def on_selection_changed(self, current: 'QIndex', _: None) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        self.validated.emit(current.isValid())

    def get_selected(self) -> 'DataItem|None':
        ''' Return data entry of currently selected row. '''
        return self.currentIndex().data(QtCore.Qt.ItemDataRole.UserRole)


#################################################
# Model
#################################################

class ListModel(QtCore.QAbstractListModel):
    def __init__(self, data: list['DataItem']) -> None:
        super().__init__()
        self.rows = data

    def rowCount(self, parent: 'QIndex|None' = None) -> int:
        return 0 if parent and parent.isValid() else len(self.rows)

    def data(
        self, index: 'QIndex', role: int = QtCore.Qt.ItemDataRole.UserRole,
    ) -> 'DataItem|str|None':
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self.rows[index.row()]
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return self.rows[index.row()].tooltip
        return None


#################################################
# Filter
#################################################

class ListFilter(QtCore.QSortFilterProxyModel):
    filtered = QtCore.Signal()

    def __init__(self, source_model: QtCore.QAbstractListModel):
        super().__init__()
        self.query = ''
        self.incl_desc = False

        self.setSourceModel(source_model)
        # self.setFilterCaseSensitivity(
        #     QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def setOptions(self, *, desc: bool) -> None:
        self.incl_desc = desc
        if self.query:
            self.invalidateFilter()
            self.filtered.emit()

    def setQuery(self, query: str) -> None:
        self.query = query.casefold()
        self.setFilterFixedString(query)
        self.filtered.emit()

    def filterAcceptsRow(self, source_row: int, source_parent: 'QIndex') \
            -> bool:
        index = self.sourceModel().index(source_row, 0, source_parent)
        item: DataItem = self.sourceModel().data(index)
        return self.query in item.title.casefold() or (
            self.incl_desc and self.query in item.desc.casefold())
