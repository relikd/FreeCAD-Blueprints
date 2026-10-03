'''
Main entry point.
'''
import FreeCADGui

from .helper.utils import RES_ROOT
from .register_workbench import PseudoWorkbench

# Allow `Commands.py` to find referenced icons
FreeCADGui.addIconPath(str(RES_ROOT / 'icons'))

FreeCADGui.addWorkbenchManipulator(PseudoWorkbench())
