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
        """
        Initializes the Selection/Interactions tool.
        
        Args:
            widget: The HexWidget canvas where selection happens.
        """
        super().__init__(widget)
        # Selection Identifiers
        self.selected_entity_id = None
        self.selected_zone_id   = None
        
        # Dragging state flags
        self.dragging_entity    = False
        self.dragging_zone      = False
        
        # Temp storage for movement calculations
        self.drag_start_hex     = None
        self.original_zone_data    = None
        self.original_entity_pos   = None
        
        # SPATIAL INDEX: A dictionary {Hex -> zone_id} for O(1) performance lookup.
        # This prevents looping through every zone when you click on the map.
        self._zone_index       = {}
        self._zone_index_valid = False

    # ------------------------------------------------------------------
    # PERFORMANCE OPTIMIZATION: Spatial Indexing
    # ------------------------------------------------------------------
    def _rebuild_zone_index(self):
        """
        Flattens the zone list into a single dictionary for lightning-fast lookups.
        Runs once when needed and invalidates when map data changes.
        """
        self._zone_index = {
            h: zid
            for zid, zdata in self.state.map.get_zones().items()
            for h in zdata.get("hexes", [])
        }
        self._zone_index_valid = True

    def _get_zone_at(self, hex_obj):
        """
        O(1) lookup: Instantly tells you if a zone exists at the given coordinate.
        """
        if not self._zone_index_valid:
            self._rebuild_zone_index()
        return self._zone_index.get(hex_obj)

    def invalidate_zone_index(self):
        """
        Call whenever zones are added/removed/resized to force a re-index.
        """
        self._zone_index_valid = False

    def activate(self):
        """Called when this tool is selected from the sidebar."""
        super().activate()
        self._zone_index_valid = False   # Always rebuild to ensure accuracy.


    def mousePressEvent(self, event):
        """
        Handles clicks: Identifies if you clicked a Unit, a Zone, or open land.
        """
        if event.button() == Qt.LeftButton:
            # Mathematical conversion from screen pixel to hex coordinate
            click_hex = self.widget.screen_to_hex(event.x(), event.y())

            # PRIORITY 1: Check for Units at this location
            entities = self.state.map.get_entities_at(click_hex)
            if entities:
                self.selected_entity_id = entities[0]
                self.selected_zone_id   = None
                self.dragging_entity    = True
                self.drag_start_hex     = click_hex
                self.original_entity_pos = click_hex
                log.debug("User grabbed Unit: %s", self.selected_entity_id)
                self.widget.hex_clicked.emit(click_hex)
                self.widget.update()
                return

            # PRIORITY 2: Check for Strategic Zones using our optimized index
            zid = self._get_zone_at(click_hex)
            if zid:
                zones = self.state.map.get_zones()
                zdata = zones.get(zid, {})
                self.selected_zone_id   = zid
                self.selected_entity_id = None
                self.dragging_zone      = True
                self.drag_start_hex     = click_hex
                # Make a snapshot of the zone before it moves (for Undo/Redo)
                self.original_zone_data = copy.deepcopy(zdata)
                log.debug("User grabbed Zone: %s", zid)
                self.widget.hex_clicked.emit(click_hex)
                self.widget.update()
                return

            # FALLBACK: User clicked empty land (deselect everything)
            self.selected_entity_id = None
            self.selected_zone_id   = None
            self.widget.hex_clicked.emit(click_hex)
            self.widget.update()

            
    def mouseMoveEvent(self, event):
        """
        Handles dragging: Calculates shifts in position and updates coordinates.
        """
        if not self.drag_start_hex:
            return
            
        current_hex = self.widget.screen_to_hex(event.x(), event.y())
        # Do nothing if the mouse hasn't crossed a hexagon boundary
        if current_hex == self.drag_start_hex:
            return

        # CASE: Moving a single unit
        if self.dragging_entity and self.selected_entity_id:
            # INTERACTIVE DRAG: Move unit instantly to the latest hex for smooth feel.
            self.state.map.place_entity(self.selected_entity_id, current_hex)
            self.drag_start_hex = current_hex
            self.widget.update()

        # CASE: Reshifting an entire colored Zone
        elif self.dragging_zone and self.selected_zone_id:
            # SHIFT CALCULATION: How many steps has the mouse moved in hex-space?
            dq = current_hex.q - self.drag_start_hex.q
            dr = current_hex.r - self.drag_start_hex.r
            ds = current_hex.s - self.drag_start_hex.s
            
            zdata = self.state.map.get_zones().get(self.selected_zone_id)
            if zdata:
                # APPLY OFFSET: Every hex in the zone shifts by (dq, dr, ds)
                from engine.core.hex_math import Hex
                new_hexes = []
                for h in zdata['hexes']:
                    new_h = Hex(h.q + dq, h.r + dr, h.s + ds)
                    new_hexes.append(new_h)
                zdata['hexes'] = new_hexes
                
                # SHIFT VERTICES: Also move the boundary points that draw the shape
                if 'vertices' in zdata:
                    new_verts = []
                    for v in zdata['vertices']:
                        new_v = Hex(v.q + dq, v.r + dr, v.s + ds)
                        new_verts.append(new_v)
                    zdata['vertices'] = new_verts
                
                self.drag_start_hex = current_hex
                self.widget.update() # Repaint to show the zone sliding

    def mouseReleaseEvent(self, event):
        """
        Handles completion: Finalizes movement and saves actions to the Undo stack.
        """
        if event.button() == Qt.LeftButton:
            # 1. FINALIZING UNIT MOVES: Save 'Move Receipt' to undo history
            if self.dragging_entity and self.selected_entity_id:
                current_hex = self.widget.screen_to_hex(event.x(), event.y())
                
                # Only record if the position actually changed
                if current_hex != self.original_entity_pos:
                    if hasattr(self.state, 'undo_stack'):
                        from engine.core.undo_system import MoveEntityCommand
                        cmd = MoveEntityCommand(self.state.map, self.selected_entity_id, current_hex, self.original_entity_pos)
                        self.state.undo_stack.push(cmd)
                        self.log(f"Finalized movement of unit to {current_hex.q}, {current_hex.r}")

            # 2. FINALIZING ZONE MOVES: Save 'Relocation Receipt' to undo history
            elif self.dragging_zone and self.selected_zone_id:
                zdata = self.state.map.get_zones().get(self.selected_zone_id)
                self.invalidate_zone_index() # Force re-index as zone has moved
                
                if hasattr(self.state, 'undo_stack') and self.original_zone_data:
                    from engine.core.undo_system import MoveZoneCommand
                    import copy
                    new_data = copy.deepcopy(zdata)
                    cmd = MoveZoneCommand(self.state.map, self.selected_zone_id, new_data, self.original_zone_data)
                    self.state.undo_stack.push(cmd)
                    log.info("Relocated Strategic Zone: %s", self.selected_zone_id)

            # CLEANUP: Reset the tool's temporary variables
            self.dragging_entity = False
            self.dragging_zone = False
            self.drag_start_hex = None
            self.original_zone_data = None
            self.original_entity_pos = None

    def mouseDoubleClickEvent(self, event):
        """
        SHORTCUTS: Quick actions performed on a double-click.
        """
        click_hex = self.widget.screen_to_hex(event.x(), event.y())
        
        # FEATURE: Double-click a Zone to enter 'Vertex Edit' mode immediately.
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            if click_hex in zdata.get('hexes', []):
                # Request the main application window to switch active tools
                mw = self.widget.window() 
                if hasattr(mw, 'set_tool'):
                    mw.set_tool('edit') 
                    # Focus the Edit Tool on this specific zone
                    self.widget.editing_zone_id = zid
                    self.widget.update()
                return

        # FEATURE: Double-click an Agent (to be implemented: open detailed profile)
        pass

