from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF
import math

class TacticalArrowPainter:
    """
    THE TACTICIAN: Draws professional military-grade arrows.
    Used for movement paths, attack vectors, and mission objectives.
    """
    
    @staticmethod
    def draw_arrow(painter, start_pos, end_pos, color, width=3, style=Qt.SolidLine, double_headed=False):
        """
        Draws a tactical arrow from start to end.
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(color), width, style)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        # 1. THE SHAFT
        painter.drawLine(start_pos, end_pos)
        
        # 2. THE HEAD(S)
        TacticalArrowPainter._draw_head(painter, start_pos, end_pos, color, width)
        if double_headed:
            TacticalArrowPainter._draw_head(painter, end_pos, start_pos, color, width)
            
        painter.restore()

    @staticmethod
    def _draw_head(painter, start, end, color, width):
        """Internal helper to draw the triangle at the end of a line."""
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        head_size = width * 4
        
        # Calculate points for a sharp tactical triangle
        p1 = end
        p2 = QPointF(end.x() - head_size * math.cos(angle - math.pi/6),
                    end.y() - head_size * math.sin(angle - math.pi/6))
        p3 = QPointF(end.x() - head_size * math.cos(angle + math.pi/6),
                    end.y() - head_size * math.sin(angle + math.pi/6))
        
        poly = QPolygonF([p1, p2, p3])
        
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)

    @staticmethod
    def draw_curved_arrow(painter, points, color, width=3, style=Qt.SolidLine):
        """
        Draws a tactical arrow following a series of points (a path).
        """
        if len(points) < 2: return
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(color, width, style)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        path = QPainterPath()
        path.moveTo(points[0])
        
        for i in range(1, len(points)):
            path.lineTo(points[i])
            
        painter.drawPath(path)
        
        # Draw the head at the final point
        TacticalArrowPainter._draw_head(painter, points[-2], points[-1], color, width)
        
        painter.restore()
