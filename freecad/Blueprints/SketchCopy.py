'''
Code related to copying geometry from one Sketch to another.
'''
from .helper.constraints import Constr
from .helper.geodraw import Draw, moveTo
from .helper.georef import GeoId, GeoRef
from .helper.notify import Notify
from .SketchTargetConf import SketchTargetConf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from FreeCAD import Vector


def _validate(sketch: 'Sketch') -> None:
    ''' Ensure sketch is well-structured to avoid common mistakes. '''
    if Constr.any(sketch.Constraints, GeoId.isExt):
        Notify.warn('External reference found',
                    'Blueprints cannot have references on external geometry.')


def duplicateSketch(src: 'Sketch', dst: 'Sketch', conf: SketchTargetConf) \
        -> None:
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
        _V, _H = _createArtificialAxes(dst, conf.placement)
    else:
        _V, _H = GeoId.HAxis, GeoId.VAxis

    # after (potential) artificial axis
    # used to fix references when importing from other sketch
    geoid_offset, cid_offset = dst.GeometryCount, dst.ConstraintCount

    _copy_geometry(src, dst, toPos=conf.placement)
    _copy_constraints(src, dst, geoid_start=geoid_offset, h_axis=_H, v_axis=_V)
    _copy_expressions(src, dst, cid_start=cid_offset)

    if conf.allowRotate:
        dst.removeAxesAlignment(list(range(initial_geoid, dst.GeometryCount)))

    # a single solve at the end should be enough as we dont manipulate geometry
    dst.solve()

    if hasArtificialAxis and conf.constrainTo:
        _constrain_origin(dst, origin=GeoRef.S(_H), toTarget=conf.constrainTo)


############################################################
# Helper methods
############################################################

def _createArtificialAxes(sketch: 'Sketch', toPos: 'Vector|None') \
        -> tuple[int, int]:
    '''
    Create artificial axis to allow translation.
    Returns geo-ids for artificial axis `(vertical, horizontal)` (both lines)
    '''
    # TODO: use minimal axis OR expand axis to sketch bounds?
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
        con_list.append(con)
    dst.addConstraint(con_list)
    # dst.solve()  # no need, done at the end


def _copy_expressions(src: 'Sketch', dst: 'Sketch', cid_start: int) -> None:
    ''' Duplicate expressions. Offset constraint indices by `cid_start`. '''
    for field, val in src.ExpressionEngine:
        if field.startswith('Constraints['):
            new_index = int(field.removesuffix(']')[12:]) + cid_start
            dst.setExpression(f'Constraints[{new_index}]', val)
        else:
            Notify.Log.err(f'Unhandled expr variant: "{field}". '
                           'Please report this error on GitHub.')


def _constrain_origin(dst: 'Sketch', origin: GeoRef, toTarget: GeoRef) -> None:
    if toTarget.pos == 0:
        dst.addConstraint(Constr.PointOnObject(origin, toTarget.geoid))
    else:
        dst.addConstraint(Constr.Coincident(toTarget, origin))
