"""
FILE: ui/tools/selection_tool.py
ROLE: The "Hand" (Interaction Tool).

DESCRIPTION:
    Click to select entities/zones, drag to move them.
    Uses a spatial index for O(1) zone hit-detection.
"""

import copy
import logging

from .base_tool import MapTool
from PyQt5.QtCore import Qt

log = logging.getLogger(__name__)

class SelectionTool(MapTool):
    """
    Handles picking up, moving, and selecting objects on the map.
    Uses a {Hex -> zone_id} spatial index for O(1) zone lookup.
    """
    def __init__(self, widget):
        super().__init__(widget)
        self.selected_entity_id = None
        self.selected_zone_id   = None
        self.dragging_entity    = False
        self.dragging_zone      = False
        self.drag_start_hex     = None
        self.original_zone_data    = None
        self.original_entity_pos   = None
        # Spatial index: {Hex -> zone_id}
        self._zone_index       = {}
        self._zone_index_valid = False

    # ------------------------------------------------------------------
    # Spatial index
    # ------------------------------------------------------------------
    def _rebuild_zone_index(self):
        """Build {hex -> zone_id} from the current zone list (O(n) once)."""
        self._zone_index = {
            h: zid
            for zid, zdata in self.state.map.get_zones().items()
            for h in zdata.get("hexes", [])
        }
        self._zone_index_valid = True

    def _get_zone_at(self, hex_obj):
        """O(1) zone lookup using the spatial index."""
        if not self._zone_index_valid:
            self._rebuild_zone_index()
        return self._zone_index.get(hex_obj)

    def invalidate_zone_index(self):
        """Call whenever zones are added/removed/modified."""
        self._zone_index_valid = False

    def activate(self):
        super().activate()
        self._zone_index_valid = False   # Always rebuild on tool activation.


    def mousePressEvent(self, event):
        """Called when you click the left mouse button."""
        if event.button() == Qt.LeftButton:
            click_hex = self.widget.screen_to_hex(event.x(), event.y())

            # 1. Check for entities at this hex
            entities = self.state.map.get_entities_at(click_hex)
            if entities:
                self.selected_entity_id = entities[0]
                self.selected_zone_id   = None
                self.dragging_entity    = True
                self.drag_start_hex     = click_hex
                self.original_entity_pos = click_hex
                log.debug("Selected entity: %s", self.selected_entity_id)
                self.widget.hex_clicked.emit(click_hex)
                self.widget.update()
                return

            # 2. O(1) zone lookup via spatial index
            zid = self._get_zone_at(click_hex)
            if zid:
                zones = self.state.map.get_zones()
                zdata = zones.get(zid, {})
                self.selected_zone_id   = zid
                self.selected_entity_id = None
                self.dragging_zone      = True
                self.drag_start_hex     = click_hex
                self.original_zone_data = copy.deepcopy(zdata)
                log.debug("Selected zone: %s", zid)
                self.widget.hex_clicked.emit(click_hex)
                self.widget.update()
                return

            # 3. Empty hex
            self.selected_entity_id = None
            self.selected_zone_id   = None
            self.widget.hex_clicked.emit(click_hex)
            self.widget.update()

            
    def mouseMoveEvent(self, event):
        """Called while you move the mouse across the map."""
        if not self.drag_start_hex:
            return
            
        current_hex = self.widget.screen_to_hex(event.x(), event.y())
        # If the mouse is still over the same hex, do nothing.
        if current_hex == self.drag_start_hex:
            return

        if self.dragging_entity and self.selected_entity_id:
            # INTERACTIVE DRAG: Move the unit instantly to follow your cursor.
            # This provides smooth visual feedback as you 'carry' the unit.
            self.state.map.place_entity(self.selected_entity_id, current_hex)
            self.drag_start_hex = current_hex
            self.widget.update()

        elif self.dragging_zone and self.selected_zone_id:
            # AREA DRAG: Move the entire shape of the zone.
            # We calculate how many hexes you've moved from the start point.
            dq = current_hex.q - self.drag_start_hex.q
            dr = current_hex.r - self.drag_start_hex.r
            ds = current_hex.s - self.drag_start_hex.s
            
            zdata = self.state.map.get_zones().get(self.selected_zone_id)
            if zdata:
                # Shift every single hexagon that makes up this zone by the same distance.
                from engine.core.hex_math import Hex, HexMath
                new_hexes = []
                for h in zdata['hexes']:
                    new_h = Hex(h.q + dq, h.r + dr, h.s + ds)
                    new_hexes.append(new_h)
                zdata['hexes'] = new_hexes
                
                # Also shift the boundary lines (vertices) of the zone.
                if 'vertices' in zdata:
                    new_verts = []
                    for v in zdata['vertices']:
                        new_v = Hex(v.q + dq, v.r + dr, v.s + ds)
                        new_verts.append(new_v)
                    zdata['vertices'] = new_verts
                
                self.drag_start_hex = current_hex
                self.widget.update() # Redraw the zone in its new position.

    def mouseReleaseEvent(self, event):
        """Called when you let go of the mouse button."""
        if event.button() == Qt.LeftButton:
            # 1. Finalize Unit Move (and record it for Undo).
            if self.dragging_entity and self.selected_entity_id:
                current_hex = self.widget.screen_to_hex(event.x(), event.y())
                
                # Check if the unit actually moved to a different spot.
                if current_hex != self.original_entity_pos:
                    if hasattr(self.state, 'undo_stack'):
                        # Create a 'Receipt' for this move so we can undo it.
                        from engine.core.undo_system import MoveEntityCommand
                        cmd = MoveEntityCommand(self.state.map, self.selected_entity_id, current_hex, self.original_entity_pos)
                        self.state.undo_stack.push(cmd)
                        self.log(f"Moved Entity <b>{self.selected_entity_id[:8]}</b> to {current_hex.q}, {current_hex.r}")

            # 2. Finalize Zone Move (and record it for Undo).
            elif self.dragging_zone and self.selected_zone_id:
                zdata = self.state.map.get_zones().get(self.selected_zone_id)
                
                if hasattr(self.state, 'undo_stack') and self.original_zone_data:
                    # Record the original and new data for the Undo system.
                    from engine.core.undo_system import MoveZoneCommand
                    import copy
                    new_data = copy.deepcopy(zdata)
                    cmd = MoveZoneCommand(self.state.map, self.selected_zone_id, new_data, self.original_zone_data)
                    self.state.undo_stack.push(cmd)
                    print(f"Moved Zone {self.selected_zone_id}")

            # Reset all temporary 'dragging' flags.
            self.dragging_entity = False
            self.dragging_zone = False
            self.drag_start_hex = None
            self.original_zone_data = None
            self.original_entity_pos = None

    def mouseDoubleClickEvent(self, event):
        """Called when you click twice quickly."""
        click_hex = self.widget.screen_to_hex(event.x(), event.y())
        print(f"Double Click at {click_hex}")
        
        # 1. Edit Zone
        # If you double-click an area, switch to the 'Edit' tool so you 
        # can reshape its boundaries.
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            if click_hex in zdata.get('hexes', []):
                print(f"Switching to Edit Mode for Zone {zid}")
                
                # Attempt to tell the Main Window to switch tools automatically.
                mw = self.widget.window() 
                if hasattr(mw, 'set_tool'):
                    mw.set_tool('edit') # Switch to the Edit (Vertex) tool.
                    
                    # Store which exact zone we are now editing.
                    self.widget.editing_zone_id = zid
                    self.widget.update()
                return

        # 2. Edit Agent (Placeholder)
        # In the future, double-clicking a unit might open an equipment screen or detailed stats.
        pass

