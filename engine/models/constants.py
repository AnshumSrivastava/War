"""
FILE:    engine/models/constants.py
LAYER:   Backend
ROLE:    Single source of truth for all canonical string keys and identifiers.

DESCRIPTION:
    All string constants used anywhere in the engine live here and ONLY here.
    This eliminates the three parallel naming systems ("Attacker"/"Red"/"ally")
    and attribute key mismatches ("hp"/"health"/"personnel") that cause bugs.

    RULES:
    - Every string that appears in more than one file MUST be a constant here.
    - Never hardcode side names, terrain names, or attribute keys in engine code.
    - Import from `engine.models` (the package), not this file directly.

DOES NOT IMPORT FROM:
    - Any UI code
    - services/
    - engine.state
"""

# =============================================================================
# SIDES — Who is fighting whom
# =============================================================================
SIDE_ATTACKER = "Attacker"
SIDE_DEFENDER = "Defender"
SIDE_NEUTRAL  = "Neutral"

# =============================================================================
# TERRAIN TYPES — Canonical terrain identifiers used in content/ JSON files
# =============================================================================
TERRAIN_PLAINS    = "plains"
TERRAIN_FOREST    = "forest"
TERRAIN_URBAN     = "urban"
TERRAIN_WATER     = "water"
TERRAIN_ROAD      = "road"
TERRAIN_SLOPE     = "slope"
TERRAIN_ELEVATION = "elevation"
TERRAIN_MUD       = "mud"

# =============================================================================
# ENTITY ATTRIBUTE KEYS — Canonical keys for entity.get_attribute() / set_attribute()
# Use these constants everywhere. Do NOT hardcode "hp", "health", "personnel" strings.
# =============================================================================
ATTR_PERSONNEL     = "personnel"       # Number of people/vehicles in the unit
ATTR_MAX_PERSONNEL = "max_personnel"   # Starting/max strength
ATTR_HEALTH        = "personnel"       # Alias — health IS personnel count in this system
ATTR_SUPPRESSION   = "suppression"     # Suppression level 0–100+
ATTR_SIDE          = "side"            # Which side this entity belongs to
ATTR_TYPE          = "type"            # Unit type string (e.g. "HeavyGunner")
ATTR_WEIGHT        = "weight"          # For stacking/weight-limit calculations
ATTR_TOKENS        = "tokens"          # Action tokens remaining this turn
ATTR_FIRE_RANGE    = "fire_range"      # Direct fire range in hexes
ATTR_VISION_RANGE  = "vision_range"    # Sensor/spotting range in hexes
ATTR_UNDER_FIRE    = "under_fire"      # Bool: was this entity shot at this turn?
ATTR_VISITED_HEXES = "visited_hexes"   # List of recently visited hex coords (anti-loop)
ATTR_LEARNED       = "learned"         # Bool: uses pre-trained Q-table vs. ephemeral

# =============================================================================
# ZONE TYPES — Canonical zone/area categories
# =============================================================================
ZONE_DESIGNATED_AREA = "Designated Area"
ZONE_GOAL_AREA       = "Goal Area"
ZONE_OBSTACLE        = "Obstacle"
ZONE_RESTRICTED      = "Restricted"

# =============================================================================
# OBSTACLE SUBTYPES
# =============================================================================
OBSTACLE_MINE       = "mine"
OBSTACLE_WIRE       = "wire"
OBSTACLE_BARRIER    = "barrier"

# =============================================================================
# ACTION TYPES — Canonical names for simulation actions
# =============================================================================
ACTION_MOVE         = "MOVE"
ACTION_FIRE         = "FIRE"
ACTION_CLOSE_COMBAT = "CLOSE_COMBAT"
ACTION_COMMIT       = "COMMIT"
ACTION_HOLD         = "HOLD / END TURN"

# =============================================================================
# PATH MODES — How paths are drawn/interpreted
# =============================================================================
PATH_MODE_CENTER    = "Center-to-Center"
PATH_MODE_EDGE      = "Edge-to-Edge"
