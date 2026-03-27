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
sys.modules["PyQt5.QtWebEngine"] = mock_qt
sys.modules["PyQt5.QtWebEngineWidgets"] = mock_qt

# Add paths to make imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.state.global_state import GlobalState
from engine.simulation.act_model import ActionModel
from engine.core.entity_manager import Agent
from engine.core.hex_math import Hex
from engine.simulation.command import AgentCommand

class TestCommanderFix(unittest.TestCase):
    def setUp(self):
        # Reset GlobalState singleton for clean test
        GlobalState._instance = None
        self.state = GlobalState()
        self.state.entity_manager.clear()
        
        # Setup a small 10x10 map
        self.state.map.width = 10
        self.state.map.height = 10
        # Clear terrain to default plain
        self.state.map._terrain = {}
        
        self.model = ActionModel(self.state)

    def test_command_persistence(self):
        # 1. Setup Agent
        agent = Agent(agent_id="UNIT_TEST", name="Test Agent")
        agent.set_attribute("side", "Attacker")
        agent.set_attribute("personnel", 100)
        agent.set_attribute("fire_range", 3)
        agent.set_attribute("vision_range", 5)
        
        self.state.entity_manager.register_entity(agent)
        start_hex = Hex(0, 0, 0)
        self.state.map.place_entity(agent.id, start_hex)
        
        # Add an enemy so the commander has something to target
        enemy = Agent(agent_id="ENEMY", name="Enemy Agent")
        enemy.set_attribute("side", "Defender")
        enemy.set_attribute("personnel", 100)
        self.state.entity_manager.register_entity(enemy)
        self.state.map.place_entity(enemy.id, Hex(5, 0, -5)) # 5 steps away
        
        # 2. Initial mission assignment (happens on first step)
        self.model.step_all_agents(step_number=1)
        
        original_command = agent.current_command
        self.assertIsNotNone(original_command, "Agent should have been assigned a command")
        self.assertFalse(original_command.is_user_assigned, "Command should be commander-assigned")
        
        original_target = original_command.target_hex
        print(f"Original Target: {original_target}")
        
        # 3. Run multiple steps and verify target hex doesn't change
        # We ensure the agent doesn't "arrive" by NOT moving it yet.
        # ActionModel might move it if RL picks MOVE, but with tokens=2 it takes time.
        
        for i in range(2, 10):
            self.model.step_all_agents(step_number=i)
            # The command object should be EXACTLY the same instance.
            # If it's a different instance, it means assign_mission was called.
            self.assertIs(agent.current_command, original_command, f"Command was re-assigned at step {i}")
            self.assertEqual(agent.current_command.target_hex, original_target)

        # 4. Move agent to target and verify it DOES re-assign
        self.state.map.place_entity(agent.id, original_target)
        self.model.step_all_agents(step_number=10)
        
        # Now it should have a NEW command (or at least the flag set)
        # arriving at target hex (distance 0) triggers the refresher.
        self.assertTrue(getattr(agent, 'mission_refreshed', False), "Mission should have been refreshed after arriving")

if __name__ == "__main__":
    unittest.main()
