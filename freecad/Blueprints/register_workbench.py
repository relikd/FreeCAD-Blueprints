'''
Register (and auto-enable) toolbar and menu items.
'''
import FreeCADGui


# see https://github.com/FreeCAD/Addon-Academy/blob/2c2e7a97f2094752eafb6b67848b4238ce461e42/Source/Demos/New-Toolbar/Source/freecad/Calvinball/Manipulator.py#L25-L33
def isSketcher() -> bool:
    # `FreeCADGui.activeWorkbench().name()` cannot be used here, see above
    active = FreeCADGui.activeWorkbench()
    for name, handler in FreeCADGui.listWorkbenches().items():  # type: ignore[attr-defined]
        if handler is active:
            return name == 'SketcherWorkbench'
    return False


# see https://github.com/FreeCAD/FreeCAD/blob/main/src/Gui/WorkbenchManipulatorPython.cpp
class PseudoWorkbench:
    ''' Postpone register commands and global, so `init_gui.py` stays fast. '''

    def modifyMenuBar(self) -> list[dict[str, str]]:
        if isSketcher():
            from .register_commands import CMD_NAME  # noqa: PLC0415
            return [
                {'menuItem': 'Geometries', 'append': 'Separator'},
                {'menuItem': 'Geometries', 'append': CMD_NAME},
            ]
        return []

    def modifyToolBars(self) -> list[dict[str, str]]:
        if isSketcher():
            from .register_commands import CMD_NAME  # noqa: PLC0415
            from .register_global import TOOLBAR_NAME, recompute_visibility  # noqa: PLC0415
            recompute_visibility()
            # FreeCAD is about to rebuild the toolbar and show it.
            # Re-apply current state, since the QToolBar does not exist yet.
            return [
                # Append shows the icon after 'Toggle Construction Geometry'
                # {'toolBar': 'Geometries', 'append': X},
                # Insert places the icon before the Point Geometry
                # {'toolItem': 'Sketcher_CreatePoint', 'insert': X},
                # standalone toolbar
                {'toolBar': '', 'append': TOOLBAR_NAME},
                {'toolBar': TOOLBAR_NAME, 'append': CMD_NAME},
            ]
        return []

    # def modifyContextMenu(self) -> list[dict[str, str]]:
