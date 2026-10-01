'''
Code related to copying geometry from one Sketch to another.
'''
import re
from dataclasses import dataclass

from .helper.constraints import Constr
from .helper.geodraw import Draw, moveTo
from .helper.georef import GeoId, GeoRef
from .helper.notify import Notify

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from FreeCAD import Vector


def _validate(sketch: 'Sketch') -> None:
    ''' Ensure sketch is well-structured to avoid common mistakes. '''
    if Constr.any(sketch.Constraints, GeoId.isExt):
        Notify.warn('External reference found',
                    'Blueprints cannot have references on external geometry.')


@dataclass
class BlueprintDuplicator:
    '''
    placement:
        Place blueprint at these coordinates (instead of origin).
    constrainTo:
        If user has selected an Edge or Vertex prior to loading the blueprint,
        add an `PointOnObject` / `Coincident` constraint (respectively).
    allowRotate:
        After import, run `removeAxesAlignment` to allow blueprint rotation.
        This depends heavily on the quality of the source sketch.
        Please avoid `DistanceX` and `DistanceY` constraints.
    '''
    placement: 'Vector|None'
    constrainTo: 'GeoRef|None'
    allowRotate: bool = False

    def copyTo(self, dst: 'Sketch', *, src: 'Sketch') -> None:
        ''' Copy a sketch from one document to another. '''
        # bounds = src.Shape.BoundBox
        _validate(src)

        # where newly created geo ids start
        # used to group everything which was created by this process
        initial_geoid = dst.GeometryCount

        # check if sketch contains references on any of the axes
        # override original axis (if necessary) to allow translation
        hasArtificialAxis = Constr.any(src.Constraints, GeoId.isAxis)
        if hasArtificialAxis:
            _V, _H = _createArtificialAxes(dst, self.placement)
        else:
            _V, _H = GeoId.HAxis, GeoId.VAxis

        # after (potential) artificial axis
        # used to fix references when importing from other sketch
        geoid_offset, cid_offset = dst.GeometryCount, dst.ConstraintCount

        _copy_geometry(src, dst, toPos=self.placement)
        _copy_constraints(src, dst, geoid_offset, h_axis=_H, v_axis=_V)
        _copy_expressions(src, dst, cid_start=cid_offset)

        if self.allowRotate:
            dst.removeAxesAlignment(
                list(range(initial_geoid, dst.GeometryCount)))

        # solve at the end should be sufficient as we dont manipulate geometry
        dst.solve()

        if hasArtificialAxis and self.constrainTo:
            _constrain_origin(dst, GeoRef.S(_H), self.constrainTo)


############################################################
# Helper methods
############################################################

def _createArtificialAxes(sketch: 'Sketch', toPos: 'Vector|None') \
        -> tuple[int, int]:
    '''
    Create artificial axis to allow translation.
    Returns geo-ids for artificial axis `(vertical, horizontal)` (both lines)
    '''
    axis_len = 1
    v, h = sketch.addGeometry([  # type: ignore[misc]
        moveTo(toPos, Draw.line(0, 0, 0, axis_len)),
        moveTo(toPos, Draw.line(0, 0, axis_len, 0)),
    ], True)  # construction
    # add constraints
    cons = sketch.addConstraint([
        Constr.Coincident(GeoRef.S(h), GeoRef.S(v)),
        Constr.Perpendicular.Lines(v, h),
        Constr.Distance.Line(v, length=axis_len),
        Constr.Distance.Line(h, length=axis_len),
        Constr.Horizontal.Line(h),
    ])
    sketch.setVirtualSpace(cons, True)  # hide from user
    # sketch.solve()  # no need, done at the end
    return v, h


def _copy_geometry(src: 'Sketch', dst: 'Sketch', toPos: 'Vector|None') -> None:
    ''' Duplicate geometry. Translate geometry by `toPos` vector. '''
    if toPos:
        for geo in src.Geometry:
            dst.addGeometry(moveTo(toPos, geo))
    else:
        dst.addGeometry(src.Geometry)  # else, copy whole list verbatim


def _copy_constraints(
    src: 'Sketch', dst: 'Sketch', geoid_start: int, h_axis: int, v_axis: int,
) -> None:
    '''
    Duplicate constraints. Offset geo-ids by `geoid_start`.
    Replace original axes with `h_axis` and `v_axis` respectively.
    (use `h_axis=GeoId.HAxis, v_axis=GeoId.VAxis` if no artificial axes exist)
    '''
    def fn(geoid: int) -> int:
        if geoid >= 0:  # normal geometry
            return geoid_start + geoid
        if geoid == GeoId.HAxis:
            return h_axis
        if geoid == GeoId.VAxis:
            return v_axis
        return geoid

    con_list = []
    for con in src.Constraints:
        con.First = fn(con.First)
        if con.Second != GeoId.Undef:
            con.Second = fn(con.Second)
        if con.Third != GeoId.Undef:
            con.Third = fn(con.Third)
        # TODO: if same name, increment as new name?
        con_list.append(con)
    dst.addConstraint(con_list)
    # dst.solve()  # no need, done at the end


def _copy_expressions(src: 'Sketch', dst: 'Sketch', cid_start: int) -> None:
    ''' Duplicate expressions. Offset constraint indices by `cid_start`. '''
    for field, val in src.ExpressionEngine:
        if field.startswith('Constraints['):
            field = _re_index_expressions(field, cid_start)
        elif field.startswith('.Constraints.'):
            # TODO: if same name, increment as new name?
            pass  # copy named constraint as is
        else:
            Notify.Log.err(f'Unhandled expr variant: "{field}". '
                           'Please report this error on GitHub.')
            continue
        dst.setExpression(field, _re_index_expressions(val, cid_start))


def _constrain_origin(dst: 'Sketch', origin: GeoRef, toTarget: GeoRef) -> None:
    if toTarget.pos == 0:
        dst.addConstraint(Constr.PointOnObject(origin, toTarget.geoid))
    else:
        dst.addConstraint(Constr.Coincident(toTarget, origin))


rx_exp = re.compile(r'Constraints\[([0-9]+)\]')


def _re_index_expressions(exp: str, start: int) -> str:
    return rx_exp.sub(lambda x: f'Constraints[{start + int(x.group(1))}]', exp)
