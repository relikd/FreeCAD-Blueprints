from pathlib import Path
from dataclasses import dataclass, field
from functools import cached_property


@dataclass
class Node:
    path: Path
    parent: 'Node|None' = field(repr=False)
    expanded: bool = True  # by default: expanded

    def __post_init__(self) -> None:
        if self.path.is_dir():
            self.name = self.path.name
        else:
            self.name = self.path.name[:-6]  # remove suffix (case insensitive)

    @cached_property
    def children(self) -> list['Node']:
        if not self.path.is_dir():
            return []
        dirs = []
        files = []
        for child in self.path.iterdir():
            if child.name.startswith('.'):
                continue  # dont descend into ".git" dir (and hidden files)
            if child.is_dir():
                node = Node(child, self)
                if node.children:  # recursive call + filter out empty dirs
                    dirs.append(node)
            elif child.suffix.lower() == '.fcstd':
                files.append(Node(child, self))
        return sorted(dirs, key=lambda x: x.name.casefold()) \
            + sorted(files, key=lambda x: x.name.casefold())
