'''
Initial detector (run once on blueprint load).
'''
from dataclasses import dataclass

from .axis import detect_axis, ReferencedAxis
from .constraints import validate_constraints
from .expressions import detect_external, DetectedExpr

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


@dataclass
class DetectedStats:
    axis: ReferencedAxis
    expr: list[DetectedExpr]

    def __init__(self, sketch: 'Sketch') -> None:
        validate_constraints(sketch)
        self.axis = detect_axis(sketch)
        self.expr = detect_external(sketch)
