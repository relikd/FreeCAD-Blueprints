from dataclasses import dataclass
from pathlib import Path

from ..qt import QtWidgets, Icon, ElidedButton, OpenFileLocationAction
from .base import SketcherTool
from .ext_expr import collect_fields, expr_cleanup, install_bindings, make_form

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...blueprint_duplicator import ExternalExpressionsRepl
    from ...blueprint_inserter import BlueprintInserter


@dataclass
class State:
    rotation: bool
    equal_named: bool
    hide_unnamed: bool
    repl_expr: 'ExternalExpressionsRepl'


class BlueprintSketcherTool(SketcherTool):
    TITLE = 'Blueprint Parameters'
    ICON = Icon.with_name('toolbar.svg')

    def __init__(self, inserter: 'BlueprintInserter') -> None:
        super().__init__()
        self.inserter = inserter
        sketch = inserter.blueprint
        path = Path(sketch.Document.FileName)

        # blueprint source file info
        if sketch.Name != sketch.Label:
            shortname = f'{sketch.Label} ({path.name})'
        else:
            shortname = path.name
        file_combo = ElidedButton(shortname)
        file_combo.setToolTip(str(path))
        file_combo_menu = QtWidgets.QMenu(file_combo)
        OpenFileLocationAction(path).addTo(file_combo_menu)
        file_combo_menu.addAction('Edit in FreeCAD', self.on_edit_sketch)
        file_combo.setMenu(file_combo_menu)

        fileinfo = QtWidgets.QHBoxLayout()
        fileinfo.addWidget(QtWidgets.QLabel(f'Source ({sketch.DoF} DoF):'))
        fileinfo.addWidget(file_combo, 1)  # use full width

        # insert options
        rotation = QtWidgets.QCheckBox('Allow rotation (M)')
        rotation.setToolTip('Remove Axes Alignment')
        rotation.setIcon(Icon.with_name('tool-allow-rotate.svg'))
        self.rotation = rotation

        equal_named = QtWidgets.QCheckBox('Equal named constraints (J)')
        equal_named.setToolTip(
            'Create equal-constraints (named constraints only)')
        equal_named.setIcon(Icon.with_name('tool-equal-named.svg'))
        self.equal_named = equal_named

        hide_unnamed = QtWidgets.QCheckBox('Hide unnamed constraints')
        hide_unnamed.setToolTip('Only show named constraints in Sketcher')
        self.hide_unnamed = hide_unnamed

        self.form = make_form(inserter.blueprint)

        layout = QtWidgets.QVBoxLayout(self)
        if self.form.rowCount() > 0:
            layout.addLayout(self.form)
            layout.addSpacerItem(QtWidgets.QSpacerItem(0, 12))
        layout.addWidget(rotation)
        layout.addWidget(equal_named)
        layout.addWidget(hide_unnamed)
        layout.addLayout(fileinfo)

        # interconnections
        install_bindings(self.form, inserter.current)  # adds (fx) button

    def stop(self) -> None:
        expr_cleanup(self.form, self.inserter.current)
        super().stop()

    def on_hotkey(self, letter: str) -> bool:
        if letter == 'M':
            self.rotation.toggle()
        elif letter == 'J':
            self.equal_named.toggle()
        else:
            return False
        return True

    def get_state(self) -> State:
        return State(
            rotation=self.rotation.isChecked(),
            equal_named=self.equal_named.isChecked(),
            hide_unnamed=self.hide_unnamed.isChecked(),
            repl_expr=collect_fields(self.form),
        )

    def on_edit_sketch(self) -> None:
        self.inserter.close(reopenInEditMode=True)
