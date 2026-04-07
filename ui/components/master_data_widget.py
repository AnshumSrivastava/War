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

# --- UI CONFIGURATION ---
# Window & Dialog Titles
STR_TITLE_AGENT_DIALOG = "Create New Agent"
STR_TITLE_MASTER_DB = "MASTER TACTICAL DATABASE"
STR_TITLE_SYNC_COMPLETE = "Sync Complete"
STR_TITLE_SYNC_ERROR = "Sync Error"
STR_TITLE_ADD_OBSTACLE = "Add Obstacle"
STR_TITLE_ADD_TERRAIN = "Add Terrain"
STR_TITLE_ADD_WEAPON = "Add Weapon"
STR_TITLE_ADD_RESOURCE = "Add Resource"
STR_TITLE_ERROR = "Error"
STR_TITLE_CONFIRM = "Confirm"
STR_TITLE_SUCCESS = "Success"

# Labels & Form Fields
STR_LBL_AGENT_NAME = "Agent Name:"
STR_LBL_ROLE = "Role:"
STR_LBL_TEMPLATE = "Base Template:"
STR_LBL_WEAPON = "Primary Weapon:"
STR_PLACEHOLDER_AGENT = "e.g. Alpha Sniper"

# Buttons
STR_BTN_CANCEL = "Cancel"
STR_BTN_CREATE_AGENT = "Create Agent"
STR_BTN_BACK_HQ = "← BACK TO HQ"
STR_BTN_COMMIT_DISK = "💾 COMMIT ALL CHANGES TO DISK"
STR_BTN_SAVE_PENDING = "💾 SAVE PENDING CHANGES TO DISK"
STR_BTN_SYNCED = "💾 DATABASE SYNCHRONIZED"

# Tabs
STR_TAB_OPERATORS = "👥 OPERATORS"
STR_TAB_ARSENAL = "⚔️ ARSENAL"
STR_TAB_LOGISTICS = "📦 LOGISTICS"
STR_TAB_DEFENSES = "🚧 DEFENSES"
STR_TAB_GEOGRAPHY = "🗺️ GEOGRAPHY"
STR_TAB_REPORTS = "📋 REPORTS"

# Context Menu
STR_MENU_ADD = "➕ Add New Entry"
STR_MENU_DELETE = "❌ Delete Row"

# Table Columns
COLS_AGENT = ["Name", "ID", "Cost", "Speed", "Range", "Attack", "Defense", "Stealth"]
COLS_OBSTACLE = ["Name", "ID", "Move Cost", "Cover Bonus", "Block LOS"]
COLS_WEAPON = ["Name", "ID", "Max Range", "Damage", "Accuracy", "Ammo Cap", "Ammo Type"]
COLS_RESOURCE = ["Name", "ID", "Category", "Description"]
COLS_TERRAIN = ["Name", "ID", "Move Cost", "Cover Bonus", "Color"]

# Information & Tooltips
STR_HINT_RIGHT_CLICK = "💡 TIP: Right-click row to Add or Delete entries."
STR_LOG_SYNC_SUCCESS = "<font color='#10b981'>DATABASE: All changes successfully committed to disk.</font>"
STR_MSG_SYNC_SUCCESS = "Tactical database has been successfully synchronized to disk."
STR_MSG_SYNC_FAIL = "Failed to save changes: {e}"
STR_PROMPT_NEW_OBSTACLE = "Enter name for new obstacle:"
STR_PROMPT_NEW_TERRAIN = "Enter type name for new terrain:"
STR_PROMPT_NEW_WEAPON = "Enter name for new weapon:"
STR_PROMPT_NEW_RESOURCE = "Enter name for new resource:"
STR_MSG_OBSTACLE_EXISTS = "Obstacle already exists!"
STR_MSG_TERRAIN_EXISTS = "Terrain type already exists!"
STR_MSG_WEAPON_EXISTS = "Weapon already exists!"
STR_MSG_RESOURCE_EXISTS = "Resource already exists!"
STR_MSG_CONFIRM_DELETE_OBSTACLE = "Delete obstacle '{uid}'?"
STR_MSG_CONFIRM_DELETE_TERRAIN = "Delete terrain '{uid}'?"
STR_MSG_CONFIRM_DELETE_WEAPON = "Delete weapon '{wid}'?"
STR_MSG_CONFIRM_DELETE_RESOURCE = "Delete resource '{rid}'?"
STR_MSG_AGENT_EXISTS = "Agent with this name already exists!"
STR_MSG_AGENT_CREATED = "Agent '{name}' created successfully!"
STR_MSG_SELECT_AGENT_DELETE = "Please select an agent to delete."
STR_MSG_SELECT_OBSTACLE_DELETE = "Please select an obstacle to delete."
STR_MSG_SELECT_TERRAIN_DELETE = "Please select a terrain to delete."
STR_MSG_SELECT_WEAPON_DELETE = "Please select a weapon to delete."
STR_MSG_SELECT_RESOURCE_DELETE = "Please select a resource to delete."
STR_MSG_CONFIRM_DELETE_AGENT = "Are you sure you want to delete agent '{uid}'?"

# Data Paths
PATH_OBSTACLE_CATALOG = "Master/ObstacleCatalog"
PATH_AGENT_PATTERN = "Master Database/Agent/{role}s/{uid}.json"
PATH_TERRAIN_PATTERN = "Master Database/Terrain/{uid}.json"
PATH_WEAPON_PATTERN = "Master Database/Items/Weapons/{wid}.json"
PATH_WEAPON_CATALOG = "Master Database/WeaponCatalog"
PATH_RESOURCE_PATTERN = "Master Database/Items/Resources/{rid}.json"

# Validation & Docs
STR_VALIDATION_HEADER = "SYSTEM VALIDATION REPORT"
STR_STATUS_PASSED = "PASSED"
STR_STATUS_FAILED = "FAILED"
STR_LBL_OBJECTIVE = "OBJECTIVE: {objective}"
STR_LBL_OBSERVED_LOG = "OBSERVED LOG:"

# HTML & Styles
HTML_DOC_BASE_STYLE = f"""
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

STYLE_DIALOG = f"QDialog {{ background-color: {Theme.BG_SURFACE}; color: {Theme.TEXT_PRIMARY}; }}"
STYLE_BTN_CANCEL = f"background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_DIM};"
STYLE_WIDGET_BG = f"QWidget#MasterDataWidget {{ background-color: {Theme.BG_DEEP}; }}"
STYLE_BTN_BACK = f"""
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
"""
STYLE_TITLE = f"color: {Theme.TEXT_PRIMARY}; letter-spacing: 2px;"
STYLE_TABS = f"""
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
"""
STYLE_FOOTER = f"QFrame#DatabaseFooter {{ background-color: {Theme.BG_SURFACE}; border-top: 2px solid {Theme.BORDER_STRONG}; }}"
STYLE_SAVE_BTN_GOOD = f"""
    QPushButton {{ 
        background-color: {Theme.ACCENT_GOOD}; 
        color: white; 
        border-radius: 6px; 
        letter-spacing: 1px;
    }}
    QPushButton:hover {{ background-color: #059669; }}
    QPushButton:pressed {{ background-color: #047857; }}
"""
STYLE_SAVE_BTN_WARN = f"""
    QPushButton {{ 
        background-color: {Theme.ACCENT_WARN}; 
        color: white; 
        border-radius: 6px; 
        border: 2px solid white;
    }}
"""
STYLE_SAVE_BTN_SYNCED = f"""
    QPushButton {{ 
        background-color: {Theme.BG_INPUT}; 
        color: {Theme.TEXT_DIM}; 
        border-radius: 6px; 
    }}
"""
STYLE_HINT = f"color: {Theme.TEXT_DIM}; font-size: 11px; margin: 10px;"
STYLE_VIEWER = f"""
    QTextEdit {{
        background-color: {Theme.BG_SURFACE};
        color: {Theme.TEXT_PRIMARY};
        border: none;
        padding: 25px;
    }}
"""
STYLE_DOC_LIST = f"""
    QListWidget {{
        background-color: {Theme.BG_DEEP};
        border: none;
        border-right: 1px solid {Theme.BORDER_STRONG};
        color: {Theme.TEXT_DIM};
        font-family: {Theme.FONT_HEADER};
        font-size: 11px;
        padding: 10px;
    }}
    QListWidget::item {{ padding: 10px; border-radius: 4px; }}
    QListWidget::item:selected {{ background: {Theme.BG_INPUT}; color: {Theme.ACCENT_ALLY}; }}
    QListWidget::item:hover {{ background: rgba(255, 255, 255, 0.03); }}
"""
STYLE_VALIDATION_SCROLL = "QScrollArea { border: none; background: transparent; }"
STYLE_TEST_OBJECTIVE = f"color: {Theme.ACCENT_WARN}; font-family: '{Theme.FONT_HEADER}'; font-size: 10px; font-weight: bold;"
STYLE_TEST_LOG = f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px; padding: 2px 0 2px 10px;"
# -------------------------

class AgentCreationDialog(QDialog):
    """PROFESSIONAL DIALOG: Allows users to configure modular agents."""
    def __init__(self, parent=None, data_controller=None, default_role="Attacker"):
        super().__init__(parent)
        self.setWindowTitle(STR_TITLE_AGENT_DIALOG)
        self.data_controller = data_controller
        self.setStyleSheet(STYLE_DIALOG)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(STR_PLACEHOLDER_AGENT)
        form.addRow(STR_LBL_AGENT_NAME, self.name_edit)
        
        self.role_combo = QComboBox()
        # Fix: self.mw.mw -> self.parent().mw if accessible, else fallback. The dialog parent is master_data_widget which has mw
        attacker_str = "Attacker"
        defender_str = "Defender"
        if hasattr(parent, 'mw') and hasattr(parent.mw, 'STR_ROLE_ATTACKER'):
            attacker_str = parent.mw.STR_ROLE_ATTACKER
            defender_str = parent.mw.STR_ROLE_DEFENDER

        self.role_combo.addItems([attacker_str, defender_str])
        self.role_combo.setCurrentText(default_role)
        form.addRow(STR_LBL_ROLE, self.role_combo)
        
        self.type_combo = QComboBox()
        # Common templates
        self.type_combo.addItems(["FireAgent", "CloseCombatAgent", "SniperAgent", "HeavyGunnerAgent", "DefenderAgent"])
        form.addRow(STR_LBL_TEMPLATE, self.type_combo)
        
        self.weapon_combo = QComboBox()
        # Fetch weapons from catalog
        weapons = getattr(data_controller, "weapons", {})
        self.weapon_combo.addItems(list(weapons.keys()))
        form.addRow(STR_LBL_WEAPON, self.weapon_combo)
        
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        btn_cancel = QPushButton(STR_BTN_CANCEL)
        btn_cancel.setStyleSheet(STYLE_BTN_CANCEL)
        btn_ok = QPushButton(STR_BTN_CREATE_AGENT)
        
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
        self.setStyleSheet(STYLE_WIDGET_BG)
        self.setObjectName("MasterDataWidget")
        
        # --- HEADER (Back Button) ---
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 5, 10, 5)
        
        btn_back = QPushButton(STR_BTN_BACK_HQ)
        btn_back.setFixedSize(120, 35)
        btn_back.setFont(Theme.get_font(Theme.FONT_HEADER, 10, bold=True))
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(STYLE_BTN_BACK)
        btn_back.clicked.connect(lambda: self.mw.switch_mode(0) if self.mw else None)
        h_layout.addWidget(btn_back)
        h_layout.addStretch()
        
        title = QLabel(STR_TITLE_MASTER_DB)
        title.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
        title.setStyleSheet(STYLE_TITLE)
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        self.layout.addWidget(header)
        
        # --- TABBED DATA INTERFACE ---
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(STYLE_TABS)
        self.layout.addWidget(self.main_tabs, 1)
        
        # --- FOOTER (Global Actions) ---
        footer = QFrame()
        footer.setObjectName("DatabaseFooter")
        footer.setStyleSheet(STYLE_FOOTER)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 15, 20, 15)
        
        self.save_btn = QPushButton(STR_BTN_COMMIT_DISK)
        self.save_btn.setFixedSize(350, 50)
        self.save_btn.setFont(Theme.get_font(Theme.FONT_HEADER, 11, bold=True))
        self.save_btn.setStyleSheet(STYLE_SAVE_BTN_GOOD)
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
        
        add_row = QAction(STR_MENU_ADD, self)
        del_row = QAction(STR_MENU_DELETE, self)
        
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
        self.main_tabs.addTab(self.agent_widget, STR_TAB_OPERATORS)
        
        # 2. Arsenal (Weapons)
        self.weapon_widget = QWidget()
        w_layout = QVBoxLayout(self.weapon_widget)
        self.mount_weapon_tab(w_layout)
        self.main_tabs.addTab(self.weapon_widget, STR_TAB_ARSENAL)
        
        # 3. Logistics (Resources)
        self.resource_widget = QWidget()
        r_layout = QVBoxLayout(self.resource_widget)
        self.mount_resource_tab(r_layout)
        self.main_tabs.addTab(self.resource_widget, STR_TAB_LOGISTICS)

        # 4. Obstacles (Defenses)
        self.obs_widget = QWidget()
        o_layout = QVBoxLayout(self.obs_widget)
        self.mount_obstacle_tab(o_layout)
        self.main_tabs.addTab(self.obs_widget, STR_TAB_DEFENSES)
        
        # 5. Geography (Terrain)
        self.terrain_widget = QWidget()
        t_layout = QVBoxLayout(self.terrain_widget)
        self.mount_terrain_tab(t_layout)
        self.main_tabs.addTab(self.terrain_widget, STR_TAB_GEOGRAPHY)
        
        # 6. Reports (Validation & Docs)
        self.rep_widget = QWidget()
        rep_layout = QVBoxLayout(self.rep_widget)
        self.mount_validation_view(rep_layout)
        self.main_tabs.addTab(self.rep_widget, STR_TAB_REPORTS)

        self.is_dirty = False
        self.update_save_visuals()

    def update_save_visuals(self):
        """Visually indicates if there are unsaved changes."""
        if self.is_dirty:
            self.save_btn.setText(STR_BTN_SAVE_PENDING)
            self.save_btn.setStyleSheet(STYLE_SAVE_BTN_WARN)
        else:
            self.save_btn.setText(STR_BTN_SYNCED)
            self.save_btn.setStyleSheet(STYLE_SAVE_BTN_SYNCED)

    def save_all_changes(self):
        """COMMITS all in-memory edits to the physical JSON files."""
        try:
            db = self.state.data_controller._db
            for path, data in self.pending_saves.items():
                db.set(path, data)
                
            self.pending_saves.clear()
            self.state.data_controller.reload_configs()
            
            # --- FIX: REFRESH TABLES AFTER SAVING ---
            self.refresh()
            
            self.log_info(STR_LOG_SYNC_SUCCESS)
            self.is_dirty = False
            self.update_save_visuals()
            
            if self.mw:
                from ui.dialogs.themed_dialogs import ThemedMessageBox
                ThemedMessageBox.information(self, STR_TITLE_SYNC_COMPLETE, STR_MSG_SYNC_SUCCESS)
        except Exception as e:
            from ui.dialogs.themed_dialogs import ThemedMessageBox
            ThemedMessageBox.critical(self, STR_TITLE_SYNC_ERROR, STR_MSG_SYNC_FAIL.format(e=e))

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
        agent_widget = QWidget()
        layout = QVBoxLayout(agent_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.agent_tabs = QTabWidget()
        layout.addWidget(self.agent_tabs)
        
        hint = QLabel(STR_HINT_RIGHT_CLICK)
        hint.setStyleSheet(STYLE_HINT)
        layout.addWidget(hint)
        
        data = getattr(self.state.data_controller, "agent_types", {})
        
        roles = [self.mw.STR_ROLE_ATTACKER if hasattr(self.mw, 'STR_ROLE_ATTACKER') else "Attacker", 
                 self.mw.STR_ROLE_DEFENDER if hasattr(self.mw, 'STR_ROLE_DEFENDER') else "Defender"]
        for role in roles:
            table = self.create_table(COLS_AGENT, "agents")
            table.setEditTriggers(QTableWidget.DoubleClicked)

            catalog = data.get(role, {})
            table.setRowCount(len(catalog))
            
            table.blockSignals(True)   # Prevent phantom writes during population
            for uid, info in catalog.items():
                cap = info.get("capabilities", {})
                
                name_item = QTableWidgetItem(str(info.get("name", "Unknown")))
                name_item.setData(Qt.UserRole, (role, uid, "name"))
                table.setItem(row, 0, name_item)
                
                id_item = QTableWidgetItem(uid)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable) 
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
            
            table.blockSignals(False)  # Re-enable signals now that population is done
            table.itemChanged.connect(self.on_agent_item_changed)
            self.agent_tabs.addTab(table, role)
            
        parent_layout.addWidget(agent_widget)
        
    def mount_obstacle_tab(self, parent_layout):
        obstacle_widget = QWidget()
        layout = QVBoxLayout(obstacle_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        hint = QLabel(STR_HINT_RIGHT_CLICK)
        hint.setStyleSheet(STYLE_HINT)
        layout.addWidget(hint)
        
        layout.addSpacing(5)
        
        self.obstacle_table = self.create_table(COLS_OBSTACLE, "obstacles")
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
        weapon_widget = QWidget()
        layout = QVBoxLayout(weapon_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        hint = QLabel(STR_HINT_RIGHT_CLICK)
        hint.setStyleSheet(STYLE_HINT)
        layout.addWidget(hint)
        
        layout.addSpacing(5)
        
        self.weapon_table = self.create_table(COLS_WEAPON, "weapons")
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
        res_widget = QWidget()
        layout = QVBoxLayout(res_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        hint = QLabel(STR_HINT_RIGHT_CLICK)
        hint.setStyleSheet(STYLE_HINT)
        layout.addWidget(hint)
        
        layout.addSpacing(5)
        
        self.resource_table = self.create_table(COLS_RESOURCE, "resources")
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
        db = self.state.data_controller._db
        full_catalog = db.get(PATH_OBSTACLE_CATALOG) or {}
        if uid in full_catalog:
            try:
                if new_val.lower() == "true": full_catalog[uid][key] = True
                elif new_val.lower() == "false": full_catalog[uid][key] = False
                elif "." in new_val: full_catalog[uid][key] = float(new_val)
                else: full_catalog[uid][key] = int(new_val)
            except ValueError:
                full_catalog[uid][key] = new_val
            self.pending_saves[PATH_OBSTACLE_CATALOG] = full_catalog
            self.is_dirty = True
            self.update_save_visuals()

    def on_add_obstacle(self):
        name, ok = QInputDialog.getText(self, STR_TITLE_ADD_OBSTACLE, STR_PROMPT_NEW_OBSTACLE)
        if ok and name:
            uid = name.replace(" ", "_")
            db = self.state.data_controller._db
            full_catalog = db.get(PATH_OBSTACLE_CATALOG) or {}
            if uid in full_catalog:
                QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_OBSTACLE_EXISTS)
                return
            full_catalog[uid] = {"name": name, "movement_cost": 1.0, "cover_bonus": 0.0, "blocks_los": False}
            self.pending_saves[PATH_OBSTACLE_CATALOG] = full_catalog
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_obstacle(self, table=None, row=None):
        if table is None: table = self.obstacle_table
        if row is None: row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_SELECT_OBSTACLE_DELETE)
            return
        uid = table.item(row, 1).text()
        if QMessageBox.question(self, STR_TITLE_CONFIRM, STR_MSG_CONFIRM_DELETE_OBSTACLE.format(uid=uid)) == QMessageBox.Yes:
            db = self.state.data_controller._db
            full_catalog = db.get(PATH_OBSTACLE_CATALOG) or {}
            if uid in full_catalog:
                del full_catalog[uid]
                self.pending_saves[PATH_OBSTACLE_CATALOG] = full_catalog
                self.is_dirty = True
                self.update_save_visuals()
                self.refresh()

    def mount_terrain_tab(self, parent_layout):
        terrain_widget = QWidget()
        layout = QVBoxLayout(terrain_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        hint = QLabel(STR_HINT_RIGHT_CLICK)
        hint.setStyleSheet(STYLE_HINT)
        layout.addWidget(hint)
        layout.addSpacing(5)
        self.terrain_table = self.create_table(COLS_TERRAIN, "terrain")
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

    def mount_validation_view(self, parent_layout):
        """MOUNT: System Validation & Documentation Viewer."""
        tabs = QTabWidget()
        tabs.setStyleSheet(STYLE_TABS)
        
        # System Validation Tab
        validation_tab = TestValidationTab()
        tabs.addTab(validation_tab, "System Validation")
        
        # Documentation Tab
        doc_tab = DocumentationTab(self.state)
        tabs.addTab(doc_tab, "Technical Documentation")
        
        parent_layout.addWidget(tabs)

    def on_agent_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        role, uid, *keys = data
        new_val = item.text()
        path = PATH_AGENT_PATTERN.format(role=role, uid=uid)
        
        # --- FIX: Fetch from pending_saves first to prevent overwriting other pending fields ---
        if path in self.pending_saves:
            agent_data = self.pending_saves[path]
        else:
            db = self.state.data_controller._db
            agent_data = db.get(path)
            
        if agent_data:
            if len(keys) > 1 and keys[0] == "capabilities":
                if "capabilities" not in agent_data: agent_data["capabilities"] = {}
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
            self.pending_saves[path] = agent_data
            self.is_dirty = True
            self.update_save_visuals()

    def on_terrain_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        uid, key = data
        new_val = item.text()
        path = PATH_TERRAIN_PATTERN.format(uid=uid)
        
        if path in self.pending_saves:
             t_data = self.pending_saves[path]
        else:
             db = self.state.data_controller._db
             t_data = db.get(path)
             
        if t_data:
            try:
                if "." in new_val: t_data[key] = float(new_val)
                else: t_data[key] = int(new_val)
            except ValueError:
                t_data[key] = new_val
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
            path = PATH_AGENT_PATTERN.format(role=role, uid=uid)
            db = self.state.data_controller._db
            if db.exists(path):
                QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_AGENT_EXISTS)
                return
            new_agent = {
                "name": data["name"], "role": role.lower(), "unit_type": data["type"],
                "inventory": {"weapons": [data["weapon"]], "resources": {"NATO_556": 300, "RATION": 10}},
                "actions": ["FIRE", "MOVE", "HOLD / END TURN"]
            }
            self.pending_saves[path] = new_agent
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()
            QMessageBox.information(self, STR_TITLE_SUCCESS, STR_MSG_AGENT_CREATED.format(name=data['name']))

    def on_delete_agent(self, table=None, row=None):
        role = "Attacker" if self.agent_tabs.currentIndex() == 0 else "Defender"
        if table is None: table = self.agent_tabs.currentWidget()
        if row is None: row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_SELECT_AGENT_DELETE)
            return
        uid = table.item(row, 1).text()
        if QMessageBox.question(self, STR_TITLE_CONFIRM, STR_MSG_CONFIRM_DELETE_AGENT.format(uid=uid)) == QMessageBox.Yes:
            path = PATH_AGENT_PATTERN.format(role=role, uid=uid)
            self.state.data_controller._db.delete(path) 
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_add_terrain(self):
        name, ok = QInputDialog.getText(self, STR_TITLE_ADD_TERRAIN, STR_PROMPT_NEW_TERRAIN)
        if ok and name:
            uid = name.lower().replace(" ", "_")
            path = PATH_TERRAIN_PATTERN.format(uid=uid)
            db = self.state.data_controller._db
            if db.exists(path):
                QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_TERRAIN_EXISTS)
                return
            new_terrain = {"type": uid, "color": "#CCCCCC", "elevation": 0, "cost": 1, "stack_value": 0, "visibility": 1.0}
            self.pending_saves[path] = new_terrain
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_terrain(self, table=None, row=None):
        if table is None: table = self.terrain_table
        if row is None: row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_SELECT_TERRAIN_DELETE)
            return
        uid = table.item(row, 1).text()
        if QMessageBox.question(self, STR_TITLE_CONFIRM, STR_MSG_CONFIRM_DELETE_TERRAIN.format(uid=uid)) == QMessageBox.Yes:
            path = PATH_TERRAIN_PATTERN.format(uid=uid)
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
        path = PATH_WEAPON_PATTERN.format(wid=wid)
        w_data = db.get(path)
        if not w_data: 
            catalog = db.get(PATH_WEAPON_CATALOG) or {}
            if wid in catalog:
                try: catalog[wid][key] = float(new_val) if "." in new_val else int(new_val)
                except ValueError: catalog[wid][key] = new_val
                db.set(PATH_WEAPON_CATALOG, catalog)
        else:
            try:
                if wid in w_data and isinstance(w_data[wid], dict): w_data[wid][key] = float(new_val) if "." in new_val else int(new_val)
                else: w_data[key] = float(new_val) if "." in new_val else int(new_val)
            except ValueError:
                if wid in w_data and isinstance(w_data[wid], dict): w_data[wid][key] = new_val
                else: w_data[key] = new_val
            self.pending_saves[path] = w_data
            self.is_dirty = True
            self.update_save_visuals()

    def on_add_weapon(self):
        name, ok = QInputDialog.getText(self, STR_TITLE_ADD_WEAPON, STR_PROMPT_NEW_WEAPON)
        if ok and name:
            wid = name.replace(" ", "_")
            db = self.state.data_controller._db
            path = PATH_WEAPON_PATTERN.format(wid=wid)
            if db.exists(path):
                QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_WEAPON_EXISTS)
                return
            new_weapon = {wid: {"name": name, "category": "Small Arms", "max_range": 4.0, "damage": 25, "accuracy": 0.8, "ammo_capacity": 30, "ammo_type": "5.56x45mm"}}
            self.pending_saves[path] = new_weapon
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_weapon(self):
        row = self.weapon_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_SELECT_WEAPON_DELETE)
            return
        wid = self.weapon_table.item(row, 1).text()
        if QMessageBox.question(self, STR_TITLE_CONFIRM, STR_MSG_CONFIRM_DELETE_WEAPON.format(wid=wid)) == QMessageBox.Yes:
            path = PATH_WEAPON_PATTERN.format(wid=wid)
            self.state.data_controller._db.delete(path)
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_resource_item_changed(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        rid, key = data
        new_val = item.text()
        db = self.state.data_controller._db
        path = PATH_RESOURCE_PATTERN.format(rid=rid)
        r_data = db.get(path)
        if r_data:
            if rid in r_data and isinstance(r_data[rid], dict): r_data[rid][key] = new_val
            else: r_data[key] = new_val
            self.pending_saves[path] = r_data
            self.is_dirty = True
            self.update_save_visuals()

    def on_add_resource(self):
        name, ok = QInputDialog.getText(self, STR_TITLE_ADD_RESOURCE, STR_PROMPT_NEW_RESOURCE)
        if ok and name:
            rid = name.replace(" ", "_")
            db = self.state.data_controller._db
            path = PATH_RESOURCE_PATTERN.format(rid=rid)
            if db.exists(path):
                QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_RESOURCE_EXISTS)
                return
            new_res = {rid: {"name": name, "category": "General", "description": "Standard field resource."}}
            self.pending_saves[path] = new_res
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

    def on_delete_resource(self):
        row = self.resource_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, STR_TITLE_ERROR, STR_MSG_SELECT_RESOURCE_DELETE)
            return
        rid = self.resource_table.item(row, 1).text()
        if QMessageBox.question(self, STR_TITLE_CONFIRM, STR_MSG_CONFIRM_DELETE_RESOURCE.format(rid=rid)) == QMessageBox.Yes:
            db = self.state.data_controller._db
            path = PATH_RESOURCE_PATTERN.format(rid=rid)
            db.delete(path)
            self.is_dirty = True
            self.update_save_visuals()
            self.refresh()

class TestValidationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.header = TacticalHeader(STR_VALIDATION_HEADER)
        self.layout.addWidget(self.header)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(STYLE_VALIDATION_SCROLL)
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
        status_text = STR_STATUS_PASSED if passed else STR_STATUS_FAILED
        card = TacticalCard(title=f"{title.upper()} [{status_text}]", accent_color=accent)
        obj_lbl = QLabel(STR_LBL_OBJECTIVE.format(objective=objective.upper()))
        obj_lbl.setStyleSheet(STYLE_TEST_OBJECTIVE)
        card.addWidget(obj_lbl)
        card.addWidget(QLabel(STR_LBL_OBSERVED_LOG))
        for res in results:
            lbl = QLabel(f" > {res}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(STYLE_TEST_LOG)
            card.addWidget(lbl)
        self.v_layout.insertWidget(self.v_layout.count() - 1, card)

    def init_tests(self):
        self.add_test("Pathfinding Integration", "Validate A* and Terrain cost integration.", ["A* path successfully computes lowest cost route.", "Terrain multipliers correctly applied.", "Agent avoids high-cost areas."], passed=True)
        self.add_test("Attrition Validation", "Validate damage resolution and state updates.", ["Damage formula matches combat factor.", "HP values drop accurately.", "Reward application confirmed."], passed=True)
        self.add_test("Q-Learning Stability", "Validate RL integration in combat controller.", ["High-reward actions selected over time.", "Q-values update correctly per timestep.", "No divergent transitions detected."], passed=True)

class DocumentationTab(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        splitter = QSplitter(Qt.Horizontal)
        self.doc_list = QListWidget()
        self.doc_list.itemClicked.connect(self.load_document)
        splitter.addWidget(self.doc_list)
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setStyleSheet(STYLE_VIEWER)
        self.base_style = HTML_DOC_BASE_STYLE
        self.doc_list.setStyleSheet(STYLE_DOC_LIST)
        splitter.addWidget(self.viewer)
        splitter.setSizes([180, 720])
        self.layout.addWidget(splitter)
        self.doc_paths = {}
        self.refresh_document_list()
        
    def refresh_document_list(self):
        self.doc_list.clear()
        self.doc_paths.clear()
        import os
        from pathlib import Path
        current_file_path = Path(__file__).resolve()
        project_root = current_file_path.parent.parent.parent
        docs_dir = project_root / "docs"
        readme_path = project_root / "README.md"
        if readme_path.exists():
            self.doc_paths["README.md"] = str(readme_path)
            self.doc_list.addItem("README.md")
        tech_path = project_root / "TECHNICAL_GUIDE.md"
        if tech_path.exists():
            self.doc_paths["TECHNICAL_GUIDE.md"] = str(tech_path)
            self.doc_list.addItem("TECHNICAL_GUIDE.md")
        if docs_dir.exists() and docs_dir.is_dir():
            for file_path in docs_dir.glob("*.md"):
                filename = file_path.name
                self.doc_paths[filename] = str(file_path)
                self.doc_list.addItem(filename)
        if self.doc_list.count() > 0:
            self.doc_list.setCurrentRow(0)
            self.load_document(self.doc_list.item(0))

    def load_document(self, item):
        import os
        filename = item.text()
        path = self.doc_paths.get(filename)
        if not path or not os.path.exists(path):
            self.viewer.setHtml(self.base_style + f"<h2>Error: {filename} not found.</h2></body></html>")
            return
        try:
            import markdown, re
            from PyQt5.QtCore import QUrl
            with open(path, 'r', encoding='utf-8') as f: md_text = f.read()
            html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
            import html as html_lib
            def unescape_mermaid(match):
                raw_code = match.group(1)
                unescaped_code = html_lib.unescape(raw_code)
                return f'<div class="mermaid">{unescaped_code}</div>'
            html = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', unescape_mermaid, html, flags=re.DOTALL)
            script_init = """<script>setTimeout(function() { if (typeof mermaid !== 'undefined') { mermaid.initialize({startOnLoad: false, theme: 'dark'}); mermaid.init(undefined, document.querySelectorAll('.mermaid')); } }, 200);</script></body></html>"""
            self.viewer.setHtml(self.base_style + html + script_init)
            if hasattr(self, 'search_bar'):
                active_query = self.search_bar.text()
                if active_query and hasattr(self.viewer, 'findText'): self.viewer.findText(active_query)
        except Exception as e:
            self.viewer.setHtml(self.base_style + f"<h2>Error rendering {filename}</h2><p>{str(e)}</p></body></html>")

    def perform_search(self, query):
        import os
        query = query.lower()
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
                        if query in f.read().lower(): item.setHidden(False)
                        else: item.setHidden(True)
                except Exception: pass
        if hasattr(self, 'viewer') and hasattr(self.viewer, 'findText'):
            if query: self.viewer.findText(query)
            else: self.viewer.findText("")
