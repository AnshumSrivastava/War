"""
FILE:    engine/state/__init__.py
LAYER:   Backend
ROLE:    Runtime state containers for the simulation.

PACKAGES:
    world_state.py   — WorldState dataclass (primary, replaces GlobalState singleton)
    global_state.py  — GlobalState singleton (legacy compat shim, do not add new features)
    threat_map.py    — Derived danger-zone overlay per faction
    ui_settings.py   — DEPRECATED: moved to ui/styles/ui_state.py

DEPENDENCY RULE:
    May import from engine.core and engine.models.
    Must NOT import from services/, ui/, ui/, or PyQt5.
"""
