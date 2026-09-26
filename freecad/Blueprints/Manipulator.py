'''
Register (and auto-enable) toolbar and menu items.
'''
import FreeCADGui

_TOOLBAR_NAME = 'Sketcher Blueprints'


def active_workbench_name() -> str:
    ''' Current workbench name (fixed) '''
    active = FreeCADGui.activeWorkbench()
    for name, handler in FreeCADGui.listWorkbenches().items():  # type: ignore
        if handler is active:
            return name
    return ''


def isSketcher() -> bool:
    return active_workbench_name() == 'SketcherWorkbench'


# see https://github.com/FreeCAD/FreeCAD/blob/main/src/Gui/WorkbenchManipulatorPython.cpp
class Manipulator:
    def modifyMenuBar(self) -> list[dict[str, str]]:
        if isSketcher():
            return [
                {'menuItem': 'Geometries', 'append': 'Separator'},
                {'menuItem': 'Geometries', 'append': 'Blueprints_Add'},
            ]
            # Use `Blueprints_Grp` if you want a submenu
        return []

    def modifyToolBars(self) -> list[dict[str, str]]:
        if isSketcher():
            # Postpone registering so init_gui.py stays fast
            from . import Commands  # noqa: F401, PLC0415
            from .EditModeObserver import recompute_visibility  # noqa: PLC0415
            # FreeCAD is about to rebuild the toolbar and show it.
            # Re-apply current state, since the QToolBar does not exist yet.
            recompute_visibility()
            return [
                # Append shows the icon after 'Toggle Construction Geometry'
                # {'toolBar': 'Geometries', 'append': X},
                # Insert places the icon before the Point Geometry
                # {'toolItem': 'Sketcher_CreatePoint', 'insert': X},
                # standalone toolbar
                {'toolBar': '', 'append': _TOOLBAR_NAME},
                {'toolBar': _TOOLBAR_NAME, 'append': 'Blueprints_Add'},
            ]
        return []

    # def modifyContextMenu(self) -> list[dict[str, str]]:
