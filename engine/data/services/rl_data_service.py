"""
FILE: data/services/rl_data_service.py
ROLE: The "Math Tutor" (RLDataService).

DESCRIPTION:
This service is the expert in Reinforcement Learning (RL) data. While the 
databases just store numbers, this file knows what those numbers MEAN.

It handles the 'Brain' data (Q-Values) and provides the mathematical functions 
needed for the AI to make decisions, such as:
1. "What is the best possible score I can get in this situation?"
2. "Which action should I take to get the most points?"
3. "Dump the whole brain into a format that can be saved to a file."
"""

from typing import Dict, List, Any
import numpy as np
from engine.data.api.base_db import BaseDB

class RLDataService:
    """
    A specialized service for managing AI learning data.
    """
    def __init__(self, db: BaseDB):
        # We give the service a database (like Memory or JSON) to store its numbers in.
        self.db = db
        # Initial setup: check if we've ever run before.
        if not self.db.exists("q_table_initialized"):
            self.db.set("q_table_initialized", True)

    def _get_q_key(self, state: int, action: int) -> str:
        """INTERNAL: Generates a unique label for a specific situation and action."""
        return f"q_val:{state}:{action}"

    def get_q_value(self, state: Any, action: int) -> float:
        """
        READ: Finds the 'Score' for a specific action in a specific situation.
        Supports both single index states and list of features (Tile Coding).
        """
        if isinstance(state, (list, tuple)):
            # TILE CODING: Q(s,a) is the sum of weights for all active tiles.
            total = 0.0
            for tile in state:
                val = self.db.get(self._get_q_key(tile, action))
                total += float(val) if val is not None else 0.0
            return total / len(state) if state else 0.0
            
        val = self.db.get(self._get_q_key(state, action))
        return float(val) if val is not None else 0.0

    def set_q_value(self, state: Any, action: int, value: float) -> bool:
        """
        WRITE: Updates the 'Score' after the AI learns something new.
        If state is a list, updates all active tiles (Linear Function Approximation update).
        """
        if isinstance(state, (list, tuple)):
            # Each tile gets a fraction of the update
            num_tiles = len(state)
            if num_tiles == 0: return False
            
            # NOTE: The 'value' passed here is usually the TARGET or the NEW_Q.
            # However, for linear approximation, we usually update weights 
            # by (target - Q) * alpha / n_tiles.
            # To keep RLDataService generic, if a list is passed, we assume 
            # the caller wants to set the MEAN weight to this value? No.
            
            # Better: The caller (QTableManager) should handle the math and 
            # call set_q_value for each tile individually if they want precise control.
            # But for batch and other services, we can distribute it.
            # Actually, let's keep it simple: if you pass a list, you are setting 
            # the value for EACH tile (not recommended, use get_q_value and individual sets).
            for tile in state:
                self.db.set(self._get_q_key(tile, action), value)
            return True
            
        return self.db.set(self._get_q_key(state, action), value)

    def get_max_q_value(self, state: Any, available_actions: List[int]) -> float:
        """
        LOOK AHEAD: Finds the HIGHEST possible score available in a given situation.
        This is used to help the AI realize: "If I move here, what's the best I can do next?"
        """
        if not available_actions:
            return 0.0
            
        max_val = float('-inf')
        for action in available_actions:
            val = self.get_q_value(state, action)
            if val > max_val:
                max_val = val
                
        return max_val if max_val != float('-inf') else 0.0

    def get_best_action(self, state: Any, available_actions: List[int]) -> int:
        """
        DECIDE: Picks the action with the absolute highest score.
        This is the command used when the unit is 'playing for real' (Exploitation).
        """
        if not available_actions:
            raise ValueError("Cannot select action from empty list.")
            
        max_val = float('-inf')
        candidates = []
        
        for action in available_actions:
            val = self.get_q_value(state, action)
            if val > max_val:
                max_val = val
                candidates = [action]
            elif val == max_val:
                candidates.append(action)
                
        if not candidates:
             return available_actions[0]
             
        import random
        return random.choice(candidates)

    def get_all_q_values(self, state: Any, available_actions: List[int]) -> Dict[int, float]:
        """
        UI DISPLAY: Returns a list of all scores so the human user can see what the AI is 'thinking'.
        Supports both single index states and list of features (Tile Coding).
        """
        return {action: self.get_q_value(state, action) for action in available_actions}

    def update_q_value_batch(self, batch, alpha, gamma, action_size):
        """
        BATCH UPDATE: Applies updates for multiple transitions at once.
        Supports Tile Coding if 'state' and 'next_state' are lists.
        """
        for state, action, reward, next_state, done in batch:
            q_s_a = self.get_q_value(state, action)
            
            if done:
                next_max = 0.0
            else:
                next_max = self.get_max_q_value(next_state, list(range(action_size)))
            
            # Target = r + gamma * max Q(s', a')
            target = reward + gamma * next_max
            
            # Error = Target - Q(s, a)
            error = target - q_s_a
            
            if isinstance(state, (list, tuple)):
                # Update each weight (tile)
                num_tiles = len(state)
                delta = alpha * error / num_tiles
                for tile in state:
                    old_w = self.get_q_value(tile, action) # Get individual tile weight
                    self.set_q_value(tile, action, old_w + delta)
            else:
                # Standard Tabular update
                new_value = q_s_a + alpha * error
                self.set_q_value(state, action, new_value)

    def dump_active_table(self, state_size: int, action_size: int) -> np.ndarray:
        """
        EXPORT: Converts the entire brain database into a giant grid of numbers (a Numpy Table).
        This is perfect for saving the brain to a file.
        """
        table = np.zeros((state_size, action_size))
        
        for s in range(state_size):
            for a in range(action_size):
                table[s, a] = self.get_q_value(s, a)
                
        return table

    def load_active_table(self, table: np.ndarray) -> None:
        """
        IMPORT: Takes a grid of numbers from a file and pours it into the active database memory.
        """
        rows, cols = table.shape
        for s in range(rows):
            for a in range(cols):
                val = table[s, a]
                if val != 0.0:  # Small optimization: we only bother saving non-zero scores.
                    self.set_q_value(s, a, float(val))
