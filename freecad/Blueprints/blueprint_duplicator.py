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
    NamedEquals = dict[str, int]


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
    namedEquals:
        Dictionary with `{constraint-name: constraint-id}` mapping (or empty).
        If provided, constraints with the same name will create an
        equals-constraint instead of duplicating the source constraint.
        Dictionary is populated with new entries during processing.
        You can store and reuse the result after `copyTo`.
    '''
    placement: 'Vector|None'
    constrainTo: 'GeoRef|None'
    allowRotate: bool
    namedEquals: 'NamedEquals'  # use empty dict to ignore

    def copyTo(self, dst: 'Sketch', *, src: 'Sketch') -> None:
        ''' Copy a sketch from one document to another. '''
        _validate(src)

        # where newly created geo ids start
        # used to group everything which was created by this process
        initial_geoid = dst.GeometryCount

        # check if sketch contains references on any of the axes
        # override original axis (if necessary) to allow translation
        axis = _createArtificialAxis(dst, self.placement, _axisUsage(src))

        # after (potential) artificial axis but before copying geometry!
        shifter = IdShifter(dst, axis, self.namedEquals)
        _copy_geometry(src, dst, self.placement)
        _copy_constraints(src, dst, shifter)
        _copy_expressions(src, dst, shifter)

        if self.allowRotate:
            dst.removeAxesAlignment(
                list(range(initial_geoid, dst.GeometryCount)))

        # solve at the end should be sufficient as we dont manipulate geometry
        dst.solve()

        if axis and self.constrainTo:
            _constrain_origin(dst, GeoRef.S(axis.origin), self.constrainTo)


#################################################
# Axis detection
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


#################################################
# Artificial axis creation
#################################################

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


#################################################
# Offset indices for geometry and constraints
#################################################

def _validate_equals(equals: 'NamedEquals', target: 'Sketch') -> 'NamedEquals':
    '''Before processing, verify previous state still points to valid cids.'''
    max_id = target.ConstraintCount
    # We COULD remove only invalid cid's and keep a valid-only subset.
    # But I am not sure what consequences that will have.
    # Its safer to destroy the whole state, so user may notice it earlier.
    for expected_name, cid in equals.items():
        if cid >= max_id:
            equals.clear()  # use `clear` to keep `prev_state` of caller active
            break
        actual = target.Constraints[cid].Name
        if actual != expected_name and not actual.startswith(expected_name):
            equals.clear()
            break
    return equals


@dataclass
class IdShifter:
    '''
    - Offset all geo-ids for newly added constraints.
    - Replace original axis with artificial axis (if any).
    - Rename named constraints to avoid duplicates.
    - Reindex all referenced ids in expressions.
    '''
    geoid_start: int
    cid_start: int
    name_map: dict[str, str]  # renamed constraints: `{old-name: new-name}`

    def __init__(
        self,
        target: 'Sketch',
        axis: ArtificialAxis | None,
        equals: 'NamedEquals',
    ) -> None:
        self.geoid_start = target.GeometryCount
        self.cid_start = target.ConstraintCount
        self._existing_names = {x.Name for x in target.Constraints} - {''}
        self.name_map = {}
        self.named_equals = _validate_equals(equals, target)

        if axis:
            def fn(geoid: int, _pos: int) -> int:
                if geoid >= 0:  # normal geometry
                    return self.geoid_start + geoid
                if geoid == GeoId.HAxis:
                    return axis.origin if _pos == PointPos.start else axis.h
                if geoid == GeoId.VAxis:
                    return axis.v
                return geoid
        else:  # use original axis
            def fn(geoid: int, _pos: int) -> int:
                if geoid >= 0:  # normal geometry
                    return self.geoid_start + geoid
                return geoid
        self.shift_index = fn

    def shift_name(self, name: str) -> str:
        ''' Map "name" to "name_2", etc. Does nothing if `name` empty. '''
        if name in self._existing_names:
            for suffix in range(2, 999):
                new_name = f'{name}_{suffix}'
                if new_name not in self._existing_names:
                    self.name_map[name] = new_name
                    self._existing_names.add(new_name)
                    return new_name
        return name

    def can_equalize_name(self, index: int, name: str) -> 'int|None':
        ''' Either gets previous constraint-id or stores cid for next use. '''
        if name:
            # Called regardless if `named_equals` is provided or not.
            # But an empty input dict will never run into this return branch.
            if (prev_cid := self.named_equals.get(name)) is not None:
                return prev_cid  # subsequent copies
            # `cid_start` offset is the magic here. The first copy stores the
            # offset, while subsequent copies use the offset of the first copy.
            self.named_equals[name] = self.cid_start + index  # first copy
        return None

    def reindex(self, exp: str) -> str:
        ''' Shift indices for indexed- and named- constraints. '''
        return rx_expr.sub(self._reindex_both, exp)

    def _reindex_both(self, match: re.Match) -> str:
        ''' input: `Constraints[<000>]` or `.Constraints.<Name>` '''
        cid, name = match.groups()  # matches either, not both
        if cid:  # a string, so even "0" is not False
            return f'Constraints[{self.cid_start + int(cid)}]'
        if name:
            return '.Constraints.' + self.name_map.get(name, name)
        return match.group(0)  # fallback to original string


rx_expr = re.compile(r'Constraints\[([0-9]+)\]|\.Constraints\.([a-zA-Z_]\w*)')


#################################################
# Duplicator methods
#################################################

def _copy_geometry(src: 'Sketch', dst: 'Sketch', toPos: 'Vector|None') -> None:
    ''' Duplicate geometry. Translate geometry by `toPos` vector. '''
    if toPos:
        dst.addGeometry([moveTo(toPos, geo) for geo in src.Geometry])
    else:
        dst.addGeometry(src.Geometry)  # else, copy whole list verbatim


def _copy_constraints(src: 'Sketch', dst: 'Sketch', shiftr: IdShifter) -> None:
    ''' Duplicate constraints. Indices shifted according to `IdShifter`. '''
    con_list = []
    for i, con in enumerate(src.Constraints):
        con.First = shiftr.shift_index(con.First, con.FirstPos)

        # if `namedEquals`, replace with equals constraint
        if (prev_cid := shiftr.can_equalize_name(i, con.Name)) is not None:
            prev_con = dst.Constraints[prev_cid]
            shiftr.name_map[con.Name] = prev_con.Name  # name could be shifted
            con_list.append(Constr.Equal(prev_con.First, con.First))
            continue

        if con.Second != GeoId.Undef:
            con.Second = shiftr.shift_index(con.Second, con.SecondPos)
        if con.Third != GeoId.Undef:
            con.Third = shiftr.shift_index(con.Third, con.ThirdPos)
        con.Name = shiftr.shift_name(con.Name)
        con_list.append(con)
    dst.addConstraint(con_list)
    # dst.solve()  # no need, done at the end


def _copy_expressions(src: 'Sketch', dst: 'Sketch', shiftr: IdShifter) -> None:
    ''' Duplicate expressions. Indices shifted according to `IdShifter`. '''
    for field, val in src.ExpressionEngine:
        if field.startswith(('Constraints[', '.Constraints.')):
            dst.setExpression(shiftr.reindex(field), shiftr.reindex(val))
        else:
            Notify.Log.err(f'Unhandled expr variant: "{field}". '
                           'Please report this error on GitHub.')


def _constrain_origin(dst: 'Sketch', origin: GeoRef, toTarget: GeoRef) -> None:
    if toTarget.pos == PointPos.none:
        dst.addConstraint(Constr.PointOnObject(origin, toTarget.geoid))
    else:
        dst.addConstraint(Constr.Coincident(toTarget, origin))
