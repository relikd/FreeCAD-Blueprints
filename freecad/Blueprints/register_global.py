'''
Code which should run at app start but is postponed until after workbench
registration.
'''
import FreeCADGui

from .events.doc_observer import DocObserver
from .helper.qt import QtCore, QtWidgets


TOOLBAR_NAME = 'Sketcher Blueprints'


#################################################
# Change toolbar visibility depending on edit mode
#################################################


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
    for bar in available_toolbars():
        if bar.objectName() == TOOLBAR_NAME:
            bar.setVisible(_state[0])
            bar.toggleViewAction().setVisible(_state[0])
            return


DocObserver(
    onEditStart=lambda: _update_visibility(show=True),
    onEditEnd=lambda: _update_visibility(show=False),
)


#################################################
# Typed helper
#################################################

def available_toolbars() -> list[QtWidgets.QToolBar]:
    return FreeCADGui.getMainWindow().findChildren(QtWidgets.QToolBar)
