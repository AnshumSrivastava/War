"""
FILE:    engine/models/__init__.py
LAYER:   Backend
ROLE:    Public interface for all shared data models and constants.

DESCRIPTION:
    This package contains TypedDict definitions and canonical constants
    used across the entire engine. Import from here, not from sub-modules,
    to keep imports stable as the model definitions evolve.

DOES NOT IMPORT FROM:
    - Any UI code (ui/, web_ui/)
    - services/
    - engine.state.global_state
"""

from engine.models.constants import (
    SIDE_ATTACKER, SIDE_DEFENDER, SIDE_NEUTRAL,
    TERRAIN_PLAINS, TERRAIN_FOREST, TERRAIN_URBAN, TERRAIN_WATER,
    ATTR_PERSONNEL, ATTR_HEALTH, ATTR_SUPPRESSION, ATTR_SIDE, ATTR_TYPE,
    ATTR_WEIGHT, ATTR_TOKENS, ATTR_FIRE_RANGE, ATTR_VISION_RANGE,
)
from engine.models.entity_model import AgentData
from engine.models.hex_model import HexData
from engine.models.scenario_model import ScenarioData

__all__ = [
    # Side constants
    "SIDE_ATTACKER", "SIDE_DEFENDER", "SIDE_NEUTRAL",
    # Terrain constants
    "TERRAIN_PLAINS", "TERRAIN_FOREST", "TERRAIN_URBAN", "TERRAIN_WATER",
    # Attribute key constants
    "ATTR_PERSONNEL", "ATTR_HEALTH", "ATTR_SUPPRESSION", "ATTR_SIDE",
    "ATTR_TYPE", "ATTR_WEIGHT", "ATTR_TOKENS", "ATTR_FIRE_RANGE",
    "ATTR_VISION_RANGE",
    # TypedDicts
    "AgentData", "HexData", "ScenarioData",
]
