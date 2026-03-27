"""
FILE:    ui/styles/ui_state.py
LAYER:   Frontend
ROLE:    UI-only settings — tool selection, display preferences, visual toggles.

DESCRIPTION:
    This module stores user-interface preferences and the current active
    tool. It has been moved OUT of engine/state/ because these settings
    are purely a UI concern — the backend engine should never need to
    know which tool is selected or what the theme mode is.

    One UIState instance is created in main.py and passed to MainWindow.
    No other part of the system touches it directly.

    MIGRATION NOTE:
    - Old location: engine/state/ui_settings.py (UISettings class)
    - GlobalState still has delegation properties for backward compat.
    - New code should reference ui_state directly, not GlobalState.ui.*

DOES NOT IMPORT FROM:
    - engine/ (anything)
    - services/
    - PyQt5
"""


class UIState:
    """
    Holds all UI-specific preferences for the current session.

    This is not a singleton — one instance is created at app startup
    and passed down wherever UI components need it.
    """

    def __init__(self):
        # --- TOOL SELECTION ---
        # The name of the currently active drawing/editing tool.
        self.selected_tool: str = "Select"

        # --- DISPLAY PREFERENCES ---
        self.theme_mode: str  = "dark"        # "dark" or "light"
        self.grid_mode: str   = "bounded"     # "bounded" or "infinite"

        # --- SCENARIO EDITING ---
        # Which side is currently being edited in the scenario panel.
        self.active_scenario_side: str = "Attacker"
        # Maps color labels to side roles (e.g. {"Red": "Defender"}).
        self.role_allocation: dict = {"Red": "Defender", "Blue": "Attacker"}

        # --- INSPECTOR DEFAULTS ---
        # Default values shown in the zone/path drawing inspector.
        self.zone_opt_type: str    = "Designated Area"
        self.zone_opt_subtype: str = "Red Area 1"
        self.zone_terrain_type: str = "Plains"
        self.path_mode: str        = "Center-to-Center"

        # --- CUSTOM DEFINITIONS ---
        # User-defined path types and their display colors.
        self.custom_path_types: list  = []
        self.custom_path_colors: dict = {}

        # --- VISUAL TOGGLES ---
        self.show_sections: bool = True
        self.show_borders: bool  = True
