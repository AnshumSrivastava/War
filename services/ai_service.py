"""
FILE:    services/ai_service.py
LAYER:   Middle-End
ROLE:    AI brain inspection and control — epsilon, Q-values, brain mode.

DESCRIPTION:
    The UI uses this service to read AI state for the inspector panel
    (Q-values, epsilon, mode) and to switch brains or adjust learning params.
    The UI never imports engine.ai directly.

DOES NOT IMPORT FROM:
    - ui/ or ui/
    - PyQt5 / Flask
"""

from typing import Optional
from services.service_result import ServiceResult, ok, err

_state = None


def init(state) -> None:
    """Inject WorldState. Call once at startup."""
    global _state
    _state = state


def _require_state() -> Optional[ServiceResult]:
    if _state is None:
        return err("AI service not initialized.", code="NOT_INITIALIZED")
    return None


def _get_model():
    """Get the ActionModel from simulation_service (shared instance)."""
    from services import simulation_service
    return simulation_service._get_model()


def get_epsilon() -> ServiceResult:
    """Return the current epsilon (exploration rate) of the active Q-table."""
    guard = _require_state()
    if guard: return guard
    try:
        eps = _get_model().q_manager_ephemeral.epsilon
        return ok({"epsilon": eps})
    except Exception as e:
        return err(f"Could not read epsilon: {e}")


def set_epsilon(value: float) -> ServiceResult:
    """
    Manually set the exploration rate.

    Args:
        value: Epsilon value between 0.0 (no exploration) and 1.0 (pure exploration).
    """
    guard = _require_state()
    if guard: return guard
    try:
        value = max(0.0, min(1.0, value))
        _get_model().q_manager_ephemeral.epsilon = value
        return ok({"epsilon": value})
    except Exception as e:
        return err(f"Could not set epsilon: {e}")


def get_agent_brain_info(agent_name: str) -> ServiceResult:
    """
    Return the last recorded AI debug info for a specific agent.

    Returns:
        ServiceResult with data=dict containing state, q_values, action, reward, etc.
    """
    guard = _require_state()
    if guard: return guard
    try:
        info = _get_model().agent_debug_info.get(agent_name)
        if info is None:
            return err(f"No brain info available for '{agent_name}'.", code="NOT_FOUND")
        return ok(info)
    except Exception as e:
        return err(f"Could not get brain info for '{agent_name}': {e}")


def get_all_brain_info() -> ServiceResult:
    """Return brain info for all agents (for the dashboard view)."""
    guard = _require_state()
    if guard: return guard
    try:
        info = _get_model().agent_debug_info
        return ok(info or {})
    except Exception as e:
        return err(f"Could not get brain info: {e}")
