from ..qt import QtCore, QtWidgets
from .entry import Node

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _build_tree(root_dir: 'Path') -> Node:
    root = Node(path=root_dir.resolve(), is_dir=True)
    queue = [root]
    i = 0
    while i < len(queue):
        parent: Node = queue[i]
        i += 1
        for child in parent.children:
            parent.widget.addChild(child.widget)
            if child.is_dir:
                queue.append(child)
    return root


class TreeWidget(QtWidgets.QTreeWidget):
    validated = QtCore.Signal(int)

    def __init__(self, root_dir: 'Path') -> None:
        super().__init__()
        self.has_valid_selection = False

        self.root_node = _build_tree(root_dir)

        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.addTopLevelItem(self.root_node.widget)
        self.setRootIndex(self.indexFromItem(self.root_node.widget))
        self.currentItemChanged.connect(self.on_selection_changed)
        self.itemExpanded.connect(self.on_expand_toggle)
        self.itemCollapsed.connect(self.on_expand_toggle)

    def _selection_valid(self, sel: 'QtWidgets.QTreeWidgetItem|None') -> bool:
        if not sel or sel.isHidden():
            return False
        node = node_of(sel)
        return not node.is_dir and node.path.exists()

    def on_selection_changed(
        self, current: 'QtWidgets.QTreeWidgetItem|None', _previous: None,
    ) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        self.has_valid_selection = self._selection_valid(current)
        self.validated.emit(self.has_valid_selection)

    def on_expand_toggle(self, item: QtWidgets.QTreeWidgetItem) -> None:
        ''' Update Node on expand change. '''
        node_of(item).expanded = item.isExpanded()

    def apply_filter(self, text: str) -> None:
        ''' Filter entries on search query change. '''
        search_active = bool(text)
        search_term = text.lower()
        queue = [self.root_node]
        i = 0
        is_first = True
        while i < len(queue):
            for child in queue[i].children:
                if child.is_dir:
                    queue.append(child)
                else:
                    hidden = search_term not in child.plain_name
                    child.widget.setHidden(hidden)
                    # select first non-dir item to allow confirm with return
                    if is_first and not hidden:
                        is_first = False
                        self.setCurrentItem(child.widget)
            i += 1

        if is_first:
            self.setCurrentItem(None)  # type: ignore[call-overload]

        # disable while searching to not change user-expanded items
        self.itemExpanded.disconnect()

        # for all dirs, expand or collapse
        for item in reversed(queue):
            hidden = all(x.widget.isHidden() for x in item.children)
            item.widget.setHidden(hidden)
            item.widget.setExpanded(True if search_active else item.expanded)

        # re-enable after search
        self.itemExpanded.connect(self.on_expand_toggle)

    def selected_node(self, *, allowDir: bool = False) -> 'Node|None':
        ''' Return current selection if Node is a file item. '''
        if items := self.selectedItems():
            node = node_of(items[0])
            if not node.path.exists():
                return None  # if someone modified files while GUI was open
            if not node.is_dir or allowDir:
                return node
        return None


#################################################
# Helper
#################################################

def node_of(widget: 'QtWidgets.QTreeWidgetItem') -> 'Node':
    ''' Helper calls: `widget.data(0, QtCore.Qt.ItemDataRole.UserRole)` '''
    return widget.data(0, QtCore.Qt.ItemDataRole.UserRole)
