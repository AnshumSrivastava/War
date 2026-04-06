"""
FILE: ui/widgets/data_widget.py
ROLE: Data Visualization Overlay.
DESCRIPTION: Toggleable overlay for displaying debug information (Q-values, health) directly on the map.
"""
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from ui.styles.theme import Theme

class DataWidget(QWidget):
    """
    Widget to display the current Data Assets (Terrains, Agents, Scenarios).
    """
    def __init__(self, global_state):
        super().__init__()
        self.state = global_state
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["DATA ASSETS", "DETAILS", "INFO"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
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
        
        self.layout.addWidget(self.tree)
        
        self.refresh_tree()
        
    def refresh_tree(self):
        self.tree.clear()
        dc = getattr(self.state, "data_controller", None)
        if not dc: return
        
        # 1. Scenarios
        scen_root = QTreeWidgetItem(self.tree, ["SCENARIOS"])
        scen_root.setExpanded(True)
        scen_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        scenarios = getattr(dc, 'scenarios', {})
        for name, path in scenarios.items():
            path_str = os.path.basename(path) if isinstance(path, str) else str(path)
            item = QTreeWidgetItem(scen_root, [name.upper(), "Mission Config", path_str])
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            
        # 2. Terrains
        ter_root = QTreeWidgetItem(self.tree, ["TERRAINS"])
        ter_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        for t_type, data in dc.terrain_types.items():
            cost = str(data.get("cost", data.get("movement_cost", 1.0)))
            color = data.get("color", "#CCCCCC")
            item = QTreeWidgetItem(ter_root, [t_type.upper(), f"COST: {cost}x", color])
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            
        # 3. Agents — Show hierarchy: Side → Agent Type → Stats
        agent_root = QTreeWidgetItem(self.tree, ["AGENTS"])
        agent_root.setExpanded(True)
        agent_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        
        for role, types in dc.agent_types.items():
            role_node = QTreeWidgetItem(agent_root, [role.upper(), f"{len(types)} types", ""])
            role_color = QColor(Theme.ACCENT_ALLY) if "ATTACKER" in role.upper() else QColor(Theme.ACCENT_ENEMY)
            role_node.setForeground(0, role_color)
            role_node.setExpanded(True)
            
            for a_type, data in types.items():
                # Read capabilities properly
                caps = data.get("capabilities", {})
                name = data.get("name", a_type)
                speed = caps.get("speed", "?")
                attack = caps.get("attack", "?")
                defense = caps.get("defense", "?")
                fire_range = caps.get("range", "?")
                
                detail = f"SPD:{speed} ATK:{attack} DEF:{defense} RNG:{fire_range}"
                item = QTreeWidgetItem(role_node, [name.upper(), detail, a_type])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
                item.setFont(1, Theme.get_font(Theme.FONT_MONO, 8))
        
        # 4. Weapons
        weapons = getattr(dc, 'weapons', {})
        if weapons:
            wep_root = QTreeWidgetItem(self.tree, ["WEAPONS"])
            wep_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
            for wid, wdata in weapons.items():
                name = wdata.get("name", wid)
                dmg = wdata.get("damage", "?")
                rng = wdata.get("max_range", "?")
                item = QTreeWidgetItem(wep_root, [name.upper(), f"DMG:{dmg} RNG:{rng}", wid])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
        
        # 5. Obstacles
        obstacles = getattr(dc, 'obstacle_types', {})
        if obstacles:
            obs_root = QTreeWidgetItem(self.tree, ["OBSTACLES"])
            obs_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
            for oid, odata in obstacles.items():
                name = odata.get("name", oid)
                cost = odata.get("movement_cost", "?")
                item = QTreeWidgetItem(obs_root, [name.upper(), f"MOVE COST: {cost}", oid])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))

