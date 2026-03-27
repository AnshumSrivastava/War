"""
FILE: engine/ai/commander_rl.py
ROLE: The Reinforcement Learning Brain for Strategic Decision Making.

DESCRIPTION:
This agent controls the Commander's macroscopic decisions (e.g., Choosing 
which Axis of Movement to take). 
It has been upgraded to support trajectory-based learning and discount factors.
"""
import random
import os
import json
import numpy as np

class CommanderRLAgent:
    def __init__(self, q_table_path="data/models/commander_q_table.json"):
        self.q_table_path = q_table_path
        self.learning_rate = 0.1
        self.discount_factor = 0.95 # Higher discount for long-term strategic goals
        self.epsilon = 0.2
        
        # State: (Threat_Level_0_to_3, Distance_0_to_2)
        # Actions: 0 (Direct), 1 (Safe), 2 (Fast)
        self.num_states = 12
        self.num_actions = 3
        
        self.q_table = [[0.0 for _ in range(self.num_actions)] for _ in range(self.num_states)]
        self.load_model(q_table_path)
        
    def load_model(self, path=None):
        target_path = path or self.q_table_path
        if os.path.exists(target_path):
            try:
                with open(target_path, "r") as f:
                    self.q_table = json.load(f)
                self.q_table_path = target_path
            except Exception as e:
                print(f"CommanderRL: Error loading model from {target_path} - {e}")
                
    def save_model(self):
        os.makedirs(os.path.dirname(self.q_table_path), exist_ok=True)
        try:
            with open(self.q_table_path, "w") as f:
                json.dump(self.q_table, f)
        except Exception as e:
            pass
        
    def _discretize_state(self, avg_threat: float, distance_to_target: int) -> int:
        threat_bucket = 0
        if avg_threat > 0.1: threat_bucket = 1
        if avg_threat > 0.5: threat_bucket = 2
        if avg_threat > 1.0: threat_bucket = 3
        
        dist_bucket = 0
        if distance_to_target > 5: dist_bucket = 1
        if distance_to_target > 10: dist_bucket = 2
        
        return (threat_bucket * 3) + dist_bucket

    def select_axis(self, paths_stats: dict, is_training: bool = True) -> (int, int):
        """Returns (action_idx, state_idx)."""
        base_threat = paths_stats.get(0, {}).get("avg_threat", 0.0)
        base_dist = paths_stats.get(0, {}).get("length", 1)
        
        state_idx = self._discretize_state(base_threat, base_dist)
        
        if is_training and random.uniform(0, 1) < self.epsilon:
            action = random.randint(0, self.num_actions - 1)
        else:
            action = max(enumerate(self.q_table[state_idx]), key=lambda x: x[1])[0]
            
        return action, state_idx

    def update(self, state_idx: int, action: int, reward: float):
        """Standard single-step update."""
        old_value = self.q_table[state_idx][action]
        # Contextual bandit update (no s')
        self.q_table[state_idx][action] = old_value + self.learning_rate * (reward - old_value)

    def learn_from_trajectory(self, trajectory: list, total_reward: float):
        """
        LEARN: Updates the brain using a trajectory of decisions and a final outcome.
        Uses a discounted reward across the steps.
        trajectory: list of (state_idx, action_idx)
        """
        if not trajectory:
            return
            
        # We propagate the final total_reward back through the trajectory
        # with discounting. This helps the AI connect early decisions to late outcomes.
        G = total_reward
        for state_idx, action_idx in reversed(trajectory):
            old_q = self.q_table[state_idx][action_idx]
            self.q_table[state_idx][action_idx] = old_q + self.learning_rate * (G - old_q)
            G = G * self.discount_factor # Discount for the previous step
