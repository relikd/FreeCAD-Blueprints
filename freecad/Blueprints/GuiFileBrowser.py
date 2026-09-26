'''
GUI code for sketch selection (select document in file browser).
'''
from pathlib import Path
from dataclasses import dataclass
from functools import cached_property

import FreeCADGui

from .helper.qt import QtCore, QtWidgets, MenuAction, Icon, QuickGui
from .helper.settings import Settings
from .helper.utils import get_user_collection, open_in_file_manager


@dataclass
class Node:
    path: Path
    is_dir: bool
    expanded: bool = True  # by default: expanded

    @staticmethod
    def of_widget(widget: QtWidgets.QTreeWidgetItem) -> 'Node':
        ''' Helper calls: `widget.data(0, QtCore.Qt.ItemDataRole.UserRole)` '''
        return widget.data(0, QtCore.Qt.ItemDataRole.UserRole)

    @cached_property
    def widget(self) -> QtWidgets.QTreeWidgetItem:
        ''' Widget used by tree. Data contains self-reference on Node. '''
        rv = QtWidgets.QTreeWidgetItem([self.path.name.removesuffix('.FCStd')])
        rv.setData(0, QtCore.Qt.ItemDataRole.UserRole, self)
        if self.is_dir:
            rv.setIcon(0, Icon.folder())
        else:
            rv.setIcon(0, Icon.freecad_file())
        # rv.setExpanded(self.expanded)  # not applied unless rendered first
        return rv

    @cached_property
    def children(self) -> list['Node']:
        dirs = []
        files = []
        for child in self.path.iterdir():
            if child.name.startswith('.'):
                continue  # dont descend into ".git" dir (and hidden files)
            if child.is_dir():
                dirs.append(Node(child, is_dir=True))
            elif child.suffix == '.FCStd':
                files.append(Node(child, is_dir=False))
        return sorted(dirs, key=lambda x: x.plain_name) \
            + sorted(files, key=lambda x: x.plain_name)

    @cached_property
    def plain_name(self) -> str:
        ''' Used for search and sorting. '''
        return self.path.with_suffix('').name.lower()


def _build_tree(root_dir: Path) -> Node:
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

    def __init__(self, root_dir: Path) -> None:
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
        node = Node.of_widget(sel)
        return not node.is_dir and node.path.exists()

    def on_selection_changed(
        self, current: 'QtWidgets.QTreeWidgetItem|None', _previous: None,
    ) -> None:
        ''' Auto-enable Ok button on valid selection. '''
        self.has_valid_selection = self._selection_valid(current)
        self.validated.emit(self.has_valid_selection)

    def on_expand_toggle(self, item: QtWidgets.QTreeWidgetItem) -> None:
        ''' Update Node on expand change. '''
        Node.of_widget(item).expanded = item.isExpanded()

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
            node = Node.of_widget(items[0])
            if not node.path.exists():
                return None  # if someone modified files while GUI was open
            if not node.is_dir or allowDir:
                return node
        return None


class FileBrowser(QtWidgets.QDialog):
    def __init__(self, root_dir: Path):
        super().__init__(FreeCADGui.getMainWindow())

        self.setWindowTitle('Choose Blueprint')
        self.resize(*Settings.getWinSize('FileBrowser', (400, 550)))

        # Search bar
        search_bar = QuickGui.search_bar(self, self.on_search)

        # Tree
        tree = TreeWidget(root_dir)
        tree.itemDoubleClicked.connect(self.accept)
        self.tree = tree

        # Right-click context menu
        tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        MenuAction.open_file_location(tree, self.on_open_fm)

        # Buttons
        buttons, self.accept_button = QuickGui.buttons(self, cancel=True)
        # auto-enable accept button on selection change
        tree.validated.connect(self.accept_button.setEnabled)

        # apply initial expanded state + hide empty dirs
        # triggers `on_selection_changed`, thus `self.accept_button` must exist
        self.tree.apply_filter('')

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(search_bar)
        layout.addWidget(tree)
        layout.addWidget(buttons)

        self.finished.connect(self.save_settings)

    def save_settings(self, _: int) -> None:
        ''' Persist window size in settings. '''
        Settings.setWinSize('FileBrowser', self)

    def on_open_fm(self) -> 'Node|None':
        if node := self.tree.selected_node(allowDir=True):
            open_in_file_manager(node.path)

    def on_search(self, text: str) -> None:
        ''' Callback method when user changes text in search bar. '''
        self.tree.apply_filter(text)

    def accept(self) -> None:
        ''' Ensure double-click has a valid target. '''
        if self.tree.has_valid_selection:
            super().accept()

    def get_selected(self) -> 'Node|None':
        ''' Return selection if Node is a file item. '''
        return self.tree.selected_node()


def open_blueprint_browser() -> 'Path|None':
    root = get_user_collection()
    # TODO: if possible, integrate as Task Panel inside Sketcher
    dialog = FileBrowser(root)
    if dialog.exec_() == QtWidgets.QDialog.DialogCode.Accepted:
        if node := dialog.get_selected():
            return node.path
    return None
