"""
FILE:    engine/models/entity_model.py
LAYER:   Backend
ROLE:    TypedDict schema for agent/entity data returned by the engine.

DESCRIPTION:
    Defines the canonical shape of an agent's data dictionary as it flows
    through the system. Any function that returns entity data should conform
    to AgentData. This makes static analysis, IDE autocomplete, and team
    collaboration far more reliable.

    This is a READ-ONLY schema definition. It contains no logic.

DOES NOT IMPORT FROM:
    - Any UI code
    - services/
    - engine.state
"""

from typing import TypedDict, Optional, List

class AgentData(TypedDict, total=False):
    """
    The canonical shape of an agent entity's attribute dictionary.

    All keys are optional (total=False) because agents may not have all
    attributes populated at all times (e.g. during placement before config
    is resolved). Consumers must use .get() with a default.

    Attribute keys here MUST match the constants in engine.models.constants.
    """
    # Identity
    id:             str             # Unique agent ID (e.g. "agent_001")
    name:           str             # Display name (e.g. "Alpha Squad")
    type:           str             # Unit type key (maps to content/ definition)
    side:           str             # SIDE_ATTACKER or SIDE_DEFENDER

    # Position — stored as (q, r) axial coords; s is derived
    q:              int
    r:              int

    # Strength
    personnel:      int             # Current strength (0 = destroyed)
    max_personnel:  int             # Starting/full strength

    # Combat stats (resolved from unit config at runtime)
    fire_range:     int             # Direct fire range in hexes
    vision_range:   int             # Spotting range in hexes
    weight:         float           # For stacking weight limits

    # Status
    suppression:    float           # 0 = normal, 50 = suppressed, 100+ = pinned
    under_fire:     bool            # Was shot at this turn
    tokens:         float           # Action tokens remaining

    # Learning flags
    learned:        bool            # If True, uses persistent Q-table

    # Navigation history (anti-loop system)
    visited_hexes:  List[List[int]] # Recent positions as [q, r, s] lists
