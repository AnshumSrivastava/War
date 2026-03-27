from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen, QColor, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF
from engine.core.hex_math import HexMath, Hex
from engine.state.global_state import GlobalState

class HexRenderer:
    """
    Static utility class to render Map data to an image (QPixmap).
    Used for generating clean thumbnails without UI overlays.
    """
    
    @staticmethod
    def render_map_to_image(map_instance, width=500, height=400):
        """
        Render the provided Map object to a QPixmap of specified dimensions.
        Automatically scales the grid to fit the bounds.
        """
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(20, 20, 25)) # Void Color background
        
        if not map_instance:
            return pixmap
            
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Determine Map Bounds
        map_w = max(1, map_instance.width)
        map_h = max(1, map_instance.height)
        
        # 2. Calculate Scale
        # HexMath: width of hex = sqrt(3) * size
        # Height of hex = 2 * size
        # Col spacing = width
        # Row spacing = height * 0.75
        
        # Total Width approx = cols * sqrt(3) * size
        # Total Height approx = rows * 1.5 * size + 0.5 * size
        
        w_factor = map_w * 1.732 
        h_factor = map_h * 1.5 + 0.5
        
        scale_x = width / w_factor
        scale_y = height / h_factor
        
        hex_size = min(scale_x, scale_y) * 0.9 # 90% fit for margin
        
        # Center content
        content_w = w_factor * hex_size
        content_h = h_factor * hex_size
        
        offset_x = (width - content_w) / 2
        offset_y = (height - content_h) / 2
        
        # Use GlobalState singleton for data controller access (Terrain Colors)
        state = GlobalState()
        controller = state.data_controller
        
        # 3. Draw Hexes
        grid_color = QColor(60, 60, 65)
        pen = QPen(grid_color)
        pen.setWidthF(1.0)
        
        for col in range(map_w):
            for row in range(map_h):
                h = HexMath.offset_to_cube(col, row)
                
                # Calculate pixel position relative to 0,0
                # Using HexMath logic but we need to supply hex_size
                # HexMath.hex_to_pixel returns cartesian coords centered at 0? No, q,r based.
                # Let's trust HexMath logic but offset the result
                
                wx, wy = HexMath.hex_to_pixel(h, hex_size)
                
                # HexMath usually assumes 0,0 is center of specific hex? 
                # Actually HexMath: x = size * (sqrt(3) * q + sqrt(3)/2 * r)
                # This creates 'negative' coords if q,r are small?
                # We need to normalize.
                # Let's just use the raw output and Apply Offset.
                # Wait, HexMath logic assumes origin at (0,0).
                # But our Grid starts at col=0, row=0.
                # Let's map 0,0 to the top left visually.
                
                # Shift so (0,0) is at top left
                # h_0_0 = HexMath.offset_to_cube(0,0) -> q=0, r=0.
                # x, y = 0, 0.
                # h_0_1 -> q=-1, r=1? No, offset to cube.
                # Even columns (0): q=col, r = row - (col+(col&1))//2 
                # (0,0) -> (0,0,0). Pixel (0,0).
                
                # So (0,0) is drawing origin.
                # We simply add offset_x, offset_y, but we might need to shift to keep it positive?
                # Hexes stick out to left?
                # Actually, standard pointy top:
                # (0,0) center is at 0,0.
                # Left corner is at -sqrt(3)/2 * size.
                # So we need margin hex_size.
                
                sx = wx + offset_x + hex_size # Add margin
                sy = wy + offset_y + hex_size
                
                # Corners
                corners = HexMath.get_corners(sx, sy, hex_size - 1)
                poly = QPolygonF([QPointF(x, y) for x, y in corners])
                
                # Attributes
                attrs = controller.get_hex_full_attributes(h, map_instance)
                color_code = attrs.get("color", "#1E1E23")
                elevation = attrs.get("elevation", 0)
                
                brush_color = QColor(color_code)
                # Simple elevation alpha logic
                alpha_val = 50 + (abs(elevation) * 20)
                alpha_val = max(50, min(255, int(alpha_val)))
                brush_color.setAlpha(alpha_val)
                
                painter.setBrush(QBrush(brush_color))
                painter.setPen(pen)
                painter.drawPolygon(poly)
                
                # Terrain Features (Optional: Forests/Urban icons?)
                # For now just color is sufficient for thumbnail.
                
        painter.end()
        return pixmap
