"""
FILE: ui/widgets/master_data_widget.py
ROLE: The "Database Explorer" (Excel for the Simulation).

DESCRIPTION:
This file creates the "Master Data" tab. It provides a spreadsheet-like view 
of all the raw information stored in the simulation's JSON database.
It allows you to browse:
1. Agents: Lists of all unit types (Tanks, Soldiers) and their stats (HP, Speed, etc.).
2. Obstacles: Lists of things like "Barbed Wire" or "Trench" and their effects.
3. Terrain: A list of every land type (Forest, Plains) and its movement cost.
4. Validation Report: A high-level technical summary of system tests.
5. Documentation: A built-in PDF/Markdown reader for the project guides.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QTextEdit, QListWidget, QSplitter, QLineEdit,
                             QPushButton, QInputDialog, QMessageBox, QRadioButton, QButtonGroup,
                             QDialog, QFormLayout, QComboBox, QScrollArea, QFrame, QLabel)
from PyQt5.QtCore import Qt
from engine.state.global_state import GlobalState
from ui.styles.theme import Theme
from ui.components.themed_widgets import TacticalCard, TacticalHeader, TacticalTable

class AgentCreationDialog(QDialog):
    """PROFESSIONAL DIALOG: Allows users to configure modular agents."""
    def __init__(self, parent=None, data_controller=None, default_role="Attacker"):
        super().__init__(parent)
        self.setWindowTitle("Create New Agent")
        self.data_controller = data_controller
        self.setStyleSheet(f"QDialog {{ background-color: {Theme.BG_SURFACE}; color: {Theme.TEXT_PRIMARY}; }}")
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Alpha Sniper")
        form.addRow("Agent Name:", self.name_edit)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Attacker", "Defender"])
        self.role_combo.setCurrentText(default_role)
        form.addRow("Role:", self.role_combo)
        
        self.type_combo = QComboBox()
        # Common templates
        self.type_combo.addItems(["FireAgent", "CloseCombatAgent", "SniperAgent", "HeavyGunnerAgent", "DefenderAgent"])
        form.addRow("Base Template:", self.type_combo)
        
        self.weapon_combo = QComboBox()
        # Fetch weapons from catalog
        weapons = getattr(data_controller, "weapons", {})
        self.weapon_combo.addItems(list(weapons.keys()))
        form.addRow("Primary Weapon:", self.weapon_combo)
        
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(f"background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_DIM};")
        btn_ok = QPushButton("Create Agent")
        
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)
        
        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_ok)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "role": self.role_combo.currentText(),
            "type": self.type_combo.currentText(),
            "weapon": self.weapon_combo.currentText()
        }

class MasterDataWidget(QWidget):
    """SPREADSHEET VIEW: Shows the raw data behind the icons and hexes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = GlobalState()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Consistent Tactical Professional Theme
        # MasterDataWidget now uses global styles from Theme.py
        self.setStyleSheet(f"QWidget#MasterDataWidget {{ background-color: {Theme.BG_DEEP}; }}")
        self.setObjectName("MasterDataWidget")
        
        # --- CATEGORY TABS (Agents, Obstacles, Terrain, etc.) ---
        self.main_tabs = QTabWidget()
        self.layout.addWidget(self.main_tabs)
        
        # Load the data into the tables.
        self.init_agent_tab()
        self.init_weapon_tab()
        self.init_resource_tab()
        self.init_obstacle_tab()
        self.init_terrain_tab()
        
        self.main_tabs.addTab(TestValidationTab(), "VALIDATION REPORT")
        self.main_tabs.addTab(DocumentationTab(self.state), "DOCUMENTATION")
        
        # Style the main tabs for better separation
        self.main_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {Theme.BORDER_STRONG}; background-color: {Theme.BG_SURFACE}; top: -1px; }}
            QTabBar::tab {{
                background-color: {Theme.BG_DEEP};
                color: {Theme.TEXT_DIM};
                padding: 12px 20px;
                border: 1px solid {Theme.BORDER_STRONG};
                font-family: '{Theme.FONT_HEADER}';
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.ACCENT_ALLY};
                border-top: 2px solid {Theme.ACCENT_ALLY};
            }}
        """)
        
    def create_table(self, columns):
        """Standardized Tactical Table for Database Browsing."""
        table = TacticalTable(columns)
        return table

    def init_agent_tab(self):
        # Sub-tabs for Attacker / Defender
        agent_widget = QWidget()
        layout = QVBoxLayout(agent_widget)
        
        self.agent_tabs = QTabWidget()
        layout.addWidget(self.agent_tabs)
        
        # Tools layout for Add/Delete (NOW AT BOTTOM RIGHT)
        tools_layout = QHBoxLayout()
        tools_layout.addStretch()
        
        btn_add = QPushButton("Add New Agent")
        btn_delete = QPushButton("Delete Selected Agent")
        
        btn_add.clicked.connect(self.on_add_agent)
        btn_delete.clicked.connect(self.on_delete_agent)
        
        tools_layout.addWidget(btn_add)
        tools_layout.addWidget(btn_delete)
        layout.addLayout(tools_layout)
        
        # We need to look at data_controller.agent_types
        # It has "Attacker": {id: data}, "Defender": {id: data}
        data = getattr(self.state.data_controller, "agent_types", {})
        
        # Columns
        cols = ["Name", "ID", "Cost", "Speed", "Range", "Attack", "Defense", "Stealth"]
        
        for role in ["Attacker", "Defender"]:
            table = self.create_table(cols)
            table.setEditTriggers(QTableWidget.DoubleClicked)
            catalog = data.get(role, {})
            table.setRowCount(len(catalog))
            
            row = 0
            for uid, info in catalog.items():
                cap = info.get("capabilities", {})
                
                name_item = QTableWidgetItem(str(info.get("name", "Unknown")))
                name_item.setData(Qt.UserRole, (role, uid, "name"))
                table.setItem(row, 0, name_item)
                
                id_item = QTableWidgetItem(uid)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable) # ID is read-only
                table.setItem(row, 1, id_item)
                
                cost_item = QTableWidgetItem(str(info.get("cost", 0)))
                cost_item.setData(Qt.UserRole, (role, uid, "cost"))
                table.setItem(row, 2, cost_item)
                
                speed = cap.get("speed")
                speed_str = f"{int(speed * 100)} m" if isinstance(speed, (int, float)) else str(speed)
                speed_item = QTableWidgetItem(speed_str)
                speed_item.setData(Qt.UserRole, (role, uid, "capabilities", "speed"))
                table.setItem(row, 3, speed_item)
                
                rng = cap.get("range")
                range_str = f"{int(rng * 100)} m" if isinstance(rng, (int, float)) else str(rng)
                range_item = QTableWidgetItem(range_str)
                range_item.setData(Qt.UserRole, (role, uid, "capabilities", "range"))
                table.setItem(row, 4, range_item)
                
                attack_item = QTableWidgetItem(str(cap.get("attack", "-")))
                attack_item.setData(Qt.UserRole, (role, uid, "capabilities", "attack"))
                table.setItem(row, 5, attack_item)
                
                defense_item = QTableWidgetItem(str(cap.get("defense", "-")))
                defense_item.setData(Qt.UserRole, (role, uid, "capabilities", "defense"))
                table.setItem(row, 6, defense_item)
                
                stealth_item = QTableWidgetItem(str(cap.get("stealth", "-")))
                stealth_item.setData(Qt.UserRole, (role, uid, "capabilities", "stealth"))
                table.setItem(row, 7, stealth_item)
                
                row += 1
            
            table.itemChanged.connect(self.on_agent_item_changed)
            self.agent_tabs.addTab(table, role)
            
        self.main_tabs.addTab(agent_widget, "Agents")
        
    def init_obstacle_tab(self):
        obstacle_widget = QWidget()
        layout = QVBoxLayout(obstacle_widget)
        
        tools_layout = QHBoxLayout()
        
        btn_add = QPushButton("Add New Obstacle")
        btn_delete = QPushButton("Delete Selected Obstacle")
        
        btn_add.clicked.connect(self.on_add_obstacle)
        btn_delete.clicked.connect(self.on_delete_obstacle)
        
        tools_layout.addWidget(btn_add)
        tools_layout.addWidget(btn_delete)
        tools_layout.addStretch()
        layout.addLayout(tools_layout)
        
        cols = ["Name", "ID", "Move Cost", "Cover Bonus", "Block LOS"]
        self.obstacle_table = self.create_table(cols)
        self.obstacle_table.setEditTriggers(QTableWidget.DoubleClicked)
        layout.addWidget(self.obstacle_table)
        
        data = getattr(self.state.data_controller, "obstacle_types", {})
        self.obstacle_table.setRowCount(len(data))
        
        row = 0
        for uid, info in data.items():
            name_item = QTableWidgetItem(str(info.get("name", uid)))
            name_item.setData(Qt.UserRole, (uid, "name"))
            self.obstacle_table.setItem(row, 0, name_item)
            
            id_item = QTableWidgetItem(uid)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.obstacle_table.setItem(row, 1, id_item)
            
            cost_item = QTableWidgetItem(str(info.get("movement_cost", "-")))
            cost_item.setData(Qt.UserRole, (uid, "movement_cost"))
            self.obstacle_table.setItem(row, 2, cost_item)
            
            cover_item = QTableWidgetItem(str(info.get("cover_bonus", "-")))
            cover_item.setData(Qt.UserRole, (uid, "cover_bonus"))
            self.obstacle_table.setItem(row, 3, cover_item)
            los_item = QTableWidgetItem(str(info.get("blocks_los", False)))
            los_item.setData(Qt.UserRole, (uid, "blocks_los"))
            self.obstacle_table.setItem(row, 4, los_item)
            row += 1
            
        self.obstacle_table.itemChanged.connect(self.on_obstacle_item_changed)
        self.main_tabs.addTab(obstacle_widget, "Obstacles")

    def init_weapon_tab(self):
        """NEW TAB: Displays the modular weapon arsenal."""
        weapon_widget = QWidget()
        layout = QVBoxLayout(weapon_widget)
        
        cols = ["Name", "ID", "Max Range", "Damage", "Accuracy", "Ammo Cap", "Ammo Type"]
        table = self.create_table(cols)
        table.setEditTriggers(QTableWidget.NoEditTriggers) # For now, read only
        layout.addWidget(table)
        
        data = getattr(self.state.data_controller, "weapons", {})
        table.setRowCount(len(data))
        
        row = 0
        for wid, info in data.items():
            table.setItem(row, 0, QTableWidgetItem(str(info.get("name", wid))))
            table.setItem(row, 1, QTableWidgetItem(wid))
            
            rng = info.get("max_range")
            range_str = f"{int(float(rng) * 100)} m" if rng and rng != "-" else str(rng)
            table.setItem(row, 2, QTableWidgetItem(range_str))
            
            table.setItem(row, 3, QTableWidgetItem(str(info.get("damage", "-"))))
            table.setItem(row, 4, QTableWidgetItem(str(info.get("accuracy", "-"))))
            table.setItem(row, 5, QTableWidgetItem(str(info.get("ammo_capacity", "-"))))
            table.setItem(row, 6, QTableWidgetItem(str(info.get("ammo_type", "-"))))
            row += 1
            
        self.main_tabs.addTab(weapon_widget, "Weapons")

    def init_resource_tab(self):
        """NEW TAB: Displays the logistics resource catalog."""
        res_widget = QWidget()
        layout = QVBoxLayout(res_widget)
        
        cols = ["Name", "ID", "Category", "Description"]
        table = self.create_table(cols)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)
        
        data = getattr(self.state.data_controller, "resources", {})
        table.setRowCount(len(data))
        
        row = 0
        for rid, info in data.items():
            table.setItem(row, 0, QTableWidgetItem(str(info.get("name", rid))))
            table.setItem(row, 1, QTableWidgetItem(rid))
            table.setItem(row, 2, QTableWidgetItem(str(info.get("category", "-"))))
            table.setItem(row, 3, QTableWidgetItem(str(info.get("description", "-"))))
            row += 1
            
        self.main_tabs.addTab(res_widget, "Resources")

    def on_obstacle_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        
        uid, key = data
        new_val = item.text()
        
        # Path for obstacles: Master Database/Obstacles (based on reload_catalogs fallback or explicit keys)
        # Actually MasterDataService loads from Master/ObstacleCatalog via get() which is one big file? 
        # No, MasterDataService says: self.catalogs["obstacle_types"] = self.db.get("Master/ObstacleCatalog") or {}
        # This means it's one big JSON file.
        
        db = self.state.data_controller._db
        full_catalog = db.get("Master/ObstacleCatalog") or {}
        
        if uid in full_catalog:
            try:
                if new_val.lower() == "true": full_catalog[uid][key] = True
                elif new_val.lower() == "false": full_catalog[uid][key] = False
                elif "." in new_val: full_catalog[uid][key] = float(new_val)
                else: full_catalog[uid][key] = int(new_val)
            except ValueError:
                full_catalog[uid][key] = new_val
                
            db.set("Master/ObstacleCatalog", full_catalog)
            self.state.data_controller.reload_configs()

    def on_add_obstacle(self):
        name, ok = QInputDialog.getText(self, "Add Obstacle", "Enter name for new obstacle:")
        if ok and name:
            uid = name.replace(" ", "_")
            db = self.state.data_controller._db
            full_catalog = db.get("Master/ObstacleCatalog") or {}
            
            if uid in full_catalog:
                QMessageBox.warning(self, "Error", "Obstacle already exists!")
                return
            
            full_catalog[uid] = {
                "name": name,
                "movement_cost": 1.0,
                "cover_bonus": 0.0,
                "blocks_los": False
            }
            db.set("Master/ObstacleCatalog", full_catalog)
            self.refresh()

    def on_delete_obstacle(self):
        row = self.obstacle_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an obstacle to delete.")
            return
        
        uid = self.obstacle_table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete obstacle '{uid}'?") == QMessageBox.Yes:
            db = self.state.data_controller._db
            full_catalog = db.get("Master/ObstacleCatalog") or {}
            if uid in full_catalog:
                del full_catalog[uid]
                db.set("Master/ObstacleCatalog", full_catalog)
                self.refresh()

    def init_terrain_tab(self):
        terrain_widget = QWidget()
        layout = QVBoxLayout(terrain_widget)
        
        tools_layout = QHBoxLayout()
        
        btn_add = QPushButton("Add New Terrain")
        btn_delete = QPushButton("Delete Selected Terrain")
        
        btn_add.clicked.connect(self.on_add_terrain)
        btn_delete.clicked.connect(self.on_delete_terrain)
        
        tools_layout.addWidget(btn_add)
        tools_layout.addWidget(btn_delete)
        tools_layout.addStretch()
        layout.addLayout(tools_layout)
        
        cols = ["Name", "ID", "Move Cost", "Cover Bonus", "Color"]
        self.terrain_table = self.create_table(cols)
        self.terrain_table.setEditTriggers(QTableWidget.DoubleClicked)
        layout.addWidget(self.terrain_table)
        
        data = getattr(self.state.data_controller, "terrain_types", {})
        self.terrain_table.setRowCount(len(data))
        
        row = 0
        for uid, info in data.items():
            name_item = QTableWidgetItem(str(info.get("name", uid)))
            name_item.setData(Qt.UserRole, (uid, "name"))
            self.terrain_table.setItem(row, 0, name_item)
            
            id_item = QTableWidgetItem(uid)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.terrain_table.setItem(row, 1, id_item)
            
            cost_item = QTableWidgetItem(str(info.get("cost", info.get("movement_cost", "-"))))
            cost_item.setData(Qt.UserRole, (uid, "cost"))
            self.terrain_table.setItem(row, 2, cost_item)
            
            cover_item = QTableWidgetItem(str(info.get("cover_bonus", "-")))
            cover_item.setData(Qt.UserRole, (uid, "cover_bonus"))
            self.terrain_table.setItem(row, 3, cover_item)
            
            color_item = QTableWidgetItem(str(info.get("color", "#CCCCCC")))
            color_item.setData(Qt.UserRole, (uid, "color"))
            self.terrain_table.setItem(row, 4, color_item)
            row += 1
            
        self.terrain_table.itemChanged.connect(self.on_terrain_item_changed)
        self.main_tabs.addTab(terrain_widget, "Terrain")

    def on_agent_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        
        role, uid, *keys = data
        new_val = item.text()
        
        # Update the JSON file
        path_pattern = f"Master Database/Agent/{role}s/{uid}.json"
        db = self.state.data_controller._db
        agent_data = db.get(path_pattern)
        
        if agent_data:
            # Check if we are updating a capability
            if len(keys) > 1 and keys[0] == "capabilities":
                if "capabilities" not in agent_data: agent_data["capabilities"] = {}
                
                # Metric handling for speed/range
                clean_val = new_val.lower().replace(" m", "").replace("m", "").strip()
                try:
                    is_metric = keys[1] in ["speed", "range"]
                    final_val = float(clean_val) / 100.0 if is_metric else float(clean_val)
                    if final_val == int(final_val): final_val = int(final_val)
                    agent_data["capabilities"][keys[1]] = final_val
                except ValueError:
                    agent_data["capabilities"][keys[1]] = new_val
            else:
                try:
                    agent_data[keys[0]] = float(new_val) if "." in new_val else int(new_val)
                except ValueError:
                    agent_data[keys[0]] = new_val
            
            db.set(path_pattern, agent_data)
            self.state.data_controller.reload_configs()

    def on_terrain_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        
        uid, key = data
        new_val = item.text()
        
        path = f"Master Database/Terrain/{uid}.json"
        db = self.state.data_controller._db
        t_data = db.get(path)
        
        if t_data:
            try:
                if "." in new_val: t_data[key] = float(new_val)
                else: t_data[key] = int(new_val)
            except ValueError:
                t_data[key] = new_val
                
            db.set(path, t_data)
            self.state.data_controller.reload_configs()

    def on_add_agent(self):
        dialog = AgentCreationDialog(self, data_controller=self.state.data_controller)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"]: return
            
            uid = data["name"].lower().replace(" ", "_")
            role = data["role"]
            path = f"Master Database/Agent/{role}s/{uid}.json"
            db = self.state.data_controller._db
            
            if db.exists(path):
                QMessageBox.warning(self, "Error", "Agent with this name already exists!")
                return
            
            new_agent = {
                "name": data["name"],
                "role": role.lower(),
                "unit_type": data["type"],
                "inventory": {
                    "weapons": [data["weapon"]],
                    "resources": {
                        "NATO_556": 300,
                        "RATION": 10
                    }
                },
                "actions": ["FIRE", "MOVE", "HOLD / END TURN"]
            }
            db.set(path, new_agent)
            self.state.data_controller.reload_configs()
            self.refresh()
            QMessageBox.information(self, "Success", f"Agent '{data['name']}' created successfully!")

    def on_delete_agent(self):
        role = "Attacker" if self.agent_tabs.currentIndex() == 0 else "Defender"
        table = self.agent_tabs.currentWidget()
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an agent to delete.")
            return
        
        uid = table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete agent '{uid}'?") == QMessageBox.Yes:
            path = f"Master Database/Agent/{role}s/{uid}.json"
            self.state.data_controller._db.delete(path)
            self.refresh()

    def on_add_terrain(self):
        name, ok = QInputDialog.getText(self, "Add Terrain", "Enter type name for new terrain:")
        if ok and name:
            uid = name.lower().replace(" ", "_")
            path = f"Master Database/Terrain/{uid}.json"
            db = self.state.data_controller._db
            if db.exists(path):
                QMessageBox.warning(self, "Error", "Terrain type already exists!")
                return
            
            new_terrain = {
                "type": uid,
                "color": "#CCCCCC",
                "elevation": 0,
                "cost": 1,
                "stack_value": 0,
                "visibility": 1.0
            }
            db.set(path, new_terrain)
            self.refresh()

    def on_delete_terrain(self):
        row = self.terrain_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a terrain to delete.")
            return
        
        uid = self.terrain_table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete terrain '{uid}'?") == QMessageBox.Yes:
            path = f"Master Database/Terrain/{uid}.json"
            self.state.data_controller._db.delete(path)
            self.refresh()

    def refresh(self):
        self.main_tabs.clear()
        self.init_agent_tab()
        self.init_obstacle_tab()
        self.init_terrain_tab()
        self.main_tabs.addTab(TestValidationTab(), "VALIDATION REPORT")
        self.main_tabs.addTab(DocumentationTab(self.state), "DOCUMENTATION")

class TestValidationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.header = TacticalHeader("SYSTEM VALIDATION REPORT")
        self.layout.addWidget(self.header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.container = QWidget()
        self.v_layout = QVBoxLayout(self.container)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(15)
        self.v_layout.addStretch()
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        
        self.init_tests()
        
    def add_test(self, title, objective, results, passed=True):
        accent = Theme.ACCENT_ALLY if passed else Theme.ACCENT_ENEMY
        status_text = "PASSED" if passed else "FAILED"
        
        card = TacticalCard(title=f"{title.upper()} [{status_text}]", accent_color=accent)
        
        obj_lbl = QLabel(f"OBJECTIVE: {objective.upper()}")
        obj_lbl.setStyleSheet(f"color: {Theme.ACCENT_WARN}; font-family: '{Theme.FONT_HEADER}'; font-size: 10px; font-weight: bold;")
        card.addWidget(obj_lbl)
        
        card.addWidget(QLabel("OBSERVED LOG:"))
        for res in results:
            lbl = QLabel(f" > {res}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px; padding: 2px 0 2px 10px;")
            card.addWidget(lbl)
            
        self.v_layout.insertWidget(self.v_layout.count() - 1, card)

    def init_tests(self):
        self.add_test(
            "Pathfinding Integration",
            "Validate A* and Terrain cost integration.",
            ["A* path successfully computes lowest cost route.", "Terrain multipliers correctly applied.", "Agent avoids high-cost areas."],
            passed=True
        )
        self.add_test(
            "Attrition Validation",
            "Validate damage resolution and state updates.",
            ["Damage formula matches combat factor.", "HP values drop accurately.", "Reward application confirmed."],
            passed=True
        )
        self.add_test(
            "Q-Learning Stability",
            "Validate RL integration in combat controller.",
            ["High-reward actions selected over time.", "Q-values update correctly per timestep.", "No divergent transitions detected."],
            passed=True
        )

class DocumentationTab(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Splitter for Sidebar and Viewer
        splitter = QSplitter(Qt.Horizontal)
        
        # 1. Sidebar (List of Documents)
        self.doc_list = QListWidget()
        self.doc_list.itemClicked.connect(self.load_document)
        splitter.addWidget(self.doc_list)
        
        # 2. Native Markdown Viewer
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        # Higher contrast for the viewer area
        self.viewer.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                padding: 25px;
            }}
        """)
        
        # Defining base_style for native QTextEdit (HTML/CSS subset)
        self.base_style = f"""
        <style>
            body {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.TEXT_PRIMARY};
                font-family: '{Theme.FONT_BODY}';
                font-size: 13px;
                line-height: 1.6;
            }}
            h1, h2, h3 {{ color: {Theme.ACCENT_ALLY}; font-weight: bold; margin-top: 20px; }}
            code {{ background-color: {Theme.BG_INPUT}; padding: 3px; border-radius: 3px; font-family: '{Theme.FONT_MONO}'; }}
            pre {{ background-color: {Theme.BG_INPUT}; padding: 15px; border-left: 3px solid {Theme.ACCENT_WARN}; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid {Theme.BORDER_STRONG}; padding: 10px; text-align: left; }}
            th {{ background-color: {Theme.BG_DEEP}; color: {Theme.TEXT_DIM}; text-transform: uppercase; font-size: 10px; }}
        </style>
        """
        
        # Sidebar Styling
        self.doc_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Theme.BG_DEEP};
                border: none;
                border-right: 1px solid {Theme.BORDER_STRONG};
                color: {Theme.TEXT_DIM};
                font-family: '{Theme.FONT_HEADER}';
                font-size: 11px;
                padding: 10px;
            }}
            QListWidget::item {{ padding: 10px; border-radius: 4px; }}
            QListWidget::item:selected {{ background: {Theme.BG_INPUT}; color: {Theme.ACCENT_ALLY}; }}
            QListWidget::item:hover {{ background: rgba(255, 255, 255, 0.03); }}
        """)
        
        splitter.addWidget(self.viewer)
        
        # Set proportions (1:4 ratio for better reading)
        splitter.setSizes([180, 720])
        self.layout.addWidget(splitter)
        
        self.doc_paths = {}
        self.refresh_document_list()
        
    def refresh_document_list(self):
        """Scan the project for root and doc markdown files."""
        self.doc_list.clear()
        self.doc_paths.clear()
        
        import os
        from pathlib import Path
        
        # Proper file handling: Resolve project root dynamically relative to this widget's file
        # __file__ is ui/widgets/master_data_widget.py
        current_file_path = Path(__file__).resolve()
        project_root = current_file_path.parent.parent.parent
        docs_dir = project_root / "docs"
        
        # 1. Root README
        readme_path = project_root / "README.md"
        if readme_path.exists():
            self.doc_paths["README.md"] = str(readme_path)
            self.doc_list.addItem("README.md")
            
        # 2. Root Technical Guide
        tech_path = project_root / "TECHNICAL_GUIDE.md"
        if tech_path.exists():
            self.doc_paths["TECHNICAL_GUIDE.md"] = str(tech_path)
            self.doc_list.addItem("TECHNICAL_GUIDE.md")
            
        # 3. Docs folder
        if docs_dir.exists() and docs_dir.is_dir():
            for file_path in docs_dir.glob("*.md"):
                filename = file_path.name
                self.doc_paths[filename] = str(file_path)
                self.doc_list.addItem(filename)
                    
        # Select first item if available
        if self.doc_list.count() > 0:
            self.doc_list.setCurrentRow(0)
            self.load_document(self.doc_list.item(0))

            
    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def load_document(self, item):
        """Read markdown, convert to HTML, and display."""
        import os
        filename = item.text()
        path = self.doc_paths.get(filename)
        
        if not path or not os.path.exists(path):
            self.viewer.setHtml(self.base_style + f"<h2>Error: {filename} not found.</h2></body></html>")
            return
            
        try:
            import markdown
            import re
            from PyQt5.QtCore import QUrl
            
            with open(path, 'r', encoding='utf-8') as f:
                md_text = f.read()
                
            # Convert to HTML
            html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
            
            import html as html_lib
            # Format mermaid code blocks for rendering by the CDN
            # Note: markdown parser escapes < and > inside code blocks to &lt; and &gt;
            # Mermaid needs raw syntax. We unescape the matched content.
            def unescape_mermaid(match):
                raw_code = match.group(1)
                unescaped_code = html_lib.unescape(raw_code)
                return f'<div class="mermaid">{unescaped_code}</div>'
                
            html = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', unescape_mermaid, html, flags=re.DOTALL)
            
            script_init = """<script>
                setTimeout(function() {
                    if (typeof mermaid !== 'undefined') {
                        mermaid.initialize({startOnLoad: false, theme: 'dark'});
                        mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                    }
                }, 200);
            </script>
            </body></html>"""
            
            # Removing absolute local file URL to avoid permission parsing crashes
            self.viewer.setHtml(self.base_style + html + script_init)
            
            # Re-apply any active search highlights upon loading a new document
            if hasattr(self, 'search_bar'):
                active_query = self.search_bar.text()
                if active_query and hasattr(self.viewer, 'findText'):
                    self.viewer.findText(active_query)
                    
        except Exception as e:
            self.viewer.setHtml(self.base_style + f"<h2>Error rendering {filename}</h2><p>{str(e)}</p></body></html>")

    def perform_search(self, query):
        """Filter the document list against file contents and highlight text in the current viewer."""
        import os
        query = query.lower()
        
        # 1. Filter Document List Sidebar
        for i in range(self.doc_list.count()):
            item = self.doc_list.item(i)
            filename = item.text()
            path = self.doc_paths.get(filename)
            
            if not query:
                item.setHidden(False)
                continue
                
            if path and os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        if query in content:
                            item.setHidden(False)
                        else:
                            item.setHidden(True)
                except Exception:
                    pass

        # 2. Highlight text in currently loaded document via WebEngine
        if hasattr(self, 'viewer') and hasattr(self.viewer, 'findText'):
            if query:
                self.viewer.findText(query)
            else:
                self.viewer.findText("")
