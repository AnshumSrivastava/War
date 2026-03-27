"""
FILE: ui/widgets/data_widget.py
ROLE: Data Visualization Overlay.
DESCRIPTION: Toggleable overlay for displaying debug information (Q-values, health) directly on the map.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QLabel
from PyQt5.QtCore import Qt
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
        
        # Tools
        tool_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.refresh_tree)
        tool_layout.addWidget(refresh_btn)
        self.layout.addLayout(tool_layout)
        
        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["DATA ASSETS", "DETAILS", "PATH"])
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
        for name, path in dc.scenarios.items():
            item = QTreeWidgetItem(scen_root, [name.upper(), "Mission Config", os.path.basename(path)])
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            
        # 2. Terrains
        ter_root = QTreeWidgetItem(self.tree, ["TERRAINS"])
        ter_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        for t_type, data in dc.terrain_types.items():
            cost = str(data.get("cost", 1.0))
            item = QTreeWidgetItem(ter_root, [t_type.upper(), f"COST: {cost}x", ""])
            item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
            
        # 3. Agents
        agent_root = QTreeWidgetItem(self.tree, ["AGENTS"])
        agent_root.setExpanded(True)
        agent_root.setFont(0, Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        for role, types in dc.agent_types.items():
            role_node = QTreeWidgetItem(agent_root, [role.upper()])
            role_node.setForeground(0, Theme.ACCENT_ALLY if "ATTACKER" in role.upper() else Theme.ACCENT_ENEMY)
            for a_type, data in types.items():
                hp = str(data.get("attributes", {}).get("health", "?"))
                item = QTreeWidgetItem(role_node, [a_type.upper(), f"HP: {hp}", ""])
                item.setFont(0, Theme.get_font(Theme.FONT_MONO, 9))
