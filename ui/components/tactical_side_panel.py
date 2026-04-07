from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStackedWidget, QLabel, QFrame, 
                             QGroupBox, QFormLayout, QSpinBox, QComboBox, QLineEdit, 
                             QCheckBox, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from ui.styles.theme import Theme
from ui.components.themed_widgets import TacticalHeader, TacticalCard

# --- UI CONFIGURATION ---
# Object Names
OBJ_SIDE_PANEL = "TacticalSidePanel"

# Header Titles
STR_HEADER_OPS = "OPERATIONS CENTER"
STR_HEADER_TERRAIN = "TERRAIN SCULPTING"
STR_HEADER_AREA_FMT = "{side} PERIMETER"
STR_HEADER_GARRISON_FMT = "{side} GARRISON"
STR_HEADER_EXECUTION = "TACTICAL EXECUTION"

# Card Titles
STR_CARD_INTEL = "MISSION INTEL"
STR_CARD_BRUSH = "BRUSH EMITTER"
STR_CARD_ZONE = "ZONE CONFIGURATION"
STR_CARD_ROSTER = "ROSTER PALETTE"
STR_CARD_VISUAL = "VISUALIZATION"
STR_CARD_LOG = "ENGAGEMENT LOG"

# Labels & Metrics
STR_LBL_THEATER_FMT = "OP THEATER: {val}"
STR_LBL_SIDE_FMT = "ACTIVE SIDE: {val}"
STR_LBL_ASSETS_FMT = "DEPLOYED ASSETS: {val}"
STR_LBL_DEPLOYED_SIDE_ASSETS_FMT = "DEPLOYED {side} ASSETS: {count}"
STR_LBL_SIM_IDLE = "Simulation Idle..."
STR_CHK_THREAT = "Threat Map Overlay"
STR_CHK_REWARD = "Reward Visualizer"

# Default Values
STR_VAL_UNASSIGNED = "[UNASSIGNED]"
STR_VAL_NEUTRAL = "[NEUTRAL]"
STR_VAL_LOCAL_SECTOR = "LOCAL SECTOR"

# Stylesheets
STYLE_SIDE_PANEL = f"background-color: {Theme.BG_SURFACE}; border-left: 1px solid {Theme.BORDER_STRONG};"
STYLE_INTEL_LBL = f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;"
STYLE_INTEL_SIDE_BOLD = "color: {color}; font-family: '{Theme.FONT_MONO}'; font-size: 10px; font-weight: bold;"
STYLE_STATS_LBL = f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;"
STYLE_ROSTER_EMPTY_BOX = "QGroupBox { border: none; padding: 0; }"
# -------------------------

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
        self.setObjectName(OBJ_SIDE_PANEL)
        
        # --- PHASE HEADER ---
        self.header = TacticalHeader(STR_HEADER_OPS)
        self.layout.addWidget(self.header)
        
        # --- TACTICAL INTEL (Persistent Summary) ---
        self.intel_card = TacticalCard(title=STR_CARD_INTEL)
        self.lbl_intel_theater = QLabel(STR_LBL_THEATER_FMT.format(val=STR_VAL_UNASSIGNED))
        self.lbl_intel_side = QLabel(STR_LBL_SIDE_FMT.format(val=STR_VAL_NEUTRAL))
        self.lbl_intel_assets = QLabel(STR_LBL_ASSETS_FMT.format(val=0))
        
        for lbl in [self.lbl_intel_theater, self.lbl_intel_side, self.lbl_intel_assets]:
            lbl.setStyleSheet(STYLE_INTEL_LBL)
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
        self.setStyleSheet(STYLE_SIDE_PANEL)

    def sync_to_mode(self, mode_index):
        """Called by ModeStateMachine to flip the stack based on current phase."""
        # Modes: maps(0), terrain(1), rules(2), def_areas(3), def_agents(4), atk_areas(5), atk_agents(6), play(7)
        self._refresh_intel()
        
        if mode_index == 1: # Terrain
            self.header.setText(STR_HEADER_TERRAIN)
            self.stack.setCurrentIndex(0)
            self._refresh_terrain_ui()
        elif mode_index in [3, 5]: # Areas
            side = "DEFENDER" if mode_index == 3 else "ATTACKER"
            self.header.setText(STR_HEADER_AREA_FMT.format(side=side))
            self.stack.setCurrentIndex(1)
            self._refresh_area_ui(side)
        elif mode_index in [4, 6]: # Agents
            side = "DEFENDER" if mode_index == 4 else "ATTACKER"
            self.header.setText(STR_HEADER_GARRISON_FMT.format(side=side))
            self.stack.setCurrentIndex(2)
            self._refresh_deploy_ui(side)
        elif mode_index == 7: # Play
            self.header.setText(STR_HEADER_EXECUTION)
            self.stack.setCurrentIndex(3)
        else:
            self.header.setText(STR_HEADER_OPS)

    def _refresh_intel(self):
        """Update the persistent intel summary."""
        theater = getattr(self.state.current_map, 'upper', lambda: STR_VAL_LOCAL_SECTOR)()
        self.lbl_intel_theater.setText(STR_LBL_THEATER_FMT.format(val=theater))
        
        side = getattr(self.state, "active_scenario_side", "Combined")
        color = Theme.ACCENT_ENEMY if side == "Attacker" else Theme.ACCENT_ALLY
        if side == "Combined": color = Theme.TEXT_PRIMARY
        
        self.lbl_intel_side.setText(STR_LBL_SIDE_FMT.format(val=side.upper()))
        self.lbl_intel_side.setStyleSheet(STYLE_INTEL_SIDE_BOLD.format(color=color, Theme=Theme))
        
        if self.state.entity_manager:
            entities = self.state.entity_manager.get_all_entities()
            count = 0
            for e in entities:
                e_side = e.get_attribute("side", "Neutral")
                if side == "Combined" or e_side.upper() == side.upper():
                    count += 1
            self.lbl_intel_assets.setText(STR_LBL_DEPLOYED_SIDE_ASSETS_FMT.format(side=side.upper(), count=count))
            
    # --- SUB-PANEL CREATION ---

    def _create_terrain_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.terrain_card = TacticalCard(title=STR_CARD_BRUSH)
        layout.addWidget(self.terrain_card)
        
        self.terrain_options_container = QVBoxLayout()
        self.terrain_card.addLayout(self.terrain_options_container)
        
        layout.addStretch()
        return panel

    def _create_area_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.area_card = TacticalCard(title=STR_CARD_ZONE)
        layout.addWidget(self.area_card)
        
        self.area_options_container = QVBoxLayout()
        self.area_card.addLayout(self.area_options_container)
        
        layout.addStretch()
        return panel

    def _create_deploy_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        self.deploy_card = TacticalCard(title=STR_CARD_ROSTER)
        layout.addWidget(self.deploy_card)
        
        self.deploy_options_container = QVBoxLayout()
        self.deploy_card.addLayout(self.deploy_options_container)
        
        layout.addStretch()
        return panel

    def _create_play_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        card = TacticalCard(title=STR_CARD_VISUAL)
        v_layout = QVBoxLayout()
        
        chk_threat = QCheckBox(STR_CHK_THREAT)
        chk_threat.toggled.connect(self.mw.toggle_threat_map)
        v_layout.addWidget(chk_threat)
        
        chk_reward = QCheckBox(STR_CHK_REWARD)
        chk_reward.toggled.connect(self.mw.toggle_reward_viz)
        v_layout.addWidget(chk_reward)
        
        card.addLayout(v_layout)
        layout.addWidget(card)
        
        res_card = TacticalCard(title=STR_CARD_LOG)
        self.lbl_stats = QLabel(STR_LBL_SIM_IDLE)
        self.lbl_stats.setStyleSheet(STYLE_STATS_LBL)
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
        opts = ZoneOptionsWidget(self.mw, self.state)
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
                box.setStyleSheet(STYLE_ROSTER_EMPTY_BOX)
                
        self.deploy_options_container.addWidget(palette)
        # Single deferred refresh to ensure data is populated after widget layout
        QTimer.singleShot(50, tool.refresh_roster)
