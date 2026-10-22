from dataclasses import dataclass
from pathlib import Path

from ...logic.expressions import make_form_fields, ExprReplacer
from ..qt import QtWidgets, Icon, ElidedButton, OpenFileLocationAction
from .base import SketcherTool

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...blueprint_inserter import BlueprintInserter


@dataclass
class State:
    rotation: bool
    equal_named: bool
    hide_unnamed: bool
    repl_expr: ExprReplacer


class BlueprintSketcherTool(SketcherTool):
    TITLE = 'Blueprint Parameters'
    ICON = Icon.res('toolbar.svg')

    def __init__(self, inserter: 'BlueprintInserter') -> None:
        super().__init__()
        self.inserter = inserter
        src, dst = inserter.blueprint, inserter.current
        path = Path(src.Document.FileName)

        # blueprint source file info
        if src.Name != src.Label:
            shortname = f'{src.Label} ({path.name})'
        else:
            shortname = path.name
        file_combo = ElidedButton(shortname)
        file_combo.setToolTip(str(path))
        file_combo_menu = QtWidgets.QMenu(file_combo)
        OpenFileLocationAction(path).addTo(file_combo_menu)
        file_combo_menu.addAction('Edit in FreeCAD', self.on_edit_sketch)
        file_combo.setMenu(file_combo_menu)

        fileinfo = QtWidgets.QHBoxLayout()
        fileinfo.addWidget(QtWidgets.QLabel(f'Source ({src.DoF} DoF):'))
        fileinfo.addWidget(file_combo, 1)  # use full width

        # insert options
        rotation = QtWidgets.QCheckBox('Remove Axes Alignment (M)')
        rotation.setToolTip('Allow rotation of object after insert.')
        rotation.setIcon(
            Icon.freecad('tools/Sketcher_RemoveAxesAlignment.svg'))

        self.rotation = rotation

        equal_named = QtWidgets.QCheckBox('Equal named constraints (J)')
        equal_named.setToolTip(
            'Create equal-constraints (named constraints only)')
        # Icon.freecad('constraints/Constraint_EqualLength.svg'))
        equal_named.setIcon(Icon.res('tool-equal-named.svg'))
        self.equal_named = equal_named

        hide_unnamed = QtWidgets.QCheckBox('Hide unnamed constraints')
        hide_unnamed.setToolTip('Only show named constraints in Sketcher')
        hide_unnamed.setIcon(Icon.freecad('TreeItemInvisible.svg'))
        self.hide_unnamed = hide_unnamed

        form, self.expr_fields = make_form_fields(src, dst)

        layout = QtWidgets.QVBoxLayout(self)
        if form.rowCount() > 0:
            layout.addLayout(form)
            layout.addSpacerItem(QtWidgets.QSpacerItem(0, 12))
        layout.addWidget(rotation)
        layout.addWidget(equal_named)
        layout.addWidget(hide_unnamed)
        layout.addLayout(fileinfo)

    def stop(self) -> None:
        for field in self.expr_fields:
            field.cleanup(self.inserter.current)
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
            repl_expr=ExprReplacer(self.expr_fields, self.inserter.current),
        )

    def on_edit_sketch(self) -> None:
        self.inserter.close(reopenInEditMode=True)
