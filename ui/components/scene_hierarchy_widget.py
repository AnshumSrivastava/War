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

class SceneHierarchyWidget(QWidget):
    item_selected = pyqtSignal(str, str) # kind, ident
    
    def __init__(self, parent_window, state=None):
        """
        Initializes the Map Hierarchy Tree.
        
        Args:
            parent_window: The main application window (used for redraw triggers).
            state: The GlobalState object containing the map layers and entity lists.
        """
        super().__init__()
        self.parent_window = parent_window
        if state is None:
            raise ValueError("SceneHierarchyWidget requires a 'state' object for initialization.")
        self.state = state
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # The main tree view component
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["HIERARCHY", "VIZ"])
        # Column 0: Name of the object (stretches to fill space)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        # Column 1: Visibility checkbox/indicator (fixed width)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.setColumnWidth(1, 50)
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        # Apply tactical 'Dark Mode' styling to the tree
        self.tree.setStyleSheet(f"""
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
        """)
        
        layout.addWidget(self.tree)
        self.refresh_tree()

    def refresh_tree(self):
        """
        Completely rebuilds the tree structure from the current GlobalState.
        Organizes the map into logical groups: Zones, Units, Paths, and Toggles.
        """
        self.tree.clear()
        
        # Root Node: Represents the entire Map
        root = QTreeWidgetItem(self.tree)
        root.setText(0, "SCENE ROOT")
        root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 10, bold=True))
        root.setExpanded(True)
        root.setData(0, Qt.UserRole, ("map", None))
        
        # CATEGORY: ZONES (Strategic areas on the map)
        zones_group = QTreeWidgetItem(root)
        zones_group.setText(0, "ZONES")
        zones_group.setExpanded(True)
        zones_group.setData(0, Qt.UserRole, ("group", "zones"))
        
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            item = QTreeWidgetItem(zones_group)
            item.setText(0, zdata.get("name", "Unnamed Zone"))
            item.setData(0, Qt.UserRole, ("zone", zid))
            
        # CATEGORY: UNITS (The active agents/armies)
        units_group = QTreeWidgetItem(root)
        units_group.setText(0, "UNITS")
        units_group.setExpanded(True)
        units_group.setData(0, Qt.UserRole, ("group", "units"))
        
        for entity in self.state.entity_manager.get_all_entities():
            item = QTreeWidgetItem(units_group)
            side = entity.get_attribute("side", "Neutral")
            # Tactical prefix for quick identification
            prefix = "ATK" if side == "Attacker" else "DEF" if side == "Defender" else "NEU"
            item.setText(0, f"[{prefix}] {entity.name.upper()}")
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            item.setData(0, Qt.UserRole, ("entity", entity.id))
            
            # Vital Status Indicator in the 'VIZ' column (Checkmark or X)
            hp = int(entity.get_attribute("health", 100))
            status = "[\u2714]" if hp > 0 else "[X]"
            item.setText(1, status)
            item.setTextAlignment(1, Qt.AlignCenter)
            
            # Color coding based on team affiliation
            color_str = Theme.ACCENT_ALLY if side == "Attacker" else Theme.ACCENT_ENEMY if side == "Defender" else Theme.TEXT_DIM
            item.setForeground(1, QBrush(Qt.GlobalColor.white)) 
            item.setForeground(0, QBrush(QColor(color_str)))
            
        # CATEGORY: PATHS (Maneuver vectors and arrows)
        paths_group = QTreeWidgetItem(root)
        paths_group.setText(0, "PATHS")
        paths_group.setExpanded(True)
        paths_group.setData(0, Qt.UserRole, ("group", "paths"))
        
        paths = self.state.map.get_paths()
        for pid, pdata in paths.items():
            item = QTreeWidgetItem(paths_group)
            item.setText(0, pdata.get("name", "Unnamed Path").upper())
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            item.setData(0, Qt.UserRole, ("path", pid))
            
        # CATEGORY: SYSTEM TOGGLES (Global visibility settings)
        scen_group = QTreeWidgetItem(root)
        scen_group.setText(0, "SCENARIO ELEMENTS")
        scen_group.setExpanded(True)
        scen_group.setData(0, Qt.UserRole, ("group", "scenario"))
        
        # Toggle: Territory boundaries (drawn with Voronoi)
        sec_item = QTreeWidgetItem(scen_group)
        sec_item.setText(0, "Territory Sections")
        sec_item.setText(1, "[\u2714]" if getattr(self.state, 'show_sections', False) else "[  ]")
        sec_item.setData(0, Qt.UserRole, ("toggle", "sections"))
        sec_item.setTextAlignment(1, Qt.AlignCenter)
        
        # Toggle: External map borders
        border_item = QTreeWidgetItem(scen_group)
        border_item.setText(0, "Map Borders")
        border_item.setText(1, "[\u2714]" if getattr(self.state, 'show_borders', False) else "[  ]")
        border_item.setData(0, Qt.UserRole, ("toggle", "borders"))
        border_item.setTextAlignment(1, Qt.AlignCenter)

    def on_item_clicked(self, item, column):
        """
        Handles mouse clicks on tree items. 
        If it's a toggle, it flips the system state.
        If it's an object, it emits a signal to show properties.
        """
        data = item.data(0, Qt.UserRole)
        if not data: return
        kind, ident = data
        
        # SPECIAL CASE: Toggles directly modify the GlobalState Boolean
        if kind == "toggle":
            if ident == "sections":
                self.state.show_sections = not getattr(self.state, 'show_sections', False)
                item.setText(1, "[\u2714]" if self.state.show_sections else "[  ]")
            elif ident == "borders":
                self.state.show_borders = not getattr(self.state, 'show_borders', False)
                item.setText(1, "[\u2714]" if self.state.show_borders else "[  ]")
            # Trigger a repaint of the map
            self.parent_window.hex_widget.update()
            return
            
        # Emits signal so the 'Properties' panel knows what to show
        self.item_selected.emit(kind, ident)

    def select_by_hex(self, hex_obj):
        """
        REVERSE LOOKUP: When you click on the MAP, this function finds that 
        object in the TREE and highlights it.
        """
        # Check for Entities (Units) at this hex
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
                
        # Check for Zones that contain this hex
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
                    
        # Fallback: Just select the Map root if nothing specific is found
        top = self.tree.topLevelItem(0)
        if top:
            self.tree.setCurrentItem(top)
            self.item_selected.emit("map", None)

