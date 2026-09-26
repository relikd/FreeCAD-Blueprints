'''
Code related to geometry contraint editing (mostly creation)
'''
import math  # pi

from Sketcher import Constraint as _C

from .georef import GeoRef

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


def _rad(deg: float) -> float:
    ''' Degrees to radians '''
    return deg * math.pi / 180


class Constr:
    @staticmethod
    def any(constraints: list[_C], matches: 'Callable[[int], bool]') -> bool:
        for con in constraints:
            if matches(con.First) or matches(con.Second) or matches(con.Third):
                return True
        return False

    # https://wiki.freecad.org/Sketcher_ConstrainCoincident
    @staticmethod  # 1
    def Coincident(fixed: GeoRef, move: GeoRef) -> _C:
        ''' Between two points (sets `move` onto `fixed`) '''
        return _C('Coincident', fixed.geoid, fixed.pos, move.geoid, move.pos)

    # https://wiki.freecad.org/Sketcher_ConstrainHorizontal
    class Horizontal:  # 2
        @staticmethod
        def Line(geoid: int) -> _C:
            return _C('Horizontal', geoid)

        @staticmethod
        def Points(a: GeoRef, b: GeoRef) -> _C:
            return _C('Horizontal', a.geoid, a.pos, b.geoid, b.pos)

    # https://wiki.freecad.org/Sketcher_ConstrainVertical
    class Vertical:  # 3
        @staticmethod
        def Line(geoid: int) -> _C:
            return _C('Vertical', geoid)

        @staticmethod
        def Points(a: GeoRef, b: GeoRef) -> _C:
            return _C('Vertical', a.geoid, a.pos, b.geoid, b.pos)

    # https://wiki.freecad.org/Sketcher_ConstrainParallel
    @staticmethod  # 4
    def Parallel(cidA: int, cidB: int) -> _C:
        return _C('Parallel', cidA, cidB)

    # https://wiki.freecad.org/Sketcher_ConstrainTangent
    class Tangent:  # 5
        @staticmethod
        def Lines(cidA: int, cidB: int) -> _C:
            ''' Direct tangency '''
            return _C('Tangent', cidA, cidB)

        @staticmethod
        def Points(a: GeoRef, b: GeoRef) -> _C:
            ''' Point-to-point tangency '''
            return _C('Tangent', a.geoid, a.pos, b.geoid, b.pos)

        @staticmethod
        def PointLine(a: GeoRef, cidB: int) -> _C:
            ''' Point-to-curve tangency '''
            return _C('Tangent', a.geoid, a.pos, cidB)

        @staticmethod
        def ViaPoint(cidA: int, cidB: int, pt: GeoRef) -> _C:
            ''' Tangent-via-point (helpers are not added automatically) '''
            return _C('TangentViaPoint', cidA, cidB, pt.geoid, pt.pos)

    # https://wiki.freecad.org/Sketcher_ConstrainDistance
    class Distance:  # 6
        @staticmethod
        def Line(geoid: int, *, length: float) -> _C:
            ''' Distance between start and end point '''
            return _C('Distance', geoid, length)

        @staticmethod
        def Points(a: GeoRef, b: GeoRef, *, length: float) -> _C:
            ''' Distance between points '''
            return _C('Distance', a.geoid, a.pos, b.geoid, b.pos, length)

    # https://wiki.freecad.org/Sketcher_ConstrainDistanceX
    class DistanceX:  # 7
        @staticmethod
        def Line(geoid: int, *, length: float) -> _C:
            ''' Horizontal distance between start and end point '''
            return _C('DistanceX', geoid, length)

        @staticmethod
        def Points(a: GeoRef, b: 'GeoRef|None' = None, *, length: float) -> _C:
            ''' If `b = None`, sets distance from Y-axis '''
            if b:
                return _C('DistanceX', a.geoid, a.pos, b.geoid, b.pos, length)
            return _C('DistanceX', a.geoid, a.pos, length)

    # https://wiki.freecad.org/Sketcher_ConstrainDistanceY
    class DistanceY:  # 8
        @staticmethod
        def Line(geoid: int, *, length: float) -> _C:
            ''' Vertical distance between start and end point '''
            return _C('DistanceY', geoid, length)

        @staticmethod
        def Points(a: GeoRef, b: 'GeoRef|None' = None, *, length: float) \
                -> _C:
            ''' If `b = None`, sets distance from X-axis '''
            if b:
                return _C('DistanceY', a.geoid, a.pos, b.geoid, b.pos, length)
            return _C('DistanceY', a.geoid, a.pos, length)

    # https://wiki.freecad.org/Sketcher_ConstrainAngle
    class Angle:  # 9
        @staticmethod
        def Line(cidA: int, *, deg: float) -> _C:
            return _C('Angle', cidA, _rad(deg))

        @staticmethod
        def Lines(cidA: int, cidB: int, *, deg: float) -> _C:
            return _C('Angle', cidA, cidB, _rad(deg))

        @staticmethod
        def Points(a: GeoRef, b: GeoRef, *, deg: float) -> _C:
            return _C('Angle', a.geoid, a.pos, b.geoid, b.pos, _rad(deg))

        @staticmethod
        def ViaPoint(cidA: int, cidB: int, pt: GeoRef, *, deg: float) -> _C:
            '''Angle-via-point (helpers are not added automatically)'''
            return _C('AngleViaPoint', cidA, cidB, pt.geoid, pt.pos, _rad(deg))

    # https://wiki.freecad.org/Sketcher_ConstrainPerpendicular
    class Perpendicular:  # 10
        @staticmethod
        def Lines(cidA: int, cidB: int) -> _C:
            ''' Direct perpendicularity '''
            return _C('Perpendicular', cidA, cidB)

        @staticmethod
        def Points(a: GeoRef, b: GeoRef) -> _C:
            ''' Point-to-point perpendicularity '''
            return _C('Perpendicular', a.geoid, a.pos, b.geoid, b.pos)

        @staticmethod
        def PointLine(a: GeoRef, cidB: int) -> _C:
            ''' Point-to-curve perpendicularity '''
            return _C('Perpendicular', a.geoid, a.pos, cidB)

        @staticmethod
        def ViaPoint(cidA: int, cidB: int, pt: GeoRef) -> _C:
            '''Perpendicular-via-point (helpers are not added automatically)'''
            return _C('PerpendicularViaPoint', cidA, cidB, pt.geoid, pt.pos)

    # https://wiki.freecad.org/Sketcher_ConstrainRadius
    @staticmethod  # 11
    def Radius(geoid: int, *, radius: float) -> _C:
        return _C('Radius', geoid, radius)

    # https://wiki.freecad.org/Sketcher_ConstrainEqual
    @staticmethod  # 12
    def Equal(cidA: int, cidB: int) -> _C:
        return _C('Equal', cidA, cidB)

    # https://wiki.freecad.org/Sketcher_ConstrainPointOnObject
    @staticmethod  # 13
    def PointOnObject(point: GeoRef, line: int) -> _C:
        ''' Fixes points on edges or axes '''
        return _C('PointOnObject', point.geoid, point.pos, line)

    # https://wiki.freecad.org/Sketcher_ConstrainSymmetric
    class Symmetric:  # 14
        @staticmethod
        def PointsLine(a: GeoRef, b: GeoRef, cidS: int) -> _C:
            ''' Two points and a symmetry line '''
            return _C('Symmetric', a.geoid, a.pos, b.geoid, b.pos, cidS)

        @staticmethod
        def PointsPoint(a: GeoRef, b: GeoRef, s: GeoRef) -> _C:
            ''' Two points and a symmetry point '''
            return _C('Symmetric', a.geoid, a.pos, b.geoid, b.pos, s.geoid, s.pos)

        @staticmethod
        def LinePoint(line: int, s: GeoRef) -> _C:
            ''' A line and a symmetry point '''
            return _C('Symmetric', line, 1, line, 2, s.geoid, s.pos)

    # InternalAlignment = 15
    # SnellsLaw = 16

    # https://wiki.freecad.org/Sketcher_ConstrainBlock
    @staticmethod  # 17
    def Block(geoid: int) -> _C:
        ''' blocks edges in place with a single constraint '''
        return _C('Block', geoid)

    # https://wiki.freecad.org/Sketcher_ConstrainDiameter
    @staticmethod  # 18
    def Diameter(geoid: int, *, diameter: float) -> _C:
        return _C('Diameter', geoid, diameter)

    # Weight = 19

    # @staticmethod  # 20
    # def Group(cids: list[int]) -> _C:
    #     return _C('Group', cids)

    # Text = 21
