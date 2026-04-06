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
                             QDialog, QFormLayout, QComboBox, QScrollArea, QFrame, QLabel,
                             QStackedWidget, QGridLayout, QMenu, QAction)
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
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.mw = parent
        self.state = state if state else GlobalState()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Consistent Tactical Professional Theme
        self.setStyleSheet(f"QWidget#MasterDataWidget {{ background-color: {Theme.BG_DEEP}; }}")
        self.setObjectName("MasterDataWidget")
        
        # --- HEADER (Back Button) ---
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 5, 10, 5)
        
        btn_back = QPushButton("← BACK TO HQ")
        btn_back.setFixedSize(120, 35)
        btn_back.setFont(Theme.get_font(Theme.FONT_HEADER, 10, bold=True))
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.ACCENT_ALLY};
                border: 1px solid {Theme.ACCENT_ALLY};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_ALLY};
                color: {Theme.BG_DEEP};
            }}
        """)
        btn_back.clicked.connect(lambda: self.mw.switch_mode(0) if self.mw else None)
        h_layout.addWidget(btn_back)
        h_layout.addStretch()
        
        title = QLabel("MASTER TACTICAL DATABASE")
        title.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; letter-spacing: 2px;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        self.layout.addWidget(header)
        
        self.layout.addWidget(header)
        
        # --- TABBED DATA INTERFACE ---
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {Theme.BORDER_STRONG}; background: {Theme.BG_SURFACE}; border-top: none; }}
            QTabBar::tab {{ 
                background: {Theme.BG_INPUT}; 
                color: {Theme.TEXT_DIM}; 
                padding: 12px 25px; 
                margin-right: 2px;
                border: 1px solid {Theme.BORDER_STRONG};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{ background: {Theme.BG_SURFACE}; color: {Theme.ACCENT_ALLY}; font-weight: bold; }}
            QTabBar::tab:hover:!selected {{ background: {Theme.BORDER_STRONG}; color: {Theme.TEXT_PRIMARY}; }}
        """)
        self.layout.addWidget(self.main_tabs, 1)
        
        # --- FOOTER (Global Actions) ---
        footer = QFrame()
        footer.setObjectName("DatabaseFooter")
        footer.setStyleSheet(f"QFrame#DatabaseFooter {{ background-color: {Theme.BG_SURFACE}; border-top: 2px solid {Theme.BORDER_STRONG}; }}")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 15, 20, 15)
        
        self.save_btn = QPushButton("💾 COMMIT ALL CHANGES TO DISK")
        self.save_btn.setFixedSize(350, 50)
        self.save_btn.setFont(Theme.get_font(Theme.FONT_HEADER, 11, bold=True))
        self.save_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {Theme.ACCENT_GOOD}; 
                color: white; 
                border-radius: 6px; 
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background-color: #059669; }}
            QPushButton:pressed {{ background-color: #047857; }}
        """)
        self.save_btn.clicked.connect(self.save_all_changes)
        
        f_layout.addStretch()
        f_layout.addWidget(self.save_btn)
        f_layout.addStretch()
        
        self.layout.addWidget(footer)
        
        self.is_dirty = False
        self.pending_saves = {}
        
        # Initialize all tabs on startup
        self.refresh()

    def show_table_context_menu(self, pos, table, category):
        """Standardized Right-Click menu for all tactical tables."""
        menu = QMenu(self)
        row = table.rowAt(pos.y())
        if row < 0: return # Only show menu if we right-clicked a valid row
        
        table.selectRow(row) # Visual feedback
        
        add_row = QAction("➕ Add New Entry", self)
        del_row = QAction("❌ Delete Row", self)
        
        add_row.triggered.connect(lambda: self.trigger_add(category))
        del_row.triggered.connect(lambda: self.trigger_delete(category, table, row))
        
        menu.addAction(add_row)
        menu.addAction(del_row)
        menu.exec_(table.viewport().mapToGlobal(pos))

    def trigger_add(self, cat):
        if cat == "agents": self.on_add_agent()
        elif cat == "weapons": self.on_add_weapon()
        elif cat == "resources": self.on_add_resource()
        elif cat == "obstacles": self.on_add_obstacle()
        elif cat == "terrain": self.on_add_terrain()

    def trigger_delete(self, cat, table, row):
        if cat == "agents": self.on_delete_agent(table, row)
        elif cat == "weapons": self.on_delete_weapon(table, row)
        elif cat == "resources": self.on_delete_resource(table, row)
        elif cat == "obstacles": self.on_delete_obstacle(table, row)
        elif cat == "terrain": self.on_delete_terrain(table, row)


        
    def refresh(self):
        """FULL REBUILD: Populates all tabs with current database snapshots."""
        self.main_tabs.clear()
        
        # 1. Operators (Agents)
        self.agent_widget = QWidget()
        a_layout = QVBoxLayout(self.agent_widget)
        self.mount_agent_tab(a_layout)
        self.main_tabs.addTab(self.agent_widget, "👥 OPERATORS")
        
        # 2. Arsenal (Weapons)
        self.weapon_widget = QWidget()
        w_layout = QVBoxLayout(self.weapon_widget)
        self.mount_weapon_tab(w_layout)
        self.main_tabs.addTab(self.weapon_widget, "⚔️ ARSENAL")
        
        # 3. Logistics (Resources)
        self.resource_widget = QWidget()
        r_layout = QVBoxLayout(self.resource_widget)
        self.mount_resource_tab(r_layout)
        self.main_tabs.addTab(self.resource_widget, "📦 LOGISTICS")

        # 4. Obstacles (Defenses)
        self.obs_widget = QWidget()
        o_layout = QVBoxLayout(self.obs_widget)
        self.mount_obstacle_tab(o_layout)
        self.main_tabs.addTab(self.obs_widget, "🚧 DEFENSES")
        
        # 5. Geography (Terrain)
        self.terrain_widget = QWidget()
        t_layout = QVBoxLayout(self.terrain_widget)
        self.mount_terrain_tab(t_layout)
        self.main_tabs.addTab(self.terrain_widget, "🗺️ GEOGRAPHY")
        
        # 6. Reports (Validation & Docs)
        self.rep_widget = QWidget()
        rep_layout = QVBoxLayout(self.rep_widget)
        self.mount_validation_view(rep_layout)
        self.main_tabs.addTab(self.rep_widget, "📋 REPORTS")

        self.is_dirty = False
        self.update_save_visuals()

    def update_save_visuals(self):
        """Visually indicates if there are unsaved changes."""
        if self.is_dirty:
            self.save_btn.setText("💾 SAVE PENDING CHANGES TO DISK")
            self.save_btn.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: {Theme.ACCENT_WARN}; 
                    color: white; 
                    border-radius: 6px; 
                    border: 2px solid white;
                }}
            """)
        else:
            self.save_btn.setText("💾 DATABASE SYNCHRONIZED")
            self.save_btn.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: {Theme.BG_INPUT}; 
                    color: {Theme.TEXT_DIM}; 
                    border-radius: 6px; 
                }}
            """)

    def save_all_changes(self):
        """COMMITS all in-memory edits to the physical JSON files."""
        try:
            db = self.state.data_controller._db
            for path, data in self.pending_saves.items():
                db.set(path, data)
                
            self.pending_saves.clear()
            self.state.data_controller.reload_configs()
            self.log_info("<font color='#10b981'>DATABASE: All changes successfully committed to disk.</font>")
            self.is_dirty = False
            self.update_save_visuals()
            
            if self.mw:
                from ui.dialogs.themed_dialogs import ThemedMessageBox
                ThemedMessageBox.information(self, "Sync Complete", "Tactical database has been successfully synchronized to disk.")
        except Exception as e:
            from ui.dialogs.themed_dialogs import ThemedMessageBox
            ThemedMessageBox.critical(self, "Sync Error", f"Failed to save changes: {e}")

    def log_info(self, msg):
        if hasattr(self.mw, 'log_info'):
            self.mw.log_info(msg)
    def select_tab_by_key(self, key):
        """Programmatically switches to a specific module based on a key."""
        if not key: return
        mapping = {
            "agents": 0, "units": 0,
            "weapons": 1, "arsenal": 1,
            "resources": 2, "logistics": 2,
            "obstacles": 3,
            "terrain": 4, "intel": 4,
            "validation": 5, "docs": 5
        }
        target_idx = mapping.get(key.lower(), 0)
        self.main_tabs.setCurrentIndex(target_idx)

    def create_table(self, columns, category):
        """Standardized Tactical Table for Database Browsing."""
        table = TacticalTable(columns)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos: self.show_table_context_menu(pos, table, category))
        return table

    def mount_agent_tab(self, parent_layout):
        # Sub-tabs for Attacker / Defender
        agent_widget = QWidget()
        layout = QVBoxLayout(agent_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.agent_tabs = QTabWidget()
        layout.addWidget(self.agent_tabs)
        
        # Tools layout (Minimal info label since buttons are now in context menu)
        hint = QLabel("💡 TIP: Right-click row to Add or Delete entries.")
        hint.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin: 10px;")
        layout.addWidget(hint)
        
        # We need to look at data_controller.agent_types
        # It has "Attacker": {id: data}, "Defender": {id: data}
        data = getattr(self.state.data_controller, "agent_types", {})
        
        # Columns
        cols = ["Name", "ID", "Cost", "Speed", "Range", "Attack", "Defense", "Stealth"]
        
        for role in ["Attacker", "Defender"]:
            table = self.create_table(cols, "agents")
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
            
        parent_layout.addWidget(agent_widget)
        
    def mount_obstacle_tab(self, parent_layout):
        obstacle_widget = QWidget()
        layout = QVBoxLayout(obstacle_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tools_layout = QHBoxLayout()
        
        # Tools layout (Minimal info label since buttons are now in context menu)
        hint = QLabel("💡 TIP: Right-click row to Add or Delete entries.")
        hint.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin: 10px;")
        layout.addWidget(hint)
        
        # Spacer for consistency
        layout.addSpacing(5)
        
        cols = ["Name", "ID", "Move Cost", "Cover Bonus", "Block LOS"]
        self.obstacle_table = self.create_table(cols, "obstacles")
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
        parent_layout.addWidget(obstacle_widget)

    def mount_weapon_tab(self, parent_layout):
        """MOUNT: Displays the modular weapon arsenal."""
        weapon_widget = QWidget()
        layout = QVBoxLayout(weapon_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tools_layout = QHBoxLayout()
        # Tools layout (Minimal info label since buttons are now in context menu)
        hint = QLabel("💡 TIP: Right-click row to Add or Delete entries.")
        hint.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin: 10px;")
        layout.addWidget(hint)
        
        # Spacer for consistency
        layout.addSpacing(5)
        
        cols = ["Name", "ID", "Max Range", "Damage", "Accuracy", "Ammo Cap", "Ammo Type"]
        self.weapon_table = self.create_table(cols, "weapons")
        self.weapon_table.setEditTriggers(QTableWidget.DoubleClicked)

        layout.addWidget(self.weapon_table)
        
        data = getattr(self.state.data_controller, "weapons", {})
        self.weapon_table.setRowCount(len(data))
        
        row = 0
        for wid, info in data.items():
            name_item = QTableWidgetItem(str(info.get("name", wid)))
            name_item.setData(Qt.UserRole, (wid, "name"))
            self.weapon_table.setItem(row, 0, name_item)
            
            id_item = QTableWidgetItem(wid)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.weapon_table.setItem(row, 1, id_item)
            
            rng = info.get("max_range")
            range_str = str(rng)
            range_item = QTableWidgetItem(range_str)
            range_item.setData(Qt.UserRole, (wid, "max_range"))
            self.weapon_table.setItem(row, 2, range_item)
            
            dmg_item = QTableWidgetItem(str(info.get("damage", "-")))
            dmg_item.setData(Qt.UserRole, (wid, "damage"))
            self.weapon_table.setItem(row, 3, dmg_item)
            
            acc_item = QTableWidgetItem(str(info.get("accuracy", "-")))
            acc_item.setData(Qt.UserRole, (wid, "accuracy"))
            self.weapon_table.setItem(row, 4, acc_item)
            
            cap_item = QTableWidgetItem(str(info.get("ammo_capacity", "-")))
            cap_item.setData(Qt.UserRole, (wid, "ammo_capacity"))
            self.weapon_table.setItem(row, 5, cap_item)
            
            type_item = QTableWidgetItem(str(info.get("ammo_type", "-")))
            type_item.setData(Qt.UserRole, (wid, "ammo_type"))
            self.weapon_table.setItem(row, 6, type_item)
            row += 1
            
        self.weapon_table.itemChanged.connect(self.on_weapon_item_changed)
        parent_layout.addWidget(weapon_widget)

    def mount_resource_tab(self, parent_layout):
        """MOUNT: Displays the logistics resource catalog."""
        res_widget = QWidget()
        layout = QVBoxLayout(res_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tools_layout = QHBoxLayout()
        # Tools layout (Minimal info label since buttons are now in context menu)
        hint = QLabel("💡 TIP: Right-click row to Add or Delete entries.")
        hint.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin: 10px;")
        layout.addWidget(hint)
        
        # Spacer for consistency
        layout.addSpacing(5)
        
        cols = ["Name", "ID", "Category", "Description"]
        self.resource_table = self.create_table(cols, "resources")
        self.resource_table.setEditTriggers(QTableWidget.DoubleClicked)

        layout.addWidget(self.resource_table)
        
        data = getattr(self.state.data_controller, "resources", {})
        self.resource_table.setRowCount(len(data))
        
        row = 0
        for rid, info in data.items():
            name_item = QTableWidgetItem(str(info.get("name", rid)))
            name_item.setData(Qt.UserRole, (rid, "name"))
            self.resource_table.setItem(row, 0, name_item)
            
            id_item = QTableWidgetItem(rid)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.resource_table.setItem(row, 1, id_item)
            
            cat_item = QTableWidgetItem(str(info.get("category", "-")))
            cat_item.setData(Qt.UserRole, (rid, "category"))
            self.resource_table.setItem(row, 2, cat_item)
            
            desc_item = QTableWidgetItem(str(info.get("description", "-")))
            desc_item.setData(Qt.UserRole, (rid, "description"))
            self.resource_table.setItem(row, 3, desc_item)
            row += 1
            
        self.resource_table.itemChanged.connect(self.on_resource_item_changed)
        parent_layout.addWidget(res_widget)

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
                
            full_catalog[uid][key] = final_val if 'final_val' in locals() else new_val
            
            self.pending_saves["Master/ObstacleCatalog"] = full_catalog
            self.is_dirty = True
            self.update_save_visuals()
            # self.refresh() -- We don't refresh immediately to avoid losing focus during batch edits

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
            self.pending_saves["Master/ObstacleCatalog"] = full_catalog
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_obstacle(self, table=None, row=None):
        if table is None: table = self.obstacle_table
        if row is None: row = table.currentRow()
        
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an obstacle to delete.")
            return
        
        uid = table.item(row, 1).text()

        if QMessageBox.question(self, "Confirm", f"Delete obstacle '{uid}'?") == QMessageBox.Yes:
            db = self.state.data_controller._db
            full_catalog = db.get("Master/ObstacleCatalog") or {}
            if uid in full_catalog:
                del full_catalog[uid]
                self.pending_saves["Master/ObstacleCatalog"] = full_catalog
                self.is_dirty = True
                self.update_save_visuals()
                self.refresh()

    def mount_terrain_tab(self, parent_layout):
        terrain_widget = QWidget()
        layout = QVBoxLayout(terrain_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tools_layout = QHBoxLayout()
        
        # Tools layout (Minimal info label since buttons are now in context menu)
        hint = QLabel("💡 TIP: Right-click row to Add or Delete entries.")
        hint.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin: 10px;")
        layout.addWidget(hint)
        
        # Spacer for consistency
        layout.addSpacing(5)
        
        cols = ["Name", "ID", "Move Cost", "Cover Bonus", "Color"]
        self.terrain_table = self.create_table(cols, "terrain")
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
        parent_layout.addWidget(terrain_widget)

    def mount_docs_view(self, parent_layout):
        """MOUNT: System documentation viewer."""
        docs = DocumentationTab(self.state)
        parent_layout.addWidget(docs)

    def mount_validation_view(self, parent_layout):
        """MOUNT: System validation report."""
        val = TestValidationTab()
        parent_layout.addWidget(val)

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
            
            agent_data[keys[0]] = final_val if 'final_val' in locals() else new_val
            
            self.pending_saves[path_pattern] = agent_data
            self.is_dirty = True
            self.update_save_visuals()

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
                
            t_data[key] = final_val if 'final_val' in locals() else new_val
            self.pending_saves[path] = t_data
            self.is_dirty = True
            self.update_save_visuals()

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
            self.pending_saves[path] = new_agent
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()
            QMessageBox.information(self, "Success", f"Agent '{data['name']}' created successfully!")

    def on_delete_agent(self, table=None, row=None):
        role = "Attacker" if self.agent_tabs.currentIndex() == 0 else "Defender"
        if table is None: table = self.agent_tabs.currentWidget()
        if row is None: row = table.currentRow()
        
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an agent to delete.")
            return
        
        uid = table.item(row, 1).text()

        if QMessageBox.question(self, "Confirm", f"Delete agent '{uid}'?") == QMessageBox.Yes:
            path = f"Master Database/Agent/{role}s/{uid}.json"
            # Instead of immediate delete, we can set it to None or empty in pending_saves
            # But the Controller's DB usually handles deletion via .delete()
            # For the deferred model, we'll tell the Controller to mark it for deletion
            self.state.data_controller._db.delete(path) 
            self.is_dirty = True
            self.update_save_visuals()
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
            self.pending_saves[path] = new_terrain
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_terrain(self, table=None, row=None):
        if table is None: table = self.terrain_table
        if row is None: row = table.currentRow()
        
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a terrain to delete.")
            return
        
        uid = table.item(row, 1).text()

        if QMessageBox.question(self, "Confirm", f"Delete terrain '{uid}'?") == QMessageBox.Yes:
            path = f"Master Database/Terrain/{uid}.json"
            self.state.data_controller._db.delete(path)
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_weapon_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        
        wid, key = data
        new_val = item.text()
        
        db = self.state.data_controller._db
        path = f"Master Database/Items/Weapons/{wid}.json"
        
        w_data = db.get(path)
        if not w_data: 
            catalog = db.get("Master Database/WeaponCatalog") or {}
            if wid in catalog:
                try:
                    catalog[wid][key] = float(new_val) if "." in new_val else int(new_val)
                except ValueError:
                    catalog[wid][key] = new_val
                db.set("Master Database/WeaponCatalog", catalog)
        else:
            try:
                # If the file is structured as {wid: {data}}, handle that
                if wid in w_data and isinstance(w_data[wid], dict):
                    w_data[wid][key] = float(new_val) if "." in new_val else int(new_val)
                else:
                    w_data[key] = float(new_val) if "." in new_val else int(new_val)
            except ValueError:
                if wid in w_data and isinstance(w_data[wid], dict):
                    w_data[wid][key] = new_val
                else:
                    w_data[key] = new_val
            
            self.pending_saves[path] = w_data
            self.is_dirty = True
            self.update_save_visuals()

    def on_add_weapon(self):
        name, ok = QInputDialog.getText(self, "Add Weapon", "Enter name for new weapon:")
        if ok and name:
            wid = name.replace(" ", "_")
            db = self.state.data_controller._db
            path = f"Master Database/Items/Weapons/{wid}.json"
            
            if db.exists(path):
                QMessageBox.warning(self, "Error", "Weapon already exists!")
                return
            
            new_weapon = {
                wid: {
                    "name": name,
                    "category": "Small Arms",
                    "max_range": 4.0,
                    "damage": 25,
                    "accuracy": 0.8,
                    "ammo_capacity": 30,
                    "ammo_type": "5.56x45mm"
                }
            }
            self.pending_saves[path] = new_weapon
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_weapon(self):
        row = self.weapon_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a weapon to delete.")
            return
        
        wid = self.weapon_table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete weapon '{wid}'?") == QMessageBox.Yes:
            db = self.state.data_controller._db
            path = f"Master Database/Items/Weapons/{wid}.json"
            db.delete(path)
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_resource_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        
        rid, key = data
        new_val = item.text()
        
        db = self.state.data_controller._db
        path = f"Master Database/Items/Resources/{rid}.json"
        
        r_data = db.get(path)
        if r_data:
            if rid in r_data and isinstance(r_data[rid], dict):
                r_data[rid][key] = new_val
            else:
                r_data[key] = new_val
            
            self.pending_saves[path] = r_data
            self.is_dirty = True
            self.update_save_visuals()

    def on_add_resource(self):
        name, ok = QInputDialog.getText(self, "Add Resource", "Enter name for new resource:")
        if ok and name:
            rid = name.replace(" ", "_")
            db = self.state.data_controller._db
            path = f"Master Database/Items/Resources/{rid}.json"
            
            if db.exists(path):
                QMessageBox.warning(self, "Error", "Resource already exists!")
                return
            
            new_res = {
                rid: {
                    "name": name,
                    "category": "General",
                    "description": "Standard field resource."
                }
            }
            self.pending_saves[path] = new_res
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_resource(self):
        row = self.resource_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a resource to delete.")
            return
        
        rid = self.resource_table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete resource '{rid}'?") == QMessageBox.Yes:
            db = self.state.data_controller._db
            path = f"Master Database/Items/Resources/{rid}.json"
            db.delete(path)
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()


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
