'''
Create form fields for user overwrites of existing expression variables.
'''
from dataclasses import dataclass

import FreeCAD
import FreeCADGui

from ...gui.qt import QtWidgets
from .detector import detect_external
from .widgets import property_to_widget

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from .detector import DetectedExpr


PRFX = '__ext_expr_'


@dataclass
class UserExprField:
    key: str
    type_id: str
    bind_key: str
    field: QtWidgets.QWidget

    def __init__(self, expref: 'DetectedExpr', index: int) -> None:
        self.key = expref.key
        self.type_id = expref.type_id
        self.bind_key = PRFX + str(index)
        self.field = property_to_widget(expref.obj, expref.prop)

    def meta_tooltip(self) -> str:
        return f'type: {self.type_id}\nkey: {self.key}'

    def install_binding(self, dst: 'Sketch') -> None:
        '''
        Bind form field via `ExpressionBinding` to (transient) sketch property.
        The binding needs to be on the sketch itself, or else, we wont be
        able to reference constraints and VarSets from this document.
        '''
        if not _can_bind(self.field):
            return
        dst.addProperty(
            self.type_id, self.bind_key, group='_BlueprintsTransientProps',
            doc=self.meta_tooltip(),
            attr=FreeCAD.PropertyType.Prop_Transient,  # type: ignore[attr-defined]
            hidden=True)
        FreeCADGui.ExpressionBinding(self.field).bind(dst, self.bind_key)  # type: ignore

    def cleanup(self, dst: 'Sketch') -> None:
        ''' Remove all transient properties from sketch. '''
        # FreeCAD will crash if property is removed while ExpressionBinding
        # is still active. (happens if the widget is present in some view)
        # Thus we first try to remove all form fields with ExpressionBinding.
        try:
            self.field.setParent(None)
        except RuntimeError:
            # ignore Qt object already deleted (Cmd+Q while editing sketch)
            pass
        dst.removeProperty(self.bind_key)  # does not need to exist


def make_form_fields(src: 'Sketch', dst: 'Sketch') \
        -> tuple[QtWidgets.QFormLayout, list[UserExprField]]:
    ''' Create form fields and internal field mapping. '''
    rv = []
    form = QtWidgets.QFormLayout()
    for i, expref in enumerate(detect_external(src), _prev_idx(dst) + 1):
        item = UserExprField(expref, i)
        rv.append(item)
        # label
        lbl = QtWidgets.QLabel(expref.display_name)
        lbl.setToolTip(
            f'{item.meta_tooltip()}\n\n{item.field.toolTip()}'.rstrip())
        form.addRow(lbl, item.field)
        item.install_binding(dst)  # adds (fx) button
    return form, rv


#################################################
# Helper methods
#################################################

def _prev_idx(dst: 'Sketch') -> int:
    ''' If there are any previously bound fields, get current max index. '''
    # NOTE: if other properties with the same prefix appear, this will break
    return max((int(x.removeprefix(PRFX)) for x in dst.PropertiesList
            if x.startswith(PRFX)), default=0)


def _can_bind(widget: QtWidgets.QWidget) -> bool:
    ''' Whether the form field can be bound to expression engine. '''
    cls = str(widget.metaObject().className())
    return cls.startswith('Gui::') and cls != 'Gui::FileChooser'
