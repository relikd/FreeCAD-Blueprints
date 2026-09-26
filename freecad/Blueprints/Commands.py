'''
Code related to command registration. Do as little logic as possible.
'''
import FreeCAD
import FreeCADGui

from .helper.notify import Notify
from .SketchCopy import duplicateSketch
from .SketchLoader import chooseBlueprint
from .SketchTargetConf import SketchTargetConf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


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

        # save current selection / UI state before `chooseBlueprint()`
        conf = SketchTargetConf(currentSketch, allowRotate=False)

        if otherSketch := chooseBlueprint():
            thisDoc.openTransaction('Load Blueprint (Sketch)')
            try:
                duplicateSketch(otherSketch, currentSketch, conf)
                thisDoc.commitTransaction()
            except Exception:
                thisDoc.abortTransaction()
                raise
            finally:
                FreeCAD.closeDocument(otherSketch.Document.Name)


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


FreeCADGui.addCommand('Blueprints_Add', Blueprints_Add_Cmd())


##################################################
# Group commands (drop-down in toolbar, submenus in menu)
##################################################

# class CommandGroup:
#     def GetDefaultCommand(self) -> int:
#         return 1

#     def GetResources(self) -> dict[str, str]:
#         return {
#             'MenuText': 'Blueprints',
#             'ToolTip': 'Blueprints addon extension',
#             'Pixmap': 'toolbar.svg',
#             'CmdType': 'ForEdit AlterDoc AlterSelection',
#         }

#     def GetCommands(self) -> list[str]:
#         return ['Blueprints_Add', 'Blueprints_Add']

#     def Activated(self, cmd: int = 0) -> None:
#         Console.PrintError(f'Run {cmd} (doesnt call child).\n')


# FreeCADGui.addCommand('Blueprints_Grp', CommandGroup())
