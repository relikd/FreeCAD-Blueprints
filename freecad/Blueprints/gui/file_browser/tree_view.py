from pathlib import Path
from ..qt import QtCore, QtWidgets

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    QIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class TreeView(QtWidgets.QTreeView):
    validated = QtCore.Signal(int)

    def __init__(self, root_dir: 'Path') -> None:
        super().__init__()

        source = QtWidgets.QFileSystemModel(self)
        source.setFilter(
            QtCore.QDir.Filter.AllDirs |
            QtCore.QDir.Filter.Files |
            QtCore.QDir.Filter.NoDotAndDotDot)

        root_node = source.setRootPath(str(root_dir))

        proxy = FileFilter(source, self)
        self.setModel(proxy)
        self.setRootIndex(proxy.mapFromSource(root_node))
        self.setCurrentIndex(self.rootIndex())
        self.setHeaderHidden(True)
        self.selectionModel().currentChanged.connect(self.on_selection_changed)

        # show only name column
        for column in range(1, source.columnCount()):
            self.hideColumn(column)

        # directories are loaded asynchronously, need to expand recursively
        source.directoryLoaded.connect(lambda x:
            None if Path(x).name.startswith('.') else self.expandAll())
        self.expandAll()

    @property
    def filter(self) -> 'FileFilter':
        return self.model()  # type: ignore[return-value]

    def apply_initial(self) -> None:
        ''' Call after validated is wired. '''
        self.on_selection_changed(self.currentIndex(), None)

    def on_selection_changed(self, current: 'QIndex', _: None) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        path = self.filter.path_for(current)
        self.validated.emit(path and path.exists() and not path.is_dir())

    def get_selected(self, *, allowDir: bool = False) -> 'Path|None':
        ''' Return current selection. By default: only if file selected. '''
        if path := self.filter.path_for(self.currentIndex()):
            # file may not exist if someone deleted while GUI was open
            if path.exists() and (not path.is_dir() or allowDir):
                return path
        return None


#################################################
# Filter
#################################################

class FileFilter(QtCore.QSortFilterProxyModel):
    EXT: Final = '.FCStd'.lower()

    def __init__(self, source: QtWidgets.QFileSystemModel, parent: TreeView) \
            -> None:
        super().__init__(parent)
        self._query = ''
        # self._root = source.rootPath()
        self.setSourceModel(source)
        self.setRecursiveFilteringEnabled(True)

    def set_query(self, query: str) -> None:
        self._query = query.casefold()
        self.invalidateFilter()

    @property
    def model(self) -> QtWidgets.QFileSystemModel:
        return self.sourceModel()  # type: ignore[return-value]

    def path_for(self, index: 'QIndex') -> 'Path|None':
        rv = self.model.filePath(self.mapToSource(index))
        return Path(rv) if rv else None

    def filterAcceptsRow(self, row: int, parent: 'QIndex') -> bool:
        source = self.model
        index = source.index(row, 0, parent)
        path = Path(source.filePath(index)).resolve()

        if path.name.startswith('.'):
            return False  # ignore hidden

        if source.isDir(index):
            # we could return False during search to hide empty dirs, but that
            # would invalidate the underlying index and unset expanded state.
            # IF we decide to go that way, return True for path == self._root,
            # or else the index invalidation sets root to "/"
            return True

        return path.suffix.lower() == self.EXT \
            and self._query in path.with_suffix('').name.casefold()
