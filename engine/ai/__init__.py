"""
FILE:    engine/ai/__init__.py
LAYER:   Backend
ROLE:    Reinforcement learning algorithms and AI decision-making.

PACKAGES:
    encoder.py       — Converts game state to feature vectors for the Q-table
    q_table.py       — Q-table storage, lookup, and batch update
    replay_buffer.py — Experience replay circular buffer
    reward.py        — Reward shaping model (all rewards defined here)
    commander.py     — Strategic mission assignment (non-RL heuristic)
    commander_rl.py  — Reinforcement-learning commander policy

DEPENDENCY RULE:
    May import from engine.core and engine.models.
    Must NOT import from services/, ui/, ui/, or PyQt5.
"""
