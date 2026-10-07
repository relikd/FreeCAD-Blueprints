from ...helper.settings import Settings
from ...helper.utils import open_in_file_manager
from ..qt import QtCore, QtWidgets, MenuAction, QuickGui, SearchBar
from .tree_view import TreeView

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class FileBrowser(QtWidgets.QDialog):
    def __init__(self, root_dir: 'Path'):
        super().__init__()

        self.setWindowTitle('Choose Blueprint')
        self.resize(*Settings.getWinSize('FileBrowser', (400, 550)))

        # Search bar
        search_bar = SearchBar(self, 'Search ...')

        # Tree
        tree = TreeView(root_dir)
        self.tree = tree

        # Right-click context menu
        tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        MenuAction.open_file_location(tree, self.on_open_fm)

        # Buttons
        buttons, self.accept_button = QuickGui.buttons(self, cancel=True)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(search_bar)
        layout.addWidget(tree)
        layout.addWidget(buttons)

        # interconnections
        search_bar.textChanged.connect(tree.filter.set_query)
        search_bar.on_up_down.connect(self.on_up_down)
        tree.doubleClicked.connect(self.accept)
        tree.validated.connect(self.accept_button.setEnabled)
        self.finished.connect(self.save_settings)

        tree.apply_initial()

    def save_settings(self, _: int) -> None:
        ''' Persist window size in settings. '''
        Settings.setWinSize('FileBrowser', self)

    def on_up_down(self, up: bool) -> None:  # noqa: FBT001
        ''' React to up-down arrow keys. '''
        idx = self.tree.currentIndex()
        idx = self.tree.indexAbove(idx) if up else self.tree.indexBelow(idx)
        if idx.isValid():
            self.tree.setCurrentIndex(idx)
            self.tree.scrollTo(idx)

    def on_open_fm(self) -> 'Path|None':
        ''' Open in file manager. '''
        if path := self.tree.get_selected(allowDir=True):
            open_in_file_manager(path)

    def accept(self) -> None:
        ''' Ensure double-click has a valid target. '''
        if self.tree.get_selected():
            super().accept()

    def get_selected(self) -> 'Path|None':
        ''' Return selection if Node is a file item. '''
        return self.tree.get_selected()
