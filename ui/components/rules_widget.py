"""
FILE: ui/widgets/rules_widget.py
ROLE: The "Rulebook" Editor.
DESCRIPTION: A panel for modifying simulation-wide constants like learning rate, weapon lethality, and movement speeds.
"""
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, 
                             QLabel, QPushButton, QMessageBox)
from engine.state.global_state import GlobalState
from ui.styles.theme import Theme
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QScrollArea, QHBoxLayout, QLineEdit, QComboBox, QSplitter
from PyQt5.QtCore import Qt

# --- UI CONFIGURATION ---
# Titles & Headers
STR_TITLE_RULES = "📄 Configure Your Mission Forces"
STR_GRP_DEPLOYMENTS = "Mission Limits"
STR_GRP_ATK_ROSTER = "Attacking Force Roster"
STR_GRP_DEF_ROSTER = "Defending Force Roster"

# Labels
STR_LBL_ATK_MAX = "Number of Attacking Units:"
STR_LBL_DEF_MAX = "Number of Defending Units:"
STR_LBL_STACK_LIMIT = "Max Units per Location:"
STR_LBL_COL_NAME = "Agent Name"
STR_LBL_COL_WEAPON = "Primary Weapon"
STR_LBL_COL_HIERARCHY = "Hierarchy"
STR_LBL_COL_PERSONNEL = "Personnel"
STR_LBL_COL_AMMO_TYPE = "Ammo Type"
STR_LBL_COL_TOTAL_AMMO = "Total Ammo"
STR_LBL_AGENT_NAME_PLACEHOLDER = "e.g. A/Company1"
LABEL_BTN_INFO = "?"

# Roles
STR_ROLE_ATTACKER = "Attacker"
STR_ROLE_DEFENDER = "Defender"

# Options
LIST_UNIT_TYPES = ["Section", "Platoon", "Company"]
DICT_UNIT_PERSONNEL = {"Section": 10, "Platoon": 30, "Company": 110}

# Dialogs & Info
STR_INFO_WEAPON_TITLE = "Weapon Intel"
STR_INFO_WEAPON_FMT = """
<b>Weapon:</b> {name}<br><br>
<b>Damage:</b> {damage}<br>
<b>Max Range:</b> {max_range}<br>
<b>Min Range:</b> {min_range}<br>
<b>Fire Rate:</b> {fire_rate}<br>
"""

# Stylesheets
STYLE_TITLE = f"font-family: '{Theme.FONT_HEADER}'; font-size: 16px; font-weight: bold; color: {Theme.ACCENT_WARN};"
STYLE_GROUPBOX = "QGroupBox { font-weight: bold; padding-top: 15px; }"
# -------------------------

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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        title = QLabel(STR_TITLE_RULES)
        title.setStyleSheet(STYLE_TITLE)
        main_layout.addWidget(title)
        
        # --- TROOP LIMITS ---
        group_troops = QGroupBox(STR_GRP_DEPLOYMENTS)
        group_troops.setStyleSheet(STYLE_GROUPBOX)
        form_troops = QFormLayout(group_troops)
        
        self.sb_atk_force = QSpinBox()
        self.sb_atk_force.setRange(1, 999)
        self.sb_atk_force.valueChanged.connect(self.update_roster_ui)
        self.sb_atk_force.valueChanged.connect(self.auto_save)
        form_troops.addRow(STR_LBL_ATK_MAX, self.sb_atk_force)

        self.sb_def_force = QSpinBox()
        self.sb_def_force.setRange(1, 999)
        self.sb_def_force.valueChanged.connect(self.update_roster_ui)
        self.sb_def_force.valueChanged.connect(self.auto_save)
        form_troops.addRow(STR_LBL_DEF_MAX, self.sb_def_force)
        
        self.sb_max_agents = QSpinBox()
        self.sb_max_agents.setRange(1, 100)
        self.sb_max_agents.valueChanged.connect(self.auto_save)
        form_troops.addRow(STR_LBL_STACK_LIMIT, self.sb_max_agents)
        
        main_layout.addWidget(group_troops)
        
        # --- ROSTER SPLITTER ---
        roster_splitter = QSplitter(Qt.Horizontal)
        
        # Attacker Scroll
        self.atk_scroll = QScrollArea()
        self.atk_scroll.setWidgetResizable(True)
        self.atk_scroll.setMinimumWidth(300)
        atk_container = QGroupBox(STR_GRP_ATK_ROSTER)
        self.atk_layout = QVBoxLayout(atk_container)
        self.atk_layout.addWidget(self.create_header_row())
        self.atk_layout.addStretch()
        self.atk_scroll.setWidget(atk_container)
        roster_splitter.addWidget(self.atk_scroll)
        
        # Defender Scroll
        self.def_scroll = QScrollArea()
        self.def_scroll.setWidgetResizable(True)
        self.def_scroll.setMinimumWidth(300)
        def_container = QGroupBox(STR_GRP_DEF_ROSTER)
        self.def_layout = QVBoxLayout(def_container)
        self.def_layout.addWidget(self.create_header_row())
        self.def_layout.addStretch()
        self.def_scroll.setWidget(def_container)
        roster_splitter.addWidget(self.def_scroll)
        
        main_layout.addWidget(roster_splitter, 1) # Expand
        
    def create_header_row(self):
        header_widget = QWidget()
        h_layout = QHBoxLayout(header_widget)
        h_layout.setContentsMargins(0, 5, 30, 5)
        
        headers = [
            (STR_LBL_COL_NAME, 150),
            (STR_LBL_COL_WEAPON, 120),
            (STR_LBL_COL_HIERARCHY, 100),
            (STR_LBL_COL_PERSONNEL, 60),
            (STR_LBL_COL_AMMO_TYPE, 120),
            (STR_LBL_COL_TOTAL_AMMO, 80)
        ]
        
        for text, width in headers:
            lbl = QLabel(f"<b>{text}</b>")
            lbl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px; text-transform: uppercase;")
            lbl.setFixedWidth(width)
            h_layout.addWidget(lbl)
        
        h_layout.addStretch()
        return header_widget

    def calculate_tactical_name(self, index, hierarchy_text):
        """Generates name from index & hierarchy: A/Platoon1, B/Platoon1..."""
        letters = ["A", "B", "C", "D"]
        letter = letters[index % 4]
        num = (index // 4) + 1
        
        # Clean hierarchy text: "Section (10)" -> "Section"
        hierarchy = hierarchy_text.split(" ")[0].strip()
        return f"{letter}/{hierarchy}{num}"

    def spawn_roster_row(self, side, index, layout_target):
        """Creates a single agent UI configuration row."""
        row_widget = QWidget()
        h_layout = QHBoxLayout(row_widget)
        h_layout.setContentsMargins(0, 5, 0, 5)
        
        # 1. Agent Name
        initial_hierarchy = LIST_UNIT_TYPES[0]
        default_name = self.calculate_tactical_name(index, initial_hierarchy)
        name_edit = QLineEdit(default_name)
        name_edit.setPlaceholderText(STR_LBL_AGENT_NAME_PLACEHOLDER)
        name_edit.setFixedWidth(150)
        name_edit.textChanged.connect(self.auto_save)
        h_layout.addWidget(name_edit)
        
        # 2. Weapon Check
        combo_wep = QComboBox()
        combo_wep.setFixedWidth(120)
        weapons = self.state.data_controller.weapons if hasattr(self.state, 'data_controller') else {}
        for wid, wdata in weapons.items():
            name = wdata.get('name', wid)
            combo_wep.addItem(name, userData=wid)
        
        # 3. Unit Type (Hierarchy Selection)
        combo_type = QComboBox()
        combo_type.setFixedWidth(100)
        combo_type.addItems(LIST_UNIT_TYPES)
        h_layout.addWidget(combo_wep)
        h_layout.addWidget(combo_type)
        
        # 4. Personnel Count (Display Only)
        lbl_personnel = QLabel()
        lbl_personnel.setFixedWidth(60)
        lbl_personnel.setAlignment(Qt.AlignCenter)
        lbl_personnel.setStyleSheet(f"color: {Theme.ACCENT_GOOD}; font-weight: bold;")
        h_layout.addWidget(lbl_personnel)
        
        # 5. Ammo Type (Dropdown synchronized with weapon)
        ammo_type_combo = QComboBox()
        ammo_type_combo.setFixedWidth(120)
        ammo_type_combo.currentIndexChanged.connect(self.auto_save)
        h_layout.addWidget(ammo_type_combo)

        # 6. Total Ammo
        total_ammo_edit = QLineEdit("300")
        total_ammo_edit.setFixedWidth(80)
        total_ammo_edit.setPlaceholderText("Total")
        total_ammo_edit.textChanged.connect(self.auto_save)
        h_layout.addWidget(total_ammo_edit)

        def update_row_logic():
            t_text = combo_type.currentText()
            p_count = DICT_UNIT_PERSONNEL.get(t_text.split(" ")[0], 10)
            lbl_personnel.setText(str(p_count))
            
            # Update name ONLY if it was previously matching the tactical auto-format
            current_name = name_edit.text()
            is_default = any(self.calculate_tactical_name(index, h) == current_name for h in LIST_UNIT_TYPES)
            if is_default or not current_name:
                name_edit.setText(self.calculate_tactical_name(index, t_text))
            
            self.auto_save()

        def update_ammo_for_weapon():
            wid = combo_wep.currentData()
            wep_info = weapons.get(wid, {})
            default_ammo = wep_info.get("ammo_type", "NATO_556")
            
            ammo_type_combo.blockSignals(True)
            ammo_type_combo.clear()
            
            # Fetch all resource categories for ammo
            resources = self.state.data_controller.resources if hasattr(self.state, 'data_controller') else {}
            ammo_list = [rid for rid, rinfo in resources.items() if rinfo.get("category") == "Ammo"]
            
            # Add default first
            if default_ammo in ammo_list:
                if default_ammo in ammo_list: ammo_list.remove(default_ammo)
                ammo_list.insert(0, default_ammo)
            
            for rid in ammo_list:
                rinfo = resources.get(rid, {})
                display_name = rinfo.get("name", rid)
                ammo_type_combo.addItem(display_name, userData=rid)
            
            ammo_type_combo.blockSignals(False)
            self.auto_save()

        combo_type.currentIndexChanged.connect(update_row_logic)
        combo_wep.currentIndexChanged.connect(update_row_logic)
        combo_wep.currentIndexChanged.connect(update_ammo_for_weapon)
        
        update_row_logic() # Initial state
        update_ammo_for_weapon()
        
        # Info Button
        btn_info = QPushButton(LABEL_BTN_INFO)
        btn_info.setFixedWidth(30)
        btn_info.clicked.connect(lambda _, cb=combo_wep: self.show_weapon_info(cb.currentData()))
        h_layout.addWidget(btn_info)
        
        row_dict = {
            "widget": row_widget,
            "name_edit": name_edit,
            "weapon_combo": combo_wep,
            "type_combo": combo_type,
            "personnel_lbl": lbl_personnel,
            "ammo_type_combo": ammo_type_combo,
            "total_ammo_edit": total_ammo_edit
        }
        
        # Insert before stretch
        layout_target.insertWidget(layout_target.count() - 1, row_widget)
        return row_dict
        
    def show_weapon_info(self, weapon_id):
        if not weapon_id: return
        weapons = self.state.data_controller.weapons if hasattr(self.state, 'data_controller') else {}
        wdata = weapons.get(weapon_id, {})
        
        info = STR_INFO_WEAPON_FMT.format(
            name=wdata.get('name', weapon_id),
            damage=wdata.get('damage', 0),
            max_range=wdata.get('max_range', 0),
            min_range=wdata.get('min_range', 0),
            fire_rate=wdata.get('fire_rate', 1)
        )
        QMessageBox.information(self, STR_INFO_WEAPON_TITLE, info)
        
    def update_roster_ui(self, save=True):
        """Rebuilds the roster rows dynamically based on the spinboxes."""
        atk_target = self.sb_atk_force.value()
        def_target = self.sb_def_force.value()
        
        # Simple adjustment for Attackers
        while len(self.atk_roster_rows) < atk_target:
            self.atk_roster_rows.append(self.spawn_roster_row(STR_ROLE_ATTACKER, len(self.atk_roster_rows), self.atk_layout))
        while len(self.atk_roster_rows) > atk_target:
            row = self.atk_roster_rows.pop()
            row["widget"].setParent(None)
            
        # Simple adjustment for Defenders
        while len(self.def_roster_rows) < def_target:
            self.def_roster_rows.append(self.spawn_roster_row(STR_ROLE_DEFENDER, len(self.def_roster_rows), self.def_layout))
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
        saved_roster = rules.get("roster", {STR_ROLE_ATTACKER: [], STR_ROLE_DEFENDER: []})
        
        for i, row in enumerate(self.atk_roster_rows):
            if i < len(saved_roster.get(STR_ROLE_ATTACKER, [])):
                entry = saved_roster[STR_ROLE_ATTACKER][i]
                row["name_edit"].blockSignals(True)
                default_name = self.calculate_tactical_name(i, LIST_UNIT_TYPES[0])
                row["name_edit"].setText(entry.get("name", default_name))
                row["name_edit"].blockSignals(False)
                idx_w = row["weapon_combo"].findData(entry.get("weapon_id"))
                if idx_w >= 0: row["weapon_combo"].setCurrentIndex(idx_w)
                idx_t = row["type_combo"].findText(entry.get("type_display", LIST_UNIT_TYPES[0]))
                if idx_t >= 0: row["type_combo"].setCurrentIndex(idx_t)
                
                # Restore ammo dropdown
                idx_a = row["ammo_type_combo"].findData(entry.get("ammo_type"))
                if idx_a >= 0: row["ammo_type_combo"].setCurrentIndex(idx_a)
                
                row["total_ammo_edit"].setText(str(entry.get("total_ammo", "300")))
                
        for i, row in enumerate(self.def_roster_rows):
            if i < len(saved_roster.get(STR_ROLE_DEFENDER, [])):
                entry = saved_roster[STR_ROLE_DEFENDER][i]
                row["name_edit"].blockSignals(True)
                default_name = self.calculate_tactical_name(i, LIST_UNIT_TYPES[0])
                row["name_edit"].setText(entry.get("name", default_name))
                row["name_edit"].blockSignals(False)
                idx_w = row["weapon_combo"].findData(entry.get("weapon_id"))
                if idx_w >= 0: row["weapon_combo"].setCurrentIndex(idx_w)
                idx_t = row["type_combo"].findText(entry.get("type_display", LIST_UNIT_TYPES[0]))
                if idx_t >= 0: row["type_combo"].setCurrentIndex(idx_t)

                # Restore ammo dropdown
                idx_a = row["ammo_type_combo"].findData(entry.get("ammo_type"))
                if idx_a >= 0: row["ammo_type_combo"].setCurrentIndex(idx_a)

                row["total_ammo_edit"].setText(str(entry.get("total_ammo", "300")))

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
        
        # Save exact entity rosters (preserving 'placed' status and UIDs from existing data)
        roster_data = {STR_ROLE_ATTACKER: [], STR_ROLE_DEFENDER: []}
        existing_roster = rules.get("roster", {STR_ROLE_ATTACKER: [], STR_ROLE_DEFENDER: []})
        
        for i, row in enumerate(self.atk_roster_rows):
            t_text = row["type_combo"].currentText()
            personnel = DICT_UNIT_PERSONNEL.get(t_text.split(" ")[0], 10)
            
            # Preserve existing placement status and UID
            was_placed = False
            existing_uid = None
            atks = existing_roster.get(STR_ROLE_ATTACKER, [])
            if i < len(atks):
                was_placed = atks[i].get("placed", False)
                existing_uid = atks[i].get("uid")
            
            roster_data[STR_ROLE_ATTACKER].append({
                "uid": existing_uid or str(uuid.uuid4())[:8],
                "name": row["name_edit"].text().strip(),
                "weapon_id": row["weapon_combo"].currentData(),
                "type_display": row["type_combo"].currentText(),
                "personnel": personnel,
                "ammo_type": row["ammo_type_combo"].currentData(),
                "total_ammo": row["total_ammo_edit"].text().strip(),
                "side": STR_ROLE_ATTACKER,
                "placed": was_placed
            })
            
        for i, row in enumerate(self.def_roster_rows):
            t_text = row["type_combo"].currentText()
            personnel = DICT_UNIT_PERSONNEL.get(t_text.split(" ")[0], 10)
            
            # Preserve existing placement status and UID
            was_placed = False
            existing_uid = None
            defs = existing_roster.get(STR_ROLE_DEFENDER, [])
            if i < len(defs):
                was_placed = defs[i].get("placed", False)
                existing_uid = defs[i].get("uid")
            
            roster_data[STR_ROLE_DEFENDER].append({
                "uid": existing_uid or str(uuid.uuid4())[:8],
                "name": row["name_edit"].text().strip(),
                "weapon_id": row["weapon_combo"].currentData(),
                "type_display": row["type_combo"].currentText(),
                "personnel": personnel,
                "ammo_type": row["ammo_type_combo"].currentData(),
                "total_ammo": row["total_ammo_edit"].text().strip(),
                "side": STR_ROLE_DEFENDER,
                "placed": was_placed
            })
            
        rules["roster"] = roster_data
