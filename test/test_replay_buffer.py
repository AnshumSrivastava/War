# test/test_replay_buffer.py
import unittest
from engine.ai.replay_buffer import ReplayBuffer

class TestReplayBuffer(unittest.TestCase):
    def test_push_and_sample(self):
        buffer = ReplayBuffer(capacity=10)
        for i in range(5):
            buffer.push(i, i, i, i+1, False)
        
        self.assertEqual(len(buffer), 5)
        
        batch = buffer.sample(3)
        self.assertEqual(len(batch), 3)
        for item in batch:
            self.assertEqual(len(item), 5) # (s, a, r, ns, d)

    def test_capacity(self):
        buffer = ReplayBuffer(capacity=5)
        for i in range(10):
            buffer.push(i, i, i, i+1, False)
        
        self.assertEqual(len(buffer), 5)
        # Check that it kept the LATEST 5
        self.assertEqual(buffer.buffer[0][0], 5)

if __name__ == "__main__":
    unittest.main()
