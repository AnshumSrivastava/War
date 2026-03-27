"""
FILE: engine/state/global_state.py
ROLE: The "Source of Truth" (Central Brain).

DESCRIPTION:
Think of GlobalState as a shared notebook that every part of the application
(the Map, the AI, the UI) carries around. 
1. If the UI changes a setting (like switching to "Dark Mode"), it writes it here.
2. If the Map adds a new hex or unit, it records it here.
3. If the AI wants to know its current position, it looks here.

Because it follows the "Singleton" pattern, there is ONLY EVER ONE notebook.
No matter where you are in the code, calling `GlobalState()` gives you access 
to the exact same data as everyone else.
"""

from engine.core.map import Map
from engine.core.entity_manager import EntityManager
from engine.data.loaders.data_manager import DataManager as DataController
from engine.state.threat_map import ThreatMap
from engine.state.ui_settings import UISettings

class GlobalState:
    """
    The central data store. It keeps track of the 'World State' and 'User Settings'.
    """
    _instance = None

    def __new__(cls):
        # SINGLETON: Only ever create ONE instance.
        if cls._instance is None:
            cls._instance = super(GlobalState, cls).__new__(cls)
            self = cls._instance
            
            # --- THE UI LAYER ---
            self.ui = UISettings()
            
            # --- THE WORLD DATA ---
            self.map = Map()
            self.entity_manager = EntityManager()
            self.threat_map = ThreatMap()
            
            # --- THE DATA LAYER ---
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(base_dir))
            content_path = os.path.join(root_dir, "content")
            
            self.data_controller = DataController(content_root=content_path)
            self.terrain_controller = self.data_controller
            
        # Ensure infrastructure is initialized on every new lookup
        from engine.core.undo_system import UndoStack
        if not hasattr(cls._instance, 'undo_stack'):
            cls._instance.undo_stack = UndoStack(limit=50)

        # Current File Context
        if not hasattr(cls._instance, 'project_path'):
            cls._instance.project_path = None
            cls._instance.current_project = None
            cls._instance.current_map = None 
            
        return cls._instance

    # --- DELEGATION PROPERTIES ---
    # These properties keep the engine backward-compatible with 
    # the old 'GlobalState().selected_tool' style while storing data in self.ui.

    @property
    def selected_tool(self): return self.ui.selected_tool
    @selected_tool.setter
    def selected_tool(self, val): self.ui.selected_tool = val

    @property
    def theme_mode(self): return self.ui.theme_mode
    @theme_mode.setter
    def theme_mode(self, val): self.ui.theme_mode = val

    @property
    def grid_mode(self): return self.ui.grid_mode
    @grid_mode.setter
    def grid_mode(self, val): self.ui.grid_mode = val

    @property
    def active_scenario_side(self): return self.ui.active_scenario_side
    @active_scenario_side.setter
    def active_scenario_side(self, val): self.ui.active_scenario_side = val

    @property
    def role_allocation(self): return self.ui.role_allocation
    @role_allocation.setter
    def role_allocation(self, val): self.ui.role_allocation = val

    @property
    def zone_opt_type(self): return self.ui.zone_opt_type
    @zone_opt_type.setter
    def zone_opt_type(self, val): self.ui.zone_opt_type = val

    @property
    def zone_opt_subtype(self): return self.ui.zone_opt_subtype
    @zone_opt_subtype.setter
    def zone_opt_subtype(self, val): self.ui.zone_opt_subtype = val

    @property
    def zone_terrain_type(self): return self.ui.zone_terrain_type
    @zone_terrain_type.setter
    def zone_terrain_type(self, val): self.ui.zone_terrain_type = val

    @property
    def path_mode(self): return self.ui.path_mode
    @path_mode.setter
    def path_mode(self, val): self.ui.path_mode = val

    @property
    def custom_path_types(self): return self.ui.custom_path_types
    @custom_path_types.setter
    def custom_path_types(self, val): self.ui.custom_path_types = val

    @property
    def custom_path_colors(self): return self.ui.custom_path_colors
    @custom_path_colors.setter
    def custom_path_colors(self, val): self.ui.custom_path_colors = val

    @property
    def show_sections(self): return self.ui.show_sections
    @show_sections.setter
    def show_sections(self, val): self.ui.show_sections = val

    @property
    def show_borders(self): return self.ui.show_borders
    @show_borders.setter
    def show_borders(self, val): self.ui.show_borders = val
