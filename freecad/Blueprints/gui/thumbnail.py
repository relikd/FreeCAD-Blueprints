'''
Draw thumbnail from sketch geometry.
'''
from .qt import QtCore, QtGui

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


def sketch_thumbnail(
    sketch: 'Sketch', width: int = 128, height: int = 128, padding: int = 5,
) -> 'QtGui.QPixmap':
    shape = sketch.Shape

    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtGui.QColor(35, 35, 35))

    if shape.isNull() or not shape.Edges:
        return pixmap

    # Convert all edges to polylines
    polylines = []
    points = [(0.0, 0.0)]  # include origin

    for edge in shape.Edges:
        edge_points = edge.discretize(Deflection=0.025)

        if len(edge_points) >= 2:
            polyline = [(p.x, p.y) for p in edge_points]
            polylines.append(polyline)
            points.extend(polyline)

    if not points:
        return pixmap

    # Sketch bounding box
    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)

    model_width = max(max_x - min_x, 1e-9)
    model_height = max(max_y - min_y, 1e-9)

    scale = min(
        (width - 2 * padding) / model_width,
        (height - 2 * padding) / model_height,
    )

    offset_x = (width - model_width * scale) / 2
    offset_y = (height - model_height * scale) / 2

    def map_point(x: float, y: float) -> 'QtCore.QPointF':
        screen_x = offset_x + (x - min_x) * scale
        screen_y = height - offset_y - (y - min_y) * scale  # flipped Y
        return QtCore.QPointF(screen_x, screen_y)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

    pen = QtGui.QPen(QtGui.QColor(235, 235, 235))
    pen.setWidthF(1.5)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

    for polyline in polylines:
        path = QtGui.QPainterPath()
        path.moveTo(map_point(*polyline[0]))

        for point in polyline[1:]:
            path.lineTo(map_point(*point))

        painter.drawPath(path)

    # Draw origin marker
    origin_pen = QtGui.QPen(QtGui.QColor(255, 80, 80))
    origin_pen.setWidthF(1.0)
    painter.setPen(origin_pen)
    painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 80, 80)))
    radius = 3.0
    painter.drawEllipse(map_point(0, 0), radius, radius)

    painter.end()
    pixmap.setDevicePixelRatio(2)
    return pixmap
