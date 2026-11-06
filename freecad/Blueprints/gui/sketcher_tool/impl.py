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

        equal_named = QtWidgets.QCheckBox('Create equal-constraints (J)')
        equal_named.setToolTip(
            'Treat all named constraints as equal.\n'
            'Newly inserted copies will depend on the previous copy.')
        # Icon.freecad('constraints/Constraint_EqualLength.svg'))
        equal_named.setIcon(Icon.res('tool-equal-named.svg'))
        self.equal_named = equal_named
        if not inserter.detected.constraints.has_named:
            equal_named.setEnabled(False)
            equal_named.setToolTip(
                'Disabled: Blueprint does not contain any named constraints.')

        eval_expr = QtWidgets.QCheckBox('Evaluate expressions (U)')
        eval_expr.setToolTip(
            'Replace all expressions with static values.\n'
            'User-provided expressions are not affected.\n'
            'This improves performance (less computations) but reduces '
            'editability.')
        eval_expr.setIcon(Icon.freecad('bound-expression-unset.svg'))
        self.eval_expr = eval_expr
        if not inserter.detected.constraints.has_expr:
            eval_expr.setEnabled(False)
            eval_expr.setToolTip(
                'Disabled: Blueprint does not contain any expressions.')

        form, self.expr_fields = make_form_fields(inserter.detected.expr, dst)

        layout = QtWidgets.QVBoxLayout(self)
        if form.rowCount() > 0:
            layout.addLayout(form)
            layout.addSpacerItem(QtWidgets.QSpacerItem(0, 12))
        layout.addWidget(rotation)
        layout.addWidget(equal_named)
        layout.addWidget(eval_expr)
        layout.addLayout(fileinfo)

    def stop(self) -> None:
        for field in self.expr_fields:
            field.cleanup(self.inserter.current)
        super().stop()

    def on_hotkey(self, letter: str) -> bool:
        if letter == 'M':
            self.rotation.toggle()
        elif letter == 'J':
            if self.inserter.detected.constraints.has_named:
                self.equal_named.toggle()
        elif letter == 'U':
            if self.inserter.detected.constraints.has_expr:
                self.eval_expr.toggle()
        else:
            return False
        return True

    def get_state(self) -> State:
        return State(
            rotation=self.rotation.isChecked(),
            equal_named=self.equal_named.isChecked(),
            repl_expr=ExprReplacer(self.expr_fields, self.inserter.current,
                                   resolve=self.eval_expr.isChecked()),
        )

    def on_edit_sketch(self) -> None:
        self.inserter.close(reopenInEditMode=True)
