"""
FILE:    services/map_service.py
LAYER:   Middle-End
ROLE:    All map operations — create, load, query, modify terrain and zones.

DESCRIPTION:
    This service is the ONLY way the UI interacts with the map.
    The UI never imports engine.core.map directly.

    On success, functions return ServiceResult(ok=True, data=<payload>).
    On failure, they return ServiceResult(ok=False, error=<message>).
    They NEVER raise exceptions to the caller.

    Events emitted:
    - "map_loaded"       payload: {"width": int, "height": int}
    - "terrain_painted"  payload: {"hex": (q, r), "terrain_type": str}
    - "zone_updated"     payload: {"zone_id": str, "hexes": [...]}
    - "map_cleared"      payload: None

DOES NOT IMPORT FROM:
    - ui/ or web_ui/
    - PyQt5 / Flask
"""

from typing import Optional, Any
from services.service_result import ServiceResult, ok, err
from services import event_bus
from engine.api import DomainAPI


# =============================================================================
# STATE REFERENCE — injected at startup via init()
# =============================================================================
_state = None   # WorldState instance
_api = None


def init(state) -> None:
    """
    Inject the WorldState. Must be called once at app startup.

    Args:
        state: WorldState instance from engine.state.world_state.
    """
    global _state, _api
    _state = state
    _api = DomainAPI(state)


def _require_api() -> Optional[ServiceResult]:
    """Returns an error ServiceResult if state is not initialized."""
    if _api is None:
        return err("Map service not initialized. Call map_service.init(state) first.",
                   code="NOT_INITIALIZED")
    return None


# =============================================================================
# QUERY OPERATIONS
# =============================================================================

def get_map_info() -> ServiceResult:
    """
    Return basic info about the currently loaded map.

    Returns:
        ServiceResult with data={"width": int, "height": int, "hex_count": int}
    """
    guard = _require_api()
    if guard: return guard
    try:
        m = _api.map
        return ok({"width": m.width, "height": m.height})
    except Exception as e:
        return err(f"Could not read map info: {e}")


def get_hex(q: int, r: int) -> ServiceResult:
    """
    Return terrain data for a single hex.

    Args:
        q: Hex axial column coordinate.
        r: Hex axial row coordinate.

    Returns:
        ServiceResult with data=HexData dict, or error if hex not found.
    """
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)
        terrain = _api.map.get_terrain(hex_coord)
        if terrain is None:
            return err(f"Hex ({q},{r}) has no terrain data.", code="NOT_FOUND")
        return ok(terrain)
    except Exception as e:
        return err(f"Error reading hex ({q},{r}): {e}")


def get_zones() -> ServiceResult:
    """
    Return all zone definitions on the current map.

    Returns:
        ServiceResult with data=dict of {zone_id: zone_data}.
    """
    guard = _require_api()
    if guard: return guard
    try:
        zones = _api.map.get_zones()
        return ok(zones or {})
    except Exception as e:
        return err(f"Could not read zones: {e}")


def get_paths() -> ServiceResult:
    """Return all drawn path definitions on the current map."""
    guard = _require_api()
    if guard: return guard
    try:
        paths = _api.map.get_paths() if hasattr(_api.map, 'get_paths') else {}
        return ok(paths or {})
    except Exception as e:
        return err(f"Could not read paths: {e}")


# =============================================================================
# MUTATION OPERATIONS
# =============================================================================

def paint_terrain(q: int, r: int, terrain_type: str) -> ServiceResult:
    """
    Set the terrain type of a hex.

    Args:
        q:            Hex axial column.
        r:            Hex axial row.
        terrain_type: Terrain type key (use engine.models.constants.TERRAIN_*).

    Returns:
        ServiceResult with data={"hex": (q, r), "terrain_type": terrain_type}
    """
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)
        # paint_hex sets terrain on the map
        _api.map.paint_hex(hex_coord, terrain_type, _api.config)
        payload = {"hex": (q, r), "terrain_type": terrain_type}
        event_bus.emit("terrain_painted", payload)
        return ok(payload)
    except Exception as e:
        return err(f"Could not paint terrain at ({q},{r}): {e}")


def clear_hex(q: int, r: int) -> ServiceResult:
    """Remove terrain and any content from a hex. Includes Undo support."""
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)
        
        # UNDO PREPARATION
        old_data = _api.map._terrain.get(tuple(hex_coord))
        if old_data and _api.undo_stack:
            from engine.core.undo_system import ClearTerrainCommand
            cmd = ClearTerrainCommand(_api.map, hex_coord, old_data.copy())
            _api.undo_stack.push(cmd)
            
        _api.map.set_terrain(hex_coord, None)
        event_bus.emit("hex_cleared", {"hex": (q, r)})
        return ok({"hex": (q, r)})
    except Exception as e:
        return err(f"Could not clear hex ({q},{r}): {e}")


def load_map(file_path: str) -> ServiceResult:
    """
    Load a map from a JSON file into the current world state.

    Args:
        file_path: Absolute path to the map JSON file.

    Returns:
        ServiceResult with data={"width": int, "height": int} on success.
    """
    guard = _require_api()
    if guard: return guard
    try:
        import json
        with open(file_path) as f:
            map_data = json.load(f)
        _api.map.load(map_data)
        _state.current_map = file_path
        payload = {"width": _api.map.width, "height": _api.map.height}
        event_bus.emit("map_loaded", payload)
        return ok(payload)
    except FileNotFoundError:
        return err(f"Map file not found: {file_path}", code="NOT_FOUND")
    except Exception as e:
        return err(f"Failed to load map: {e}")


def save_map(file_path: str) -> ServiceResult:
    """
    Save the current terrain and map dimensions to a JSON file.

    Args:
        file_path: Absolute path to the output JSON file.

    Returns:
        ServiceResult with data={"path": str} on success.
    """
    guard = _require_api()
    if guard: return guard
    try:
        import json
        import os
        # include_scenarios=False because map service only handles terrain/zones.
        # Scenario service handles the full project/scenario state.
        data = _api.map.to_dict(include_scenarios=False)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        event_bus.emit("map_saved", {"path": file_path})
        
        # Generate Thumbnail
        try:
            from services.thumbnail_service import ThumbnailService
            thumb_path = os.path.join(os.path.dirname(file_path), "thumbnail.png")
            ThumbnailService.generate_thumbnail(_api.map, thumb_path)
        except Exception as te:
            print(f"Non-critical thumbnail error: {te}")
            
        return ok({"path": file_path})
    except Exception as e:
        return err(f"Failed to save map to {file_path}: {e}")


def load_project_folder(map_dir: str) -> ServiceResult:
    """
    Load a project folder containing Terrain.json and a Scenarios/ subfolder.
    
    Args:
        map_dir: Absolute path to the map directory.
        
    Returns:
        ServiceResult with data={"map_name": str, "scenarios_loaded": int}
    """
    guard = _require_api()
    if guard: return guard
    try:
        import json
        import os
        terrain_path = os.path.join(map_dir, "Terrain.json")
        if not os.path.exists(terrain_path):
            return err(f"Terrain.json not found in {map_dir}", code="NOT_FOUND")
            
        # 1. Load Terrain
        with open(terrain_path, 'r') as f:
            terrain_data = json.load(f)
        _api.map.load_from_dict(terrain_data)
        _state.current_map = os.path.basename(map_dir)
        _state.project_path = map_dir # Update project path
        
        # 2. Load Scenarios
        scenarios_dir = os.path.join(map_dir, "Scenarios")
        loaded_scens = 0
        if os.path.exists(scenarios_dir):
            # Clear existing scenarios in the map object
            _api.map.scenarios = {} 
            for fname in os.listdir(scenarios_dir):
                if fname.endswith(".json"):
                    try:
                        s_path = os.path.join(scenarios_dir, fname)
                        with open(s_path, 'r') as f:
                            s_data = json.load(f)
                        
                        s_name = s_data.get("name", os.path.splitext(fname)[0])
                        print(f"DEBUG: Loading scenario '{s_name}' from {s_path}")
                        from engine.core.map import Scenario
                        scen = Scenario(s_name)
                        # Populates manager and scenario object
                        scen.load_from_dict_with_entities(s_data, _api.entities)
                        
                        _api.map.scenarios[s_name] = scen
                        loaded_scens += 1
                    except Exception as e:
                        print(f"Error loading scenario {fname}: {e}")
        
        # 3. Auto-select first scenario or create a default if empty
        if loaded_scens > 0:
            first_key = list(_api.map.scenarios.keys())[0]
            _api.map.active_scenario = _api.map.scenarios[first_key]
        else:
            from engine.core.map import Scenario
            _api.map.active_scenario = Scenario("Default")
            _api.map.scenarios["Default"] = _api.map.active_scenario
             
        payload = {"map_name": _state.current_map, "scenarios_loaded": loaded_scens}
        event_bus.emit("map_loaded", payload)
        
        # Ensure thumbnail exists
        try:
            from services.thumbnail_service import ThumbnailService
            thumb_path = os.path.join(map_dir, "thumbnail.png")
            if not os.path.exists(thumb_path):
                ThumbnailService.generate_thumbnail(_api.map, thumb_path)
        except Exception as te:
            print(f"Non-critical thumbnail error: {te}")
            
        return ok(payload)
        
    except Exception as e:
        return err(f"Failed to load project folder: {e}")
def get_project_manifest(project_name: str) -> ServiceResult:
    """
    Scans the project directory and returns a structured manifest of all 
    available maps and their associated scenarios.
    
    Returns:
        ServiceResult with data={
            "project": str,
            "root_path": str,
            "maps": {
                "MapName": {
                    "scenarios": [str, ...]
                }
            }
        }
    """
    guard = _require_api()
    if guard: return guard
    
    try:
        import os
        root = _state.data_controller.content_root
        proj_path = os.path.join(root, "Projects", project_name)
        maps_dir = os.path.join(proj_path, "Maps")
        
        manifest = {
            "project": project_name,
            "root_path": root,
            "maps": {}
        }
        
        if os.path.exists(maps_dir):
            for m_name in os.listdir(maps_dir):
                m_path = os.path.join(maps_dir, m_name)
                if os.path.isdir(m_path):
                    scen_list = []
                    scen_dir = os.path.join(m_path, "Scenarios")
                    if os.path.exists(scen_dir):
                        scen_files = [f for f in os.listdir(scen_dir) if f.endswith(".json")]
                        scen_list = [f.replace(".json", "") for f in scen_files]
                    
                    sim_list = []
                    sim_dir = os.path.join(m_path, "Simulations")
                    if os.path.exists(sim_dir):
                        sim_files = [f for f in os.listdir(sim_dir) if f.endswith(".json")]
                        sim_list = [f.replace(".json", "") for f in sim_files]
                    
                    manifest["maps"][m_name] = {
                        "scenarios": sorted(scen_list),
                        "simulations": sorted(sim_list)
                    }
                    
        return ok(manifest)
    except Exception as e:
        return err(f"Failed to build project manifest: {e}")
