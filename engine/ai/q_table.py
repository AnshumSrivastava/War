"""
FILE: engine/ai/q_table.py
ROLE: The "Long-Term Memory" of the AI.

DESCRIPTION:
This file manages the 'Q-Table'. Think of a Q-Table as a giant spreadsheet where 
the AI stores everything it has learned.
- The ROWS of the spreadsheet are the 'Situations' (States) the unit can be in.
- The COLUMNS are the 'Actions' (Move, Shoot, Wait) the unit can take.
- Each CELL contains a 'Score' (Q-Value) representing how good that action is 
  for that situation.

This file handles updating those scores based on rewards and saving the entire 
spreadsheet to a file so the AI 'remembers' its training even after the game is closed.
"""
import numpy as np
import os
import json
from engine.data.api.memory_db import MemoryDatabase
from engine.data.services.rl_data_service import RLDataService

class QTableManager:
    """
    The "Brain Storage" Manager. It handles reading from and writing to the 
    AI's long-term memory spreadsheet.
    """
    def __init__(self, state_size=2160, action_size=7, alpha=0.1, gamma=0.99, epsilon=0.1):
        self.state_size = state_size
        self.action_size = action_size
        
        # Internal tools for talking to the database.
        # This version uses MemoryDatabase directly without Redis integration.
        self.db = MemoryDatabase()
        print("Using MemoryDatabase for RL Memory.")
            
        self.service = RLDataService(self.db)
        
        # --- THE LEARNING RULES (Hyperparameters) ---
        self.alpha = alpha    # LEARNING RATE: 0 = learn nothing, 1 = learn instantly. 
        self.gamma = gamma   # PATIENCE: 0 = only care about now, 1 = care about the future.
        self.epsilon = epsilon  # CURIOSITY: 0 = never explore, 1 = always try random things.

    def update_q_value(self, state, action, reward, next_state, next_state_available_actions=None):
        """
        THE LEARNING MOMENT: This is where the AI actually gets smarter.
        It uses a math formula called the 'Bellman Equation'.
        """
        if next_state_available_actions is None:
            next_state_available_actions = list(range(self.action_size))

        # 1. Look up what we currently think about this action.
        old_value = self.service.get_q_value(state, action)
        
        # 2. Look ahead: If we take this action, what is the best possible 
        # thing we could do in the NEXT turn?
        next_max = self.service.get_max_q_value(next_state, next_state_available_actions)
        
        # 3. THE FORMULA: 
        # New Score = (Old Score) + (Learning Rate) * [Reward + (Future Value) - (Old Score)]
        new_value = (1 - self.alpha) * old_value + \
                    self.alpha * (reward + self.gamma * next_max)
        
        # 4. MEMORIZE: Save the new, smarter score back into the spreadsheet.
        self.service.set_q_value(state, action, new_value)

    def update_batch(self, batch):
        """
        BATCH LEARNING: Updates the Q-table using a batch of experiences.
        This is more stable than single-step updates.
        """
        self.service.update_q_value_batch(batch, self.alpha, self.gamma, self.action_size)

    def get_action(self, state, available_actions_indices):
        """WISDOM: Look at the spreadsheet and pick the action with the HIGHEST score."""
        return self.service.get_best_action(state, available_actions_indices)

    def get_q_values(self, state, available_actions_indices):
        """THINKING: Returns the scores for EVERYTHING the AI is considering."""
        return self.service.get_all_q_values(state, available_actions_indices)

    def save_q_table(self, filename="data/training/q_table.npy"):
        """PERSISTENCE: Saves the AI's training to a file on the hard drive."""
        table = self.service.dump_active_table(self.state_size, self.action_size)
        
        # Save as a fast computer-readable file (.npy).
        try:
            np.save(filename, table)
        except Exception as e:
            print(f"Error saving Q-Table Binary: {e}")
            
        # Save as a human-readable text file (.json) for debugging.
        try:
            json_file = filename.replace(".npy", ".json")
            sparse_data = {}
            for s in range(self.state_size):
                state_data = {}
                for a in range(self.action_size):
                    val = table[s, a]
                    if val != 0.0: # To save space, we only save actions that have a score.
                        state_data[str(a)] = float(val)
                if state_data:
                    sparse_data[str(s)] = state_data
            
            with open(json_file, 'w') as f:
                json.dump(sparse_data, f, indent=4)
        except Exception as e:
            print(f"Error saving Q-Table JSON: {e}")

    def load_q_table(self, filename="data/training/q_table.npy"):
        """RECALL: Loads a previously saved brain into memory."""
        # 1. Try to load the fast computer file first.
        if os.path.exists(filename):
            try:
                table = np.load(filename)
                self.service.load_active_table(table)
                return
            except Exception as e:
                print(f"Failed to load binary Q-Table: {e}")
            
        # 2. If that fails, try the human-readable text file.
        json_file = filename.replace(".npy", ".json")
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    sparse_data = json.load(f)
                
                table = np.zeros((self.state_size, self.action_size))
                for s_str, actions in sparse_data.items():
                    s = int(s_str)
                    for a_str, val in actions.items():
                        a = int(a_str)
                        if s < self.state_size and a < self.action_size:
                            table[s, a] = val
                
                self.service.load_active_table(table)
            except Exception as e:
                print(f"Error loading Q-Table JSON: {e}")