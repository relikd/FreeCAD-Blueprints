'''
Code related to copying geometry from one Sketch to another.
'''
import re
from dataclasses import dataclass

from .helper.constraints import Constr
from .helper.geodraw import Draw, moveTo
from .helper.georef import GeoId, GeoRef, PointPos
from .helper.notify import Notify
from .helper.utils import default_props

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from FreeCAD import Vector, DocumentObject as DocObj
    from Part import Geometry
    NamedEquals = dict[str, str]
    ExternalExpressionsDict = dict[str, tuple[DocObj, str]]
    ExternalExpressionsRepl = dict[str, str]


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
    hideUnnamed:
        If enabled, set virtual space for all constraints except named ones.
    namedEquals:
        Dictionary with `{original-name: first-copy-name}` (or empty).
        If provided, subsequent copies will create equals-constraints on the
        first copy (named constraints only). Parameter is populated with new
        entries during processing. Store and reuse the result after `copyTo`.
    '''
    placement: 'Vector|None'
    constrainTo: 'GeoRef|None'
    allowRotate: bool
    hideUnnamed: bool
    namedEquals: 'NamedEquals'  # use empty dict to ignore
    externalExpressions: 'ExternalExpressionsRepl'

    def copyTo(self, dst: 'Sketch', *, src: 'Sketch') -> None:
        ''' Copy a sketch from one document to another. '''
        _validate(src)

        # where newly created geo ids start
        # used to group everything which was created by this process
        geoid_0, cid_0 = dst.GeometryCount, dst.ConstraintCount

        # check if sketch contains references on any of the axes
        # override original axis (if necessary) to allow translation
        axis = _createArtificialAxis(dst, self.placement, _axisUsage(src))

        # after (potential) artificial axis but before copying geometry!
        shifter = IdShifter(dst, axis, self.namedEquals)
        _copy_geometry(src, dst, self.placement)
        _copy_constraints(src, dst, shifter)
        _copy_expressions(src, dst, shifter, self.externalExpressions)

        # TODO: don't hide equal-names constraints
        # - If `allowRotate`, then `hideUnnamed`:
        #   all cid's in `name_to_id` will be invalid.
        # - If `hideUnnamed`, then `allowRotate`:
        #   the latter will create new constraints, which are not hidden.
        # - There is no reliable way to get a cid before-after mapping.
        #   Constraint names can't be edited after committing `addConstraint`.
        #   And we really don't want to create unnecessary names.

        if self.allowRotate:
            # this changes existing constraints, be careful with cid references
            # `_constrain_origin` is unaffected but `name_to_id` may invalidate
            dst.removeAxesAlignment(list(range(geoid_0, dst.GeometryCount)))

        if self.hideUnnamed:
            # before `_constrain_origin` to keep that constraint visible
            dst.setVirtualSpace([
                i for i in range(cid_0, dst.ConstraintCount)
                if not dst.Constraints[i].Name], True)

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
    is_first_copy: bool  # whether or not a `prev_state` was provided
    name_to_name: dict[str, str]  # `{original-name: new-name}`
    name_to_id: dict[str, int]  # `{original-name: absolute constraint-id}`

    def __init__(
        self,
        target: 'Sketch',
        axis: ArtificialAxis | None,
        equals: 'NamedEquals',
    ) -> None:
        self.geoid_start = target.GeometryCount
        self.cid_start = target.ConstraintCount
        self._existing_names = {x.Name for x in target.Constraints} - {''}
        self.name_to_name = {}
        self.name_to_id = {}

        # validate if (potetially shifted) names still exist.
        if set(equals.values()) - {con.Name for con in target.Constraints}:
            # We COULD keep valid refs but it's safer to destroy whole state
            equals.clear()  # use `clear` to update `prev_state` of caller

        self.named_equals = equals
        self.is_first_copy = not equals

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

    def _next_name(self, name: str) -> str:
        ''' Map "name" to "name_2", etc. Does nothing if `name` empty. '''
        if name in self._existing_names:
            for suffix in range(2, 999):
                new_name = f'{name}_{suffix}'
                if new_name not in self._existing_names:
                    self.name_to_name[name] = new_name
                    self._existing_names.add(new_name)
                    return new_name
        return name

    def shift_name(self, index: int, name: str) -> str:
        ''' Auto-increment constraint name and update `prev_state`. '''
        if name:
            if self.is_first_copy:
                new_name = self._next_name(name)
                self.named_equals[name] = new_name
                return new_name
            # subsequent copies:
            if prev_name := self.named_equals.get(name):
                self.name_to_name[name] = prev_name
                self.name_to_id[name] = self.cid_start + index
                # Named equals are replaced with indexed constraints.
                # A new calculated "equals" expression is created afterwards.
                return ''
        return name

    def reindex(self, exp: str) -> str:
        ''' Shift indices for indexed- and named- constraints. '''
        return rx_expr.sub(self._reindex_both, exp)

    def _reindex_both(self, match: re.Match) -> str:
        ''' input: `Constraints[<000>]` or `.Constraints.<Name>` '''
        cid, name = match.groups()  # matches either, not both
        if cid:  # a string, so even "0" is not False
            return f'Constraints[{self.cid_start + int(cid)}]'
        if name:
            # all subsequent copies are indexed
            if (indexed := self.name_to_id.get(name)) is not None:
                return f'Constraints[{indexed}]'
            # first copy is only renamed
            if new_name := self.name_to_name.get(name):
                return '.Constraints.' + new_name
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
        if con.Second != GeoId.Undef:
            con.Second = shiftr.shift_index(con.Second, con.SecondPos)
        if con.Third != GeoId.Undef:
            con.Third = shiftr.shift_index(con.Third, con.ThirdPos)
        if con.Name:
            con.Name = shiftr.shift_name(i, con.Name)
        con_list.append(con)
    dst.addConstraint(con_list)
    # dst.solve()  # no need, done at the end


def _copy_expressions(
    src: 'Sketch', dst: 'Sketch', shiftr: IdShifter,
    extExprMap: 'ExternalExpressionsRepl',
) -> None:
    ''' Duplicate expressions. Indices shifted according to `IdShifter`. '''
    for field, expr_str in src.ExpressionEngine:
        if field.startswith(('Constraints[', '.Constraints.')):
            new_expr = shiftr.reindex(expr_str)
            if extExprMap:
                # TODO: remove expression for plain-num expressions
                new_expr = rx_ext_expr.sub(lambda x, with_end=new_expr + ' ':
                    repl if (repl := extExprMap.get(x.group())) is not None
                    and with_end[x.end()] != '(' else x.group(),
                    new_expr)
            dst.setExpression(shiftr.reindex(field), new_expr)
        else:
            Notify.Log.err(f'Unhandled expr variant: "{field}". '
                           'Please report this error on GitHub.')

    # create (or overwrite) expression for all named expressions
    # set "equals" expression on first-copy constraint (by name)
    for name, idx in shiftr.name_to_id.items():
        dst.setExpression(f'Constraints[{idx}]',  # newly created after reindex
                          '.Constraints.' + shiftr.name_to_name[name])


def _constrain_origin(dst: 'Sketch', origin: GeoRef, toTarget: GeoRef) -> None:
    if toTarget.pos == PointPos.none:
        dst.addConstraint(Constr.PointOnObject(origin, toTarget.geoid))
    else:
        dst.addConstraint(Constr.Coincident(toTarget, origin))


#################################################
# External expressions
#################################################

rx_ext_expr = re.compile(r'[a-zA-Z0-9_.<>]+')


def detect_external(src: 'Sketch') -> 'ExternalExpressionsDict':
    '''
    Detect if expression engine uses any external references like VarSet.
    Where object is either `Sketch` or `VarSet` (use `getPropertyByName()`).

    Returns: `{expr-substring: (object, property-name)}`.
    '''
    rv: ExternalExpressionsDict = {}

    # find actually used references
    concat = '|'.join(expr for _, expr in src.ExpressionEngine) + '|'
    used = {x.group() for x in rx_ext_expr.finditer(concat)
            if concat[x.end()] != '('}  # excluding "name()" (command calls)

    # find potentially referencable props
    v_ignore, s_ignore = default_props('App::VarSet', 'Sketcher::SketchObject')

    # sketch properties
    sk_props = set(src.PropertiesList) - s_ignore
    for prop in used.intersection(sk_props | {'.' + x for x in sk_props}):
        rv[prop] = (src, prop.removeprefix('.'))

    # VarSets
    for varset in src.Document.findObjects('App::VarSet'):
        var_props = set(varset.PropertiesList) - v_ignore
        for prop in used.intersection({n for x in var_props for n in (
                f'{varset.Name}.{x}', f'<<{varset.Label}>>.{x}')}):
            rv[prop] = (varset, prop.split('.', 1)[1])

    return rv
