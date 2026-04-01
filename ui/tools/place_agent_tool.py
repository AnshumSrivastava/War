"""
FILE: ui/tools/place_agent_tool.py
ROLE: The "Roster Deployment Palette" (Drag & Drop).

DESCRIPTION:
Instead of clicking the map to spawn generic units, this panel displays the 
explicit Roster established during the Rules Phase. Users grab an agent's 
card and drag it onto the tactical map to deploy it.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt, QTimer, QSize, QMimeData, QByteArray
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QAbstractItemView, QGroupBox, QMessageBox, QPushButton)
from ui.styles.theme import Theme
import json

class DraggableRosterList(QListWidget):
    """Custom ListWidget that handles the tactical drag payload."""
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.state = state
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setIconSize(QSize(24, 24))

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item: return
        
        payload_str = item.data(Qt.UserRole)
        mimeData = QMimeData()
        mimeData.setData("application/x-war-agent", QByteArray(payload_str.encode('utf-8')))
        
        from PyQt5.QtGui import QDrag
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec_(Qt.MoveAction)


class PlaceAgentTool(MapTool):
    def __init__(self, widget):
        super().__init__(widget)
        self.list_widget = None
        self._active = False

    def activate(self):
        self._active = True
        super().activate()
        self.refresh_roster()

    def deactivate(self):
        self._active = False
        super().deactivate()

    def get_options_widget(self, parent=None):
        """Builds the Draggable Roster UI."""
        widget = QWidget(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        info_lbl = QLabel("DRAG & DROP DEPLOYMENT\nDrag a unit's card onto the map.")
        info_lbl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-style: italic; font-size: 11px;")
        layout.addWidget(info_lbl)
        
        # --- SYNC BUTTON ---
        btn_layout = QHBoxLayout()
        btn_sync = QPushButton("Sync Roster")
        btn_sync.clicked.connect(self.refresh_roster)
        btn_sync.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                color: {Theme.TEXT_PRIMARY};
                font-size: 10px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background: {Theme.BORDER_STRONG};
            }}
        """)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_sync)
        layout.addLayout(btn_layout)
        
        # --- ROSTER LIST ---
        roster_group = QGroupBox("Awaiting Deployment")
        roster_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; padding-top: 10px; color: {Theme.ACCENT_WARN}; border: none; }}")
        r_layout = QVBoxLayout()
        
        self.list_widget = DraggableRosterList(state=self.state)
        self.list_widget.setStyleSheet(f"""
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Theme.BORDER_SUBTLE};
                background: {Theme.BG_INPUT};
                margin-bottom: 4px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background: {Theme.BORDER_STRONG};
            }}
        """)
        
        r_layout.addWidget(self.list_widget)
        roster_group.setLayout(r_layout)
        layout.addWidget(roster_group)
        
        widget.setLayout(layout)
        QTimer.singleShot(100, self.refresh_roster)
        
        btn_seed = QPushButton("SEED DEFAULT UNITS")
        btn_seed.setStyleSheet(f"background-color: {Theme.BG_DEEP}; color: {Theme.ACCENT_GOOD}; border: 1px solid {Theme.ACCENT_GOOD}; font-weight: bold; margin-top: 10px;")
        btn_seed.clicked.connect(self.seed_default_units)
        layout.addWidget(btn_seed)
        
        return widget

    def seed_default_units(self):
        """Emergency seeding of units if the Rules tab was skipped."""
        if not self.state.map or not self.state.map.active_scenario: return
        
        rules = self.state.map.active_scenario.rules
        if "roster" not in rules: rules["roster"] = {"Attacker": [], "Defender": []}
        roster = rules["roster"]
        
        side = getattr(self.state, "active_scenario_side", "Attacker")
        if side not in roster: roster[side] = []
        
        # Baseline NATO forces
        roster[side].extend([
            {"name": f"{side} HQ", "weapon_id": "None", "type_display": "Headquarters", "personnel": 10, "side": side, "placed": False},
            {"name": f"{side} Vanguard", "weapon_id": "Rifle", "type_display": "Section (10)", "personnel": 10, "side": side, "placed": False},
            {"name": f"{side} Support", "weapon_id": "Rifle", "type_display": "Section (10)", "personnel": 10, "side": side, "placed": False}
        ])
        
        self.refresh_roster()

    def activate(self):
        """Called when the tool is selected by the user."""
        self._active = True
        self.refresh_roster()
        self.widget.update()

    def refresh_roster(self):
        """Loads unplaced units from the Roster for the active side (Attacker/Defender)."""
        from ui.core.icon_painter import VectorIconPainter
        from ui.styles.theme import Theme
        import sip
        import json
        
        if not self.list_widget or sip.isdeleted(self.list_widget): 
            return
            
        self.list_widget.clear()
        
        if not self.state.map or not self.state.map.active_scenario:
            print("DEBUG: refresh_roster failed - No active map/scenario")
            return
            
        # Force synchronization check: Normalize side names and look carefully for roster data
        active_side = getattr(self.state, "active_scenario_side", "Attacker")
        if not active_side or active_side == "Combined": 
            active_side = "Attacker"
            
        # Normalize: 'ATTACKER' -> 'Attacker' if needed
        side = active_side.title() if hasattr(active_side, 'title') else active_side
            
        print(f"DEBUG: refresh_roster side='{side}'")
        rules = self.state.map.active_scenario.rules
        roster = rules.get("roster", {})
        
        # Support both case-sensitive and case-insensitive side names in the roster dictionary
        side_roster = roster.get(side, roster.get(side.lower(), roster.get(side.upper(), [])))
        print(f"DEBUG: side_roster found {len(side_roster)} units")
        
        if not side_roster:
            item = QListWidgetItem("Roster Empty.\n(Use Phase 2: Rules or SEED below)")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(Theme.ACCENT_WARN)
            self.list_widget.addItem(item)
            return

        for idx, agent_data in enumerate(side_roster):
            # Units already on the map are hidden from the palette
            if agent_data.get("placed", False):
                continue
                
            try:
                name = agent_data.get("name", f"{side} {idx+1}")
                wep_id = agent_data.get("weapon_id", "None")
                type_disp = agent_data.get("type_display", "Section")
                personnel = agent_data.get("personnel", 10)
                
                # Form display string
                display_text = f"{name}\n{type_disp} | Personnel: {personnel}"
                item = QListWidgetItem(display_text)
                
                # --- NATO SYMBOL MAPPING ---
                icon_type = "nato_infantry"
                w_lower = wep_id.lower() if wep_id else ""
                t_lower = type_disp.lower() if type_disp else ""
                
                if "tank" in w_lower or "armor" in w_lower: icon_type = "nato_armor"
                elif "arty" in w_lower or "artillery" in w_lower: icon_type = "nato_artillery"
                elif "mortar" in w_lower: icon_type = "nato_mortar"
                elif "mg" in w_lower or "machine" in w_lower: icon_type = "nato_mg"
                elif "hq" in t_lower or "headquarters" in t_lower: icon_type = "nato_hq"
                elif "recon" in t_lower or "scout" in t_lower: icon_type = "nato_recon"
                
                # Apply team colors and NATO size markings to icons
                icon_color = Theme.ACCENT_ENEMY if side in ["Attacker", "Red"] else Theme.ACCENT_ALLY
                try:
                    icon = VectorIconPainter.create_icon(icon_type, icon_color, type_disp)
                    item.setIcon(icon)
                except Exception as e:
                    print(f"Icon Generation Error for {name}: {e}")
                
                # Pack payload for Drag & Drop
                payload = {
                    "roster_index": idx,
                    "side": side,
                    "name": name,
                    "weapon_id": wep_id,
                    "type_display": type_disp,
                    "personnel": personnel
                }
                item.setData(Qt.UserRole, json.dumps(payload))
                self.list_widget.addItem(item)
            except Exception as e:
                print(f"Roster list item creation error for index {idx}: {e}")
            
    # --- DISABLE CLICK EVENTS ---
    def on_click(self, x, y): pass
    def on_drag(self, x, y): pass
    def on_release(self, x, y): pass
