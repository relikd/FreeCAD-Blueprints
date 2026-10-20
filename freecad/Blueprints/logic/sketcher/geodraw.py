'''
Code related to geometry manipulation (mostly creation / manually drawing)
'''
from FreeCAD import Vector
from Part import LineSegment, Point, Circle


class Draw:
    @staticmethod
    def point(x: float, y: float) -> Point:
        return Point(Vector(x, y))

    @staticmethod
    def line(x1: float, y1: float, x2: float, y2: float) -> LineSegment:
        return LineSegment(Vector(x1, y1), Vector(x2, y2))

    @staticmethod
    def circle(cx: float, cy: float, radius: float) -> Circle:
        return Circle(Vector(cx, cy), Vector(0, 0, 1), radius)
