from ..qt import QtCore, QtWidgets, Icon
from .entry import Node

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Iterator
    QIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class TreeView(QtWidgets.QTreeView):
    validated = QtCore.Signal(int)

    def __init__(self, root_dir: 'Path'):
        super().__init__()
        self.setModel(TreeFilter(TreeModel(Node(root_dir, None), self), self))
        self.setHeaderHidden(True)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.expanded.connect(self.on_expand_toggle)
        self.collapsed.connect(self.on_expand_toggle)

    @property
    def filter(self) -> 'TreeFilter':
        return self.model()  # type: ignore[return-value]

    def on_selection_changed(self) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        self.validated.emit(bool(self.get_selected()))

    def on_expand_toggle(self, index: 'QIndex') -> None:
        ''' Update Node on expand change. '''
        self.filter.get_node(index).expanded = self.isExpanded(index)

    def apply_filter(self, text: str) -> None:
        ''' Filter entries on search query change. '''
        # save current selection, then apply filter
        prev_sel = self.selectedIndexes()
        sel = self.filter.mapToSource(prev_sel[0]) if prev_sel else None
        self.filter.setQuery(text)
        if sel:
            sel = self.filter.mapFromSource(sel)
            if not sel.isValid():
                sel = None

        # disconnect to not modify user-expanded state
        self.expanded.disconnect()
        if text:
            self.expandAll()
        else:
            for index in self.filter.iter_expandable():
                self.setExpanded(index, self.filter.get_node(index).expanded)
        # re-enable after search
        self.expanded.connect(self.on_expand_toggle)

        # if current selection is still valid, don't change it
        self.selectionModel().setCurrentIndex(
            sel or self.filter.first_leaf(),
            QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )

    def get_selected(self, *, allowDir: bool = False) -> 'Path|None':
        ''' Return current selection if Node is a file item. '''
        if items := self.selectedIndexes():
            path = self.filter.get_node(items[0]).path
            # file may not exist if someone deleted while GUI was open
            if path.exists() and (not path.is_dir() or allowDir):
                return path
        return None


#################################################
# Model
#################################################

class TreeModel(QtCore.QAbstractItemModel):
    ICON_DIR = Icon.folder()
    ICON_FILE = Icon.freecad('freecad.svg')

    def __init__(self, root: Node, parent: 'TreeView'):
        super().__init__(parent)
        self.root = root

    def columnCount(self, _parent: 'QIndex') -> int:  # type: ignore[override]
        return 1

    def rowCount(self, parent: 'QIndex') -> int:  # type: ignore[override]
        if parent.isValid() and parent.column() != 0:
            return 0
        node = parent.internalPointer() if parent.isValid() else self.root
        return len(node.children)

    def index(self, row: int, column: int, parent: 'QIndex') \
            -> QtCore.QModelIndex:  # type: ignore[override]
        if column == 0 and row >= 0:
            node = parent.internalPointer() if parent.isValid() else self.root
            if row < len(node.children):
                return self.createIndex(row, 0, node.children[row])
        return QtCore.QModelIndex()

    def parent(self, index: 'QIndex') -> QtCore.QModelIndex:  # type: ignore[override]
        if index.isValid():
            node: Node = index.internalPointer()
            if (par := node.parent) and (parpar := par.parent):
                return self.createIndex(parpar.children.index(par), 0, par)
        return QtCore.QModelIndex()

    def data(
        self, index: 'QIndex', role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:  # noqa: ANN401
        if index.isValid():
            node: Node = index.internalPointer()
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return node.name
            if role == QtCore.Qt.ItemDataRole.DecorationRole:
                return self.ICON_DIR if node.path.is_dir() else self.ICON_FILE
        return None


#################################################
# Filter
#################################################

class TreeFilter(QtCore.QSortFilterProxyModel):
    def __init__(self, source_model: 'TreeModel', parent: 'TreeView'):
        super().__init__(parent)
        self.setSourceModel(source_model)
        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def setQuery(self, query: str) -> None:
        self.setFilterFixedString(query)

    def get_node(self, index: 'QIndex') -> Node:
        ''' Input is a filter index. '''
        return self.mapToSource(index).internalPointer()  # type: ignore[no-any-return]

    def first_leaf(self) -> QtCore.QModelIndex:
        ''' Returns first (nested) non-dir entry. '''
        index = QtCore.QModelIndex()
        while self.rowCount(index) > 0:
            index = self.index(0, 0, index)
        return index

    def iter_expandable(self) -> 'Iterator[QtCore.QModelIndex]':
        ''' Yields all "dir" nodes which are expandable / collapsible. '''
        queue = [QtCore.QModelIndex()]
        while queue:
            index = queue.pop()
            count = self.rowCount(index)
            if count > 0:
                if index.isValid():
                    yield index
                queue.extend(self.index(row, 0, index) for row in range(count))

    def filterAcceptsRow(self, row: int, parent: 'QIndex') -> bool:
        ''' Input is a source index. '''
        node: Node = self.sourceModel().index(row, 0, parent).internalPointer()
        if node.children:
            return False  # only search for file entries
        return super().filterAcceptsRow(row, parent)
