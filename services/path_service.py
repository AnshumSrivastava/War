"""
FILE:    services/path_service.py
LAYER:   Middle-End
ROLE:    Handles the creation, reading, and deletion of linear paths (Roads, Borders).

DESCRIPTION:
    Extracts map path logic out of `draw_path_tool.py`.
"""

import uuid
from typing import Optional
from services.service_result import ServiceResult, ok, err
from services import event_bus
from engine.api import DomainAPI

_state = None
_api = None


def init(state) -> None:
    global _state, _api
    _state = state
    _api = DomainAPI(state)


def _require_api() -> Optional[ServiceResult]:
    if _api is None:
        return err("Path service not initialized.", code="NOT_INITIALIZED")
    return None


def get_paths() -> ServiceResult:
    """Return all paths currently on the map."""
    guard = _require_api()
    if guard: return guard
    try:
        paths = _api.map.get_paths() if hasattr(_api.map, 'get_paths') else {}
        return ok(paths or {})
    except Exception as e:
        return err(f"Could not retrieve paths: {e}")


def add_path(hexes: list, path_data: dict) -> ServiceResult:
    """
    Create a new path on the map.
    """
    guard = _require_api()
    if guard: return guard
    try:
        path_id = str(uuid.uuid4())[:8]
        path_data["hexes"] = hexes
        
        if _api.undo_stack:
            from engine.core.undo_system import AddPathCommand
            cmd = AddPathCommand(_api.map, path_id, path_data)
            _api.undo_stack.push(cmd)
            
        _api.map.add_path(path_id, path_data)
        
        # Special logic for Border mode
        if path_data.get("type") == "Border":
            _api.map.border_path = hexes
            
        payload = {"path_id": path_id, "name": path_data.get("name"), "type": path_data.get("type")}
        event_bus.emit("path_added", payload)
        return ok(payload)
        
    except Exception as e:
        return err(f"Could not add path: {e}")
