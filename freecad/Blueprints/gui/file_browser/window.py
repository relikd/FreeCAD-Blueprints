from ...helper.settings import Settings
from ...helper.utils import open_in_file_manager
from ..qt import QtCore, QtWidgets, MenuAction, QuickGui
from .tree_view import TreeWidget

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from .entry import Node


class FileBrowser(QtWidgets.QDialog):
    def __init__(self, root_dir: 'Path'):
        super().__init__()

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
