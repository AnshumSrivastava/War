"""
FILE: ui/tools/edit_tool.py
ROLE: The "Sculptor" (Refinement Tool).

DESCRIPTION:
This tool is used to modify existing shapes.
1. Click on a zone or a path to put it into "Edit Mode".
2. Small white handles (vertices) will appear at every corner.
3. Click and drag these handles to change the shape of the area or the route.

It handles complex updates, such as recalculating which hexagons are 
inside a zone after you move a corner.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt

class EditTool(MapTool):
    """
    Manages the fine-tuning of existing zone and path geometry.
    """
    def __init__(self, widget):
        super().__init__(widget)
        self.dragging_vertex_idx = None # The index of the corner point you are currently dragging.

    def mousePressEvent(self, event):
        """Handles selecting objects and grabbing their corner handles."""
        if event.button() == Qt.LeftButton:
            # 1. GRABBING A HANDLE: Check if the user clicked on a small white handle.
            vertex_idx = self.widget.get_clicked_vertex(event.x(), event.y())
            if vertex_idx is not None:
                self.dragging_vertex_idx = vertex_idx
                
                # BACKUP FOR UNDO: Save exactly how the object looks before we start dragging.
                if self.widget.editing_zone_id:
                    data = self.state.map.get_zones().get(self.widget.editing_zone_id)
                    if data: self.initial_data = data.copy()
                elif self.widget.editing_path_id:
                    data = self.state.map.get_paths().get(self.widget.editing_path_id)
                    if data: self.initial_data = data.copy()
                
                print(f"Started dragging vertex {vertex_idx}")
                return

            # 2. SELECTING AN OBJECT: If we didn't click a handle, see if we clicked a new shape.
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            
            # De-select whatever we were editing before.
            self.widget.editing_zone_id = None
            self.widget.editing_path_id = None
            
            # Check every 'Zone' on the map to see if we clicked inside one.
            zones = self.state.map.get_zones()
            for zid, zdata in zones.items():
                if click_hex in zdata.get('hexes', []):
                    self.widget.editing_zone_id = zid
                    print(f"Editing zone: {zid}")
                    self.widget.update()
                    return

            # Check every 'Path' (Road/Border) to see if we clicked on one.
            paths = self.state.map.get_paths()
            for pid, pdata in paths.items():
                if click_hex in pdata.get('hexes', []):
                    self.widget.editing_path_id = pid
                    print(f"Editing path: {pid}")
                    self.widget.update()
                    return

            # If the user clicked empty ground, tell the Inspector panel which hex was picked.
            self.widget.hex_clicked.emit(click_hex)
            self.widget.update()
            
    def mouseReleaseEvent(self, event):
        """Finalizes the move when you let go of the mouse button."""
        if event.button() == Qt.LeftButton and self.dragging_vertex_idx is not None:
            print(f"Finished dragging vertex {self.dragging_vertex_idx}")
            
            # THE LOGBOOK: Record the move so the "Undo" button works correctly.
            if hasattr(self.state, 'undo_stack') and hasattr(self, 'initial_data'):
                 if self.widget.editing_zone_id:
                     from engine.core.undo_system import UpdateZoneCommand
                     new_data = self.state.map.get_zones().get(self.widget.editing_zone_id).copy()
                     cmd = UpdateZoneCommand(self.state.map, self.widget.editing_zone_id, new_data, self.initial_data)
                     self.state.undo_stack.push(cmd)
                 elif self.widget.editing_path_id:
                     from engine.core.undo_system import UpdatePathCommand
                     new_data = self.state.map.get_paths().get(self.widget.editing_path_id).copy()
                     cmd = UpdatePathCommand(self.state.map, self.widget.editing_path_id, new_data, self.initial_data)
                     self.state.undo_stack.push(cmd)

            # Clear out the temporary dragging memory.
            self.dragging_vertex_idx = None
            self.initial_data = None
            self.widget.update()
            
    def mouseMoveEvent(self, event):
        """Moves the handle along with the mouse cursor."""
        if self.dragging_vertex_idx is not None:
            # Find the new map coordinate under the mouse.
            new_hex = self.widget.screen_to_hex(event.x(), event.y())
            
            # UPDATE GEOMETRY: Tell the shape to move its corner to the new spot.
            if self.widget.editing_zone_id:
                zone_data = self.state.map.get_zones().get(self.widget.editing_zone_id)
                if zone_data and 'vertices' in zone_data:
                    vertices = zone_data['vertices']
                    if 0 <= self.dragging_vertex_idx < len(vertices):
                        vertices[self.dragging_vertex_idx] = new_hex
                        # MATH ALERT: Since the zone moved, we must re-calculate 
                        # which hexagons are now "Trapped" inside the new outline.
                        from engine.core.hex_math import HexMath
                        zone_data['hexes'] = HexMath.get_hexes_in_polygon(vertices)
                        self.widget.update()
                        
            elif self.widget.editing_path_id:
                path_data = self.state.map.get_paths().get(self.widget.editing_path_id)
                if path_data:
                    hexes = path_data['hexes']
                    if 0 <= self.dragging_vertex_idx < len(hexes):
                        # For paths, we just update the list of hex segments.
                        hexes[self.dragging_vertex_idx] = new_hex
                        self.widget.update()

    def draw_preview(self, painter):
        """Draws the small white handles (vertices) for the object being edited."""
        cx = self.widget.width() / 2
        cy = self.widget.height() / 2
        
        # Delegates the actual handle drawing to the Main Widget (HexWidget).
        if self.widget.editing_zone_id:
             self.widget.draw_edit_vertices(painter, cx, cy, "zone")
        elif self.widget.editing_path_id:
             self.widget.draw_edit_vertices(painter, cx, cy, "path")
