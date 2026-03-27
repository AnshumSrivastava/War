# test/test_logging.py
import unittest
import os
import json
from engine.core.logger import CombatLogger

class TestLogging(unittest.TestCase):
    def test_log_action(self):
        log_file = "test_log.json"
        if os.path.exists(log_file): os.remove(log_file)
        
        logger = CombatLogger(log_path=log_file)
        logger.log_action("TEST_EVENT", {"key": "value"})
        
        self.assertTrue(os.path.exists(log_file))
        
        with open(log_file, "r") as f:
            lines = f.readlines()
            # Line 0: SESSION_START
            # Line 1: TEST_EVENT
            self.assertGreaterEqual(len(lines), 2)
            entry = json.loads(lines[1])
            self.assertEqual(entry["type"], "TEST_EVENT")
            self.assertEqual(entry["data"]["key"], "value")
        
        os.remove(log_file)

if __name__ == "__main__":
    unittest.main()
