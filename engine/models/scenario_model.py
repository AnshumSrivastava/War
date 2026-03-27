"""
FILE:    engine/models/scenario_model.py
LAYER:   Backend
ROLE:    TypedDict schema for scenario and project file data.

DESCRIPTION:
    Defines the canonical shape of a scenario data dictionary as
    loaded from content/Projects/ JSON files. Services and the UI
    reference this type when passing scenario data across layer boundaries.

    This is a READ-ONLY schema definition — no logic here.

DOES NOT IMPORT FROM:
    - Any UI code
    - services/
    - engine.state
"""

from typing import TypedDict, Optional, List, Dict, Any

class SideData(TypedDict, total=False):
    """Represents one side (Attacker or Defender) inside a scenario."""
    name:       str             # Display name for this side
    color:      str             # UI color for this side's units
    agents:     List[Dict]      # List of AgentData dicts placed for this side
    goal_zones: List[str]       # Zone IDs that are objectives for this side
    sections:   List[str]       # Hex section IDs assigned to this side

class RulesData(TypedDict, total=False):
    """Combat and simulation rules for a scenario."""
    max_agents_per_hex: int     # Stacking limit (unit count fallback)
    max_weight_per_hex: float   # Stacking limit (weight-based)
    time_per_step:      int     # Simulated minutes per tick
    max_steps:          int     # Episode length in ticks
    fog_of_war:         bool    # Whether fog-of-war is active

class ScenarioData(TypedDict, total=False):
    """
    The canonical shape of a loaded scenario/project file.

    Loaded from content/Projects/<name>.json by the data service.
    """
    name:           str                     # Scenario display name
    description:    str                     # Short description
    map_file:       str                     # Relative path to the map JSON
    sides:          Dict[str, SideData]     # Keyed by side name constant
    rules:          RulesData               # Combat rules
    zones:          Dict[str, Any]          # Zone definitions (id -> zone data)
    paths:          Dict[str, Any]          # Path definitions (id -> path data)
    sections:       Dict[str, Any]          # Section definitions
