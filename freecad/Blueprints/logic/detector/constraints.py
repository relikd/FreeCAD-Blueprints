'''
Detect usage of constraints.
'''
from ...helper.notify import Notify
from ..sketcher.constraints import Constr
from ..sketcher.georef import GeoId

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


def validate_constraints(sketch: 'Sketch') -> None:
    ''' Ensure sketch is well-structured to avoid common mistakes. '''
    if Constr.any(sketch.Constraints, GeoId.isExt):
        Notify.warn('External reference found',
                    'Blueprints cannot have references on external geometry.')
