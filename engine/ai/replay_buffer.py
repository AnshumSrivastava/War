# replay_buffer.py
import random
from collections import deque

class ReplayBuffer:
    """
    A simple experience replay buffer to store tactical transitions.
    This helps stabilize learning by breaking the correlation between sequential steps.
    """
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """Adds a transition to the buffer."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """Randomly samples a batch of transitions."""
        return random.sample(self.buffer, min(len(self.buffer), batch_size))

    def __len__(self):
        return len(self.buffer)
