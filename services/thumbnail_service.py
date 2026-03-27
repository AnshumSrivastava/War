import os
from PyQt5.QtGui import QImage, QPainter, QColor, QPolygonF, QBrush, QPen
from PyQt5.QtCore import QPointF, Qt
from ui.styles.theme import Theme

class ThumbnailService:
    """
    Renders a simplified mini-preview of a Map object to a PNG file.
    """
    
    @staticmethod
    def generate_thumbnail(map_obj, output_path, size=(440, 200)):
        """
        Creates a top-down hex grid image.
        """
        if not map_obj: return False
        
        image = QImage(size[0], size[1], QImage.Format_ARGB32)
        image.fill(QColor(Theme.BG_DEEP))
        
        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Calculate hex size based on map dimensions
            cols = map_obj.width
            rows = map_obj.height
            
            # Size of total grid to fit in image
            hex_size = min(size[0] / (cols * 1.5), size[1] / (rows * 1.5))
            
            # Center offset
            offset_x = (size[0] - (cols * hex_size * 1.5)) / 2
            offset_y = (size[1] - (rows * hex_size * 1.732)) / 2
            
            from engine.core.hex_math import HexMath
            
            for q in range(cols):
                for r in range(rows):
                    # Simple offset to pixel conversion for preview
                    pos_x = offset_x + hex_size * 1.5 * q
                    pos_y = offset_y + hex_size * 1.732 * (r + 0.5 * (q & 1))
                    
                    # Fix: Use the official API instead of direct attribute access
                    h_coord = HexMath.create_hex(q, r)
                    h_data = map_obj.get_terrain(h_coord)
                    
                    terrain_type = h_data.get("type", "plain") if h_data else "plain"
                    
                    color_hex = Theme.TERRAIN_COLORS.get(terrain_type, "#2c3e50")
                    color = QColor(color_hex)
                    
                    # Standard Flat-top hex points
                    points = []
                    for i in range(6):
                        px = pos_x + hex_size * [1, 0.5, -0.5, -1, -0.5, 0.5][i]
                        py = pos_y + hex_size * [0, 0.866, 0.866, 0, -0.866, -0.866][i]
                        points.append(QPointF(px, py))
                    
                    poly = QPolygonF(points)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(QColor(Theme.BORDER_SUBTLE), 0.5))
                    painter.drawPolygon(poly)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            return image.save(output_path, "PNG")
            
        except Exception as e:
            print(f"Thumbnail Error during render: {e}")
            return False
        finally:
            # CRITICAL: Always end the painter to prevent Segmentation Fault
            if painter.isActive():
                painter.end()
