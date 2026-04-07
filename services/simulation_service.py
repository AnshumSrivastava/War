"""
FILE:    services/simulation_service.py
LAYER:   Middle-End
ROLE:    Headless simulation runner — no PyQt dependency.

DESCRIPTION:
    Runs simulation ticks and training episodes through the engine.
    The UI attaches progress callbacks or subscribes to events —
    it does NOT call engine methods directly.

    Events emitted:
    - "tick_complete"     payload: {"step": int, "events": list, "logs": list}
    - "episode_complete"  payload: {"episode": int, "epsilon": float}
    - "simulation_reset"  payload: None
    - "learning_started"  payload: {"episodes": int}
    - "learning_complete" payload: {"episodes": int}

DOES NOT IMPORT FROM:
    - ui/ or ui/
    - PyQt5 / Flask
"""

from typing import Optional, Callable
from services.service_result import ServiceResult, ok, err
from services import event_bus
from engine.api import DomainAPI

_state      = None
_api        = None
_action_model = None   # Lazy-initialized on first use


def init(state) -> None:
    """Inject WorldState. Call once at startup."""
    global _state, _action_model, _api
    _state = state
    _api = DomainAPI(state)
    _action_model = None   # Will be built on first step() call


def _require_api() -> Optional[ServiceResult]:
    if _api is None:
        return err("Simulation service not initialized.", code="NOT_INITIALIZED")
    return None


def _get_model():
    """Lazy-initialize ActionModel so we don't pay startup cost if not needed."""
    global _action_model
    if _action_model is None:
        from engine.simulation.act_model import ActionModel
        _action_model = ActionModel(_state)
    return _action_model


# =============================================================================
# SIMULATION CONTROL
# =============================================================================

def step(step_number: int = 1, episode_number: int = 1,
         max_steps: int = 50) -> ServiceResult:
    """
    Execute one simulation tick for all agents.

    Args:
        step_number:    Current step index within the episode.
        episode_number: Current episode index.
        max_steps:      Total steps per episode (used for terminal-condition checks).

    Returns:
        ServiceResult with data={"events": list, "logs": list}
    """
    guard = _require_api()
    if guard: return guard
    try:
        model = _get_model()
        events, logs = model.step_all_agents(
            step_number=step_number,
            table_mode=True,
            episode_number=episode_number,
            max_steps=max_steps
        )
        payload = {"step": step_number, "events": events, "logs": logs}
        event_bus.emit("tick_complete", payload)
        return ok(payload)
    except Exception as e:
        return err(f"Simulation step failed: {e}")


def reset() -> ServiceResult:
    """Reset the simulation for a new episode."""
    guard = _require_api()
    if guard: return guard
    try:
        model = _get_model()
        model.reset_episode()
        event_bus.emit("simulation_reset", None)
        return ok(None)
    except Exception as e:
        return err(f"Simulation reset failed: {e}")


def run_episodes(episodes: int, max_steps: int = 50,
                 progress_callback: Optional[Callable] = None) -> ServiceResult:
    """
    Run multiple training episodes in the current thread.

    The UI should call this from a background thread or connect a
    progress_callback to update a progress bar without blocking.

    Args:
        episodes:          Number of episodes to run.
        max_steps:         Steps per episode.
        progress_callback: Optional fn(episode, total_episodes, epsilon) for progress.

    Returns:
        ServiceResult with data={"episodes_run": int} on completion.
    """
    guard = _require_api()
    if guard: return guard
    try:
        model = _get_model()
        _state.is_learning = True
        event_bus.emit("learning_started", {"episodes": episodes})

        for ep in range(1, episodes + 1):
            if not getattr(_state, "is_learning", True):
                break
            model.reset_episode()
            for step_num in range(1, max_steps + 1):
                if not getattr(_state, "is_learning", True):
                    break
                model.step_all_agents(
                    step_number=step_num,
                    table_mode=False,
                    episode_number=ep,
                    max_steps=max_steps
                )
            epsilon = model.q_manager_ephemeral.epsilon
            event_bus.emit("episode_complete", {"episode": ep, "epsilon": epsilon})
            if progress_callback:
                progress_callback(ep, episodes, epsilon)

        _state.is_learning = False
        model.save_knowledge()
        event_bus.emit("learning_complete", {"episodes": episodes})
        return ok({"episodes_run": episodes})
    except Exception as e:
        _state.is_learning = False
        return err(f"Learning run failed at episode: {e}")
def check_terminal_conditions(step: int, max_steps: int) -> ServiceResult:
    """
    Check if the current episode is done.
    
    Returns:
        ServiceResult with data={"done": bool, "reason": str}
    """
    guard = _require_api()
    if guard: return guard
    try:
        # 1. TIMEOUT
        if step > max_steps:
             return ok({"done": True, "reason": "MAX_STEPS_REACHED"})
             
        # 2. ELIMINATION
        sides = {}
        for entity in _api.entities.get_all_entities():
            side = entity.get_attribute("side", "Neutral")
            personnel = int(entity.get_attribute("personnel", 0))
            if personnel > 0:
                sides[side] = sides.get(side, 0) + 1
        
        combatant_sides = [s for s in sides if s != "Neutral"]
        if len(combatant_sides) <= 1:
            winner = combatant_sides[0] if combatant_sides else "None"
            return ok({"done": True, "reason": f"ELIMINATION: {winner} Wins"})
            
        return ok({"done": False, "reason": ""})
    except Exception as e:
        return err(f"Terminal condition check failed: {e}")


def save_knowledge() -> ServiceResult:
    """Persist the AI Q-tables to disk."""
    guard = _require_api()
    if guard: return guard
    try:
        _get_model().save_knowledge()
        return ok(None)
    except Exception as e:
        return err(f"Could not save knowledge: {e}")


def get_agent_debug_info() -> ServiceResult:
    """Return the AI debug info dict for the inspector panel."""
    guard = _require_api()
    if guard: return guard
    try:
        info = _get_model().agent_debug_info
        return ok(info)
    except Exception as e:
        return err(f"Could not get debug info: {e}")


def get_stats() -> ServiceResult:
    """Return simulation action/mode statistics for the dashboard."""
    guard = _require_api()
    if guard: return guard
    try:
        stats = _get_model().stats
        return ok(stats)
    except Exception as e:
        return err(f"Could not get stats: {e}")


def reinit_models() -> ServiceResult:
    """Re-initialize models after a map size change."""
    guard = _require_api()
    if guard: return guard
    try:
        _get_model().reinit_models()
        return ok(None)
    except Exception as e:
        return err(f"Could not reinit models: {e}")


def reset_intelligence() -> ServiceResult:
    """Wipe all learned AI knowledge."""
    guard = _require_api()
    if guard: return guard
    try:
        _get_model().reset_knowledge()
        return ok({"count": 1})
    except Exception as e:
        return err(f"Failed to reset intelligence: {e}")
