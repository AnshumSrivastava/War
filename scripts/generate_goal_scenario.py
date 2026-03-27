import sys
import os
import uuid
import random

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.state.global_state import GlobalState
from engine.core.hex_math import Hex
from engine.core.entity_manager import Agent

def generate_scenario():
    print("--- Generating Goal & Mines Scenario ---")
    state = GlobalState()
    
    # 1. Setup a basic map if not exists
    if not state.map.hexes:
        print("Initializing 10x10 map...")
        for q in range(10):
            for r in range(10):
                state.map.set_terrain(Hex(q, r, -q-r), {"type": "plains"})

    # 2. Add a Goal Area for Defenders
    goal_id = "goal_" + str(uuid.uuid4())[:4]
    goal_hex = Hex(8, 0, -8)
    print(f"Adding Goal Area at {goal_hex}")
    
    state.map.add_zone(goal_id, {
        "name": "Strategic Objective",
        "type": "Goal Area",
        "color": "#00FF00",
        "hexes": [goal_hex]
    })
    
    # 3. Add some Mines in the path
    print("Scattering Mines...")
    for i in range(5):
        m_hex = Hex(random.randint(3, 6), random.randint(0, 3), 0)
        m_hex.s = -m_hex.q - m_hex.r
        state.map.add_zone(f"mine_{i}", {
            "name": f"Minefield Alpha {i}",
            "type": "Obstacle",
            "subtype": "mine",
            "color": "#555555",
            "hexes": [m_hex]
        })

    # 4. Save the scenario
    save_path = os.path.join("content", "maps", "scenarios", "goal_test_mission.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Simple manual save of scenario data since we don't want to run the full UI
    import json
    data = {
        "name": "Goal Test Mission",
        "zones": state.map.zones,
        "spawn_points": [] # Defenders will be spawned by DrawZoneTool if used, or manually here
    }
    
    # Let's manually add some defenders around the goal to match the requirement
    neighbors = [Hex(8, -1, -7), Hex(9, -1, -8), Hex(9, 0, -9), Hex(8, 1, -9)]
    for i, h in enumerate(neighbors):
        d = Agent(f"Defender_{i}")
        d.set_attribute("side", "Defender")
        d.set_attribute("home_hex", h)
        state.entity_manager.add_entity(d, h)
        data["spawn_points"].append({
            "id": d.id,
            "type": "Infantry",
            "side": "Defender",
            "hex": [h.q, h.r, h.s]
        })

    with open(save_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"SUCCESS: Scenario saved to {save_path}")
    print("You can now load 'goal_test_mission.json' in the Wargame Engine.")

if __name__ == "__main__":
    generate_scenario()
