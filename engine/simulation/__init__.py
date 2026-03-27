"""
FILE:    engine/simulation/__init__.py
LAYER:   Backend
ROLE:    Turn execution — the sense-decide-act loop for all units.

PACKAGES:
    act_model.py           — Main simulation controller (coordinates all actions)
    base_action.py         — Abstract base class for all action types
    move.py                — MoveAction: moves a unit to an adjacent hex
    fire.py                — FireAction: direct fire engagement
    close_combat.py        — CloseCombatAction: melee/assault engagement
    commit.py              — CommitAction: role commitment (suppress, support, etc.)
    command.py             — AgentCommand data class (the unit's current mission)
    simulation_controller.py — Qt-aware wrapper (timer, signals) for the desktop UI
    simulation_engine.py   — Headless tick engine (no Qt dependency)

DEPENDENCY RULE:
    May import from engine.core, engine.models, engine.ai, engine.combat.
    Must NOT import from services/, ui/, web_ui/, or PyQt5.
    EXCEPTION: simulation_controller.py may import PyQt5 (it is the Qt shim).
"""
