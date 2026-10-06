from ..qt import QtWidgets
from .entry import DataItem
from .window import Window

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


def open_sketch_chooser(sketches: 'list[Sketch]') -> 'Sketch|None':
    if not sketches:
        return None

    dialog = Window(list(map(DataItem, enumerate(sketches))))

    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        if selected := dialog.get_selected():
            dialog.deleteLater()
            return sketches[selected.index]
    dialog.deleteLater()
    return None
