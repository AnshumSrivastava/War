"""
FILE: engine/data/definitions/constants.py
ROLE: The "Rulebook" (Game Constants and Fallback Data).

DESCRIPTION:
This file contains the hardcoded constants and fallback definitions for the engine.
"""

# RL Action indices (used by Q-table)
RL_ACTION_MAP = {
    0: ("FIRE", None),
    1: ("MOVE", "east"),
    2: ("MOVE", "northeast"),
    3: ("MOVE", "northwest"),
    4: ("MOVE", "west"),
    5: ("MOVE", "southwest"),
    6: ("MOVE", "southeast"),
    7: ("HOLD / END TURN", None),
    8: ("CLOSE_COMBAT", None),
    9: ("COMMIT_FIRE", None),
    10: ("COMMIT_MOVE", None),
}

NUM_RL_ACTIONS = 11

# --- FALLBACK DATA (If JSON files are missing) ---

ROLES = {
    "attacker": {
        "speed_of_action": 8.0,
        "range_of_fire": 6.0,
        "vision_range": 9.0,
        "combat_factor": 8.0
    },
    "defender": {
        "speed_of_action": 4.0,
        "range_of_fire": 5.0,
        "vision_range": 6.0,
        "combat_factor": 9.0
    }
}

UNIT_TYPES = {
    "FireAgent": {
        "role": "attacker",
        "personnel": 110,
        "speed": 5,
        "range": 6,
        "attack": 25,
        "defense": 15,
        "stealth": 10,
        "actions": ["CLOSE_COMBAT", "FIRE", "MOVE", "HOLD / END TURN"]
    },
    "SniperAgent": {
        "role": "attacker",
        "personnel": 20,
        "speed": 6,
        "range": 15,
        "attack": 80,
        "defense": 30,
        "stealth": 80,
        "actions": ["FIRE", "MOVE", "HOLD / END TURN"]
    },
    "HeavyGunnerAgent": {
        "role": "defender",
        "personnel": 150,
        "speed": 2,
        "range": 10,
        "attack": 40,
        "defense": 40,
        "stealth": 0,
        "actions": ["FIRE", "MOVE", "HOLD / END TURN"]
    }
}
