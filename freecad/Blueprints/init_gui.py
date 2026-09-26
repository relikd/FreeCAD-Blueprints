'''
Main entry point.
'''
import FreeCADGui

from .helper.utils import RES_ROOT
from .Manipulator import Manipulator

# Allow `Commands.py` to find referenced icons
FreeCADGui.addIconPath(str(RES_ROOT / 'icons'))

FreeCADGui.addWorkbenchManipulator(Manipulator())


# class Cmd:
#     def GetResources(self) -> dict[str, str]:
#         return {
#             'MenuText': 'Testme',
#             'CmdType': 'ForEdit AlterDoc AlterSelection',
#         }
#     def Activated(self) -> None:
#         pass

# FreeCADGui.addCommand('Blueprints_Tmp', Cmd())
