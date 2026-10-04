'''
Code related to copying geometry from one Sketch to another.
'''
import re
from dataclasses import dataclass

from .helper.constraints import Constr
from .helper.geodraw import Draw, moveTo
from .helper.georef import GeoId, GeoRef, PointPos
from .helper.notify import Notify

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from FreeCAD import Vector
    from Part import Geometry


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
        _validate(src)

        # where newly created geo ids start
        # used to group everything which was created by this process
        initial_geoid = dst.GeometryCount

        # check if sketch contains references on any of the axes
        # override original axis (if necessary) to allow translation
        axis = _createArtificialAxis(dst, self.placement, _axisUsage(src))

        # after (potential) artificial axis
        # used to fix references when importing from other sketch
        geoid_offset, cid_offset = dst.GeometryCount, dst.ConstraintCount

        _copy_geometry(src, dst, self.placement)
        name_map = _copy_constraints(src, dst, geoid_offset, axis)
        _copy_expressions(src, dst, cid_offset, name_map)

        if self.allowRotate:
            dst.removeAxesAlignment(
                list(range(initial_geoid, dst.GeometryCount)))

        # solve at the end should be sufficient as we dont manipulate geometry
        dst.solve()

        if axis and self.constrainTo:
            _constrain_origin(dst, GeoRef.S(axis.origin), self.constrainTo)


#################################################
# Helper methods
#################################################

class ReferencedAxis(NamedTuple):
    v: bool
    h: bool
    origin: bool


def _axisUsage(sketch: 'Sketch') -> ReferencedAxis:
    ''' Check whether sketch references `(VAxis, HAxis, RtPnt)`. '''
    v, h, origin = False, False, False
    for con in sketch.Constraints:
        for geo, pos in (
            (con.First, con.FirstPos),
            (con.Second, con.SecondPos),
            (con.Third, con.ThirdPos),
        ):
            if geo == GeoId.VAxis:
                v = True
            elif geo == GeoId.HAxis:
                if pos == PointPos.start:
                    origin = True
                else:
                    h = True
        if v and h:  # origin not relevant. h is used as origin
            return ReferencedAxis(True, True, True)  # break early
    return ReferencedAxis(v, h, origin)


class ArtificialAxis(NamedTuple):
    v: int
    h: int
    origin: int


def _createArtificialAxis(
    sketch: 'Sketch', toPos: 'Vector|None', axis: ReferencedAxis,
) -> 'ArtificialAxis|None':
    '''
    Create artificial axis to allow translation.
    Returns `None`, if default axis should be used (no axis reference found).
    '''
    if not any(axis):
        return None

    def fn(geo: 'Geometry') -> int:
        # all are created as construction geometry ("True")
        return sketch.addGeometry(moveTo(toPos, geo), True)  # type: ignore[return-value]

    if not axis.h and not axis.v:
        return ArtificialAxis(GeoId.VAxis, GeoId.HAxis, fn(Draw.point(0, 0)))

    axis_len = 1
    v = fn(Draw.line(0, 0, 0, axis_len)) if axis.v else GeoId.VAxis
    h = fn(Draw.line(0, 0, axis_len, 0)) if axis.h else GeoId.HAxis

    # add constraints
    cons = []
    if axis.h:
        cons.extend([
            Constr.Distance.Line(h, length=axis_len),
            Constr.Horizontal.Line(h),
        ])
    if axis.v:
        cons.append(Constr.Distance.Line(v, length=axis_len))
        if axis.h:
            # if rotation is enabled, this will reduce one constraint
            cons.append(Constr.Perpendicular.Lines(v, h))
        else:
            cons.append(Constr.Vertical.Line(v))
    if axis.h and axis.v:
        cons.append(Constr.Coincident(GeoRef.S(h), GeoRef.S(v)))

    sketch.setVirtualSpace(sketch.addConstraint(cons), True)  # hide from user
    # sketch.solve()  # no need, done at the end
    return ArtificialAxis(v, h, origin=h if axis.h else v)


def _copy_geometry(src: 'Sketch', dst: 'Sketch', toPos: 'Vector|None') -> None:
    ''' Duplicate geometry. Translate geometry by `toPos` vector. '''
    if toPos:
        dst.addGeometry([moveTo(toPos, geo) for geo in src.Geometry])
    else:
        dst.addGeometry(src.Geometry)  # else, copy whole list verbatim


def _copy_constraints(
    src: 'Sketch', dst: 'Sketch', geoid_start: int,
    axis: 'ArtificialAxis|None',
) -> dict[str, str]:
    '''
    Duplicate constraints. Offset geo-ids by `geoid_start`.
    Replace original axes with `h_axis` and `v_axis` respectively.
    (use `h_axis=GeoId.HAxis, v_axis=GeoId.VAxis` if no artificial axes exist)

    Returns mapping for renamed constraints: `{old-name: new-name}`.
    '''
    if axis:
        def shift_index(geoid: int, _pos: int) -> int:
            if geoid >= 0:  # normal geometry
                return geoid_start + geoid
            if geoid == GeoId.HAxis:
                return axis.origin if _pos == PointPos.start else axis.h
            if geoid == GeoId.VAxis:
                return axis.v
            return geoid
    else:  # use original axis
        def shift_index(geoid: int, _pos: int) -> int:
            if geoid >= 0:  # normal geometry
                return geoid_start + geoid
            return geoid

    rv = {}
    existing_names = {x.Name for x in dst.Constraints} - {''}

    def shift_name(name: str) -> str:
        for suffix in range(2, 999):
            new_name = f'{name}_{suffix}'
            if new_name not in existing_names:
                rv[name] = new_name
                existing_names.add(new_name)
                return new_name
        return name

    con_list = []
    for con in src.Constraints:
        con.First = shift_index(con.First, con.FirstPos)
        if con.Second != GeoId.Undef:
            con.Second = shift_index(con.Second, con.SecondPos)
        if con.Third != GeoId.Undef:
            con.Third = shift_index(con.Third, con.ThirdPos)
        if con.Name in existing_names:
            con.Name = shift_name(con.Name)
        con_list.append(con)
    dst.addConstraint(con_list)
    # dst.solve()  # no need, done at the end
    return rv


def _copy_expressions(
    src: 'Sketch', dst: 'Sketch', cid_start: int, name_map: dict[str, str],
) -> None:
    ''' Duplicate expressions. Offset constraint indices by `cid_start`. '''
    for field, val in src.ExpressionEngine:
        if field.startswith(('Constraints[', '.Constraints.')):
            dst.setExpression(
                _re_index_expr(field, cid_start, name_map),
                _re_index_expr(val, cid_start, name_map))
        else:
            Notify.Log.err(f'Unhandled expr variant: "{field}". '
                           'Please report this error on GitHub.')


def _constrain_origin(dst: 'Sketch', origin: GeoRef, toTarget: GeoRef) -> None:
    if toTarget.pos == 0:
        dst.addConstraint(Constr.PointOnObject(origin, toTarget.geoid))
    else:
        dst.addConstraint(Constr.Coincident(toTarget, origin))


rx_expr_indexed = re.compile(r'Constraints\[([0-9]+)\]')
rx_expr_named = re.compile(r'\.Constraints\.([a-zA-Z_]\w*)')


def _re_index_expr(exp: str, start: int, name_map: dict[str, str]) -> str:
    ''' Shift indices for indexed- and named- constraints. '''
    exp = rx_expr_indexed.sub(lambda x:
        f'Constraints[{start + int(x.group(1))}]', exp)
    return rx_expr_named.sub(lambda x:
        '.Constraints.' + name_map.get(x.group(1), x.group(1)), exp)
