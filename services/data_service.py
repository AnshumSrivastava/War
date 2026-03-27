"""
FILE:    services/data_service.py
LAYER:   Middle-End
ROLE:    Game data lookup — unit definitions, terrain configs, obstacle types.

DESCRIPTION:
    All reads from the content/ directory go through this service.
    The UI never calls DataManager directly.

DOES NOT IMPORT FROM:
    - ui/ or web_ui/
    - PyQt5 / Flask
"""

from typing import Optional, List
from services.service_result import ServiceResult, ok, err

_state = None


def init(state) -> None:
    """Inject WorldState. Call once at startup."""
    global _state
    _state = state


def _require_state() -> Optional[ServiceResult]:
    if _state is None:
        return err("Data service not initialized.", code="NOT_INITIALIZED")
    return None


def get_unit_types() -> ServiceResult:
    """
    Return all available unit type definitions from content/.

    Returns:
        ServiceResult with data=dict of {type_key: unit_config}
    """
    guard = _require_state()
    if guard: return guard
    try:
        types = _state.data_controller.get_all_unit_types()
        return ok(types or {})
    except Exception as e:
        return err(f"Could not load unit types: {e}")


def get_unit_config(unit_type: str) -> ServiceResult:
    """
    Return the full config dict for a specific unit type.

    Args:
        unit_type: Unit type key (e.g. "HeavyGunner").
    """
    guard = _require_state()
    if guard: return guard
    try:
        config = _state.data_controller.get_unit_config(unit_type)
        if config is None:
            return err(f"Unit type '{unit_type}' not found.", code="NOT_FOUND")
        return ok(config)
    except Exception as e:
        return err(f"Could not load config for '{unit_type}': {e}")


def get_terrain_types() -> ServiceResult:
    """Return all terrain type definitions."""
    guard = _require_state()
    if guard: return guard
    try:
        terrain = _state.data_controller.terrain_types
        return ok(terrain or {})
    except Exception as e:
        return err(f"Could not load terrain types: {e}")


def get_hex_full_attributes(q: int, r: int) -> ServiceResult:
    """
    Return the fully-resolved attribute dict for a hex, including
    overlaid zone and section data.

    Args:
        q: Hex axial column.
        r: Hex axial row.
    """
    guard = _require_state()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)
        attrs = _state.data_controller.get_hex_full_attributes(hex_coord, _state.map)
        return ok(attrs)
    except Exception as e:
        return err(f"Could not get hex attributes for ({q},{r}): {e}")
