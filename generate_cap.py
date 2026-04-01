import sys
import copy
sys.path.append('.')
from engine.data.loaders.data_manager import DataManager
from engine.core.entity_manager import Agent
from engine.core.hex_math import Hex

dm = DataManager('content')

# Define the basic Scenario dictionary
data = {
    "name": "CAP",
    "map_name": "Default",
    "project_name": "rPresent",
    "rules": {
        "attacker_max_force": 10,
        "defender_max_force": 10,
        "max_turns": 100
    },
    "zones": {
        "goal_1": {
            "name": "Goal 1",
            "type": "Goal Area",
            "side": "Defender",
            "color": "#0000FF",
            "hexes": [[0, -2, 2]]
        },
        "goal_2": {
            "name": "Goal 2",
            "type": "Goal Area",
            "side": "Defender",
            "color": "#0000FF",
            "hexes": [[0, 2, -2]]
        },
        "mine_area": {
            "name": "Mine Area",
            "type": "Obstacle",
            "side": "Neutral",
            "color": "#FFA500",
            "hexes": [[6, -3, -3], [6, -2, -4], [6, -4, -2], [7, -3, -4], [7, -4, -3], [6, -1, -5], [6, 0, -6]]
        }
    },
    "entities": [],
    "paths": {}
}

# Add Defenders
# D1 at [0, -2, 2]
data["entities"].append({
    "id": "Defender1",
    "name": "Defender1",
    "type": "NATO_Infantry_Squad",
    "side": "Defender",
    "q": 0, "r": -2, "s": 2,
    "attributes": {"weapon": "INSAS", "hierarchy": "Squad", "personnel": 100}
})
# D2 at [0, 2, -2]
data["entities"].append({
    "id": "Defender2",
    "name": "Defender2",
    "type": "NATO_Infantry_Squad",
    "side": "Defender",
    "q": 0, "r": 2, "s": -2,
    "attributes": {"weapon": "INSAS", "hierarchy": "Squad", "personnel": 100}
})

# Reserve Defender at [-20, 8, 12]
data["entities"].append({
    "id": "Defender3",
    "name": "ReserveDefender",
    "type": "NATO_Infantry_Squad",
    "side": "Defender",
    "q": -20, "r": 8, "s": 12,
    "attributes": {"weapon": "LMG", "hierarchy": "Squad", "personnel": 100}
})

# Add Attackers
# Distance 12 from D1 [0, -2, 2]
# Center at [12, -6, -6]
data["entities"].append({
    "id": "Attacker1",
    "name": "Attacker1",
    "type": "OPFOR_Militia",
    "side": "Attacker",
    "q": 12, "r": -6, "s": -6,
    "attributes": {"weapon": "SMG", "hierarchy": "Squad", "personnel": 100}
})
data["entities"].append({
    "id": "Attacker2",
    "name": "Attacker2",
    "type": "OPFOR_Militia",
    "side": "Attacker",
    "q": 12, "r": -7, "s": -5,
    "attributes": {"weapon": "INSAS", "hierarchy": "Squad", "personnel": 100}
})

# Attacker 3 with 4-hex range weapon (Sniper Rifle matches range 4 in typical definitions, or ATGM)
data["entities"].append({
    "id": "Attacker3",
    "name": "Attacker3",
    "type": "OPFOR_Sniper",
    "side": "Attacker",
    "q": 13, "r": -6, "s": -7,
    "attributes": {"weapon": "Sniper_Rifle", "hierarchy": "Squad", "personnel": 50}
})

# Save using native service
dm.save_scenario("CAP", data, project_path="content/Projects/rPresent")
print("CAP Scenario Generated Successfully!")
