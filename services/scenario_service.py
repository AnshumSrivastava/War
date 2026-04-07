"""
FILE:    services/scenario_service.py
LAYER:   Middle-End
ROLE:    Scenario file operations — load, save, side management.

DESCRIPTION:
    All scenario and project file I/O goes through this service.
    The UI never directly reads JSON files; it asks this service.

    Events emitted:
    - "scenario_loaded"  payload: {"name": str, "path": str}
    - "scenario_saved"   payload: {"path": str}
    - "sides_updated"    payload: {"sides": dict}

DOES NOT IMPORT FROM:
    - ui/ or ui/
    - PyQt5 / Flask
"""

import json
import os
from typing import Optional
from services.service_result import ServiceResult, ok, err
from services import event_bus

_state = None


def init(state) -> None:
    """Inject WorldState. Call once at startup."""
    global _state
    _state = state


def _require_state() -> Optional[ServiceResult]:
    if _state is None:
        return err("Scenario service not initialized.", code="NOT_INITIALIZED")
    return None


def load_scenario(file_path: str) -> ServiceResult:
    """
    Load a scenario JSON file into the current world state.

    Populates map, entities, zones, rules, and side assignments.

    Args:
        file_path: Absolute path to the scenario .json file.

    Returns:
        ServiceResult with data={"name": str, "path": str}
    """
    guard = _require_state()
    if guard: return guard
    try:
        with open(file_path) as f:
            data = json.load(f)
        _state.current_project = data.get("name", os.path.basename(file_path))
        _state.project_path = file_path
        # Delegate actual loading to the map's built-in loader
        # We need the entity_manager from the state/api
        from engine.api import DomainAPI
        api = DomainAPI(_state)
        # ONLY load into the active scenario layer (preserve terrain)
        _state.map.active_scenario.load_from_dict_with_entities(data, api.entities)
        payload = {"name": _state.current_project, "path": file_path}
        event_bus.emit("scenario_loaded", payload)
        return ok(payload)
    except FileNotFoundError:
        return err(f"Scenario file not found: {file_path}", code="NOT_FOUND")
    except json.JSONDecodeError as e:
        return err(f"Invalid JSON in scenario file: {e}", code="PARSE_ERROR")
    except Exception as e:
        return err(f"Failed to load scenario: {e}")


def save_scenario(file_path: Optional[str] = None) -> ServiceResult:
    """
    Save the current scenario to disk.

    Args:
        file_path: Path to save to. Uses the last loaded path if None.

    Returns:
        ServiceResult with data={"path": str}
    """
    guard = _require_state()
    if guard: return guard
    path = file_path or _state.project_path
    if not path:
        return err("No save path specified.", code="NO_PATH")
    try:
        data = _state.map.serialize_scenario()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        event_bus.emit("scenario_saved", {"path": path})
        return ok({"path": path})
    except Exception as e:
        return err(f"Failed to save scenario: {e}")


def get_current_scenario_info() -> ServiceResult:
    """Return name and path of the currently loaded scenario."""
    guard = _require_state()
    if guard: return guard
    return ok({
        "name": _state.current_project,
        "path": _state.project_path,
        "map":  _state.current_map,
    })


def list_scenarios() -> ServiceResult:
    """
    Return a list of all available scenario files in content/Projects/.

    Returns:
        ServiceResult with data=list of {"name": str, "path": str} dicts.
    """
    guard = _require_state()
    if guard: return guard
    try:
        from engine.data.content_path import get_content_root
        projects_dir = os.path.join(get_content_root(), "Projects")
        if not os.path.isdir(projects_dir):
            return ok([])
        scenarios = []
        for fn in os.listdir(projects_dir):
            if fn.endswith(".json"):
                full_path = os.path.join(projects_dir, fn)
                try:
                    with open(full_path) as f:
                        d = json.load(f)
                    scenarios.append({"name": d.get("name", fn), "path": full_path})
                except Exception:
                    scenarios.append({"name": fn, "path": full_path})
        return ok(scenarios)
    except Exception as e:
        return err(f"Could not list scenarios: {e}")


def save_all_scenarios(project_path: str) -> ServiceResult:
    """
    Save all scenarios currently in memory to the project's Scenarios/ folder.
    
    Args:
        project_path: Absolute path to the map project directory.
        
    Returns:
        ServiceResult with data={"saved_count": int}
    """
    guard = _require_state()
    if guard: return guard
    try:
        saved_count = 0
        from engine.api import DomainAPI
        api = DomainAPI(_state)
        
        print(f"DEBUG: save_all_scenarios state.map ID: {id(_state.map)}")
        print(f"DEBUG: scenarios dict count: {len(_state.map.scenarios)}")
        
        for name, scen in _state.map.scenarios.items():
            # If it's the active one, use the live Entity Manager via API
            if _state.map.active_scenario and name == _state.map.active_scenario.name:
                data = scen.to_dict_with_entities(api.entities)
            else:
                # For inactive ones, use their internal cached state
                data = scen.to_dict()
                
            data["name"] = name
            print(f"DEBUG: Saving scenario '{name}' to {project_path}")
            
            # Use data_controller to save individual scenario file
            # content/Projects/NAME/Maps/MAPNAME/Scenarios/NAME.json
            success = _state.data_controller.save_scenario(name, data, project_path=project_path)
            if success:
                print(f"DEBUG: Successfully saved '{name}'")
                saved_count += 1
            else:
                print(f"DEBUG: FAILED to save '{name}'")
                
        event_bus.emit("all_scenarios_saved", {"count": saved_count})
        return ok({"saved_count": saved_count})
    except Exception as e:
        return err(f"Failed to save all scenarios: {e}")


def get_active_scenario_data() -> ServiceResult:
    """Return the serialized data of the active scenario, including entities."""
    guard = _require_state()
    if guard: return guard
    try:
        from engine.api import DomainAPI
        api = DomainAPI(_state)
        scen = _state.map.active_scenario
        if not scen:
            return err("No active scenario to serialize.", code="NOT_FOUND")
            
        data = scen.to_dict_with_entities(api.entity_manager)
        return ok(data)
    except Exception as e:
        return err(f"Failed to get active scenario data: {e}")
