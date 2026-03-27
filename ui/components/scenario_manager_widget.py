"""
FILE: ui/components/scenario_manager_widget.py
ROLE: Scenario & Mission Setup.
DESCRIPTION: Interface for selecting which agents are available, choosing the map, and defining win/loss conditions.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QGroupBox, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
from engine.core.map import Scenario
from engine.state.global_state import GlobalState

class ScenarioManagerWidget(QWidget):
    def __init__(self, parent_window, state=None):
        super().__init__()
        self.parent_window = parent_window
        from engine.data.loaders.data_manager import DataManager
        self.data_loader = DataManager()
        self.state = state if state else GlobalState()
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        from ui.styles.theme import Theme
        from ui.core.icon_painter import VectorIconPainter
        from PyQt5.QtWidgets import QToolButton, QSizePolicy, QFrame
        from PyQt5.QtCore import QSize
        from ui.components.themed_widgets import TacticalCard, TacticalHeader
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header = TacticalHeader("MISSION OPERATIONS")
        layout.addWidget(header)
        
        # Scenario Container
        self.card = TacticalCard(title="MISSION PROFILES")
        self.scen_list = QListWidget()
        self.scen_list.setFrameShape(QFrame.NoFrame)
        self.scen_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_HEADER}'; font-size: 11px; }}
            QListWidget::item {{ 
                padding: 10px; border-bottom: 1px solid {Theme.BORDER_STRONG}; 
                background-color: {Theme.BG_DEEP}; margin-bottom: 2px;
            }}
            QListWidget::item:selected {{ 
                background-color: {Theme.BG_INPUT}; color: {Theme.ACCENT_ALLY}; border-left: 3px solid {Theme.ACCENT_ALLY}; 
            }}
        """)
        self.scen_list.itemClicked.connect(self.on_scenario_selected)
        self.scen_list.setToolTip("Mission Profiles\nClick a scenario to load it.\nThe active scenario determines which units and zones are visible.")
        self.card.addWidget(self.scen_list)
        
        # --- Mission Intel Section (Restored) ---
        self.intel_group = QFrame()
        self.intel_group.setStyleSheet(f"background-color: {Theme.BG_DEEP}; border-top: 1px solid {Theme.BORDER_STRONG}; margin-top: 10px; padding: 10px;")
        intel_layout = QVBoxLayout(self.intel_group)
        
        self.lbl_intel_header = QLabel("TACTICAL INTEL SUMMARY")
        self.lbl_intel_header.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_HEADER}'; font-size: 10px; font-weight: bold; margin-bottom: 5px;")
        intel_layout.addWidget(self.lbl_intel_header)
        
        self.lbl_intel_units = QLabel("DEPLOYED ASSETS: 0")
        self.lbl_intel_theater = QLabel("OP THEATER: [UNASSIGNED]")
        
        for lbl in [self.lbl_intel_units, self.lbl_intel_theater]:
            lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
            intel_layout.addWidget(lbl)
            
        self.card.addWidget(self.intel_group)
        layout.addWidget(self.card, 1)
        
        # Action Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(5)
        
        self.btn_new = QToolButton()
        self.btn_new.setText("INITIALIZE NEW MISSION")
        self.btn_new.setToolTip("Create New Mission\nInitializes a fresh scenario with no units,\nthen prompts you to define the map border.")
        self.btn_new.setStyleSheet(f"background: {Theme.BG_INPUT}; color: {Theme.ACCENT_ALLY}; padding: 10px; font-weight: bold; border-radius: 4px;")
        self.btn_new.clicked.connect(self.new_scenario_dialog)
        
        btn_row.addWidget(self.btn_new)
        layout.addLayout(btn_row)
        
    def refresh_list(self):
        self.scen_list.clear()
        scenarios = self.data_loader.list_scenarios()
        for s in scenarios:
            self.scen_list.addItem(s)
            
        # Restore active scenario selection logic
        if self.state.map and hasattr(self.state.map, 'scenarios') and self.state.map.scenarios:
            active_name = None
            if hasattr(self.state.map, 'active_scenario') and self.state.map.active_scenario:
                active_name = self.state.map.active_scenario.name
            
            for name in self.state.map.scenarios:
                # Select if matches active
                if name == active_name:
                    for i in range(self.scen_list.count()):
                        if self.scen_list.item(i).text() == name:
                            self.scen_list.setCurrentRow(i)
                            break
        
    def on_scenario_selected(self, item):
        name = item.text()
        if name in self.state.map.scenarios:
            # 1. Save Old State
            if hasattr(self.state.map, 'active_scenario') and self.state.map.active_scenario:
                old_scen = self.state.map.active_scenario
                if hasattr(old_scen, 'capture_state'):
                    old_scen.capture_state(self.state.entity_manager)
            
            # 2. Switch Active
            new_scen = self.state.map.scenarios[name]
            self.state.map.active_scenario = new_scen
            print(f"Switched to Scenario: {name}")
            
            # 3. Restore New State
            if hasattr(new_scen, 'restore_state'):
                new_scen.restore_state(self.state.entity_manager)
            
            # Notify parent to update
            if hasattr(self.parent_window, 'hex_widget'):
                self.parent_window.hex_widget.update()
                
            self.update_intel(new_scen)

    def update_intel(self, scenario):
        """Standardized Intel Summary for 'at-a-glance' readability."""
        if not scenario: return
        unit_count = len(scenario.spawn_points) if hasattr(scenario, 'spawn_points') else 0
        self.lbl_intel_units.setText(f"DEPLOYED ASSETS: {unit_count}")
        theater = getattr(self.state.map, 'name', 'LOCAL SECTOR')
        self.lbl_intel_theater.setText(f"OP THEATER: {theater.upper()}")

    def refresh_intel(self, side="Combined"):
        """Update the tactical intel based on selected side."""
        if not self.state.map or not self.state.entity_manager: return
        
        entities = self.state.entity_manager.get_all_entities()
        count = 0
        for e in entities:
            e_side = e.get_attribute("side", "Neutral")
            if side == "Combined" or e_side.upper() == side.upper():
                count += 1
                
        self.lbl_intel_units.setText(f"DEPLOYED {side.upper()} ASSETS: {count}")
        theater = getattr(self.state.map, 'name', 'LOCAL SECTOR')
        self.lbl_intel_theater.setText(f"OP THEATER: {theater.upper()}")
                
    def new_scenario_dialog(self):
        name, ok = QInputDialog.getText(self, "New Scenario", "Scenario Name:")
        if ok and name:
            if name in self.state.map.scenarios:
                QMessageBox.warning(self, "Error", "Scenario name already exists.")
                return
            new_scen = Scenario(name)
            self.state.map.scenarios[name] = new_scen
            self.state.map.active_scenario = new_scen
            
            # Reset Border/Sides for new scenario
            self.state.map.border_path = []
            self.state.map.hex_sides = {}
            
            self.refresh_list()
            
            # Trigger Border Setup Prompt via MainWindow
            if hasattr(self.parent_window, 'tab_widget'):
                self.parent_window.tab_widget.setCurrentIndex(2) # Switch to Scenario Tab (Index 2)
                self.parent_window.switch_mode(2) 
            elif hasattr(self.parent_window, 'switch_mode'):
                 self.parent_window.switch_mode(2)
            
            # Notify parent
            if hasattr(self.parent_window, 'hex_widget'):
                self.parent_window.hex_widget.update()
