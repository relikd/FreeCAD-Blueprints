import FreeCAD
import FreeCADGui

from ...helper.settings import Settings
from ...helper.utils import camel_case_name
from ...blueprint_duplicator import detect_external
from ..qt import QtWidgets

from typing import TYPE_CHECKING, Literal, overload
from collections.abc import Iterator

if TYPE_CHECKING:
    from FreeCAD import DocumentObject as DocObj
    from Sketcher import SketchObject as Sketch
    from ...blueprint_duplicator import ExternalExpressionsRepl


PRFX = '__ext_expr_'


def make_form(src: 'Sketch') -> QtWidgets.QFormLayout:
    ''' Create Qt-form with all expression variables mapped to form fields. '''
    form = QtWidgets.QFormLayout()
    form.setObjectName('expr_map')

    for key, (obj, prop) in sorted(detect_external(src).items()):
        type_id = obj.getTypeIdOfProperty(prop)
        tooltip = obj.getDocumentationOfProperty(prop).strip()

        # label
        # The naming wont work with nested variables.
        # But we don't have support for these anyway.
        lbl = QtWidgets.QLabel(camel_case_name(key.rsplit('.', 1)[-1]))
        lbl.setToolTip(f'type: {type_id}\nkey: {key}\n\n{tooltip}'.rstrip())

        # input field
        if w := _property_to_widget(obj, prop):
            w.setToolTip(tooltip)
            w.setProperty(PRFX, key)
            w.setProperty(PRFX + 'type', type_id)
        else:
            w = QtWidgets.QLabel('--unsupported--')
            w.setToolTip(f'No editor for type: {type_id}')
            # don't `setProperty`, so they are not evaluated below

        form.addRow(lbl, w)
    return form


def install_bindings(form: QtWidgets.QFormLayout, dst: 'Sketch') -> None:
    '''
    Bind all form fields via `ExpressionBinding` to (transient) properties
    on sketch. The binding need to be on the sketch itself, or else, we wont be
    able to reference constraints and VarSets from this document.
    '''
    last = max((int(x.removeprefix(PRFX)) for x in dst.PropertiesList
                if x.startswith(PRFX)), default=0)
    for i, (key, field) in enumerate(_iter_form_fields(form), start=last + 1):
        if _can_bind(field):
            type_id = field.property(PRFX + 'type')
            bind_key = PRFX + str(i)
            dst.addProperty(type_id, bind_key, group=PRFX + 'grp',
                            doc=f'type: {type_id}\nkey: {key}',
                            attr=FreeCAD.PropertyType.Prop_Transient,  # type: ignore[attr-defined]
                            hidden=True)
            FreeCADGui.ExpressionBinding(field).bind(dst, bind_key)  # type: ignore


def expr_cleanup(form: QtWidgets.QFormLayout, dst: 'Sketch') -> None:
    ''' Remove all transient properties from sketch. '''
    # FreeCAD will crash if the property is removed while ExpressionBinding is
    # still active. (happens if the widget is present in some view)
    # Thus we first try to remove all form fields with ExpressionBinding.
    try:
        for _, field in _iter_form_fields(form):
            field.setParent(None)
    except RuntimeError:
        pass  # ignore Qt object already deleted (Cmd+Q while editing sketch)
    for prop in dst.PropertiesList:
        if prop.startswith(PRFX):
            dst.removeProperty(prop)


#################################################
# Helper methods
#################################################

def _can_bind(widget: QtWidgets.QWidget) -> bool:
    ''' Whether the form field can be bound to expression engine. '''
    cls = str(widget.metaObject().className())
    return cls.startswith('Gui::') and cls != 'Gui::FileChooser'


def _iter_form_fields(form: QtWidgets.QFormLayout) \
        -> Iterator[tuple[str, QtWidgets.QWidget]]:
    ''' Iterate over form fields which are mapped to a variable. '''
    for i in range(form.count() - 1, -1, -1):  # reversed so we can remove itms
        child = form.itemAt(i).widget()
        if key := child.property(PRFX):
            yield key, child


#################################################
# Map input field back to property (str)
#################################################

def collect_fields(form: QtWidgets.QFormLayout) -> 'ExternalExpressionsRepl':
    ''' Read string values for all form fields. '''
    rv = {}
    for key, field in _iter_form_fields(form):
        if isinstance(field, QtWidgets.QCheckBox):
            rv[key] = '1' if field.isChecked() else '0'
        elif isinstance(field, QtWidgets.QComboBox):
            rv[key] = str(field.currentIndex())
        elif isinstance(field, (QtWidgets.QLabel, QtWidgets.QLineEdit)):
            rv[key] = _escape_fc_string(field.text())
        elif isinstance(field, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            rv[key] = str(field.value())
        elif cls := field.metaObject().className():
            if cls == 'Gui::QuantitySpinBox':
                rv[key] = str(field.property('value'))
            elif cls == 'Gui::FileChooser':
                rv[key] = _escape_fc_string(field.property('fileName'))
    return rv


def _escape_fc_string(txt: str) -> str:
    ''' Escape string sequence for inserting into expression engine. '''
    # TODO: Cannot reliably escape string.
    # String is either truncated, or expression engine silently removes ">".
    # But at least, FreeCAD wont crash if someone uses a ">".
    # There are probably other chars that need escaping too ...
    return '<<' + str(txt).replace('>', '\\>') + '>>'


#################################################
# Map property to input field
#################################################

_QUANTITY_TYPES = {
    'App::PropertyQuantity',
    'App::PropertyQuantityConstraint',
    'App::PropertyLength',
    'App::PropertyDistance',
    'App::PropertyAngle',
    'App::PropertyArea',
    'App::PropertyVolume',
    'App::PropertySpeed',
    'App::PropertyAcceleration',
    'App::PropertyForce',
    'App::PropertyPressure',
    'App::PropertyMass',
    'App::PropertyTime',
    'App::PropertyFrequency',
    'App::PropertyPower',
    'App::PropertyEnergy',
    'App::PropertyVoltage',
    'App::PropertyCurrent',
    'App::PropertyTemperature',
}


# see https://github.com/FreeCAD/FreeCAD/blob/088f49373da7309845471e5286b2f6deb69ec8d7/src/Mod/BIM/ArchComponent.py#L2844-L2853
def _property_to_widget(obj: 'DocObj', prop: str) -> 'QtWidgets.QWidget|None':
    ''' Convert single property field to form field. '''
    type_id = obj.getTypeIdOfProperty(prop)

    w: QtWidgets.QWidget

    if type_id == 'App::PropertyBool':
        w = QtWidgets.QCheckBox()
        w.setChecked(getattr(obj, prop))

    elif type_id == 'App::PropertyString':
        w = _field('Gui::ExpLineEdit')
        w.setText(getattr(obj, prop))

    elif type_id in ('App::PropertyInteger', 'App::PropertyPercent'):
        w = _field('Gui::IntSpinBox')
        w.setValue(getattr(obj, prop))
        if type_id == 'App::PropertyPercent':
            w.setMinimum(0)
            w.setMaximum(100)

    elif type_id == 'App::PropertyFloat':
        w = _field('Gui::DoubleSpinBox')
        w.setDecimals(Settings.Units.decimals())
        w.setRange(-(2**31), 2**31)
        w.setValue(getattr(obj, prop))

    elif type_id == 'App::PropertyEnumeration':
        w = QtWidgets.QComboBox()
        w.addItems(obj.getEnumerationsOfProperty(prop))
        w.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        w.setMinimumContentsLength(20)
        idx = w.findText(getattr(obj, prop))
        if idx >= 0:
            w.setCurrentIndex(idx)

    elif type_id == 'App::PropertyFile':
        # App::PropertyPath is harder because we cant set mode via setProperty
        w = _field('Gui::FileChooser')
        w.setProperty('fileName', getattr(obj, prop))

    elif type_id in _QUANTITY_TYPES:
        w = _field('Gui::QuantitySpinBox')
        # qty: Quantity = getattr(obj, prop)
        # w.setProperty('unit', qty.getUserPreferred()[2])
        # w.setProperty('rawValue', qty.Value)
        w.setProperty('value', getattr(obj, prop))

    else:
        return None
    return w


@overload
def _field(name: Literal['Gui::ExpLineEdit']) -> QtWidgets.QLineEdit: ...
@overload
def _field(name: Literal['Gui::IntSpinBox']) -> QtWidgets.QSpinBox: ...
@overload
def _field(name: Literal['Gui::DoubleSpinBox']) -> QtWidgets.QDoubleSpinBox: ...  # noqa: E501
@overload
def _field(name: str) -> QtWidgets.QWidget: ...
def _field(name: str) -> 'QtWidgets.QWidget':
    return FreeCADGui.UiLoader().createWidget(name)  # type: ignore[attr-defined]
