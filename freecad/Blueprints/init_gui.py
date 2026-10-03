'''
Main entry point.
'''
import FreeCADGui

from .helper.utils import RES_ROOT
from .Manipulator import Manipulator

# Allow `Commands.py` to find referenced icons
FreeCADGui.addIconPath(str(RES_ROOT / 'icons'))

FreeCADGui.addWorkbenchManipulator(Manipulator())
