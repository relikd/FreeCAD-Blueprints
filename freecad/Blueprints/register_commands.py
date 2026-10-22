'''
Code related to command registration. Do as little logic as possible.
'''
import FreeCAD
import FreeCADGui

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


# see https://github.com/FreeCAD/FreeCAD/blob/f873b82f1e48632394609103e0b9071d83e46abf/src/Gui/Command.cpp#L1409
class Blueprints_Add:
    # def OnActionInit(self): ...

    def GetResources(self) -> dict[str, str]:
        return {
            'MenuText': 'Add Blueprint (Sketch)',
            'ToolTip': 'Open blueprint library to add a Sketcher template.',
            'Pixmap': 'toolbar.svg',
            'Accel': 'B',
            # active during Sketch editing
            'CmdType': 'ForEdit AlterDoc AlterSelection',
        }

    def IsActive(self) -> bool:
        ''' Only active during Sketch editing. '''
        return getActiveSketchInEditMode() is not None

    def Activated(self) -> None:
        ''' Open sketch from another file. '''
        from .helper.notify import Notify  # noqa: PLC0415
        from .blueprint_inserter import BlueprintInserter  # noqa: PLC0415
        from .blueprint_loader import chooseBlueprint  # noqa: PLC0415
        thisDoc = FreeCAD.ActiveDocument
        if not thisDoc:
            Notify.err('No Active Document', 'No active document found.')
            return

        currentSketch = getActiveSketchInEditMode()
        if not currentSketch:
            Notify.err('No Active Sketch',
                       'Open a sketch in edit mode, then try again.')
            return

        if blueprint := chooseBlueprint(BlueprintInserter.current_doc()):
            BlueprintInserter.kill_previous(ignored=blueprint.Document)
            # cancel any current geometry or constraint tool
            FreeCADGui.runCommand('Sketcher_StopOperation', 0)
            BlueprintInserter(currentSketch, blueprint)


def getActiveSketchInEditMode() -> 'Sketch|None':
    editDoc = FreeCADGui.editDocument()
    if not editDoc:
        return None
    edit = editDoc.getInEdit()
    if not edit or not edit.isDerivedFrom('SketcherGui::ViewProviderSketch'):
        return None
    if not isinstance(edit, FreeCADGui.ViewProviderDocumentObject):
        return None
    return edit.Object  # type: ignore[return-value]


CMD_NAME: Final = 'Blueprints_Add'
FreeCADGui.addCommand(CMD_NAME, Blueprints_Add())


##################################################
# Sketcher main menu, "Blueprints" submenu entry
##################################################

class Blueprints_OpenLibrary:
    def GetResources(self) -> dict[str, str]:
        return {
            'MenuText': 'Open Blueprints Library',
            'ToolTip': 'Open user library location in file manager.',
            # 'Accel': 'B, O',  # enable once #33598 is fixed
            'CmdType': 'ForEdit AlterDoc AlterSelection',
        }

    def Activated(self) -> None:
        from .helper.settings import Settings  # noqa: PLC0415
        from .helper.utils import open_in_file_manager  # noqa: PLC0415
        open_in_file_manager(Settings.databaseDir())


FreeCADGui.addCommand('Blueprints_OpenLibrary', Blueprints_OpenLibrary())


class Blueprints_NewEmpty:
    def GetResources(self) -> dict[str, str]:
        return {
            'MenuText': 'New Empty Blueprint',
            'ToolTip': 'Create a new, blank blueprint.',
            'CmdType': 'ForEdit AlterDoc AlterSelection',
        }

    def Activated(self) -> None:
        from .blueprint_creator import create_blueprint  # noqa: PLC0415
        create_blueprint()


FreeCADGui.addCommand('Blueprints_NewEmpty', Blueprints_NewEmpty())


class Blueprints_NewFromSelection:
    def GetResources(self) -> dict[str, str]:
        return {
            'MenuText': 'New Blueprint From Selection',
            'ToolTip': 'Create blueprint from currently selected geometries.',
            'CmdType': 'ForEdit AlterDoc AlterSelection',
        }

    def IsActive(self) -> bool:
        from .blueprint_creator import has_selection  # noqa: PLC0415
        return has_selection()

    def Activated(self) -> None:
        from .blueprint_creator import create_blueprint  # noqa: PLC0415
        create_blueprint(from_selection=True)


FreeCADGui.addCommand(
    'Blueprints_NewFromSelection', Blueprints_NewFromSelection())


class Blueprints_Menu:
    def GetResources(self) -> dict[str, str]:
        return {
            'MenuText': 'Blueprints',
            'CmdType': 'ForEdit AlterDoc AlterSelection',
        }

    def GetCommands(self) -> list[str]:
        return [
            'Blueprints_Add',
            'Blueprints_OpenLibrary',
            'Blueprints_NewEmpty',
            'Blueprints_NewFromSelection',
        ]


MENU_NAME: Final = 'Blueprints_Menu'
FreeCADGui.addCommand(MENU_NAME, Blueprints_Menu())
