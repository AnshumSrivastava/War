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

# --- UI CONFIGURATION ---
# Tree Column Headers
COLS_DATA = ["DATA ASSETS", "DETAILS", "INFO"]

# Category Names
STR_CAT_SCENARIOS = "SCENARIOS"
STR_CAT_TERRAINS = "TERRAINS"
STR_CAT_AGENTS = "AGENTS"
STR_CAT_WEAPONS = "WEAPONS"
STR_CAT_OBSTACLES = "OBSTACLES"

# Detail Templates & Formats
STR_DETAIL_MISSION = "Mission Config"
STR_DETAIL_TERRAIN_FMT = "COST: {cost}x"
STR_DETAIL_ROLE_FMT = "{count} types"
STR_DETAIL_AGENT_FMT = "SPD:{speed} ATK:{attack} DEF:{defense} RNG:{range}"
STR_DETAIL_WEAPON_FMT = "DMG:{dmg} RNG:{rng}"
STR_DETAIL_OBSTACLE_FMT = "MOVE COST: {cost}"

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
        self.tree.setHeaderLabels(COLS_DATA)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.tree.setStyleSheet(STYLE_TREE)
        self.layout.addWidget(self.tree)
        self.refresh_tree()
        
    def refresh_tree(self):
        self.tree.clear()
        dc = getattr(self.state, "data_controller", None)
        if not dc: return
        
        # 1. Scenarios
        scen_root = QTreeWidgetItem(self.tree, [STR_CAT_SCENARIOS])
        scen_root.setExpanded(True)
        scen_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        scenarios = getattr(dc, 'scenarios', {})
        for name, path in scenarios.items():
            path_str = os.path.basename(path) if isinstance(path, str) else str(path)
            item = QTreeWidgetItem(scen_root, [name.upper(), STR_DETAIL_MISSION, path_str])
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            
        # 2. Terrains
        ter_root = QTreeWidgetItem(self.tree, [STR_CAT_TERRAINS])
        ter_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        for t_type, data in dc.terrain_types.items():
            cost = str(data.get("cost", data.get("movement_cost", 1.0)))
            color = data.get("color", "#CCCCCC")
            item = QTreeWidgetItem(ter_root, [t_type.upper(), STR_DETAIL_TERRAIN_FMT.format(cost=cost), color])
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            
        # 3. Agents
        agent_root = QTreeWidgetItem(self.tree, [STR_CAT_AGENTS])
        agent_root.setExpanded(True)
        agent_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        
        for role, types in dc.agent_types.items():
            role_node = QTreeWidgetItem(agent_root, [role.upper(), STR_DETAIL_ROLE_FMT.format(count=len(types)), ""])
            role_color = QColor(Theme.ACCENT_ALLY) if "ATTACKER" in role.upper() else QColor(Theme.ACCENT_ENEMY)
            role_node.setForeground(0, role_color)
            role_node.setExpanded(True)
            
            for a_type, data in types.items():
                caps = data.get("capabilities", {})
                name = data.get("name", a_type)
                detail = STR_DETAIL_AGENT_FMT.format(
                    speed=caps.get("speed", "?"),
                    attack=caps.get("attack", "?"),
                    defense=caps.get("defense", "?"),
                    range=caps.get("range", "?")
                )
                item = QTreeWidgetItem(role_node, [name.upper(), detail, a_type])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
                item.setFont(1, Theme.get_font(Theme.FONT_MONO, 8))
        
        # 4. Weapons
        weapons = getattr(dc, 'weapons', {})
        if weapons:
            wep_root = QTreeWidgetItem(self.tree, [STR_CAT_WEAPONS])
            wep_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
            for wid, wdata in weapons.items():
                name = wdata.get("name", wid)
                item = QTreeWidgetItem(wep_root, [name.upper(), STR_DETAIL_WEAPON_FMT.format(
                    dmg=wdata.get("damage", "?"), rng=wdata.get("max_range", "?")
                ), wid])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
        
        # 5. Obstacles
        obstacles = getattr(dc, 'obstacle_types', {})
        if obstacles:
            obs_root = QTreeWidgetItem(self.tree, [STR_CAT_OBSTACLES])
            obs_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
            for oid, odata in obstacles.items():
                name = odata.get("name", oid)
                item = QTreeWidgetItem(obs_root, [name.upper(), STR_DETAIL_OBSTACLE_FMT.format(
                    cost=odata.get("movement_cost", "?")
                ), oid])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
