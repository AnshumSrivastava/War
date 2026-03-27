"""
FILE:    ui/utils/fallback.py
LAYER:   Frontend
ROLE:    Stub data for UI debug mode and graceful degradation.

DESCRIPTION:
    When the backend is unavailable or a service call returns an error,
    UI widgets use this module to show safe placeholder values instead
    of crashing with an exception.

    This enables:
    1. UI developers to work without a running engine.
    2. Graceful handling of missing data — shows "—" instead of crashing.
    3. Clear visual signals to the developer that data is missing.

    USAGE:
        from ui.utils.fallback import MISSING, STUB_MAP, STUB_ENTITY
        result = map_service.get_map_info()
        if result.ok:
            width, height = result.data["width"], result.data["height"]
        else:
            width, height = STUB_MAP["width"], STUB_MAP["height"]
            print(f"[ui] WARNING: {result.error}")  # or show in status bar

    DOES NOT IMPORT FROM:
    - engine/ (any)
    - services/
    - PyQt5
"""

# =============================================================================
# MISSING VALUE SENTINEL
# =============================================================================
MISSING = "—"       # Unicode em-dash — shown in any label with no data


# =============================================================================
# STUB DATA — safe defaults shown when backend is unavailable
# =============================================================================

STUB_MAP = {
    "width":     10,
    "height":    10,
    "hex_count": 0,
}

STUB_ENTITY = {
    "id":         "stub_agent",
    "name":       "[No Agent Selected]",
    "type":       "Unknown",
    "side":       "—",
    "q":          0,
    "r":          0,
    "personnel":  0,
    "max_personnel": 100,
    "fire_range": 0,
    "vision_range": 0,
    "suppression": 0.0,
    "under_fire": False,
    "tokens":     0.0,
}

STUB_SCENARIO = {
    "name":  "[No Scenario Loaded]",
    "path":  None,
    "map":   None,
}

STUB_AI_INFO = {
    "state":     MISSING,
    "q_values":  {},
    "action":    MISSING,
    "reward":    0.0,
    "last_pos":  MISSING,
    "personnel": 0,
    "mode":      MISSING,
}

STUB_STATS = {
    "actions": {},
    "modes":   {"Exploit": 0, "Explore": 0},
}


# =============================================================================
# HELPERS
# =============================================================================

def safe_get(result, key, fallback=None):
    """
    Safely extract a key from a ServiceResult's data dict.

    Returns fallback if result.ok is False or key is missing.

    Args:
        result:   ServiceResult from a service call.
        key:      Dict key to extract.
        fallback: Value to return if unavailable.
    """
    if result and result.ok and isinstance(result.data, dict):
        return result.data.get(key, fallback)
    return fallback


def warn_missing(result, context: str = "") -> None:
    """
    Print a console warning when a service call returns an error.
    Intended for debug builds; in production this could go to a log file.

    Args:
        result:  ServiceResult with ok=False.
        context: Human-readable description of what was being requested.
    """
    if result and not result.ok:
        prefix = f"[{context}]" if context else "[ui]"
        print(f"{prefix} WARNING: {result.error}")
