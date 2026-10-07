from ...helper.settings import Settings
from ...helper.utils import open_in_file_manager
from ..qt import QtCore, QtWidgets, MenuAction, QuickGui
from .tree_view import TreeView

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class FileBrowser(QtWidgets.QDialog):
    def __init__(self, root_dir: 'Path'):
        super().__init__()

        self.setWindowTitle('Choose Blueprint')
        self.resize(*Settings.getWinSize('FileBrowser', (400, 550)))

        # Tree
        tree = TreeView(root_dir)
        tree.doubleClicked.connect(self.accept)
        self.tree = tree

        # Search bar
        search_bar = QuickGui.search_bar(self, tree.filter.set_query)

        # Right-click context menu
        tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        MenuAction.open_file_location(tree, self.on_open_fm)

        # Buttons
        buttons, self.accept_button = QuickGui.buttons(self, cancel=True)
        # auto-enable accept button on selection change
        tree.validated.connect(self.accept_button.setEnabled)
        tree.apply_initial()

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(search_bar)
        layout.addWidget(tree)
        layout.addWidget(buttons)

        self.finished.connect(self.save_settings)

    def save_settings(self, _: int) -> None:
        ''' Persist window size in settings. '''
        Settings.setWinSize('FileBrowser', self)

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
