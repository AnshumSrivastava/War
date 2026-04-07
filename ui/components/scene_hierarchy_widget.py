"""
FILE: ui/widgets/scene_hierarchy_widget.py
ROLE: The "Map Tree"
DESCRIPTION: Displays a hierarchical tree of Map Elements (Zones, Units, Paths) and Visibility Toggles.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHeaderView, QTreeWidgetItemIterator, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush
from engine.state.global_state import GlobalState
from ui.styles.theme import Theme

# --- UI CONFIGURATION ---
# Tree Column Headers
COLS_HIERARCHY = ["HIERARCHY", "VIZ"]

# Node Names & Categories
STR_NODE_ROOT = "SCENE ROOT"
STR_CAT_ZONES = "ZONES"
STR_CAT_UNITS = "UNITS"
STR_CAT_PATHS = "PATHS"
STR_CAT_SCENARIO = "SCENARIO ELEMENTS"

# Default Item Names
STR_ITEM_ZONE_DEFAULT = "Unnamed Zone"
STR_ITEM_PATH_DEFAULT = "Unnamed Path"
STR_ITEM_UNIT_FMT = "[{prefix}] {name}"

# Status & Toggle Symbols
STR_SYMBOL_OK = "[\u2714]"
STR_SYMBOL_DEAD = "[X]"
STR_SYMBOL_EMPTY = "[  ]"

# Toggle Labels
STR_TOGGLE_SECTIONS = "Territory Sections"
STR_TOGGLE_BORDERS = "Map Borders"

# Side Prefixes
DICT_SIDE_PREFIXES = {
    "Attacker": "ATK",
    "Defender": "DEF",
    "Neutral": "NEU"
}

# Stylesheets
STYLE_TREE = f"""
    QTreeWidget {{
        background-color: {Theme.BG_DEEP};
        border: 1px solid {Theme.BORDER_STRONG};
        color: {Theme.TEXT_PRIMARY};
        font-family: '{Theme.FONT_BODY}';
        outline: none;
    }}
    QTreeWidget::item {{
        padding: 6px;
        border-bottom: 1px solid {Theme.BORDER_SUBTLE};
    }}
    QTreeWidget::item:selected {{
        background-color: {Theme.BG_INPUT};
        color: {Theme.ACCENT_ALLY};
    }}
    QHeaderView::section {{
        background-color: {Theme.BG_INPUT};
        color: {Theme.TEXT_DIM};
        font-weight: bold;
        text-transform: uppercase;
        font-size: 9px;
        padding: 4px;
        border: none;
        border-bottom: 1px solid {Theme.BORDER_STRONG};
    }}
"""
# -------------------------

class SceneHierarchyWidget(QWidget):
    item_selected = pyqtSignal(str, str) # kind, ident
    
    def __init__(self, parent_window, state=None):
        super().__init__()
        self.parent_window = parent_window
        if state is None:
            raise ValueError("SceneHierarchyWidget requires a 'state' object for initialization.")
        self.state = state
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(COLS_HIERARCHY)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.setColumnWidth(1, 50)
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        self.tree.setStyleSheet(STYLE_TREE)
        layout.addWidget(self.tree)
        self.refresh_tree()

    def refresh_tree(self):
        """Rebuilds the tree structure from the current GlobalState."""
        self.tree.clear()
        
        # Root Node
        root = QTreeWidgetItem(self.tree)
        root.setText(0, STR_NODE_ROOT)
        root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 10, bold=True))
        root.setExpanded(True)
        root.setData(0, Qt.UserRole, ("map", None))
        
        # CATEGORY: ZONES
        zones_group = QTreeWidgetItem(root)
        zones_group.setText(0, STR_CAT_ZONES)
        zones_group.setExpanded(True)
        zones_group.setData(0, Qt.UserRole, ("group", "zones"))
        
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            item = QTreeWidgetItem(zones_group)
            item.setText(0, zdata.get("name", STR_ITEM_ZONE_DEFAULT))
            item.setData(0, Qt.UserRole, ("zone", zid))
            
        # CATEGORY: UNITS
        units_group = QTreeWidgetItem(root)
        units_group.setText(0, STR_CAT_UNITS)
        units_group.setExpanded(True)
        units_group.setData(0, Qt.UserRole, ("group", "units"))
        
        for entity in self.state.entity_manager.get_all_entities():
            item = QTreeWidgetItem(units_group)
            side = entity.get_attribute("side", "Neutral")
            prefix = DICT_SIDE_PREFIXES.get(side, "NEU")
            item.setText(0, STR_ITEM_UNIT_FMT.format(prefix=prefix, name=entity.name.upper()))
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            item.setData(0, Qt.UserRole, ("entity", entity.id))
            
            # Vital Status Indicator
            hp = int(entity.get_attribute("health", 100))
            status = STR_SYMBOL_OK if hp > 0 else STR_SYMBOL_DEAD
            item.setText(1, status)
            item.setTextAlignment(1, Qt.AlignCenter)
            
            # Color coding
            color_str = Theme.ACCENT_ALLY if side == "Attacker" else Theme.ACCENT_ENEMY if side == "Defender" else Theme.TEXT_DIM
            item.setForeground(1, QBrush(Qt.GlobalColor.white)) 
            item.setForeground(0, QBrush(QColor(color_str)))
            
        # CATEGORY: PATHS
        paths_group = QTreeWidgetItem(root)
        paths_group.setText(0, STR_CAT_PATHS)
        paths_group.setExpanded(True)
        paths_group.setData(0, Qt.UserRole, ("group", "paths"))
        
        paths = self.state.map.get_paths()
        for pid, pdata in paths.items():
            item = QTreeWidgetItem(paths_group)
            item.setText(0, pdata.get("name", STR_ITEM_PATH_DEFAULT).upper())
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            item.setData(0, Qt.UserRole, ("path", pid))
            
        # CATEGORY: SYSTEM TOGGLES
        scen_group = QTreeWidgetItem(root)
        scen_group.setText(0, STR_CAT_SCENARIO)
        scen_group.setExpanded(True)
        scen_group.setData(0, Qt.UserRole, ("group", "scenario"))
        
        # Toggle: Territory boundaries
        sec_item = QTreeWidgetItem(scen_group)
        sec_item.setText(0, STR_TOGGLE_SECTIONS)
        sec_item.setText(1, STR_SYMBOL_OK if getattr(self.state, 'show_sections', False) else STR_SYMBOL_EMPTY)
        sec_item.setData(0, Qt.UserRole, ("toggle", "sections"))
        sec_item.setTextAlignment(1, Qt.AlignCenter)
        
        # Toggle: External map borders
        border_item = QTreeWidgetItem(scen_group)
        border_item.setText(0, STR_TOGGLE_BORDERS)
        border_item.setText(1, STR_SYMBOL_OK if getattr(self.state, 'show_borders', False) else STR_SYMBOL_EMPTY)
        border_item.setData(0, Qt.UserRole, ("toggle", "borders"))
        border_item.setTextAlignment(1, Qt.AlignCenter)

    def on_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data: return
        kind, ident = data
        
        if kind == "toggle":
            if ident == "sections":
                self.state.show_sections = not getattr(self.state, 'show_sections', False)
                item.setText(1, STR_SYMBOL_OK if self.state.show_sections else STR_SYMBOL_EMPTY)
            elif ident == "borders":
                self.state.show_borders = not getattr(self.state, 'show_borders', False)
                item.setText(1, STR_SYMBOL_OK if self.state.show_borders else STR_SYMBOL_EMPTY)
            self.parent_window.hex_widget.update()
            return
            
        self.item_selected.emit(kind, ident)

    def select_by_hex(self, hex_obj):
        # Check for Entities
        entities = self.state.map.get_entities_at(hex_obj)
        if entities:
            eid = entities[0]
            iterator = QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                data = item.data(0, Qt.UserRole)
                if data and data[0] == "entity" and data[1] == eid:
                    self.tree.setCurrentItem(item)
                    self.item_selected.emit("entity", eid)
                    return
                iterator += 1
                
        # Check for Zones
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            if hex_obj in zdata.get('hexes', []):
                iterator = QTreeWidgetItemIterator(self.tree)
                while iterator.value():
                    item = iterator.value()
                    data = item.data(0, Qt.UserRole)
                    if data and data[0] == "zone" and data[1] == zid:
                        self.tree.setCurrentItem(item)
                        self.item_selected.emit("zone", zid)
                        return
                    iterator += 1
                    
        # Fallback
        top = self.tree.topLevelItem(0)
        if top:
            self.tree.setCurrentItem(top)
            self.item_selected.emit("map", None)
