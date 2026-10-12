from dataclasses import dataclass
from pathlib import Path

from ..qt import QtWidgets, Icon, ElidedButton, OpenFileLocationAction
from .base import SketcherTool

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...blueprint_inserter import BlueprintInserter


@dataclass
class State:
    rotation: bool


class BlueprintSketcherTool(SketcherTool):
    TITLE = 'Blueprint Parameters'
    ICON = Icon.with_name('toolbar.svg')

    def __init__(self, inserter: 'BlueprintInserter') -> None:
        super().__init__()
        self.inserter = inserter
        path = Path(inserter.blueprint.Document.FileName)

        # blueprint source file info
        file_combo = ElidedButton(f'{inserter.blueprint.Label} ({path.name})')
        file_combo.setToolTip(str(path))
        file_combo_menu = QtWidgets.QMenu(file_combo)
        OpenFileLocationAction(path).addTo(file_combo_menu)
        file_combo_menu.addAction('Edit in FreeCAD', self.on_edit_sketch)
        file_combo.setMenu(file_combo_menu)

        fileinfo = QtWidgets.QHBoxLayout()
        fileinfo.addWidget(QtWidgets.QLabel('Source:'))
        fileinfo.addWidget(file_combo, 1)  # use full width

        # insert options
        rotation = QtWidgets.QCheckBox('Allow rotation')
        rotation.setToolTip('Remove Axes Alignment')
        rotation.setIcon(Icon.with_name('tool-allow-rotate.svg'))
        self.rotation = rotation

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(rotation)
        layout.addLayout(fileinfo)

    def get_state(self) -> State:
        return State(rotation=self.rotation.isChecked())

    def on_edit_sketch(self) -> None:
        self.inserter.close(reopenInEditMode=True)
