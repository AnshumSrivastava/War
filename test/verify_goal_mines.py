import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock PyQt5 before imports
mock_qt = MagicMock()
sys.modules["PyQt5"] = mock_qt
sys.modules["PyQt5.QtCore"] = mock_qt
sys.modules["PyQt5.QtWidgets"] = mock_qt
sys.modules["PyQt5.QtGui"] = mock_qt

# Add paths to make imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.state.global_state import GlobalState
from engine.simulation.act_model import ActionModel
from engine.core.entity_manager import Agent
from engine.core.hex_math import Hex
from engine.simulation.move import MoveAction

# Fix for TestVerification
MoveAction.log = MagicMock()

class TestVerification(unittest.TestCase):
    def setUp(self):
        GlobalState._instance = None
        self.state = GlobalState()
        self.state.entity_manager.clear()
        self.state.map.width = 20
        self.state.map.height = 20
        self.state.map._terrain = {}
        # Fill map with some terrain
        for q in range(-5, 5):
            for r in range(-5, 5):
                self.state.map.set_terrain(Hex(q, r, -q-r), {"type": "plain", "cost": 1.0})

    def test_mine_strike(self):
        print("\n--- Testing Mine Strike ---")
        agent = Agent(name="Tester")
        agent.set_attribute("side", "Attacker")
        agent.set_attribute("personnel", 100)
        self.state.entity_manager.register_entity(agent)
        
        start_hex = Hex(0, 0, 0)
        mine_hex = Hex(1, 0, -1)
        self.state.map.place_entity(agent.id, start_hex)
        
        # Place a mine at (1, 0) as an Obstacle Zone
        self.state.map.add_zone("mine_1", {
            "type": "Obstacle",
            "subtype": "mine",
            "hexes": [mine_hex]
        })
        
        # Move into the mine hex
        move = MoveAction()
        # In hexagonal math, (1, 0, -1) is direction 'e' (East) or similar depending on map
        # Let's just use the direction map from move.py if we can, or bypass and call execute with specific hex
        # MoveAction.execute(self, entity, game_map, direction=None, **kwargs)
        # It calculates new_hex via DIRECTION_MAP[direction]
        
        # We'll just mock the DIRECTION_MAP or use a valid key
        from engine.core.hex_math import DIRECTION_MAP
        # Find which direction leads to (1, 0, -1)
        target_dir = None
        for d, coords in DIRECTION_MAP.items():
            if coords == (1, 0, -1):
                target_dir = d
                break
        
        if not target_dir:
            # Fallback: manually trigger movement logic or check which direction is (1, 0)
            target_dir = "e" # Usually
            
        print(f"Moving agent from {start_hex} to {mine_hex} via direction '{target_dir}'")
        res, event, _ = move.execute(agent, self.state.map, direction=target_dir, entity_manager=self.state.entity_manager)
        print(f"Result: {res}")
        
        new_personnel = int(agent.get_attribute("personnel", 100))
        print(f"Personnel after move: {new_personnel}")
        
        self.assertLess(new_personnel, 100, "Personnel should have decreased due to mine strike")

    def test_goal_prioritization(self):
        print("\n--- Testing Goal Prioritization ---")
        attacker = Agent(name="Attacker")
        attacker.set_attribute("side", "Attacker")
        attacker.set_attribute("personnel", 100)
        attacker.set_attribute("fire_range", 1)
        self.state.entity_manager.register_entity(attacker)
        self.state.map.place_entity(attacker.id, Hex(0, 0, 0))
        
        # Add a Goal Area for Defender at (5, 0)
        goal_hex = Hex(5, 0, -5)
        self.state.map.add_zone("goal_1", {
            "type": "Goal Area",
            "side": "Defender",
            "hexes": [goal_hex]
        })
        
        # Add a regular enemy far away at (0, 10)
        enemy = Agent(name="Enemy")
        enemy.set_attribute("side", "Defender")
        enemy.set_attribute("personnel", 100)
        self.state.entity_manager.register_entity(enemy)
        self.state.map.place_entity(enemy.id, Hex(0, 5, -5))
        
        from engine.ai.commander import StrategicCommander
        from engine.core.hex_math import HexMath
        
        target_pos = StrategicCommander._find_best_offensive_target(Hex(0, 0, 0), attacker, self.state)
        print(f"Target Position selected by Commander: {target_pos}")
        
        # The target hex should be near the goal area (5, 0), not near the enemy (0, 5)
        dist_to_goal = HexMath.distance(target_pos, goal_hex)
        dist_to_enemy = HexMath.distance(target_pos, Hex(0, 5, -5))
        
        print(f"Distance to Goal: {dist_to_goal}")
        print(f"Distance to Enemy: {dist_to_enemy}")
        
        self.assertLess(dist_to_goal, dist_to_enemy, "Attacker should prioritize the Goal Area over the distant enemy")

if __name__ == "__main__":
    unittest.main()
