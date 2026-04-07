"""
FILE:    engine/data/__init__.py
LAYER:   Backend
ROLE:    File I/O — reading and writing all game data files.

PACKAGES:
    content_path.py  — Single resolver for the content/ root directory (start here)
    loaders/         — DataManager and individual JSON loaders
    definitions/     — Hardcoded game constants (RL_ACTION_MAP, etc.)
    api/             — External data API adapters (if any)
    redis/           — Redis integration (if any)

DEPENDENCY RULE:
    May import from engine.models (for TypedDicts).
    Must NOT import from engine.state, engine.simulation, engine.ai.
    Must NOT import from services/, ui/, ui/, or PyQt5.
"""
