"""
FILE: ui/core/mode_state_machine.py
ROLE: The "Stage Manager".

DESCRIPTION:
This controller manages the different application modes (Terrain, Scenario, Play, etc.)
and toggles the visibility of UI elements (docks, toolbars, tabs) accordingly.
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
        """Reverted to V5 5-mode logic."""
        self.current_mode_index = index
        modes = ["maps", "terrain", "scenario", "play", "master_data"]
        
        if index < len(modes):
            mode = modes[index]
        else:
            mode = "terrain"
            
        self.mw.log_info(f"Switching to mode: <b>{mode.upper()}</b>")
        self.state.app_mode = mode
        
        # Hide specialized components by default
        if hasattr(self.mw, 'map_header_tabs'): 
            self.mw.map_header_tabs.hide()
        
        if mode == "maps":
            self.mw.content_stack.setCurrentIndex(0)
            if hasattr(self.mw, 'maps_widget'):
                self.mw.maps_widget.show()
                self.mw.maps_widget.refresh_list()
            
            # Hide side panels
            self.mw.timeline_dock.hide()
            self.mw.inspector_dock.hide() 
            if hasattr(self.mw, 'hierarchy_dock'): self.mw.hierarchy_dock.hide()
            if hasattr(self.mw, 'tool_dock'): self.mw.tool_dock.hide() 
            self.mw.pause_simulation()
            
        elif mode == "master_data":
            self.mw.content_stack.setCurrentWidget(self.mw.master_data_widget)
            self.mw.timeline_dock.hide()
            self.mw.inspector_dock.hide()
            if hasattr(self.mw, 'hierarchy_dock'): self.mw.hierarchy_dock.hide()
            self.mw.tool_dock.hide()
            if hasattr(self.mw, 'maps_widget'):
                self.mw.maps_widget.hide()
            self.mw.pause_simulation()
            
        else:
            if hasattr(self.mw, 'maps_widget'):
                self.mw.maps_widget.hide()
            self.mw.content_stack.setCurrentIndex(1) 
            
            if mode == "play":
                self.mw.timeline_dock.show() 
                self.mw.inspector_dock.hide() 
                if hasattr(self.mw, 'scenario_dock'): self.mw.scenario_dock.hide()
                if hasattr(self.mw, 'hierarchy_dock'): self.mw.hierarchy_dock.hide()
                self.mw.tool_dock.hide() 
                
            elif mode == "terrain":
                self.mw.timeline_dock.hide()
                self.mw.inspector_dock.show()
                self.mw.tool_dock.show()
                self.mw.pause_simulation()
                self.mw.set_tool("draw_zone") 
                
            elif mode == "scenario": 
                if hasattr(self.mw, 'map_header_tabs'): self.mw.map_header_tabs.show()
                self.mw.timeline_dock.hide()
                self.mw.inspector_dock.show()
                if hasattr(self.mw, 'scenario_dock'): self.mw.scenario_dock.show()
                if hasattr(self.mw, 'hierarchy_dock'): self.mw.hierarchy_dock.show()
                self.mw.tool_dock.show()
                self.mw.pause_simulation()
                
                if self.state.selected_tool == "cursor":
                    self.mw.set_tool("place_agent")

        # Delegate tool visibility update to toolbar controller if available
        if hasattr(self.mw, 'toolbar_controller'):
            self.mw.toolbar_controller.update_tools_visibility()
        
        # Scenario Dock Visibility logic (simplified, always on right)
        if mode == "scenario":
            if hasattr(self.mw, 'scenario_dock'):
                self.mw.scenario_dock.show()
                if hasattr(self.mw, 'scenario_manager_group'):
                    self.mw.scenario_manager_group.refresh_list()
            self.mw.tool_opts_group.show()
        elif mode == "terrain":
            if hasattr(self.mw, 'scenario_dock'):
                self.mw.scenario_dock.hide()
            self.mw.tool_opts_group.show()
        else:
            if hasattr(self.mw, 'scenario_dock'):
                self.mw.scenario_dock.hide()
            self.mw.tool_opts_group.hide()
        
        if hasattr(self.mw, 'hex_widget'):
            self.mw.hex_widget.update()
        
        if hasattr(self.mw, 'hex_widget'):
            self.mw.hex_widget.update()
