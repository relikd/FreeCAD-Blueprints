'''
Detect usage of constraints.
'''
from dataclasses import dataclass

from ...helper.notify import Notify
from ..sketcher.constraints import Constr
from ..sketcher.georef import GeoId

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


def _validate(sketch: 'Sketch') -> None:
    ''' Ensure sketch is well-structured to avoid common mistakes. '''
    if Constr.any(sketch.Constraints, GeoId.isExt):
        Notify.warn('External reference found',
                    'Blueprints cannot have references on external geometry.')


@dataclass
class DetectedConstraints:
    has_named: bool
    has_expr: bool


def detect_constraints(sketch: 'Sketch') -> DetectedConstraints:
    _validate(sketch)
    return DetectedConstraints(
        has_named=any(x.Name and x.Driving for x in sketch.Constraints),
        has_expr=bool(sketch.ExpressionEngine),
    )
