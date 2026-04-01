"""
FILE: ui/widgets/rules_widget.py
ROLE: The "Rulebook" Editor.
DESCRIPTION: A panel for modifying simulation-wide constants like learning rate, weapon lethality, and movement speeds.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, 
                             QLabel, QPushButton, QMessageBox)
from engine.state.global_state import GlobalState

class RulesWidget(QWidget):
    """
    Widget to configure Scenario Rules and Limitations natively within Phase 2.
    It builds a pre-defined Roster of agents based on force limits.
    """
    def __init__(self, parent=None, state: GlobalState = None):
        super().__init__(parent)
        self.state = state if state else GlobalState()
        self.atk_roster_rows = []
        self.def_roster_rows = []
        self.setup_ui()
        
    def setup_ui(self):
        from ui.styles.theme import Theme
        from PyQt5.QtWidgets import QGroupBox, QGridLayout, QScrollArea, QHBoxLayout, QLineEdit, QComboBox, QSplitter
        from PyQt5.QtCore import Qt
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        title = QLabel("TACTICAL CONSTRAINTS & ROSTER CONFIGURATION")
        title.setStyleSheet(f"font-family: '{Theme.FONT_HEADER}'; font-size: 16px; font-weight: bold; color: {Theme.ACCENT_WARN};")
        main_layout.addWidget(title)
        
        # --- TROOP LIMITS ---
        group_troops = QGroupBox("Force Deployments")
        group_troops.setStyleSheet(f"QGroupBox {{ font-weight: bold; padding-top: 15px; }}")
        form_troops = QFormLayout(group_troops)
        
        self.sb_atk_force = QSpinBox()
        self.sb_atk_force.setRange(1, 999)
        self.sb_atk_force.valueChanged.connect(self.update_roster_ui)
        self.sb_atk_force.valueChanged.connect(self.auto_save)
        form_troops.addRow("Max Attacker Units:", self.sb_atk_force)

        self.sb_def_force = QSpinBox()
        self.sb_def_force.setRange(1, 999)
        self.sb_def_force.valueChanged.connect(self.update_roster_ui)
        self.sb_def_force.valueChanged.connect(self.auto_save)
        form_troops.addRow("Max Defender Units:", self.sb_def_force)
        
        self.sb_max_agents = QSpinBox()
        self.sb_max_agents.setRange(1, 100)
        self.sb_max_agents.valueChanged.connect(self.auto_save)
        form_troops.addRow("Stack Limit (Per Hex):", self.sb_max_agents)
        
        main_layout.addWidget(group_troops)
        
        # --- ROSTER SPLITTER ---
        roster_splitter = QSplitter(Qt.Horizontal)
        
        # Attacker Scroll
        self.atk_scroll = QScrollArea()
        self.atk_scroll.setWidgetResizable(True)
        self.atk_scroll.setMinimumWidth(300)
        atk_container = QGroupBox("Attacker Roster")
        self.atk_layout = QVBoxLayout(atk_container)
        self.atk_layout.addStretch()
        self.atk_scroll.setWidget(atk_container)
        roster_splitter.addWidget(self.atk_scroll)
        
        # Defender Scroll
        self.def_scroll = QScrollArea()
        self.def_scroll.setWidgetResizable(True)
        self.def_scroll.setMinimumWidth(300)
        def_container = QGroupBox("Defender Roster")
        self.def_layout = QVBoxLayout(def_container)
        self.def_layout.addStretch()
        self.def_scroll.setWidget(def_container)
        roster_splitter.addWidget(self.def_scroll)
        
        main_layout.addWidget(roster_splitter, 1) # Expand
        
    def spawn_roster_row(self, side, index, layout_target):
        """Creates a single agent UI configuration row."""
        from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QComboBox, QPushButton
        
        row_widget = QWidget()
        h_layout = QHBoxLayout(row_widget)
        h_layout.setContentsMargins(0, 5, 0, 5)
        
        # Agent Name
        lbl = QLineEdit(f"{side} {index+1}")
        lbl.setPlaceholderText("Agent Name")
        lbl.textChanged.connect(self.auto_save)
        h_layout.addWidget(lbl, 2)
        
        # Weapon Check
        combo_wep = QComboBox()
        weapons = self.state.data_controller.weapons if hasattr(self.state, 'data_controller') else {}
        for wid, wdata in weapons.items():
            name = wdata.get('name', wid)
            combo_wep.addItem(name, userData=wid)
        combo_wep.currentIndexChanged.connect(self.auto_save)
        h_layout.addWidget(combo_wep, 2)
        
        # Unit Type (Personnel Count)
        combo_type = QComboBox()
        combo_type.addItems(["Section (10)", "Platoon (30)", "Company (110)"])
        combo_type.currentIndexChanged.connect(self.auto_save)
        h_layout.addWidget(combo_type, 2)
        
        # Info Button
        btn_info = QPushButton("?")
        btn_info.setFixedWidth(30)
        btn_info.clicked.connect(lambda _, cb=combo_wep: self.show_weapon_info(cb.currentData()))
        h_layout.addWidget(btn_info)
        
        # Store refs
        row_dict = {
            "widget": row_widget,
            "name_edit": lbl,
            "weapon_combo": combo_wep,
            "type_combo": combo_type
        }
        
        # Insert before stretch
        layout_target.insertWidget(layout_target.count() - 1, row_widget)
        return row_dict
        
    def show_weapon_info(self, weapon_id):
        if not weapon_id: return
        weapons = self.state.data_controller.weapons if hasattr(self.state, 'data_controller') else {}
        wdata = weapons.get(weapon_id, {})
        
        info = f"<b>Weapon:</b> {wdata.get('name', weapon_id)}<br><br>"
        info += f"<b>Damage:</b> {wdata.get('damage', 0)}<br>"
        info += f"<b>Max Range:</b> {wdata.get('max_range', 0)}<br>"
        info += f"<b>Min Range:</b> {wdata.get('min_range', 0)}<br>"
        info += f"<b>Fire Rate:</b> {wdata.get('fire_rate', 1)}<br>"
        
        QMessageBox.information(self, "Weapon Intel", info)
        
    def update_roster_ui(self, save=True):
        """Rebuilds the roster rows dynamically based on the spinboxes."""
        atk_target = self.sb_atk_force.value()
        def_target = self.sb_def_force.value()
        
        # Simple adjustment for Attackers
        while len(self.atk_roster_rows) < atk_target:
            self.atk_roster_rows.append(self.spawn_roster_row("Attacker", len(self.atk_roster_rows), self.atk_layout))
        while len(self.atk_roster_rows) > atk_target:
            row = self.atk_roster_rows.pop()
            row["widget"].setParent(None)
            
        # Simple adjustment for Defenders
        while len(self.def_roster_rows) < def_target:
            self.def_roster_rows.append(self.spawn_roster_row("Defender", len(self.def_roster_rows), self.def_layout))
        while len(self.def_roster_rows) > def_target:
            row = self.def_roster_rows.pop()
            row["widget"].setParent(None)
            
        if save:
            self.auto_save()

    def refresh(self):
        """Load rules from active scenario when Phase 2 starts."""
        if not self.state.map or not self.state.map.active_scenario:
            self.setEnabled(False)
            return
            
        self.setEnabled(True)
        rules = self.state.map.active_scenario.rules
        
        self.sb_max_agents.blockSignals(True)
        self.sb_atk_force.blockSignals(True)
        self.sb_def_force.blockSignals(True)
        
        self.sb_max_agents.setValue(rules.get("max_agents_per_hex", 3))
        
        self.sb_atk_force.setValue(rules.get("attacker_max_force", 10))
        self.sb_def_force.setValue(rules.get("defender_max_force", 10))
        
        # Populate UI lists to match counts (WITHOUT triggering auto_save)
        self.update_roster_ui(save=False)
        
        # If there's an existing saved roster, restore the Dropdowns and Names
        saved_roster = rules.get("roster", {"Attacker": [], "Defender": []})
        
        for i, row in enumerate(self.atk_roster_rows):
            if i < len(saved_roster.get("Attacker", [])):
                entry = saved_roster["Attacker"][i]
                row["name_edit"].blockSignals(True)
                row["name_edit"].setText(entry.get("name", f"Attacker {i+1}"))
                row["name_edit"].blockSignals(False)
                idx_w = row["weapon_combo"].findData(entry.get("weapon_id"))
                if idx_w >= 0: row["weapon_combo"].setCurrentIndex(idx_w)
                idx_t = row["type_combo"].findText(entry.get("type_display", "Section (10)"))
                if idx_t >= 0: row["type_combo"].setCurrentIndex(idx_t)
                
        for i, row in enumerate(self.def_roster_rows):
            if i < len(saved_roster.get("Defender", [])):
                entry = saved_roster["Defender"][i]
                row["name_edit"].blockSignals(True)
                row["name_edit"].setText(entry.get("name", f"Defender {i+1}"))
                row["name_edit"].blockSignals(False)
                idx_w = row["weapon_combo"].findData(entry.get("weapon_id"))
                if idx_w >= 0: row["weapon_combo"].setCurrentIndex(idx_w)
                idx_t = row["type_combo"].findText(entry.get("type_display", "Section (10)"))
                if idx_t >= 0: row["type_combo"].setCurrentIndex(idx_t)

        self.sb_max_agents.blockSignals(False)
        self.sb_atk_force.blockSignals(False)
        self.sb_def_force.blockSignals(False)
        
        # PERSIST DEFAULTS: Ensure the roster is saved even if the user doesn't modify anything
        self.auto_save()
        
    def auto_save(self):
        if not self.state.map or not self.state.map.active_scenario: return
            
        rules = self.state.map.active_scenario.rules
        rules["max_agents_per_hex"] = self.sb_max_agents.value()
        rules["attacker_max_force"] = self.sb_atk_force.value()
        rules["defender_max_force"] = self.sb_def_force.value()
        
        # Save exact entity rosters (preserving 'placed' status from existing data)
        roster_data = {"Attacker": [], "Defender": []}
        existing_roster = rules.get("roster", {"Attacker": [], "Defender": []})
        
        for i, row in enumerate(self.atk_roster_rows):
            t_text = row["type_combo"].currentText()
            personnel = 10
            if "Platoon" in t_text: personnel = 30
            elif "Company" in t_text: personnel = 110
            
            # Check if this index was already placed in the current session
            was_placed = False
            atks = existing_roster.get("Attacker", [])
            if i < len(atks):
                was_placed = atks[i].get("placed", False)
            
            roster_data["Attacker"].append({
                "name": row["name_edit"].text().strip(),
                "weapon_id": row["weapon_combo"].currentData(),
                "type_display": t_text,
                "personnel": personnel,
                "side": "Attacker",
                "placed": was_placed
            })
            
        for i, row in enumerate(self.def_roster_rows):
            t_text = row["type_combo"].currentText()
            personnel = 10
            if "Platoon" in t_text: personnel = 30
            elif "Company" in t_text: personnel = 110
            
            # Check if this index was already placed in the current session
            was_placed = False
            defs = existing_roster.get("Defender", [])
            if i < len(defs):
                was_placed = defs[i].get("placed", False)
            
            roster_data["Defender"].append({
                "name": row["name_edit"].text().strip(),
                "weapon_id": row["weapon_combo"].currentData(),
                "type_display": t_text,
                "personnel": personnel,
                "side": "Defender",
                "placed": was_placed
            })
            
        rules["roster"] = roster_data
