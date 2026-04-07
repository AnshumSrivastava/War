"""
FILE:    services/project_service.py
LAYER:   Middle-End
ROLE:    Project I/O and Phase Synchronization.

DESCRIPTION:
    Handles saving and loading of projects. Supports:
    1. Monolithic JSON (Primary — Default.json containing all terrain + scenarios)
    2. Folder-based (Maps/<MapName>/Terrain.json + Scenarios/<name>.json)
    
    The monolithic format is the existing on-disk format used by the application.
    
    Project Structure on Disk:
    content/Projects/
    └── <ProjectName>/
        └── Maps/
            ├── <ProjectName>.json  (monolithic — may exist)
            └── <MapName>/
                ├── Terrain.json
                ├── thumbnail.png
                └── Scenarios/
                    └── <ScenarioName>.json

DOES NOT IMPORT FROM:
    - ui/ or ui/
    - PyQt5 / Flask
"""

import json
import os
import uuid
from typing import Optional
from services.service_result import ServiceResult, ok, err
from services import event_bus

_state = None

def init(state):
    """Inject WorldState. Call once at startup."""
    global _state
    _state = state

def _require_state() -> Optional[ServiceResult]:
    if _state is None:
        return err("Project service not initialized.", code="NOT_INITIALIZED")
    return None


# =============================================================================
# SAVE PROJECT
# =============================================================================

def save_project(path: Optional[str] = None) -> ServiceResult:
    """
    Saves the entire project using the monolithic JSON format.
    This is the primary save path matching the existing on-disk format.
    """
    guard = _require_state()
    if guard: return guard
    
    target_path = path or _state.project_path
    if not target_path:
        return err("No project path specified for saving.", code="NO_PATH")
        
    try:
        from engine.api import DomainAPI
        api = DomainAPI(_state)
        
        # Ensure .json extension for monolithic save
        if not target_path.endswith(".json"):
            # If it's a directory path, build the JSON path from it
            project_name = os.path.basename(target_path)
            root = os.path.dirname(os.path.dirname(target_path))  # Go up past Maps/
            target_path = os.path.join(root, f"{project_name}.json")
        
        # Build the full project data
        data = _state.map.to_dict(include_scenarios=True, entity_manager=api.entities)
        data["current_map_name"] = getattr(_state, 'current_map', 'Default')
        data["project_name"] = getattr(_state, 'current_project', 'Unnamed')
        
        # Inject UIDs into roster agents if missing
        _ensure_roster_uids(data)
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        _state.project_path = target_path
        
        print(f"DEBUG: Project saved -> {target_path}")
        event_bus.emit("project_saved", {"path": target_path})
        return ok({"path": target_path})
        
    except Exception as e:
        return err(f"Failed to save project: {e}")


def _ensure_roster_uids(data):
    """Inject UUIDs into roster agents that don't have one."""
    for scen_name, scen_data in data.get("scenarios", {}).items():
        roster = scen_data.get("rules", {}).get("roster", {})
        for side in ["Attacker", "Defender"]:
            for agent in roster.get(side, []):
                if "uid" not in agent:
                    agent["uid"] = str(uuid.uuid4())[:8]


# =============================================================================
# LOAD PROJECT  
# =============================================================================

def load_project(path: str) -> ServiceResult:
    """
    Loads a project. Handles both monolithic JSON and folder-based layouts.
    
    Path types:
    - "/path/to/Default.json"  → Monolithic JSON load
    - "/path/to/Maps/MapName"  → Folder-based load (Terrain.json + Scenarios/)
    """
    guard = _require_state()
    if guard: return guard
    
    if not os.path.exists(path):
        return err(f"Project path not found: {path}", code="NOT_FOUND")
    
    try:
        from engine.api import DomainAPI
        api = DomainAPI(_state)
        
        # Monolithic JSON
        if path.endswith(".json"):
            return _load_monolithic(path, api)
        
        # Folder-based (Maps/MapName/ directory)
        if os.path.isdir(path):
            terrain_path = os.path.join(path, "Terrain.json")
            if os.path.exists(terrain_path):
                return _load_folder(path, api)
                
            # Try to find monolithic JSON in parent
            parent = os.path.dirname(path)
            project_name = os.path.basename(path)
            mono_path = os.path.join(parent, f"{project_name}.json")
            if os.path.exists(mono_path):
                return _load_monolithic(mono_path, api)
        
        return err(f"Could not determine project format at: {path}", code="UNKNOWN_FORMAT")
        
    except Exception as e:
        return err(f"Failed to load project: {e}")


def _load_monolithic(path: str, api) -> ServiceResult:
    """Load from monolithic JSON format (the primary existing format)."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Load the full map including scenarios and entities
        _state.map.load_from_dict(data, entity_manager=api.entities)
        
        _state.current_project = data.get("project_name", os.path.basename(path).replace(".json", ""))
        _state.project_path = path
        _state.current_map = data.get("current_map_name", "Default")
        
        # Verify roster data exists in active scenario
        if _state.map.active_scenario:
            rules = _state.map.active_scenario.rules
            roster = rules.get("roster", {})
            atk_count = len(roster.get("Attacker", []))
            def_count = len(roster.get("Defender", []))
            print(f"DEBUG: Monolithic load complete. Active scenario roster: ATK={atk_count} DEF={def_count}")
        
        event_bus.emit("project_loaded", {"path": path, "name": _state.current_project})
        return ok({"name": _state.current_project})
        
    except Exception as e:
        return err(f"Failed to load monolithic project: {e}")


def _load_folder(map_dir: str, api) -> ServiceResult:
    """Load from folder-based format (Maps/MapName/Terrain.json + Scenarios/)."""
    try:
        import services.map_service as map_svc
        result = map_svc.load_project_folder(map_dir)
        if result.ok:
            _state.project_path = map_dir
        return result
    except Exception as e:
        return err(f"Failed to load project folder: {e}")


def auto_persist() -> ServiceResult:
    """Convenience method for phase-stepping persistence."""
    return save_project()
