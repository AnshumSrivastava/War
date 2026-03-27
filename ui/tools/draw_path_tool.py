"""
FILE: ui/tools/draw_path_tool.py
ROLE: The "Road Builder" (Route Creation Tool).

DESCRIPTION:
This tool is used to draw linear paths on the map, such as roads, rivers, 
supply lines, or international borders.
1. You click several points (anchors) to define the route.
2. The tool "stretches" a line between these points, following the hexagon grid.
3. If drawing a 'Border', it can trigger a special event to define which team 
   owns which side of that border.

Paths are used by the simulation to calculate faster movement (Roads) or 
to define restricted territory (Borders).
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QMessageBox
from engine.core.hex_math import HexMath

class DrawPathTool(MapTool):
    """
    Handles the logic for creating linear path entities on the map.
    """
    def __init__(self, widget):
        super().__init__(widget)
        self.current_path = []        # The list of main anchor points you have clicked.
        self.current_mouse_hex = None   # The hex your mouse is currently hovering over.

    def mouseMoveEvent(self, event):
        """Updates the visual 'preview' line as you move the mouse."""
        self.current_mouse_hex = self.widget.screen_to_hex(event.x(), event.y())
        self.widget.update()

    def mousePressEvent(self, event):
        """Adds a new segment to the path with a Left Click."""
        if event.button() == Qt.LeftButton:
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            self.current_path.append(click_hex)
            self.widget.update()
        elif event.button() == Qt.RightButton:
            # RIGHT CLICK finishes the path and saves it to the map.
            self.commit()

    def get_options_widget(self):
        from ui.components.tool_options.path_options_widget import PathOptionsWidget
        return PathOptionsWidget(self.widget.window(), self.state)

    def commit(self):
        """
        THE FINISH LINE: Finalizes the path and turns it into a map entity.
        """
        # We need at least 2 points to make a path (a start and an end).
        if len(self.current_path) > 1:
            import uuid
            path_id = str(uuid.uuid4())[:8] # Unique tracking ID for this specific road/border.
            
            # Check if we are building a Road (Terrain mode) or a Border (Scenario mode).
            app_mode = getattr(self.state, "app_mode", "terrain")
            p_type = getattr(self.state, 'path_opt_type', "Road" if app_mode == "terrain" else "Border")
            p_mode = getattr(self.state, 'path_mode', "Center-to-Center")
            
            # Use the custom name if the user typed one in the sidebar.
            custom_name = getattr(self.state, 'path_opt_name', "").strip()
            if custom_name:
                p_name = custom_name
            else:
                p_name = f"{p_type} {path_id}"
            
            # COLOR CODING: Assign a color based on the type of path.
            default_colors = {
                "Canal": "#00FFFF",      # Bright Blue
                "Road": "#8B4513",       # Brown
                "Border": "#FF0000",     # Red
                "Supply Line": "#00FF00" # Green
            }
            fallback_col = default_colors.get(p_type, "#FFA500")
            p_color = getattr(self.state, 'path_opt_color', fallback_col)
            
            # --- THE PATH DATA PACKAGE ---
            path_data = {
                "name": p_name,
                "hexes": self.current_path,      # The list of hexes the path goes through.
                "color": p_color,
                "mode": p_mode,
                "type": p_type,
                "app_mode": app_mode,
                "side": getattr(self.state, "active_scenario_side", "Neutral") if app_mode == "scenario" else "Neutral"
            }
            
            # Save this action in the 'Undo' history so the user can delete it if they messed up.
            if hasattr(self.state, 'undo_stack'):
                 from engine.core.undo_system import AddPathCommand
                 cmd = AddPathCommand(self.state.map, path_id, path_data)
                 self.state.undo_stack.push(cmd)
            
            # Register the new path in the map's permanent record.
            self.state.map.add_path(path_id, path_data)
            self.log(f"Path committed: <b>{path_id}</b> ({p_type})")
            
            # --- SPECIAL BORDER LOGIC ---
            # If the user just drew a 'Border', we might want to automatically 
            # start assigning territory to Red or Blue teams.
            if p_type == "Border":
                self.state.map.border_path = self.current_path
                mw = self.widget.window()
                
                # Ask a popup question: "Ready to assign sides?"
                try:
                    res = QMessageBox.question(mw, "Border Defined", 
                        "Do you want to finalize the border and assign sides now?", 
                        QMessageBox.Yes | QMessageBox.No)
                        
                    if res == QMessageBox.Yes:
                        # This triggers the automatic territory coloring system.
                        if hasattr(mw, 'start_side_assignment'):
                            mw.start_side_assignment()
                except RuntimeError:
                    pass
            
            # Update the side menu list so the new path appears there immediately.
            try:
                mw = self.widget.window()
                if hasattr(mw, 'layer_manager'):
                    mw.layer_manager.refresh_tree()
            except RuntimeError:
                pass
            
        # Reset the tool so you can start drawing a new path.
        self.current_path = []
        self.widget.update()
    
    def deactivate(self):
        """Called if you switch tools while drawing - automatically saves what you've done."""
        self.commit()

    def draw_preview(self, painter):
        """GHOST LINE: Draws a dashed line showing where the path WILL be."""
        if not self.current_path or len(self.current_path) == 0:
            return
            
        path_mode = getattr(self.state, 'path_mode', "Center-to-Center")
        cx = self.widget.width() / 2
        cy = self.widget.height() / 2
        
        pen = QPen(QColor("#FFFF00"), 3, Qt.DashLine) # A bright Yellow dashed line.
        painter.setPen(pen)
        
        # We have two ways of drawing paths: 
        # 1. Straight through the middle of hexes (Center-to-Center).
        # 2. Hugging the edges of hexes (Edge-Aligned).
        if path_mode == "Edge-Aligned":
            self._draw_edge_aligned(painter, cx, cy)
        else:
            self._draw_center_to_center(painter, cx, cy)

    def _draw_center_to_center(self, painter, cx, cy):
            """Draws a path that goes from the heart of one hex to the next."""
            all_path_hexes = []
            
            # 1. Look at all the points already clicked.
            for i in range(len(self.current_path)):
                if i == 0:
                    all_path_hexes.append(self.current_path[i])
                else:
                    # Calculate every hex between anchor A and anchor B.
                    start = self.current_path[i-1]
                    goal = self.current_path[i]
                    line_hexes = HexMath.line(start, goal)
                    if line_hexes and len(line_hexes) > 1:
                        all_path_hexes.extend(line_hexes[1:])
                    else:
                        all_path_hexes.append(goal)
            
            # 2. Add the temporary line going to the current mouse position.
            if self.current_path and self.current_mouse_hex:
                 start = self.current_path[-1]
                 goal = self.current_mouse_hex
                 line_hexes = HexMath.line(start, goal)
                 if line_hexes and len(line_hexes) > 1:
                     all_path_hexes.extend(line_hexes[1:])
                 else:
                     all_path_hexes.append(goal)

            # Convert all those hex coordinates into screen pixel coordinates.
            points = []
            for h in all_path_hexes:
                wx, wy = HexMath.hex_to_pixel(h, self.widget.hex_size)
                sx = wx - self.widget.camera_x + cx
                sy = wy - self.widget.camera_y + cy
                points.append(QPointF(sx, sy))
            
            # Draw the final connected line on the screen.
            if len(points) > 1:
                painter.drawPolyline(*points)
            elif len(points) == 1:
                # If only one point exists, draw a small dot.
                painter.drawEllipse(points[0], 5, 5)

    def _draw_edge_aligned(self, painter, cx, cy):
            """
            Draws a path that flows along the borders of the hexagons.
            (Note: Currently uses center-to-center logic as a high-performance fallback).
            """
            self._draw_center_to_center(painter, cx, cy)
