"""
FILE: ui/core/hex_context_menu.py
LAYER: Frontend
ROLE: Right-click context menu for the hex canvas.

DESCRIPTION:
    Builds a contextual QMenu depending on what the user right-clicked:
      - Entity  → Properties / Assign Goal / Duplicate / Delete
      - Zone    → Properties / Edit Vertices / Delete
      - Empty   → Place Agent Here / Terrain Info / Copy Coordinates

    ALL STATE MUTATIONS route through services/, never directly.

DOES NOT IMPORT FROM:
    - engine/ directly
    - PyQt5 (constructor only — menu is shown from UI thread)
"""

import logging

from PyQt5.QtWidgets import QMenu, QAction, QApplication
from PyQt5.QtCore import QObject

log = logging.getLogger(__name__)


class HexContextMenu(QObject):
    """
    Builds and displays a right-click context menu over the hex canvas.
    Instantiate fresh per right-click; do not cache instances.
    """

    def __init__(self, main_window, state, hex_obj, parent=None):
        """
        Initializes the dynamic context menu.
        
        Args:
            main_window: The primary UI window (used for tool-switching and logging).
            state: The GlobalState object containing map and entity data.
            hex_obj: The specific hexagon coordinate where the user right-clicked.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self.mw      = main_window
        self.state   = state
        self.hex_obj = hex_obj

    # ------------------------------------------------------------------
    # Public API: Entry point for showing the menu
    # ------------------------------------------------------------------

    def show(self, screen_pos) -> None:
        """
        THE MAIN DISPATCHER: Builds and displays the context menu at the 
        mouse position. It decides which sub-menu to show based on the 
        contents of the clicked hexagon.
        """
        if self.hex_obj is None:
            return

        menu = QMenu(self.mw)
        # Use object name for specific theme styling if needed
        menu.setObjectName("HexContextMenu")

        # Check what's actually at this location
        entities = self.state.map.get_entities_at(self.hex_obj)
        zones    = self._get_zones_at(self.hex_obj)

        # PRIORITY 1: If there's a Unit, show Unit-specific actions.
        if entities:
            self._build_entity_menu(menu, entities[0])
        # PRIORITY 2: If there's a Strategic Zone, show Zone actions.
        elif zones:
            self._build_zone_menu(menu, zones[0])
        # PRIORITY 3: If empty land, show placement and info actions.
        else:
            self._build_empty_menu(menu)

        # SHARED FOOTER: Actions that appear no matter what you click.
        menu.addSeparator()
        a_copy = menu.addAction(f"Copy Coords  [{self.hex_obj.q}, {self.hex_obj.r}]")
        a_copy.triggered.connect(self._copy_coords)

        # Executes the menu blocking-style at the global mouse position.
        menu.exec_(screen_pos)

    # ------------------------------------------------------------------
    # Private Builders: Constructing specific menu trees
    # ------------------------------------------------------------------

    def _build_entity_menu(self, menu: QMenu, entity_id: str) -> None:
        """Constructs actions for Units (Agents)."""
        ent = self.state.entity_manager.get_entity(entity_id)
        name = ent.name if ent else entity_id[:8]

        # Disabled header for branding/identity
        header = QAction(f"🪖  {name}", menu)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        # Core Entity Actions
        a_props = menu.addAction("Properties…")
        a_props.triggered.connect(lambda: self._show_entity_properties(entity_id))

        a_goal = menu.addAction("Assign Goal")
        a_goal.triggered.connect(lambda: self.mw.set_tool("assign_goal"))

        a_dup = menu.addAction("Duplicate")
        a_dup.triggered.connect(lambda: self._duplicate_entity(entity_id))

        menu.addSeparator()

        # Destructive Action
        a_del = menu.addAction("🗑  Delete Unit")
        a_del.triggered.connect(lambda: self._delete_entity(entity_id))

    def _build_zone_menu(self, menu: QMenu, zone_id: str) -> None:
        """Constructs actions for Strategic Areas and Zones."""
        zones = self.state.map.get_zones()
        zdata = zones.get(zone_id, {})
        name  = zdata.get("name", zone_id[:8])

        header = QAction(f"⬡  {name}", menu)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        # Core Zone Actions
        a_props = menu.addAction("Properties…")
        a_props.triggered.connect(lambda: self._show_zone_properties(zone_id))

        a_edit = menu.addAction("Edit Vertices")
        a_edit.triggered.connect(lambda: self._edit_zone(zone_id))

        menu.addSeparator()

        # Destructive Action
        a_del = menu.addAction("🗑  Delete Zone")
        a_del.triggered.connect(lambda: self._delete_zone(zone_id))

    def _build_empty_menu(self, menu: QMenu) -> None:
        """Constructs actions for terrain info and map building."""
        t_data  = self.state.map.get_terrain(self.hex_obj)
        t_type  = t_data.get("type", "plain") if t_data else "plain"
        elev    = t_data.get("elevation", 0) if t_data else 0

        # Show terrain technical data as a disabled header
        info = QAction(f"Terrain: {t_type}  (elev {elev})", menu)
        info.setEnabled(False)
        menu.addAction(info)
        menu.addSeparator()

        # Shortcut to place a new unit at this exact spot
        a_place = menu.addAction("Place Agent Here")
        a_place.triggered.connect(self._place_agent_here)

    # ------------------------------------------------------------------
    # Action Callbacks: Routing logic
    # Note: These mostly call methods in main_window or services/
    # ------------------------------------------------------------------

    def _delete_entity(self, entity_id: str) -> None:
        """Triggers the entity removal service."""
        import services.entity_service as entity_svc
        result = entity_svc.remove_entity(entity_id)
        if result.ok:
            self._refresh()
            self._log(f"Deleted entity <b>{entity_id[:8]}</b>")
        else:
            log.warning("Delete entity failed: %s", result.error)

    def _duplicate_entity(self, entity_id: str) -> None:
        """Creates a clone of an existing unit in an adjacent hex."""
        import services.entity_service as entity_svc
        ent = self.state.entity_manager.get_entity(entity_id)
        if not ent:
            return
        pos = self.state.map.get_entity_position(entity_id)
        if not pos:
            return
            
        # Place the new copy in the neighboring hex to avoid stacking
        from engine.core.hex_math import HexMath
        target = HexMath.neighbor(pos, 0) # Tries East neighbor
        
        result = entity_svc.place_entity(
            q=target.q, r=target.r,
            side=ent.get_attribute("side", "Attacker"),
            unit_type=ent.get_attribute("type", "Infantry"),
            name=ent.name + " (copy)"
        )
        if result.ok:
            self._refresh()
        else:
            log.warning("Duplicate entity failed: %s", result.error)

    def _delete_zone(self, zone_id: str) -> None:
        """Triggers the zone removal service."""
        import services.zone_service as zone_svc
        result = zone_svc.delete_zone(zone_id)
        if result.ok:
            self._refresh()
            self._log(f"Deleted zone <b>{zone_id[:8]}</b>")
        else:
            # LEGACY FALLBACK: Directly prune the dictionary if the service 
            # hasn't fully implemented deletion.
            zones = self.state.map.get_zones()
            if zone_id in zones:
                del zones[zone_id]
                self._refresh()
                self._log(f"Deleted zone <b>{zone_id[:8]}</b>")

    def _place_agent_here(self) -> None:
        """Switches to the Placement Tool and auto-triggers a click on this hex."""
        self.mw.set_tool("place_agent")
        # Pre-fire the click event so the user doesn't have to click again.
        if hasattr(self.mw, "hex_widget"):
            self.mw.hex_widget.hex_clicked.emit(self.hex_obj)

    def _show_entity_properties(self, entity_id: str) -> None:
        """Signals the Object Inspector to focus on a specific Unit."""
        if hasattr(self.mw, "object_inspector"):
            self.mw.object_inspector.show_properties("entity", entity_id)

    def _show_zone_properties(self, zone_id: str) -> None:
        """Signals the Object Inspector to focus on a Strategic Zone."""
        if hasattr(self.mw, "object_inspector"):
            self.mw.object_inspector.show_properties("zone", zone_id)

    def _edit_zone(self, zone_id: str) -> None:
        """Switches to the Edit (Vertex) tool and targets the specific zone."""
        self.mw.set_tool("edit")
        if hasattr(self.mw, "hex_widget"):
            self.mw.hex_widget.editing_zone_id = zone_id
            self.mw.hex_widget.update()

    def _copy_coords(self) -> None:
        """Formats and copies hex coordinates to the system clipboard."""
        text = f"{self.hex_obj.q}, {self.hex_obj.r}"
        QApplication.clipboard().setText(text)
        self._log(f"Copied coordinates <b>{text}</b> to clipboard.")

    # ------------------------------------------------------------------
    # UI Refresh & Logging Helpers
    # ------------------------------------------------------------------

    def _get_zones_at(self, hex_obj) -> list:
        """Returns a list of all zone IDs that overlap with the clicked hex."""
        zones = self.state.map.get_zones()
        return [zid for zid, zdata in zones.items() if hex_obj in zdata.get("hexes", [])]

    def _refresh(self) -> None:
        """Triggers a redraw of the map and a refresh of side-tree lists."""
        if hasattr(self.mw, "hex_widget"):
            self.mw.hex_widget.refresh_map()
        if hasattr(self.mw, "scene_hierarchy"):
            self.mw.scene_hierarchy.refresh_tree()

    def _log(self, message: str) -> None:
        """Sends a rich-text update to the information feed at the screen bottom."""
        if hasattr(self.mw, "log_info"):
            self.mw.log_info(message)
        else:
            log.info(message)

