'''
Code related to inserting another widget into Sketcher tools (docked panel).
'''
import FreeCADGui

from ..qt import QtGui, QtWidgets


class QtElementNotFound(Exception):
    pass


class SketcherTool(QtWidgets.QWidget):
    ''' Base class template for managing single tool instances. '''
    TITLE: str
    ICON: 'QtGui.QIcon|QtGui.QPixmap'

    def __init__(self):
        super().__init__()
        SketcherToolModifier.install(self)

    def cleanup(self, *, close: bool) -> None:
        ''' Use `close` to control if the tool box should keep open or not. '''
        SketcherToolModifier.uninstall(close=close)


class SketcherToolModifier:
    ''' Generic tool class manager. Inserts a `SketcherTool` into the UI. '''
    @staticmethod
    def install(tool: SketcherTool) -> None:
        '''
        Raises:
        QtElementNotFound: If `TaskSketcherTool` widget cannot be located.
        '''
        container = task_tool_container()
        if not container:
            raise QtElementNotFound('TaskSketcherTool container not found.')

        head = get_header(container)
        if not head:
            raise QtElementNotFound('TaskSketcherTool header not found.')

        body = get_body(container)
        if not body:
            raise QtElementNotFound('TaskSketcherTool body not found.')

        _remove_previous(body, hide_others=True)
        container.setHidden(False)
        head.setIcon(tool.ICON)
        head.setText(tool.TITLE)
        body.layout().addWidget(tool)
        tool.setProperty('_blueprint_tool', True)

    @staticmethod
    def uninstall(*, close: bool) -> None:
        ''' Remove current tool from sketcher tools box. '''
        if container := task_tool_container():
            if close:
                container.setHidden(True)
            if body := get_body(container):
                _remove_previous(body, hide_others=False)


def _remove_previous(body: QtWidgets.QFrame, *, hide_others: bool) -> None:
    layout = body.layout()
    for child in body.children():
        if not isinstance(child, QtWidgets.QWidget):
            continue
        if child.property('_blueprint_tool'):
            layout.removeWidget(child)
            child.setParent(None)
            child.deleteLater()
        elif hide_others:
            child.setHidden(True)


#################################################
# Helper
#################################################

def task_tool_container() -> 'QtWidgets.QWidget|None':
    ''' Widget of side-panel where all the Sketcher task tools are. '''
    mw = FreeCADGui.getMainWindow()
    dock: QtWidgets.QDockWidget = mw.findChild(QtWidgets.QWidget, 'Tasks')
    # Note: the dock contains a QWidget with the same name
    # the tools are nested within both, so this is future proof
    for child in dock.findChildren(QtWidgets.QWidget):
        if child.metaObject().className() == 'SketcherGui::TaskSketcherTool':
            return child
    return None


def _frame(container: QtWidgets.QWidget, prop: str) -> 'QtWidgets.QFrame|None':
    ''' Within a tool container, find the frame where `.class == prop`. '''
    for child in container.findChildren(QtWidgets.QFrame):
        if child.property('class') == prop:
            return child
    return None


def get_header(container: QtWidgets.QWidget) -> 'QtWidgets.QToolButton|None':
    ''' Within a tool container, find the header widget. '''
    if frame := _frame(container, 'header'):
        return frame.findChild(QtWidgets.QToolButton)
    return None


def get_body(container: QtWidgets.QWidget) -> 'QtWidgets.QFrame|None':
    ''' Within a tool container, find the content widget. '''
    return _frame(container, 'content')
