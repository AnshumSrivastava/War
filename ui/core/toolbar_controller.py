"""
FILE: ui/core/toolbar_controller.py
ROLE: The "Toolbox Manager".

DESCRIPTION:
This controller manages the creation, configuration, and switching of tools.
By separating this from MainWindow, we reduce the complexity of the main controller.
"""
from PyQt5.QtWidgets import QAction, QActionGroup, QToolBar, QDockWidget, QVBoxLayout, QWidget, QButtonGroup
from PyQt5.QtCore import Qt, QSize, QObject
from ui.core.icon_painter import VectorIconPainter

class ToolbarController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.state = main_window.state
        self.tool_actions = {}
        self.tool_group = None
        self.action_group = None
        
    def setup_left_toolbar(self):
        """Creates the vertical tool palette."""
        self.mw.tool_dock = QDockWidget("Tool Palette", self.mw)
        self.mw.tool_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.tool_toolbar = QToolBar("Tools")
        self.tool_toolbar.setOrientation(Qt.Vertical)
        self.tool_toolbar.setMovable(False)
        self.tool_toolbar.setIconSize(QSize(32, 32))
        
        wrapper = QWidget()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.tool_toolbar)
        vbox.addStretch()
        
        wrapper.setLayout(vbox)
        self.mw.tool_dock.setWidget(wrapper)
        self.mw.addDockWidget(Qt.LeftDockWidgetArea, self.mw.tool_dock)
        
        self.tool_group = QButtonGroup(self.mw)
        self.tool_group.setExclusive(True)
        
        tools = [ 
            ("Select", "cursor", "cursor",
             "Select Tool (S)\nClick on hexes, units, or zones to inspect their properties.\nDrag to pan the map view."),
            ("Edit", "edit", "edit",
             "Edit Tool (E)\nModify the terrain type, elevation, or cost of individual hexes.\nClick a hex to change its properties in the Inspector."),
            ("Eraser", "eraser", "eraser",
             "Eraser Tool (X)\nRemove units, zones, or paths from the map.\nClick on an object to delete it."),
            ("Place Agent", "place_agent", "place_agent",
             "Place Agent Tool (A)\nDrop a new unit onto the map.\nConfigure its type and side in the Inspector before placing."),
            ("Draw Zone", "draw_zone", "draw_zone",
             "Draw Zone Tool (Z)\nDefine named areas on the map (e.g., Objectives, Restricted Zones).\nClick hexes to add them to the active zone."),
            ("Paint Tool", "paint_tool", "paint_tool",
             "Paint Terrain Tool (P)\nBrush terrain types across multiple hexes.\nSelect the terrain type in the Inspector, then click-drag to paint."),
            ("Draw Path", "draw_path", "draw_path",
             "Draw Path Tool (D)\nCreate named movement routes on the map.\nClick hexes sequentially to define waypoints."),
            ("Assign Goal", "assign_goal", "assign_goal",
             "Assign Goal Tool (G)\nSet a movement objective for a selected unit.\nClick on the unit first, then click the destination hex.")
        ]
        
        for name, icon_type, tid, tooltip in tools:
            icon = VectorIconPainter.create_icon(icon_type, color="#3daee9" if tid == "cursor" else "#eeeeee")
            action = QAction(icon, name, self.mw)
            action.setData(tid)
            action.setCheckable(True)
            action.setToolTip(tooltip)
            
            if tid == "cursor":
                action.setChecked(True)
                self.state.selected_tool = "cursor"
                
            action.triggered.connect(lambda checked, t=tid: self.mw.set_tool(t))
            
            self.tool_toolbar.addAction(action)
            self.tool_actions[tid] = action
            
            btn = self.tool_toolbar.widgetForAction(action)
            if btn: self.tool_group.addButton(btn)
            
        self.tool_toolbar.addSeparator()
        
        a_border = QAction(VectorIconPainter.create_icon("draw_zone"), "Add Border", self.mw) 
        a_border.setToolTip("Add/Setup Map Border") 
        a_border.triggered.connect(self.mw.action_add_border) 
        self.tool_toolbar.addAction(a_border) 
        
        self.tool_toolbar.addSeparator() 
        
        a_refresh = QAction(VectorIconPainter.create_icon("refresh"), "Reload App", self.mw) 
        a_refresh.setToolTip("Restart the Engine to apply all code and master data changes.") 
        a_refresh.triggered.connect(self.mw.restart_app) 
        self.tool_toolbar.addAction(a_refresh) 
            
        self.update_tools_visibility()

    def update_tools_visibility(self):
        mode = getattr(self.state, "app_mode", "terrain")
        allowed = []
        if mode == "terrain":
            allowed = ["cursor", "edit", "eraser", "paint_tool"]
        elif "areas" in mode:
            allowed = ["cursor", "edit", "eraser", "draw_zone", "draw_path"]
        elif "agents" in mode:
            side = getattr(self.state, "active_scenario_side", "Attacker")
            side = side.lower() if side else "attacker"
            if side == "defender":
                allowed = ["cursor", "eraser", "place_agent"]
            else:
                allowed = ["cursor", "eraser", "place_agent", "assign_goal"]
        elif mode == "play":
            side = getattr(self.state, "active_scenario_side", "Defender")
            if side.lower() == "defender":
                allowed = ["cursor"]
            else:
                allowed = ["cursor", "assign_goal"]
            
        for tid, action in self.tool_actions.items():
            visible = tid in allowed
            action.setVisible(visible)
            action.setEnabled(visible)
                
        if self.state.selected_tool not in allowed:
            self.mw.set_tool("cursor")

