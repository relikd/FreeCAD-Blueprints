'''
Map property field to user-facing widget input field.
'''
from ...helper.settings import Settings
from ...gui.qt import QtWidgets, FCWidget

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCAD import DocumentObject as DocObj

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
def property_to_widget(obj: 'DocObj', prop: str) -> QtWidgets.QWidget:
    ''' Convert single property field to form field. '''
    type_id = obj.getTypeIdOfProperty(prop)

    w: QtWidgets.QWidget

    if type_id == 'App::PropertyBool':
        w = QtWidgets.QCheckBox()
        w.setChecked(getattr(obj, prop))

    elif type_id == 'App::PropertyString':
        w = FCWidget('Gui::ExpLineEdit')
        w.setText(getattr(obj, prop))

    elif type_id in ('App::PropertyInteger', 'App::PropertyPercent'):
        w = FCWidget('Gui::IntSpinBox')
        w.setValue(getattr(obj, prop))
        if type_id == 'App::PropertyPercent':
            w.setMinimum(0)
            w.setMaximum(100)

    elif type_id == 'App::PropertyFloat':
        w = FCWidget('Gui::DoubleSpinBox')
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
        w = FCWidget('Gui::FileChooser')
        w.setProperty('fileName', getattr(obj, prop))

    elif type_id in _QUANTITY_TYPES:
        w = FCWidget('Gui::QuantitySpinBox')
        # qty: Quantity = getattr(obj, prop)
        # w.setProperty('unit', qty.getUserPreferred()[2])
        # w.setProperty('rawValue', qty.Value)
        w.setProperty('value', getattr(obj, prop))

    else:
        w = QtWidgets.QLabel('--unsupported--')
        w.setToolTip(
            f'No editor support for type: {type_id}. If you have a use-case '
            'for this type, make a feature request on GitHub.')
        return w

    # copy tooltip from property
    w.setToolTip(obj.getDocumentationOfProperty(prop).strip())
    return w


#################################################
# Map input field back to property (str)
#################################################

def widget_to_value(field: QtWidgets.QWidget) -> 'str|None':
    ''' Read string value from form field. '''
    if isinstance(field, QtWidgets.QCheckBox):
        return '1' if field.isChecked() else '0'
    if isinstance(field, QtWidgets.QComboBox):
        return str(field.currentIndex())
    if isinstance(field, QtWidgets.QLineEdit):
        return _escape_fc_string(field.text())
    if isinstance(field, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        return str(field.value())
    cls = str(field.metaObject().className())
    if cls == 'Gui::QuantitySpinBox':
        return str(field.property('value'))
    if cls == 'Gui::FileChooser':
        return _escape_fc_string(field.property('fileName'))
    return None


def _escape_fc_string(txt: str) -> str:
    ''' Escape string sequence for inserting into expression engine. '''
    # TODO: Cannot reliably escape string.
    # String is either truncated, or expression engine silently removes ">".
    # But at least, FreeCAD wont crash if someone uses a ">".
    # There are probably other chars that need escaping too ...
    return '<<' + str(txt).replace('>', '\\>') + '>>'
