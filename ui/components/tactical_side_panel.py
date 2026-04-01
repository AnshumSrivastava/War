from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStackedWidget, QLabel, QFrame, 
                             QGroupBox, QFormLayout, QSpinBox, QComboBox, QLineEdit, 
                             QCheckBox, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from ui.styles.theme import Theme
from ui.components.themed_widgets import TacticalHeader, TacticalCard

class TacticalSidePanel(QWidget):
    """
    The Unified "Tactical Operations Center" sidebar.
    Replaces legacy Inspector, Scenario Manager, and Hierarchy docks.
    """
    def __init__(self, main_window, state):
        super().__init__(main_window)
        self.mw = main_window
        self.state = state
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)
        self.setObjectName("TacticalSidePanel")
        
        # --- PHASE HEADER ---
        self.header = TacticalHeader("OPERATIONS CENTER")
        self.layout.addWidget(self.header)
        
        # --- TACTICAL INTEL (Persistent Summary) ---
        self.intel_card = TacticalCard(title="MISSION INTEL")
        self.lbl_intel_theater = QLabel("OP THEATER: [UNASSIGNED]")
        self.lbl_intel_side = QLabel("ACTIVE SIDE: [NEUTRAL]")
        self.lbl_intel_assets = QLabel("DEPLOYED ASSETS: 0")
        
        for lbl in [self.lbl_intel_theater, self.lbl_intel_side, self.lbl_intel_assets]:
            lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
            self.intel_card.addWidget(lbl)
            
        self.layout.addWidget(self.intel_card)
        
        # --- DYNAMIC STACK ---
        self.stack = QStackedWidget()
        
        # 0: TERRAIN PANEL
        self.terrain_panel = self._create_terrain_panel()
        self.stack.addWidget(self.terrain_panel)
        
        # 1: AREA PANEL
        self.area_panel = self._create_area_panel()
        self.stack.addWidget(self.area_panel)
        
        # 2: DEPLOYMENT PANEL (ROSTER)
        self.deploy_panel = self._create_deploy_panel()
        self.stack.addWidget(self.deploy_panel)
        
        # 3: SIMULATION PANEL (PLAY)
        self.play_panel = self._create_play_panel()
        self.stack.addWidget(self.play_panel)
        
        self.layout.addWidget(self.stack, 1)
        
        # Apply Base Styling
        self.setStyleSheet(f"background-color: {Theme.BG_SURFACE}; border-left: 1px solid {Theme.BORDER_STRONG};")

    def sync_to_mode(self, mode_index):
        """Called by ModeStateMachine to flip the stack based on current phase."""
        # Modes: maps(0), terrain(1), rules(2), def_areas(3), def_agents(4), atk_areas(5), atk_agents(6), play(7)
        self._refresh_intel()
        
        if mode_index == 1: # Terrain
            self.header.setText("TERRAIN SCULPTING")
            self.stack.setCurrentIndex(0)
            self._refresh_terrain_ui()
        elif mode_index in [3, 5]: # Areas
            side = "DEFENDER" if mode_index == 3 else "ATTACKER"
            self.header.setText(f"{side} PERIMETER")
            self.stack.setCurrentIndex(1)
            self._refresh_area_ui(side)
        elif mode_index in [4, 6]: # Agents
            side = "DEFENDER" if mode_index == 4 else "ATTACKER"
            self.header.setText(f"{side} GARRISON")
            self.stack.setCurrentIndex(2)
            self._refresh_deploy_ui(side)
        elif mode_index == 7: # Play
            self.header.setText("TACTICAL EXECUTION")
            self.stack.setCurrentIndex(3)
        else:
            self.header.setText("OPERATIONS CENTER")

    def _refresh_intel(self):
        """Update the persistent intel summary."""
        theater = getattr(self.state.current_map, 'upper', lambda: "LOCAL SECTOR")()
        self.lbl_intel_theater.setText(f"OP THEATER: {theater}")
        
        side = getattr(self.state, "active_scenario_side", "Combined")
        color = Theme.ACCENT_ENEMY if side == "Attacker" else Theme.ACCENT_ALLY
        if side == "Combined": color = Theme.TEXT_PRIMARY
        
        self.lbl_intel_side.setText(f"ACTIVE SIDE: {side.upper()}")
        self.lbl_intel_side.setStyleSheet(f"color: {color}; font-family: '{Theme.FONT_MONO}'; font-size: 10px; font-weight: bold;")
        
        if self.state.entity_manager:
            entities = self.state.entity_manager.get_all_entities()
            count = 0
            for e in entities:
                e_side = e.get_attribute("side", "Neutral")
                if side == "Combined" or e_side.upper() == side.upper():
                    count += 1
            self.lbl_intel_assets.setText(f"DEPLOYED {side.upper()} ASSETS: {count}")
            
    # --- SUB-PANEL CREATION ---

    def _create_terrain_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.terrain_card = TacticalCard(title="BRUSH EMITTER")
        layout.addWidget(self.terrain_card)
        
        self.terrain_options_container = QVBoxLayout()
        self.terrain_card.addLayout(self.terrain_options_container)
        
        layout.addStretch()
        return panel

    def _create_area_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.area_card = TacticalCard(title="ZONE CONFIGURATION")
        layout.addWidget(self.area_card)
        
        self.area_options_container = QVBoxLayout()
        self.area_card.addLayout(self.area_options_container)
        
        layout.addStretch()
        return panel

    def _create_deploy_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.deploy_card = TacticalCard(title="ROSTER PALETTE")
        layout.addWidget(self.deploy_card)
        
        self.deploy_options_container = QVBoxLayout()
        self.deploy_card.addLayout(self.deploy_options_container)
        
        layout.addStretch()
        return panel

    def _create_play_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        card = TacticalCard(title="VISUALIZATION")
        v_layout = QVBoxLayout()
        
        chk_threat = QCheckBox("Threat Map Overlay")
        chk_threat.toggled.connect(self.mw.toggle_threat_map)
        v_layout.addWidget(chk_threat)
        
        chk_reward = QCheckBox("Reward Visualizer")
        chk_reward.toggled.connect(self.mw.toggle_reward_viz)
        v_layout.addWidget(chk_reward)
        
        card.addLayout(v_layout)
        layout.addWidget(card)
        
        res_card = TacticalCard(title="ENGAGEMENT LOG")
        self.lbl_stats = QLabel("Simulation Idle...")
        self.lbl_stats.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
        self.lbl_stats.setWordWrap(True)
        res_card.addWidget(self.lbl_stats)
        layout.addWidget(res_card)
        
        layout.addStretch()
        return panel

    def update_stats(self, text):
        """Update simulation/operational metrics in the sidebar."""
        if hasattr(self, 'lbl_stats'):
            import re
            clean = re.compile('<.*?>')
            plain_text = re.sub(clean, '', text)
            self.lbl_stats.setText(plain_text)

    def sync_to_tool(self, tool_id):
        """Called by MainWindow when the active tool changes within a phase."""
        if tool_id == "paint_tool":
            self.stack.setCurrentIndex(0)
            self._refresh_terrain_ui()
        elif tool_id in ["draw_zone", "draw_path"]:
            self.stack.setCurrentIndex(1)
            side = getattr(self.state, "active_scenario_side", "Attacker")
            self._refresh_area_ui(side.upper())
        elif tool_id == "place_agent":
            self.stack.setCurrentIndex(2)
            side = getattr(self.state, "active_scenario_side", "Attacker")
            self._refresh_deploy_ui(side.upper())
        elif tool_id == "cursor":
            # Selection tool: show play panel for stats or base panel
            if getattr(self.state, "app_mode", "maps") == "play":
                self.stack.setCurrentIndex(3)
            else:
                self._refresh_intel()
        else:
             # Fallback to current phase stack if unknown tool
             pass

    # --- REFRESH LOGIC ---

    def _refresh_terrain_ui(self):
        # Dynamically mount the PaintTool Brush Palette here
        while self.terrain_options_container.count():
            item = self.terrain_options_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Ensure the correct tool is active to provide its widget
        self.mw.set_tool("paint_tool")
        tool = self.mw.hex_widget.tools["paint_tool"]
        palette = tool.get_options_widget(self)
        
        self.terrain_options_container.addWidget(palette)

    def _refresh_area_ui(self, side):
        # Dynamically mount the ZoneOptionsWidget here
        while self.area_options_container.count():
            item = self.area_options_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        from ui.components.tool_options.zone_options_widget import ZoneOptionsWidget
        self.state.active_scenario_side = side.title()
        opts = ZoneOptionsWidget(self, self.state)
        # Strip header from ZoneOptionsWidget since the TOC card has its own
        for lbl in opts.findChildren(QLabel):
            if lbl.objectName() == "InspectorLabel" or "ZONE CONFIGURATION" in lbl.text():
                 lbl.hide()
        self.area_options_container.addWidget(opts)

    def _refresh_deploy_ui(self, side):
        # Dynamically mount the PlaceAgentTool Roster Palette here
        while self.deploy_options_container.count():
            item = self.deploy_options_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.state.active_scenario_side = side.title()
        self.mw.set_tool("place_agent")
        tool = self.mw.hex_widget.tools["place_agent"]
        palette = tool.get_options_widget(self)
        # Clean up the palette UI to fit the card
        for lbl in palette.findChildren(QLabel):
            if "DRAG & DROP" in lbl.text(): lbl.hide()
        for box in palette.findChildren(QGroupBox):
            if "Awaiting Deployment" in box.title(): 
                box.setTitle("")
                box.setStyleSheet("border: none; padding: 0;")
                
        self.deploy_options_container.addWidget(palette)
        # Explicit hard-refresh to ensure data is populated
        QTimer.singleShot(0, tool.refresh_roster)
        
        # Explicit synchronization: Ensure the tool has the latest data from the Rules tab
        tool.refresh_roster()
