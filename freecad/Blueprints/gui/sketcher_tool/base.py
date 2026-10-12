'''
Code related to inserting another widget into Sketcher tools (docked panel).
'''
import FreeCADGui

from ..qt import QtCore, QtGui, QtWidgets


class QtElementNotFound(Exception):
    pass


class SketcherTool(QtWidgets.QWidget):
    '''Base class for sketcher tools. Auto-adds the tool to the sketcher UI.'''
    TITLE: str
    ICON: 'QtGui.QIcon|QtGui.QPixmap'

    def __init__(self):
        '''
        Raises:
        QtElementNotFound: If `TaskSketcherTool` widget cannot be located.
        '''
        super().__init__()
        container = task_tool_container()
        if not container:
            raise QtElementNotFound('TaskSketcherTool container not found.')

        head = get_header(container)
        if not head:
            raise QtElementNotFound('TaskSketcherTool header not found.')

        body = get_body(container)
        if not body:
            raise QtElementNotFound('TaskSketcherTool body not found.')

        # hide whatever is currently visible
        for child in body.children():
            if isinstance(child, QtWidgets.QWidget):
                child.setHidden(True)
        container.setHidden(False)
        head.setIcon(self.ICON)
        head.setText(self.TITLE)
        body.layout().addWidget(self)
        # Widgets are added hidden by default. The SketcherTool -> SketcherTool
        # transition triggers `cleanup` with a one cycle delay (`singleShot`).
        # At this point, the newly added view is still hidden and thus cleanup
        # would hide the parent container. So lets set hidden immediately.
        self.setHidden(False)

    def stop(self) -> None:
        '''Remove this tool from sketcher tools box (+ auto-hide container).'''
        # Additionally to the comment above, add a delay (100) and wait for
        # other UI changes. Technically, 0 is fine for SketcherTool -> built-in
        # geometry tool transitions. 100 is fine for ST -> ST transitions, even
        # without the `setHidden(False)`. But lets be safe and do both.
        QtCore.QTimer.singleShot(100, self._internal_cleanup)

    def _internal_cleanup(self) -> None:
        ''' Hides container if all children are hidden. '''
        if container := task_tool_container():
            all_hidden = True
            if body := get_body(container):
                for child in body.children():
                    if child == self:
                        body.layout().removeWidget(self)
                        self.setParent(None)
                        self.deleteLater()

                    elif isinstance(child, QtWidgets.QWidget) \
                            and not child.isHidden():
                        # either built-in geometry tool or our own SketcherTool
                        # (a new instance overwriting the old)
                        all_hidden = False
                        break
            if all_hidden:
                container.setHidden(True)


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
