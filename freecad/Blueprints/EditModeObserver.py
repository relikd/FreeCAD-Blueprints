'''
Hide toolbar while FreeCAD is not in Sketcher Edit Mode
'''
import FreeCADGui

from .helper.qt import QtCore, QtWidgets
from .Manipulator import _TOOLBAR_NAME

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PartDesignGui import ViewProvider


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


class EditModeObserver:
    def slotInEdit(self, view_provider: 'ViewProvider') -> None:
        if not view_provider.Object.isDerivedFrom('Sketcher::SketchObject'):
            return
        _update_visibility(show=True)

    def slotResetEdit(self, view_provider: 'ViewProvider') -> None:
        if not view_provider.Object.isDerivedFrom('Sketcher::SketchObject'):
            return
        _update_visibility(show=False)


FreeCADGui.addDocumentObserver(EditModeObserver())
