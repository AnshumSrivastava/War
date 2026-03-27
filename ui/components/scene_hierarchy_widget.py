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
        super().__init__()
        self.parent_window = parent_window
        if state is None:
            raise ValueError("SceneHierarchyWidget requires a 'state' object for initialization.")
        self.state = state
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["HIERARCHY", "VIZ"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.setColumnWidth(1, 50)
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        # Apply tactical styling to the tree
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
        """Rebuilds the layer tree from GlobalState."""
        self.tree.clear()
        
        # Root: Map
        root = QTreeWidgetItem(self.tree)
        root.setText(0, "SCENE ROOT")
        root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 10, bold=True))
        root.setExpanded(True)
        root.setData(0, Qt.UserRole, ("map", None))
        
        # Group: Zones
        zones_group = QTreeWidgetItem(root)
        zones_group.setText(0, "ZONES")
        zones_group.setExpanded(True)
        zones_group.setData(0, Qt.UserRole, ("group", "zones"))
        
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            item = QTreeWidgetItem(zones_group)
            item.setText(0, zdata.get("name", "Unnamed Zone"))
            item.setData(0, Qt.UserRole, ("zone", zid))
            
        # Group: Units
        units_group = QTreeWidgetItem(root)
        units_group.setText(0, "UNITS")
        units_group.setExpanded(True)
        units_group.setData(0, Qt.UserRole, ("group", "units"))
        
        for entity in self.state.entity_manager.get_all_entities():
            item = QTreeWidgetItem(units_group)
            side = entity.get_attribute("side", "Neutral")
            prefix = "ATK" if side == "Attacker" else "DEF" if side == "Defender" else "NEU"
            item.setText(0, f"[{prefix}] {entity.name.upper()}")
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            item.setData(0, Qt.UserRole, ("entity", entity.id))
            
            # Status Indicator in Col 1
            hp = int(entity.get_attribute("health", 100))
            status = "[\u2714]" if hp > 0 else "[X]"
            item.setText(1, status)
            item.setTextAlignment(1, Qt.AlignCenter)
            color_str = Theme.ACCENT_ALLY if side == "Attacker" else Theme.ACCENT_ENEMY if side == "Defender" else Theme.TEXT_DIM
            item.setForeground(1, QBrush(Qt.GlobalColor.white)) # Will style background if possible, or just use text color
            item.setForeground(0, QBrush(QColor(color_str)))
            
        # Group: Paths
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
            
        # Group: Scenario Elements (Toggles)
        scen_group = QTreeWidgetItem(root)
        scen_group.setText(0, "Scenario Elements")
        scen_group.setExpanded(True)
        scen_group.setData(0, Qt.UserRole, ("group", "scenario"))
        
        sec_item = QTreeWidgetItem(scen_group)
        sec_item.setText(0, "Territory Sections")
        sec_item.setText(1, "[\u2714]" if getattr(self.state, 'show_sections', False) else "[  ]")
        sec_item.setData(0, Qt.UserRole, ("toggle", "sections"))
        sec_item.setTextAlignment(1, Qt.AlignCenter)
        
        border_item = QTreeWidgetItem(scen_group)
        border_item.setText(0, "Map Borders")
        border_item.setText(1, "[\u2714]" if getattr(self.state, 'show_borders', False) else "[  ]")
        border_item.setData(0, Qt.UserRole, ("toggle", "borders"))
        border_item.setTextAlignment(1, Qt.AlignCenter)

    def on_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data: return
        kind, ident = data
        
        if kind == "toggle":
            if ident == "sections":
                self.state.show_sections = not getattr(self.state, 'show_sections', False)
                item.setText(1, "[\u2714]" if self.state.show_sections else "[  ]")
            elif ident == "borders":
                self.state.show_borders = not getattr(self.state, 'show_borders', False)
                item.setText(1, "[\u2714]" if self.state.show_borders else "[  ]")
            self.parent_window.hex_widget.update()
            return
            
        self.item_selected.emit(kind, ident)

    def select_by_hex(self, hex_obj):
        """Finds items at this hex and selects them in the tree."""
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
                    
        top = self.tree.topLevelItem(0)
        if top:
            self.tree.setCurrentItem(top)
            self.item_selected.emit("map", None)
