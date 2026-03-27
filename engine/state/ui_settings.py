"""
FILE: engine/state/ui_settings.py
ROLE: The "Interface Memory".

DESCRIPTION:
This module stores user-interface preferences and current tool selections.
By separating this from the core world data, we make the engine easier 
to run in "Headless" mode (without a UI).
"""

class UISettings:
    def __init__(self):
        # --- TOOL SELECTION ---
        self.selected_tool = "Select"
        self.theme_mode = "dark"
        self.grid_mode = "bounded"
        
        # --- SCENARIO EDITING ---
        self.active_scenario_side = "Attacker"
        self.role_allocation = {"Red": "Defender", "Blue": "Attacker"}
        
        # --- INSPECTOR DEFAULTS ---
        self.zone_opt_type = "Designated Area"
        self.zone_opt_subtype = "Red Area 1"
        self.zone_terrain_type = "Plains"
        self.path_mode = "Center-to-Center"
        
        # --- CUSTOM DEFINITIONS ---
        self.custom_path_types = []
        self.custom_path_colors = {}
        
        # --- VISUAL TOGGLES ---
        self.show_sections = True
        self.show_borders = True
