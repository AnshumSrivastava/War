from PyQt5.QtGui import QIcon, QPainter, QPen, QBrush, QColor, QPainterPath, QIconEngine, QPixmap
from PyQt5.QtCore import Qt, QSize, QPointF, QRectF

class VectorIconEngine(QIconEngine):
    """
    THE ENGINE: Re-renders the icon on the fly for any requested size.
    Ensures true vector-like responsiveness.
    """
    def __init__(self, icon_type, color="#eeeeee", unit_size=""):
        super().__init__()
        self.icon_type = icon_type
        self.color = color
        self.unit_size = unit_size

    def paint(self, painter, rect, mode, state):
        VectorIconPainter.draw_vector_icon(painter, rect, self.icon_type, self.color, mode, self.unit_size)

    def pixmap(self, size, mode, state):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.paint(painter, QRectF(0, 0, size.width(), size.height()), mode, state)
        painter.end()
        return pixmap

class VectorIconPainter:
    """
    THE ARTIST: Interface to the VectorIconEngine and direct painting.
    """
    @staticmethod
    def create_icon(icon_type, color="#eeeeee", unit_size=""):
        return QIcon(VectorIconEngine(icon_type, color, unit_size))

    @staticmethod
    def draw_vector_icon(painter, rect, icon_type, color="#eeeeee", mode=QIcon.Normal, unit_size=""):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        size = min(rect.width(), rect.height())
        pen = QPen(QColor(color))
        pen.setWidthF(max(1.0, size / 16.0))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        if mode == QIcon.Disabled:
            painter.setOpacity(0.3)
        
        margin = size * 0.15
        draw_rect = QRectF(rect.center().x() - size/2 + margin, 
                           rect.center().y() - size/2 + margin, 
                           size - 2*margin, size - 2*margin)
        
        if icon_type == "cursor":
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.top())
            path.lineTo(draw_rect.right() * 0.8, draw_rect.center().y() + margin)
            path.lineTo(draw_rect.center().x(), draw_rect.center().y() + margin)
            path.lineTo(draw_rect.center().x() + margin, draw_rect.bottom())
            path.lineTo(draw_rect.center().x() - margin, draw_rect.bottom())
            path.lineTo(draw_rect.center().x() - margin, draw_rect.center().y() + margin)
            path.closeSubpath()
            painter.fillPath(path, QBrush(QColor(color)))
            painter.drawPath(path)
            
        elif icon_type == "edit":
            # Pencil Icon
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.bottom())
            path.lineTo(draw_rect.left() + margin, draw_rect.bottom())
            path.lineTo(draw_rect.right(), draw_rect.top() + margin)
            path.lineTo(draw_rect.right() - margin, draw_rect.top())
            path.lineTo(draw_rect.left(), draw_rect.bottom() - margin)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(draw_rect.left() + margin, draw_rect.bottom()), QPointF(draw_rect.left(), draw_rect.bottom() - margin))
            
        elif icon_type == "eraser":
            # 3D Block Eraser
            painter.drawRect(QRectF(draw_rect.left(), draw_rect.center().y(), draw_rect.width(), draw_rect.height()/2))
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y()), QPointF(draw_rect.left() + margin, draw_rect.top()))
            painter.drawLine(QPointF(draw_rect.left() + margin, draw_rect.top()), QPointF(draw_rect.right(), draw_rect.top()))
            painter.drawLine(QPointF(draw_rect.right(), draw_rect.top()), QPointF(draw_rect.right(), draw_rect.center().y()))
            
        elif icon_type == "place_agent":
            # Stylized Soldier/Person
            painter.drawEllipse(QPointF(draw_rect.center().x(), draw_rect.top() + margin), margin, margin)
            path = QPainterPath()
            path.moveTo(draw_rect.center().x() - margin*1.5, draw_rect.bottom())
            path.lineTo(draw_rect.center().x() + margin*1.5, draw_rect.bottom())
            path.lineTo(draw_rect.center().x() + margin, draw_rect.top() + margin*2.5)
            path.lineTo(draw_rect.center().x() - margin, draw_rect.top() + margin*2.5)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif icon_type == "draw_zone":
            # Dashed Region
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRoundedRect(draw_rect, margin, margin)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(QRectF(draw_rect.center().x() - 2, draw_rect.center().y() - 2, 4, 4))
            
        elif icon_type == "paint_tool":
            # Roller / Brush
            painter.drawRect(QRectF(draw_rect.left(), draw_rect.top(), draw_rect.width(), margin*1.5))
            painter.drawLine(draw_rect.center(), QPointF(draw_rect.center().x(), draw_rect.bottom()))
            
        elif icon_type == "draw_path":
            # Winding Path with nodes
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.bottom())
            path.quadTo(draw_rect.center(), QPointF(draw_rect.right(), draw_rect.top()))
            painter.drawPath(path)
            painter.drawEllipse(QPointF(draw_rect.left(), draw_rect.bottom()), 2, 2)
            painter.drawEllipse(QPointF(draw_rect.right(), draw_rect.top()), 2, 2)
            
        elif icon_type == "assign_goal":
            # Target / Crosshair
            painter.drawEllipse(draw_rect.center(), size/3, size/3)
            painter.drawLine(QPointF(draw_rect.center().x(), draw_rect.top()), QPointF(draw_rect.center().x(), draw_rect.bottom()))
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y()), QPointF(draw_rect.right(), draw_rect.center().y()))
            painter.drawEllipse(draw_rect.center(), 2, 2)
            
        elif icon_type == "save":
            painter.drawRect(draw_rect)
            painter.drawRect(QRectF(draw_rect.center().x() - margin, draw_rect.top(), margin*2, margin*1.5))
            
        elif icon_type == "load":
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.bottom())
            path.lineTo(draw_rect.right(), draw_rect.bottom())
            path.lineTo(draw_rect.right(), draw_rect.top() + margin)
            path.lineTo(draw_rect.center().x() + margin, draw_rect.top() + margin)
            path.lineTo(draw_rect.center().x(), draw_rect.top())
            path.lineTo(draw_rect.left(), draw_rect.top())
            path.closeSubpath()
            painter.drawPath(path)
            
        elif icon_type == "undo":
            path = QPainterPath()
            path.arcTo(draw_rect, 0, 220)
            painter.drawPath(path)
            # Arrow head
            painter.drawLine(QPointF(draw_rect.right(), draw_rect.center().y()), QPointF(draw_rect.right() + margin/2, draw_rect.center().y() - margin/2))
            
        elif icon_type == "redo":
            path = QPainterPath()
            path.arcTo(draw_rect, 180, -220)
            painter.drawPath(path)
            # Arrow head
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y()), QPointF(draw_rect.left() - margin/2, draw_rect.center().y() - margin/2))

        elif icon_type == "new_file":
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.top())
            path.lineTo(draw_rect.right() - margin, draw_rect.top())
            path.lineTo(draw_rect.right(), draw_rect.top() + margin)
            path.lineTo(draw_rect.right(), draw_rect.bottom())
            path.lineTo(draw_rect.left(), draw_rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(draw_rect.right() - margin, draw_rect.top()), QPointF(draw_rect.right() - margin, draw_rect.top() + margin))
            painter.drawLine(QPointF(draw_rect.right() - margin, draw_rect.top() + margin), QPointF(draw_rect.right(), draw_rect.top() + margin))

        elif icon_type == "settings":
            painter.drawEllipse(draw_rect.center(), size/4, size/4)
            for i in range(8):
                painter.save()
                painter.translate(draw_rect.center())
                painter.rotate(i * 45)
                painter.drawRect(QRectF(-margin/4, -size/2 + margin/4, margin/2, margin/2))
                painter.restore()

        elif icon_type == "trash":
            painter.drawRect(QRectF(draw_rect.left() + margin/2, draw_rect.top() + margin, draw_rect.width() - margin, draw_rect.height() - margin))
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.top() + margin), QPointF(draw_rect.right(), draw_rect.top() + margin))
            painter.drawRect(QRectF(draw_rect.center().x() - margin, draw_rect.top(), margin*2, margin))

        elif icon_type == "help":
            painter.drawArc(QRectF(draw_rect.left(), draw_rect.top(), draw_rect.width(), draw_rect.height()/2), 0, 180 * 16)
            painter.drawLine(QPointF(draw_rect.right(), draw_rect.center().y()), QPointF(draw_rect.center().x(), draw_rect.center().y()))
            painter.drawLine(QPointF(draw_rect.center().x(), draw_rect.center().y()), QPointF(draw_rect.center().x(), draw_rect.bottom() - margin))
            painter.drawEllipse(draw_rect.center(), 1.0, 1.0)
            
        elif icon_type == "info":
            painter.drawEllipse(draw_rect.center().x() - 1, draw_rect.top(), 2, 2)
            painter.drawRect(QRectF(draw_rect.center().x() - margin/4, draw_rect.center().y() - margin, margin/2, draw_rect.height() - margin))

        elif icon_type == "play":
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.top())
            path.lineTo(draw_rect.right(), draw_rect.center().y())
            path.lineTo(draw_rect.left(), draw_rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)

        elif icon_type == "pause":
            painter.drawRect(QRectF(draw_rect.left() + margin, draw_rect.top(), margin, draw_rect.height()))
            painter.drawRect(QRectF(draw_rect.right() - margin*2, draw_rect.top(), margin, draw_rect.height()))

        elif icon_type == "refresh":
            painter.drawArc(draw_rect, 45 * 16, 270 * 16)
            painter.drawLine(QPointF(draw_rect.center().x() + margin, draw_rect.center().y() - margin), QPointF(draw_rect.right(), draw_rect.top()))

        elif icon_type == "nato_infantry":
            # NATO Rectangle with X
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.top()), QPointF(draw_rect.right(), draw_rect.bottom()))
            painter.drawLine(QPointF(draw_rect.right(), draw_rect.top()), QPointF(draw_rect.left(), draw_rect.bottom()))

        elif icon_type == "nato_mg":
            # NATO Rectangle with Dot
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawEllipse(draw_rect.center(), size/12, size/12)

        elif icon_type == "nato_recon":
            # NATO Rectangle with single Slash
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.bottom()), QPointF(draw_rect.right(), draw_rect.top()))
            
        elif icon_type == "nato_armor":
            # NATO Rectangle with Oval (Tank)
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawRoundedRect(QRectF(draw_rect.left() + margin, draw_rect.top() + margin, draw_rect.width() - 2*margin, draw_rect.height() - 2*margin), margin, margin)

        elif icon_type == "nato_artillery":
            # NATO Rectangle with Dot (Artillery)
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(draw_rect.center(), size/12, size/12)

        elif icon_type == "nato_mortar":
            # NATO Rectangle with vertical line and dot
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawLine(QPointF(draw_rect.center().x(), draw_rect.top()), QPointF(draw_rect.center().x(), draw_rect.bottom()))
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(QPointF(draw_rect.center().x(), draw_rect.center().y()), size/16, size/16)

        elif icon_type == "nato_hq":
            # NATO Rectangle with Flagpole
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.top()), QPointF(draw_rect.left(), draw_rect.bottom() + margin))
            
        elif icon_type == "nato_motorized":
             # NATO Rectangle with Infantry X and wheels
             painter.setBrush(QBrush(QColor(color).lighter(150)))
             painter.setOpacity(0.4)
             painter.drawRect(draw_rect)
             painter.setOpacity(1.0)
             painter.setBrush(Qt.NoBrush)
             painter.drawRect(draw_rect)
             painter.drawLine(QPointF(draw_rect.left(), draw_rect.top()), QPointF(draw_rect.right(), draw_rect.bottom()))
             painter.drawLine(QPointF(draw_rect.right(), draw_rect.top()), QPointF(draw_rect.left(), draw_rect.bottom()))
             # Small 'wheels' at bottom
             w_r = margin/2
             painter.drawEllipse(QPointF(draw_rect.left() + margin, draw_rect.bottom()), w_r, w_r)
             painter.drawEllipse(QPointF(draw_rect.center().x(), draw_rect.bottom()), w_r, w_r)
             painter.drawEllipse(QPointF(draw_rect.right() - margin, draw_rect.bottom()), w_r, w_r)

        elif icon_type == "nato_engineer":
            # NATO Rectangle with E-bridge symbol
            painter.setBrush(QBrush(QColor(color).lighter(150)))
            painter.setOpacity(0.4)
            painter.drawRect(draw_rect)
            painter.setOpacity(1.0)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(draw_rect)
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y()), QPointF(draw_rect.right(), draw_rect.center().y()))
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y() - margin), QPointF(draw_rect.left(), draw_rect.center().y() + margin))
            painter.drawLine(QPointF(draw_rect.right(), draw_rect.center().y() - margin), QPointF(draw_rect.right(), draw_rect.center().y() + margin))

        # --- OBSTACLES ---
        elif icon_type == "nato_minefield":
            # Triangle with 'M' (Stylized)
            path = QPainterPath()
            path.moveTo(draw_rect.center().x(), draw_rect.top())
            path.lineTo(draw_rect.right(), draw_rect.bottom())
            path.lineTo(draw_rect.left(), draw_rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawText(draw_rect, Qt.AlignCenter, "M")

        elif icon_type == "nato_tank_ditch":
            # Sawtooth Line
            painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y()), QPointF(draw_rect.left() + margin, draw_rect.top()))
            painter.drawLine(QPointF(draw_rect.left() + margin, draw_rect.top()), QPointF(draw_rect.left() + 2*margin, draw_rect.center().y()))
            painter.drawLine(QPointF(draw_rect.left() + 2*margin, draw_rect.center().y()), QPointF(draw_rect.left() + 3*margin, draw_rect.top()))
            painter.drawLine(QPointF(draw_rect.left() + 3*margin, draw_rect.top()), QPointF(draw_rect.right(), draw_rect.center().y()))

        elif icon_type == "nato_wire":
            # S-curls (Barbed Wire)
            for i in range(3):
                cx_loc = draw_rect.left() + (i+0.5) * (draw_rect.width()/3)
                painter.drawArc(QRectF(cx_loc - margin, draw_rect.top(), margin*2, draw_rect.height()), 0, 360*16)
        
        elif icon_type == "nato_fortification":
             # Castle crenellation
             path = QPainterPath()
             path.moveTo(draw_rect.left(), draw_rect.bottom())
             path.lineTo(draw_rect.left(), draw_rect.top())
             path.lineTo(draw_rect.left() + margin, draw_rect.top())
             path.lineTo(draw_rect.left() + margin, draw_rect.top() + margin)
             path.lineTo(draw_rect.left() + 2*margin, draw_rect.top() + margin)
             path.lineTo(draw_rect.left() + 2*margin, draw_rect.top())
             path.lineTo(draw_rect.right(), draw_rect.top())
             path.lineTo(draw_rect.right(), draw_rect.bottom())
             path.closeSubpath()
             painter.drawPath(path)

        # --- TERRAIN SYMBOLS ---
        elif icon_type == "terrain_mountain":
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.bottom())
            path.lineTo(draw_rect.center().x() - margin/2, draw_rect.top() + margin)
            path.lineTo(draw_rect.center().x(), draw_rect.center().y())
            path.lineTo(draw_rect.center().x() + margin/2, draw_rect.top())
            path.lineTo(draw_rect.right(), draw_rect.bottom())
            painter.drawPath(path)

        elif icon_type == "terrain_hill":
             painter.drawArc(draw_rect, 0, 180*16)

        elif icon_type == "terrain_forest":
             # Coniferous tree
             path = QPainterPath()
             path.moveTo(draw_rect.center().x(), draw_rect.top())
             path.lineTo(draw_rect.right(), draw_rect.center().y())
             path.lineTo(draw_rect.center().x() + margin/2, draw_rect.center().y())
             path.lineTo(draw_rect.right(), draw_rect.bottom())
             path.lineTo(draw_rect.left(), draw_rect.bottom())
             path.lineTo(draw_rect.center().x() - margin/2, draw_rect.center().y())
             path.lineTo(draw_rect.left(), draw_rect.center().y())
             path.closeSubpath()
             painter.drawPath(path)

        elif icon_type == "terrain_water":
             # Multiple wave lines
             painter.drawLine(QPointF(draw_rect.left(), draw_rect.center().y()), QPointF(draw_rect.left()+margin, draw_rect.center().y()-margin/2))
             painter.drawLine(QPointF(draw_rect.left()+margin, draw_rect.center().y()-margin/2), QPointF(draw_rect.left()+2*margin, draw_rect.center().y()))
             painter.drawLine(QPointF(draw_rect.left()+2*margin, draw_rect.center().y()), QPointF(draw_rect.left()+3*margin, draw_rect.center().y()-margin/2))
             painter.drawLine(QPointF(draw_rect.left()+3*margin, draw_rect.center().y()-margin/2), QPointF(draw_rect.right(), draw_rect.center().y()))

        elif icon_type == "home":
            # Simple House Icon
            path = QPainterPath()
            path.moveTo(draw_rect.left(), draw_rect.center().y())
            path.lineTo(draw_rect.center().x(), draw_rect.top())
            path.lineTo(draw_rect.right(), draw_rect.center().y())
            path.lineTo(draw_rect.right(), draw_rect.bottom())
            path.lineTo(draw_rect.left(), draw_rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)
            # Door
            painter.drawRect(QRectF(draw_rect.center().x() - margin/2, draw_rect.bottom() - margin, margin, margin))

        elif icon_type == "database":
            # Stacked Cylinders
            for i in range(3):
                y = draw_rect.top() + i * (draw_rect.height() / 3)
                painter.drawEllipse(QRectF(draw_rect.left(), y, draw_rect.width(), draw_rect.height() / 4))
                if i < 2:
                    painter.drawLine(QPointF(draw_rect.left(), y + draw_rect.height() / 8), QPointF(draw_rect.left(), y + draw_rect.height() / 3 + draw_rect.height() / 8))
                    painter.drawLine(QPointF(draw_rect.right(), y + draw_rect.height() / 8), QPointF(draw_rect.right(), y + draw_rect.height() / 3 + draw_rect.height() / 8))

        # --- NATO SIZE MARKINGS (Draw on top of NATO boxes) ---
        if "nato_" in icon_type and unit_size:
            painter.save()
            m_pen = QPen(QColor(color))
            m_pen.setWidthF(max(1.5, size / 20.0)) # Slightly thicker for visibility
            painter.setPen(m_pen)
            
            # Draw above the main box
            top_y = draw_rect.top() - 4
            cx = draw_rect.center().x()
            
            u_lower = unit_size.lower()
            if "company" in u_lower or "ii" in u_lower:
                # II
                painter.drawLine(QPointF(cx - 3, top_y - 6), QPointF(cx - 3, top_y - 1))
                painter.drawLine(QPointF(cx + 3, top_y - 6), QPointF(cx + 3, top_y - 1))
            elif "platoon" in u_lower or "i" in u_lower:
                # I
                painter.drawLine(QPointF(cx, top_y - 6), QPointF(cx, top_y - 1))
            elif "section" in u_lower or "..." in u_lower:
                # ...
                painter.drawEllipse(QRectF(cx - 6, top_y - 4, 2, 2))
                painter.drawEllipse(QRectF(cx - 1, top_y - 4, 2, 2))
                painter.drawEllipse(QRectF(cx + 4, top_y - 4, 2, 2))
            elif "squad" in u_lower:
                # ..
                painter.drawEllipse(QRectF(cx - 4, top_y - 4, 2, 2))
                painter.drawEllipse(QRectF(cx + 2, top_y - 4, 2, 2))
                
            painter.restore()

        painter.restore()
