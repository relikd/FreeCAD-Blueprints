'''
Code related to command registration. Do as little logic as possible.
'''
import FreeCAD
import FreeCADGui

from .helper.notify import Notify
from .blueprint_inserter import BlueprintInserter
from .blueprint_loader import chooseBlueprint

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch

CMD_NAME = 'Blueprints_Add'


# see https://github.com/FreeCAD/FreeCAD/blob/f873b82f1e48632394609103e0b9071d83e46abf/src/Gui/Command.cpp#L1409
class Blueprints_Add_Cmd:
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
        thisDoc = FreeCAD.ActiveDocument
        if not thisDoc:
            Notify.err('No Active Document', 'No active document found.')
            return

        currentSketch = getActiveSketchInEditMode()
        if not currentSketch:
            Notify.err('No Active Sketch',
                       'Open a sketch in edit mode, then try again.')
            return

        if blueprint := chooseBlueprint():
            BlueprintInserter.cancel_previous()
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
    return edit.Object


FreeCADGui.addCommand(CMD_NAME, Blueprints_Add_Cmd())
