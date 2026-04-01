"""
FILE: ui/tools/draw_zone_tool.py
ROLE: The "Architect" (Area Definition Tool).

DESCRIPTION:
This tool is used to draw complex shapes (polygons) on the map to define zones.
1. You click several points (vertices) to create a outline.
2. The tool automatically finds every hexagon "trapped" inside that outline.
3. It then labels those hexagons as a specific type of zone (like a "Firing Area" 
   or a "Deployment Zone").

Zones are essential for the AI brain, as they act like "Signs" on the map 
telling units where they should go or what they should do.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QRadioButton, 
                             QButtonGroup, QComboBox, QLabel, QGroupBox, QHBoxLayout, 
                             QToolButton, QLineEdit)
from engine.core.hex_math import HexMath

class DrawZoneTool(MapTool):
    """
    Manages the creation of polygonal zones on the hexagon grid.
    """
    def __init__(self, widget):
        super().__init__(widget)
        self.current_polygon = []    # List of corner points you have clicked so far.
        self.current_mouse_hex = None # The hex currently under your mouse (used for visual previews).
        self.combo_terrain = None
        self.combo_sub = None
        self.combo_type = None

    def mouseMoveEvent(self, event):
        """Continually updates which hex the mouse is pointing at."""
        self.current_mouse_hex = self.widget.screen_to_hex(event.x(), event.y())
        self.widget.update()

    def mousePressEvent(self, event):
        """Adds a new corner point to the shape with every click."""
        if event.button() == Qt.LeftButton:
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            self.current_polygon.append(click_hex) # Add the clicked hex to our list of corners.
            
            # Auto-commit for 1-hex zones (e.g., Goal Area)
            z_type = getattr(self.state, 'zone_opt_subtype', "Area")
            z_category = getattr(self.state, 'zone_opt_type', "Designated Area")
            is_goal = "Goal" in z_type or "Goal" in z_category
            
            if is_goal and len(self.current_polygon) == 1:
                self.commit()
            else:
                self.widget.update()
        elif event.button() == Qt.RightButton:
            # RIGHT CLICK ends the drawing and 'commits' the zone to the map.
            self.commit()

    def get_options_widget(self):
        """Builds the menu in the sidebar defined by ZoneOptionsWidget."""
        from ui.components.tool_options.zone_options_widget import ZoneOptionsWidget
        return ZoneOptionsWidget(self.widget.window(), self.state)
        
    def update_terrain_subtypes(self, t_type):
        """Helper to fill valid terrain variants (like River vs Lake)."""
        try:
            self.state.zone_opt_type = t_type
            if not self.combo_sub: return
            
            self.combo_sub.clear()
            
            subtypes = []
            # Fallbacks for the most common terrain types.
            if t_type == "Vegetation": subtypes = ["Forest", "Scrub", "Orchard"]
            elif t_type == "Water": subtypes = ["River", "Lake", "Stream"]
            elif t_type == "Mountain": subtypes = ["High", "Low", "Pass"]
            else: subtypes = ["Generic"]
            
            self.combo_sub.addItems(subtypes)
        except RuntimeError:
            pass

    def commit(self):
        """
        THE FINAL SHAPE: Takes the outline you clicked and turns it into 
        a permanent part of the map.
        """
        # Get current tool settings from state (updated by ZoneOptionsWidget)
        z_type = getattr(self.state, 'zone_opt_subtype', "Area")
        z_category = getattr(self.state, 'zone_opt_type', "Designated Area")
        
        is_goal = "Goal" in z_type or "Goal" in z_category
        
        if (is_goal and len(self.current_polygon) >= 1) or (not is_goal and len(self.current_polygon) > 2):
            import uuid
            
            app_mode = getattr(self.state, "app_mode", "terrain")
            
            if is_goal:
                hexes_inside = self.current_polygon[:1] # Take only the first hex
            else:
                # MATH MAGIC: This function scans the grid and finds every hex that 
                # sits inside the outline you just drew.
                hexes_inside = HexMath.get_hexes_in_polygon(self.current_polygon)
            
            if app_mode == "terrain":
                # --- BULK PAINTING ---
                z_category = getattr(self.state, 'zone_opt_type', "Vegetation")
                z_sub = getattr(self.state, 'zone_opt_subtype', "Forest")
                
                t_type = "plain"
                candidate = z_sub.lower()
                
                if candidate in self.state.terrain_controller.get_available_terrains():
                    t_type = candidate
                elif z_category in self.state.terrain_controller.get_available_terrains():
                    t_type = z_category
                
                self.log(f"Applying Terrain <b>{t_type.upper()}</b> to {len(hexes_inside)} hexes")
                
                if hasattr(self.state, 'undo_stack'): self.state.undo_stack.begin_macro()
                
                for hex_obj in hexes_inside:
                    old_data = self.state.map.get_terrain(hex_obj)
                    new_data = {"type": t_type}
                    
                    if hasattr(self.state, 'undo_stack'):
                        from engine.core.undo_system import SetTerrainCommand
                        cmd = SetTerrainCommand(self.state.map, hex_obj, new_data, old_data.copy())
                        self.state.undo_stack.push(cmd)
                        
                    self.state.map.set_terrain(hex_obj, new_data)

                if hasattr(self.state, 'undo_stack'): self.state.undo_stack.end_macro()
                    
            else:
                # --- MISSION PLANNING ---
                from services.zone_service import add_zone, init as zone_init
                zone_init(self.state)
                
                target_side = getattr(self.state, "active_scenario_side", "Attacker")
                if hasattr(self, 'combo_side') and self.combo_side:
                    target_side = self.combo_side.currentText()
                
                z_category = "Designated Area"
                if hasattr(self, 'combo_type') and self.combo_type:
                     z_category = self.combo_type.currentText()
                
                res = add_zone(self.current_polygon if not is_goal else self.current_polygon[:1], 
                               {
                                   "type": z_category,
                                   "subtype": z_type,
                                   "side": target_side 
                               }, 
                               auto_spawn_defenders=False)
                
                if res.ok:
                    self.log(f"Zone committed: <b>{res.data['name']}</b> ({target_side})")
                else:
                    self.log(f"Error committing zone: {res.error}")
            
            # Update the 'Layers' list in the sidebar so the new zone shows up there.
            mw = self.widget.window()
            if hasattr(mw, 'layer_manager'):
                mw.layer_manager.refresh_tree()
                
            self.widget.refresh_map()
            self.widget.update()
            
        # Reset the tool so it's ready to draw a brand new shape.
        self.current_polygon = []
        self.widget.update()
        
    def deactivate(self):
        """Called if you switch tools while still drawing - finishes the current shape."""
        self.commit()

    def draw_preview(self, painter):
        """GHOST PREVIEW: Shows what the zone will look like before you finish drawing it."""
        if not self.current_polygon:
            return
            
        cx = self.widget.width() / 2
        cy = self.widget.height() / 2
        
        # Draw the outline you have clicked so far (Dashed Green line).
        pen = QPen(QColor("#00FF00"), 3, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        points = []
        for h in self.current_polygon:
             wx, wy = HexMath.hex_to_pixel(h, self.widget.hex_size)
             sx = wx - self.widget.camera_x + cx
             sy = wy - self.widget.camera_y + cy
             points.append(QPointF(sx, sy))
        
        if len(points) > 1:
            painter.drawPolyline(*points) # Connect the dots.
            
        # RUBBER BAND: Show a line following the cursor.
        if self.current_polygon and self.current_mouse_hex:
            last_hex = self.current_polygon[-1]
            first_hex = self.current_polygon[0]
            curr_hex = self.current_mouse_hex
            
            # FELLING FILL: Dynamically highlight every hex that WOULD be 
            # included if you clicked Right-Click right now.
            all_poly_hexes = self.current_polygon + [curr_hex]
            candidates = HexMath.get_hexes_in_polygon(all_poly_hexes)
            
            # Shade these potential hexes in Cyan so they stand out.
            highlight_color = QColor(0, 255, 255, 100) 
            painter.setBrush(QBrush(highlight_color))
            painter.setPen(Qt.NoPen)
            
            for h in candidates:
                wx, wy = HexMath.hex_to_pixel(h, self.widget.hex_size)
                sx = wx - self.widget.camera_x + cx
                sy = wy - self.widget.camera_y + cy
                
                corners = HexMath.get_corners(sx, sy, self.widget.hex_size)
                poly = QPolygonF([QPointF(pt[0], pt[1]) for pt in corners])
                painter.drawPolygon(poly)

            # Draw the line from the last point to the mouse.
            wx, wy = HexMath.hex_to_pixel(last_hex, self.widget.hex_size)
            lx = wx - self.widget.camera_x + cx
            ly = wy - self.widget.camera_y + cy
            
            cwx, cwy = HexMath.hex_to_pixel(curr_hex, self.widget.hex_size)
            mcx = cwx - self.widget.camera_x + cx
            mcy = cwy - self.widget.camera_y + cy
            
            painter.setPen(pen)
            painter.drawLine(QPointF(lx, ly), QPointF(mcx, mcy))
            
            # Draw a faint dotted line back to the START, showing how the polygon will 'Close'.
            wx0, wy0 = HexMath.hex_to_pixel(first_hex, self.widget.hex_size)
            fx = wx0 - self.widget.camera_x + cx
            fy = wy0 - self.widget.camera_y + cy
            
            pen_close = QPen(QColor("#FFAAAA"), 1, Qt.DotLine)
            painter.setPen(pen_close)
            painter.drawLine(QPointF(mcx, mcy), QPointF(fx, fy))

    def spawn_goal_defenders(self, zone_hexes):
        """Spawns 4 defender agents around the goal area."""
        # Automatic goal guard spawning removed as per user request.
        # Deployment is manual via Roster Palette.
        pass
