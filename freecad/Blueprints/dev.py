'''
Internal DEV helpers
'''
from PySide6 import QtCore, QtWidgets


def _l(*args: object) -> None:
    ''' Convenience logger during development. '''
    from .helper.notify import Notify  # noqa: PLC0415
    Notify.Log.err(' '.join(str(x) for x in args))


IGNORED_PROPS = {'class', '_q_styleSheetWidgetFont', '_PySideInvalidatePtr'}


def _qt_dump(obj: 'QtCore.QObject|None', indent: str = '') -> str:
    ''' Dump whole Qt tree for widget. '''
    if not obj:
        return ''
    rv = f'\n{indent}{type(obj).__name__} name="{obj.objectName()}" '
    attrs: dict[str, object] = {
        'qt-class': obj.metaObject().className(),
        'prop-class': obj.property('class'),
        'props': {
            bytes(x).decode('utf-8', errors='replace')
            for x in obj.dynamicPropertyNames()} - IGNORED_PROPS,
    }
    if isinstance(obj, QtWidgets.QWidget):
        attrs.update({
            'title': obj.windowTitle(),
            'accessibleName': obj.accessibleName(),
            'isHidden': obj.isHidden(),
            '!_isVisible': not obj.isVisible(),
            'toolTip': obj.toolTip().replace('\n', '\\n'),
        })
    if isinstance(obj, QtWidgets.QAbstractButton):
        attrs.update({
            'text': obj.text(),
            'actions': obj.actions(),
        })
    if isinstance(obj, QtWidgets.QFrame):
        attrs.update({
            'frameSize': obj.frameSize(),
            'frameShape': obj.frameShape(),
        })

    rv += ' '.join(f'{k}="{v}"' for k, v in attrs.items() if v)
    for child in obj.children():
        rv += _qt_dump(child, indent + '  ')
    if not indent:
        _l(rv)
    return rv


def add_global_test_button() -> None:
    import FreeCADGui  # noqa: PLC0415

    class Cmd:
        def GetResources(self) -> dict[str, str]:
            return {
                'MenuText': 'Testme',
                'CmdType': 'ForEdit AlterDoc AlterSelection',
            }

        def Activated(self) -> None:
            _qt_dump(FreeCADGui.getMainWindow())

    FreeCADGui.addCommand('Blueprints_Tmp', Cmd())
