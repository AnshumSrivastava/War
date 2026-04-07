"""
FILE: ui/core/mode_state_machine.py
ROLE: The "Stage Manager".

DESCRIPTION:
This controller manages the different application modes and toggles the
visibility of UI elements (docks, toolbars, tabs) accordingly.

MODES (6-phase workflow):
    0 = maps       (Dashboard / Project Gallery)
    1 = terrain    (Paint terrain, elevation)
    2 = area       (Draw zones, paths, assign sides)
    3 = agents     (Place units, assign weapons)
    4 = play       (RL Simulation)
    5 = master_data (Database editor)
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, Qt

class ModeStateMachine(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.state = main_window.state
        self.current_mode_index = 0
        
    def switch_mode(self, index):
        """Switches the application between its 8 operational phases."""
        self.current_mode_index = index
        modes = ["maps", "terrain", "rules", "def_areas", "def_agents", "atk_areas", "atk_agents", "play", "master_data"]
        
        if index < len(modes):
            mode = modes[index]
        else:
            mode = "terrain"
            
        self.mw.log_info(f"Switching to phase: <b>{mode.upper()}</b>")
        self.state.app_mode = mode
        
        # Hide internal navigation aids by default
        if hasattr(self.mw, 'map_header_tabs'): 
            self.mw.map_header_tabs.hide()
        
        # 1. Dashboard (index 0)
        if mode == "maps":
            self.mw.content_stack.setCurrentIndex(0)
            if hasattr(self.mw, 'maps_widget'):
                self.mw.maps_widget.show()
                self.mw.maps_widget.refresh_list()
            
            self.mw.toc_dock.hide()
            self.mw.timeline_panel.hide()
            if hasattr(self.mw, 'terminal_dock'): self.mw.terminal_dock.hide()
            self.mw.pause_simulation()
            
        # 2. Master Data (index 8)
        elif mode == "master_data":
            self.mw.content_stack.setCurrentWidget(self.mw.master_data_widget)
            self.mw.toc_dock.hide()
            self.mw.timeline_panel.hide()
            if hasattr(self.mw, 'terminal_dock'): self.mw.terminal_dock.hide()
            if hasattr(self.mw, 'maps_widget'): self.mw.maps_widget.hide()
            self.mw.pause_simulation()
            
        # 3. Rules (index 2)
        elif mode == "rules":
            if hasattr(self.mw, 'maps_widget'): self.mw.maps_widget.hide()
            if hasattr(self.mw, 'rules_widget'):
                self.mw.rules_widget.refresh()
            self.mw.toc_dock.hide()
            self.mw.timeline_panel.hide()
            if hasattr(self.mw, 'terminal_dock'): self.mw.terminal_dock.hide()
            self.mw.pause_simulation()
        
        # 4. Active Tactical Modes
        else:
            if hasattr(self.mw, 'maps_widget'):
                self.mw.maps_widget.hide()
            self.mw.content_stack.setCurrentIndex(1) 
            
            # Sync Mission Control Sidebar (TOC)
            if hasattr(self.mw, 'tac_panel'):
                self.mw.toc_dock.show()
                self.mw.tac_panel.sync_to_mode(index)
            
            if mode == "play":
                self.mw.timeline_panel.show()
                self.mw.toc_dock.hide() # Hide deploy tools in simulation
                if hasattr(self.mw, 'terminal_dock'): self.mw.terminal_dock.show()
            else:
                self.mw.timeline_panel.hide()
                if hasattr(self.mw, 'terminal_dock'): self.mw.terminal_dock.hide()
                self.mw.pause_simulation()
                
                # Side Assignment Logic
                if "def_" in mode:
                    self.state.active_scenario_side = "Defender"
                elif "atk_" in mode:
                    self.state.active_scenario_side = "Attacker"
                
                # Tool Activation
                if mode == "terrain":
                    self.mw.set_tool("paint_tool")
                elif "areas" in mode:
                    self.mw.set_tool("draw_zone")
                elif "agents" in mode:
                    self.mw.set_tool("place_agent")

        # Delegate tool visibility update to toolbar controller
        if hasattr(self.mw, 'toolbar_controller'):
            self.mw.toolbar_controller.update_tools_visibility()
        
        if hasattr(self.mw, 'hex_widget'):
            self.mw.hex_widget.update()

