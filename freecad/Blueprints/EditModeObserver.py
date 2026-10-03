'''
Hide toolbar while FreeCAD is not in Sketcher Edit Mode
'''
import FreeCADGui

from .events.DocObserver import DocObserver
from .helper.qt import QtCore, QtWidgets
from .Manipulator import _TOOLBAR_NAME


def recompute_visibility() -> None:
    ''' Re-set toolbar visibility after Workbench switching. '''
    QtCore.QTimer.singleShot(0, _update_visibility)


def _update_visibility(
    *, show: 'bool|None' = None, _state: list[bool] = [False],  # noqa: B006
) -> None:
    '''
    Use Python quirk for state management (avoids global variable).
    State param is re-used between calls (do NOT assign manually!).
    '''
    if show is not None:
        _state[0] = show
    for bar in FreeCADGui.getMainWindow().findChildren(QtWidgets.QToolBar):
        if bar.objectName() == _TOOLBAR_NAME:
            bar.setVisible(_state[0])
            bar.toggleViewAction().setVisible(_state[0])
            return


DocObserver(
    onEditStart=lambda: _update_visibility(show=True),
    onEditEnd=lambda: _update_visibility(show=False),
)
