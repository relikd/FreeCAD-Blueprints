from ..qt import QtCore, QtWidgets
from .entry import Node

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _build_tree(root_dir: 'Path') -> Node:
    root = Node(root_dir.resolve())
    queue = [root]
    i = 0
    while i < len(queue):
        parent = queue[i]
        i += 1
        for child in parent.children:
            parent.widget.addChild(child.widget)
            if child.path.is_dir():
                queue.append(child)
    return root


class TreeView(QtWidgets.QTreeWidget):
    validated = QtCore.Signal(int)

    def __init__(self, root_dir: 'Path') -> None:
        super().__init__()

        self.root_node = _build_tree(root_dir)

        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.addTopLevelItem(self.root_node.widget)
        self.setRootIndex(self.indexFromItem(self.root_node.widget))
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.itemExpanded.connect(self.on_expand_toggle)
        self.itemCollapsed.connect(self.on_expand_toggle)

    def on_selection_changed(self) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        self.validated.emit(bool(self.get_selected()))

    def on_expand_toggle(self, item: QtWidgets.QTreeWidgetItem) -> None:
        ''' Update Node on expand change. '''
        node_of(item).expanded = item.isExpanded()

    def apply_filter(self, text: str) -> None:
        ''' Filter entries on search query change. '''
        queue = [self.root_node]
        self._set_hidden(queue, text.casefold())
        self._update_dirs(queue, searching=bool(text))
        self._update_selection()

    def _set_hidden(self, queue: list[Node], search_term: str) -> None:
        ''' Hide children (files) if `search_term` doesn't match. '''
        i = 0
        while i < len(queue):
            for child in queue[i].children:
                if child.path.is_dir():
                    queue.append(child)
                else:
                    hidden = search_term not in child.plain_name
                    child.widget.setHidden(hidden)
            i += 1

    def _update_dirs(self, queue: list[Node], *, searching: bool) -> None:
        ''' Hide dirs if all children are hidden. Expand while searching. '''
        # disconnect while searching to not change user-expanded items
        self.itemExpanded.disconnect()

        # reversed so subfolders are hidden first
        for item in reversed(queue):
            hidden = all(x.widget.isHidden() for x in item.children)
            item.widget.setHidden(hidden)
            item.widget.setExpanded(True if searching else item.expanded)

        # re-enable after search
        self.itemExpanded.connect(self.on_expand_toggle)

    def _update_selection(self) -> None:
        ''' Select first non-dir entry (or keep current if still visible). '''
        node = self.root_node

        # at this point, dirs are hidden if all children are hidden
        if self.selectedItems() or node.widget.isHidden():
            self.on_selection_changed()  # en-/disable if no selection
            return  # current selection is still valid, don't change it

        while node.path.is_dir():
            # always finds a non-hidden child because root is visible
            node = next(x for x in node.children if not x.widget.isHidden())
        self.setCurrentItem(node.widget)

    def get_selected(self, *, allowDir: bool = False) -> 'Path|None':
        ''' Return current selection if Node is a file item. '''
        if items := self.selectedItems():
            path = node_of(items[0]).path
            # file may not exist if someone deleted while GUI was open
            if path.exists() and (not path.is_dir() or allowDir):
                return path
        return None


#################################################
# Helper
#################################################

def node_of(widget: 'QtWidgets.QTreeWidgetItem') -> 'Node':
    ''' Helper calls: `widget.data(0, QtCore.Qt.ItemDataRole.UserRole)` '''
    return widget.data(0, QtCore.Qt.ItemDataRole.UserRole)  # type: ignore[no-any-return]
