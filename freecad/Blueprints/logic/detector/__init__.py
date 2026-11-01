'''
Initial detector (run once on blueprint load).
'''
from dataclasses import dataclass

from .axis import detect_axis, ReferencedAxis
from .constraints import detect_constraints, DetectedConstraints
from .expressions import detect_external, DetectedExpr

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


@dataclass
class DetectedStats:
    axis: ReferencedAxis
    constraints: DetectedConstraints
    expr: list[DetectedExpr]

    def __init__(self, sketch: 'Sketch') -> None:
        self.axis = detect_axis(sketch)
        self.constraints = detect_constraints(sketch)
        self.expr = detect_external(sketch)
