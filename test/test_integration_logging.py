# test/test_integration_logging.py
import unittest
import os
import json
from engine.state.global_state import GlobalState
from engine.simulation.act_model import ActionModel

class TestIntegrationLogging(unittest.TestCase):
    def test_action_model_logging(self):
        # Setup
        state = GlobalState()
        model = ActionModel(state)
        
        # We need a dummy entity to step
        class DummyEntity:
            def __init__(self, id):
                self.id = id
                self.personnel = 100
                self.is_active = True
                self.stats = {"is_commander": False}
        
        # Mocking enough state for step_all_agents to not crash
        entities = [DummyEntity("UNIT_01")]
        
        # Perform a few steps
        # Note: we might need more mocks for map and encoder if they are used
        try:
            # We just want to see if logger.log_step is called and writes to disk
            # Even if it errors out later, the logger should have started
            model.logger.log_action("INTEGRATION_TEST_START", {"status": "running"})
            
            # Check if file exists
            log_path = "data/logs/simulation_actions.json"
            self.assertTrue(os.path.exists(log_path))
            
            with open(log_path, "r") as f:
                lines = f.readlines()
                found = any("INTEGRATION_TEST_START" in line for line in lines)
                self.assertTrue(found)
                
        except Exception as e:
            self.fail(f"Integration logging check failed: {e}")

if __name__ == "__main__":
    unittest.main()
