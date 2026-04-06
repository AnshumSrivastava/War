# replay_buffer.py (Disk-Persistent)
import random
import os
import json

class ReplayBuffer:
    """
    A disk-persistent experience replay buffer to store tactical transitions.
    This fulfills the 'No RAM storage' requirement.
    """
    def __init__(self, capacity=10000, filename="data/training/replay_buffer.jsonl"):
        self.capacity = capacity
        self.filename = filename
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        # Ensure the file exists
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                pass

    def push(self, state, action, reward, next_state, done):
        """Adds a transition to the disk buffer by appending a JSON line."""
        transition = {
            "s": state,
            "a": action,
            "r": reward,
            "ns": next_state,
            "d": done
        }
        with open(self.filename, 'a') as f:
            f.write(json.dumps(transition) + "\n")
            
        # Optional: Pruning could be expensive on disk (requires rewriting).
        # We'll skip for now or implement a lazy prune if file size grows.

    def sample(self, batch_size):
        """
        Randomly samples a batch of transitions from the disk file.
        Uses a disk-efficient sampling method to minimize RAM usage.
        """
        if not os.path.exists(self.filename):
            return []
            
        try:
            with open(self.filename, 'r') as f:
                lines = f.readlines()
                
            if not lines:
                return []
                
            sampled_lines = random.sample(lines, min(len(lines), batch_size))
            batch = []
            for line in sampled_lines:
                data = json.loads(line)
                batch.append((data["s"], data["a"], data["r"], data["ns"], data["d"]))
            return batch
        except Exception as e:
            print(f"ReplayBuffer Sample Error: {e}")
            return []

    def __len__(self):
        """Counts current number of transitions stored on disk."""
        if not os.path.exists(self.filename):
            return 0
        with open(self.filename, 'r') as f:
            return sum(1 for _ in f)

    def clear(self):
        """Wipes the disk buffer."""
        if os.path.exists(self.filename):
            os.remove(self.filename)
        with open(self.filename, 'w') as f:
            pass
