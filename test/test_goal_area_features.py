# Mock heavy dependencies before imports
import sys
import os
import unittest
from unittest.mock import MagicMock

mock_qt = MagicMock()
sys.modules["PyQt5"] = mock_qt
sys.modules["PyQt5.QtCore"] = mock_qt
sys.modules["PyQt5.QtWidgets"] = mock_qt
sys.modules["PyQt5.QtGui"] = mock_qt

mock_np = MagicMock()
sys.modules["numpy"] = mock_np

# Add paths to make imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.state.global_state import GlobalState
from engine.core.entity_manager import Agent
from engine.core.hex_math import Hex, HexMath
from engine.ai.commander import StrategicCommander
from engine.ai.reward import RewardModel
from ui.tools.draw_zone_tool import DrawZoneTool
from PyQt5.QtCore import Qt

class TestGoalAreaFeatures(unittest.TestCase):
    def setUp(self):
        GlobalState._instance = None
        self.state = GlobalState()
        self.state.entity_manager.clear()
        
        # Ensure DrawZoneTool is not a mock from previous tests
        global DrawZoneTool
        from ui.tools.draw_zone_tool import DrawZoneTool
        if isinstance(DrawZoneTool, MagicMock):
             import importlib
             import ui.tools.draw_zone_tool
             importlib.reload(ui.tools.draw_zone_tool)
             from ui.tools.draw_zone_tool import DrawZoneTool
        self.state.map.width = 20
        self.state.map.height = 20
        self.state.map._terrain = {}
        # Fill map with some terrain
        for q in range(-10, 10):
            for r in range(-10, 10):
                self.state.map.set_terrain(Hex(q, r, -q-r), {"type": "plain", "cost": 1.0})
        
        self.widget = MagicMock()
        self.widget.window.return_value = MagicMock()
        self.widget.hex_size = 50.0

    def test_conditional_spawn_with_designated(self):
        print("\n--- Testing Conditional Spawn (WITH Designated Area) ---")
        # 1. Create a Designated Area strictly inside the later Goal Area
        designated_hex = Hex(1, 1, -2) 
        self.state.map.add_zone("zone_1", {
            "type": "Designated Area",
            "hexes": [designated_hex]
        })
        
        # 2. Mock DrawZoneTool environment
        mock_widget = MagicMock()
        mock_window = MagicMock()
        mock_widget.window.return_value = mock_window
        mock_widget.screen_to_hex.side_effect = lambda x, y: Hex(0, 0, 0)
        
        # We'll mock the tool's commit method logic directly if inheritance is an issue,
        # but let's try to fix the class itself.
        from ui.tools.draw_zone_tool import DrawZoneTool
        # Make sure DrawZoneTool is the actual class, not a mock
        if isinstance(DrawZoneTool, MagicMock):
             print("Warning: DrawZoneTool is a Mock! Manually resolving...")
             # This can happen if some other import mocked it
        
        tool = DrawZoneTool(mock_widget)
        tool.state = self.state
        # Use a larger triangle for vertices
        vertices = [Hex(0, 0, 0), Hex(5, 0, -5), Hex(0, 5, -5)]
        tool.current_polygon = vertices
        
        # Manually set attributes
        tool.combo_type = MagicMock()
        tool.combo_type.currentText.return_value = "Strategic"
        tool.combo_subtype = MagicMock()
        tool.combo_subtype.currentText.return_value = "Goal Area"
        tool.combo_side = MagicMock()
        tool.combo_side.currentText.return_value = "Attacker"
        
        from services.zone_service import add_zone, init as zone_init
        zone_init(self.state)
        
        print(f"Testing via zone_service.add_zone with vertices {vertices}...")
        res = add_zone(vertices, {"type": "Strategic", "subtype": "Goal Area", "side": "Attacker"}, auto_spawn_defenders=True)
        print(f"Service Result: {res}")
        
        # Check if any agents were spawned
        agents = self.state.entity_manager.get_all_entities()
        print(f"Agents spawned: {[a.name for a in agents]}")
        self.assertEqual(len(agents), 4, "Should have spawned 4 goal defenders via service")

    def test_conditional_spawn_without_designated(self):
        print("\n--- Testing Conditional Spawn (WITHOUT Designated Area) ---")
        # Ensure no designated areas exist
        self.state.map.active_scenario._zones = {}
        
        from services.zone_service import add_zone, init as zone_init
        zone_init(self.state)
        
        vertices = [Hex(5, 5, -10), Hex(10, 5, -15), Hex(5, 10, -15)]
        add_zone(vertices, {"type": "Strategic", "subtype": "Goal Area", "side": "Attacker"}, auto_spawn_defenders=True)
        
        agents = self.state.entity_manager.get_all_entities()
        print(f"Agents spawned: {[a.name for a in agents]}")
        self.assertEqual(len(agents), 0, "No agents should have been spawned outside Designated Area")

    def test_targeting_priority_and_command_type(self):
        print("\n--- Testing Targeting Priority and Command Type ---")
        attacker = Agent(name="Attacker")
        attacker.set_attribute("side", "Attacker")
        attacker.set_attribute("personnel", 100)
        attacker.set_attribute("fire_range", 0) # Set to 0 to target exact hex
        self.state.entity_manager.register_entity(attacker)
        self.state.map.place_entity(attacker.id, Hex(0, 0, 0))
        
        # 1. With Goal Area
        goal_hex = Hex(5, 0, -5)
        self.state.map.add_zone("goal_1", {
            "type": "Goal Area",
            "side": "Defender",
            "hexes": [goal_hex]
        })
        
        StrategicCommander.assign_mission(attacker, self.state)
        print(f"Command assigned with Goal: {attacker.current_command.command_type} at {attacker.current_command.target_hex}")
        self.assertEqual(attacker.current_command.command_type, "CAPTURE")
        self.assertEqual(attacker.current_command.target_hex, goal_hex)
        
        # 2. Without Goal Area - Fallback to Defender Home
        self.state.map.remove_zone("goal_1")
        defender = Agent(name="Defender")
        defender.set_attribute("side", "Defender")
        defender.set_attribute("personnel", 100)
        home_hex = Hex(-5, 5, 0)
        defender.set_attribute("home_hex", home_hex)
        self.state.entity_manager.register_entity(defender)
        self.state.map.place_entity(defender.id, Hex(0, 10, -10))
        
        StrategicCommander.assign_mission(attacker, self.state)
        print(f"Command assigned fallback: {attacker.current_command.command_type} at {attacker.current_command.target_hex}")
        self.assertEqual(attacker.current_command.command_type, "MOVE")
        # With fire_range=0, it should be the exact home_hex
        self.assertEqual(attacker.current_command.target_hex, home_hex)

    def test_reward_logic(self):
        print("\n--- Testing Reward Logic ---")
        reward_model = RewardModel()
        attacker = Agent(name="Attacker")
        attacker.set_attribute("side", "Attacker")
        
        # 1. Capture Reward (High bonus)
        from engine.simulation.command import AgentCommand
        attacker.current_command = AgentCommand("CAPTURE", Hex(0, 0, 0))
        
        # Arriving at target (distance 0) and holding (action type "HOLD / END TURN")
        reward = reward_model.calculate_reward(
            attacker, "HOLD / END TURN", command_dist=0, step_number=1, max_steps=50
        )
        print(f"Capture Reward: {reward}")
        # reward_goal_completed = 500
        # In reward.py lines 81-82: reward += decayed_goal_reward * 1.5
        # decayed_goal_reward for step 1, max_steps 50: 500 * (1 - 1/50) = 490
        # 490 * 1.5 = 735
        self.assertGreater(reward, 600) 

        # 2. Defense Reward
        defender = Agent(name="Defender")
        defender.set_attribute("side", "Defender")
        home = Hex(5, 5, -10)
        defender.set_attribute("home_hex", home)
        defender.current_command = AgentCommand("DEFEND", home, objective_type="HOLD_POST")
        
        # Reward for being on post
        reward = reward_model.calculate_reward(
            defender, "HOLD / END TURN", command_dist=0
        )
        print(f"Defense Reward (on post): {reward}")
        # reward.py line 92: reward += 50.0
        self.assertEqual(reward, 50.0)

    def test_goal_area_1_hex_sequential_naming(self):
        """Verify that Goal Areas are 1-hex and named sequentially via service."""
        from services.zone_service import add_zone, init as zone_init
        zone_init(self.state)
        
        # 1. Add first Goal Area (1 hex)
        click_hex = Hex(2, 2, -4)
        res = add_zone([click_hex], {"subtype": "Goal Area", "side": "Defender"})
        
        self.assertTrue(res.ok)
        self.assertEqual(res.data["name"], "Goal Area 1")
        
        # Check map state
        zones = self.state.map.get_zones()
        zone_id = res.data["zone_id"]
        self.assertEqual(zones[zone_id]["color"], "#FFD700") # Gold
        
        # 2. Add second Goal Area
        click_hex2 = Hex(3, 3, -6)
        res2 = add_zone([click_hex2], {"subtype": "Goal Area", "side": "Defender"})
        
        self.assertTrue(res2.ok)
        self.assertEqual(res2.data["name"], "Goal Area 2")

if __name__ == "__main__":
    unittest.main()
