'''
Main entry point.
'''
import FreeCADGui

from .helper.utils import RES_ROOT
from .gui.preferences import PreferencesPage
from .register_workbench import PseudoWorkbench

# Allow `Commands.py` to find referenced icons
FreeCADGui.addIconPath(str(RES_ROOT / 'icons'))

FreeCADGui.addWorkbenchManipulator(PseudoWorkbench())
FreeCADGui.addPreferencePage(PreferencesPage, 'Blueprints')

# from .dev import add_global_test_button
# add_global_test_button()
