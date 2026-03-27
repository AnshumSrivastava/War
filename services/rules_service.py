"""
FILE:    services/rules_service.py
LAYER:   Middle-End
ROLE:    Game rule validation and terminal condition checks.

DESCRIPTION:
    All game rules live here and ONLY here. This service answers questions like:
    - Can this unit move to that hex?
    - Is the scenario over (win/loss/draw)?
    - What is the current score?

    The simulation calls check_terminal_conditions() every tick.
    The UI can call it to display a victory banner.

    Events emitted:
    - "game_over" payload: {"result": "attacker_wins"|"defender_wins"|"draw",
                            "reason": str}

DOES NOT IMPORT FROM:
    - ui/ or web_ui/
    - PyQt5 / Flask
"""

from typing import Optional
from services.service_result import ServiceResult, ok, err
from services import event_bus
from engine.models.constants import SIDE_ATTACKER, SIDE_DEFENDER, ATTR_PERSONNEL
from engine.api import DomainAPI

_state = None
_api = None
_game_over = False   # Set to True once a terminal condition fires


def init(state) -> None:
    """Inject WorldState. Call once at startup."""
    global _state, _game_over, _api
    _state = state
    _api = DomainAPI(state)
    _game_over = False


def _require_state() -> Optional[ServiceResult]:
    if _state is None:
        return err("Rules service not initialized.", code="NOT_INITIALIZED")
    return None


def reset() -> None:
    """Reset game-over state for a new episode."""
    global _game_over
    _game_over = False


# =============================================================================
# TERMINAL CONDITIONS
# =============================================================================

def check_terminal_conditions(step_number: int, max_steps: int) -> ServiceResult:
    """
    Check whether the scenario has reached a terminal state.

    Conditions checked (in priority order):
    1. All attacker units destroyed  → Defender wins.
    2. All defender units destroyed  → Attacker wins.
    3. An attacker occupies a goal zone → Attacker wins.
    4. Step limit reached with no winner → Draw.

    Args:
        step_number: Current step within the episode.
        max_steps:   Maximum steps per episode.

    Returns:
        ServiceResult with data=None if ongoing,
        or data={"result": str, "reason": str} if terminal.
    """
    global _game_over
    guard = _require_state()
    if guard: return guard
    if _game_over:
        return ok(None)   # Already fired once — don't spam events

    try:
        entities = _api.entities.get_all_entities()
        attackers = [e for e in entities
                     if e.get_attribute(ATTR_PERSONNEL, 0) > 0
                     and e.get_attribute("side") == SIDE_ATTACKER]
        defenders = [e for e in entities
                     if e.get_attribute(ATTR_PERSONNEL, 0) > 0
                     and e.get_attribute("side") == SIDE_DEFENDER]

        result = None
        reason = ""

        if not attackers and defenders:
            result, reason = "defender_wins", "All attackers eliminated."
        elif not defenders and attackers:
            result, reason = "attacker_wins", "All defenders eliminated."
        elif _attacker_in_goal_zone():
            result, reason = "attacker_wins", "Attacker controls objective zone."
        elif step_number >= max_steps:
            result, reason = "draw", f"Step limit ({max_steps}) reached."

        if result:
            _game_over = True
            payload = {"result": result, "reason": reason, "step": step_number}
            event_bus.emit("game_over", payload)
            return ok(payload)

        return ok(None)   # Still ongoing
    except Exception as e:
        return err(f"Terminal condition check failed: {e}")


def _attacker_in_goal_zone() -> bool:
    """Return True if any attacker unit occupies a hex inside a Goal Area zone."""
    try:
        zones = _state.map.get_zones()
        for zone_id, zone_data in zones.items():
            if zone_data.get("type") == "Goal Area":
                goal_hexes = [tuple(h) for h in zone_data.get("hexes", [])]
                for entity in _api.entities.get_all_entities():
                    if entity.get_attribute("side") != SIDE_ATTACKER:
                        continue
                    if int(entity.get_attribute(ATTR_PERSONNEL, 0)) <= 0:
                        continue
                    pos = _state.map.get_entity_position(entity.id)
                    if pos and tuple(pos) in goal_hexes:
                        return True
    except Exception:
        pass
    return False


# =============================================================================
# MOVE VALIDATION
# =============================================================================

def can_move(entity_id: str, q: int, r: int) -> ServiceResult:
    """
    Check whether an entity is allowed to move to a given hex.

    Args:
        entity_id: ID of the entity wanting to move.
        q:         Target hex axial column.
        r:         Target hex axial row.

    Returns:
        ServiceResult with data={"allowed": bool, "reason": str}
    """
    guard = _require_state()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)
        terrain = _state.map.get_terrain(hex_coord)
        if terrain is None:
            return ok({"allowed": False, "reason": "No terrain at destination."})
        cost = terrain.get("cost", 1.0)
        if cost >= 99.0:
            return ok({"allowed": False, "reason": "Terrain is impassable."})
        return ok({"allowed": True, "reason": ""})
    except Exception as e:
        return err(f"Move validation failed: {e}")
