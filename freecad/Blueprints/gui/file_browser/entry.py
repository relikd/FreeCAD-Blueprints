from pathlib import Path
from dataclasses import dataclass
from functools import cached_property

from ..qt import QtCore, QtWidgets, Icon


@dataclass
class Node:
    path: Path
    is_dir: bool
    expanded: bool = True  # by default: expanded

    @cached_property
    def widget(self) -> 'QtWidgets.QTreeWidgetItem':
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
