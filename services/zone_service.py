"""
FILE:    services/zone_service.py
LAYER:   Middle-End
ROLE:    Handles the creation, reading, updating, and deletion of Zones.

DESCRIPTION:
    Moves the complex zone definition logic out of the UI layer (`draw_zone_tool.py`).
"""

import uuid
from typing import Optional, List
from services.service_result import ServiceResult, ok, err
from services import event_bus
from engine.api import DomainAPI
from engine.core.hex_math import HexMath

_state = None
_api = None


def init(state) -> None:
    """Inject WorldState. Must be called once at app startup."""
    global _state, _api
    _state = state
    _api = DomainAPI(state)


def _require_api() -> Optional[ServiceResult]:
    if _api is None:
        return err("Zone service not initialized.", code="NOT_INITIALIZED")
    return None


def get_zones() -> ServiceResult:
    """Return all zones currently on the map."""
    guard = _require_api()
    if guard: return guard
    try:
        zones = _api.map.get_zones()
        return ok(zones or {})
    except Exception as e:
        return err(f"Could not retrieve zones: {e}")


def add_zone(polygon_points: list, zone_data: dict, auto_spawn_defenders: bool = False) -> ServiceResult:
    """
    Create a new polygonal zone on the map.
    
    Args:
        polygon_points: List of Hex coordinates defining the corners.
        zone_data: Dictionary containing name, type, side, color.
        auto_spawn_defenders: Whether to spawn entities for goal areas.
    """
    guard = _require_api()
    if guard: return guard
    try:
        hexes_inside = HexMath.get_hexes_in_polygon(polygon_points)
        if not hexes_inside:
            return err("Polygon contains no hexes", code="INVALID_SHAPE")
            
        # --- AUTO-INITIALIZE DATA ---
        target_side = zone_data.get("side", "Neutral")
        z_type = zone_data.get("subtype", "Area")
        z_category = zone_data.get("type", "Designated Area")
        
        # 1. Sequential Naming for Goal Areas
        if not zone_data.get("name"):
            if "Goal" in z_type:
                goal_count = 0
                for zd in _api.map.get_zones().values():
                    if "Goal" in zd.get("subtype", ""):
                        goal_count += 1
                zone_data["name"] = f"Goal Area {goal_count + 1}"
            else:
                zone_data["name"] = f"{z_type} {str(uuid.uuid4())[:8]}"

        # 2. Default Colors
        if not zone_data.get("color"):
            color = "#FFFFFF"
            if target_side == "Attacker": color = "#FF0000"
            elif target_side == "Defender": color = "#0000FF"
            
            if "Firing" in z_type or "Breach" in z_type: color = "#FF5555"
            if "Start" in z_type: color = "#AA0000" if target_side == "Attacker" else "#0000AA"
            if "Goal" in z_type: color = "#FFD700" # PREMIUM GOLD
            if "Indirect" in z_type: color = "#FFAA00"
            if z_category == "Obstacle": color = "#555555"
            zone_data["color"] = color

        zone_id = str(uuid.uuid4())[:8]
        zone_data["hexes"] = hexes_inside
        zone_data["vertices"] = polygon_points
        
        # Add to Undo stack
        if _api.undo_stack:
            from engine.core.undo_system import AddZoneCommand
            cmd = AddZoneCommand(_api.map, zone_id, zone_data)
            _api.undo_stack.push(cmd)
            
        _api.map.add_zone(zone_id, zone_data)
        
        if auto_spawn_defenders and "Goal" in zone_data.get("subtype", ""):
            # Check overlap with "Designated Area"
            is_in_designated = False
            all_zones = _api.map.get_zones()
            for ozdata in all_zones.values():
                if ozdata.get("type") == "Designated Area":
                    oz_hexes = set(tuple(h) for h in ozdata.get("hexes", []))
                    for h in hexes_inside:
                        if tuple(h) in oz_hexes:
                            is_in_designated = True
                            break
                if is_in_designated: break
            
            if is_in_designated:
                _spawn_goal_defenders(hexes_inside)
        
        if auto_spawn_defenders and "Attack" in zone_data.get("subtype", ""):
            _spawn_attackers(hexes_inside)
            
        payload = {"zone_id": zone_id, "name": zone_data.get("name"), "side": zone_data.get("side")}
        event_bus.emit("zone_added", payload)
        return ok(payload)
        
    except Exception as e:
        return err(f"Could not add zone: {e}")


def _spawn_goal_defenders(zone_hexes: list):
    """Spawns defender agents around the goal area."""
    if not zone_hexes:
        return
        
    center_hex = zone_hexes[0]
    neighbors = [HexMath.neighbor(center_hex, i) for i in range(6)]
    valid_hexes = [h for h in neighbors if _api.map.get_terrain(h)]
    
    from engine.core.entity_manager import Agent
    spawn_count = 0
    
    for h in valid_hexes:
        if spawn_count >= 4:
            break
        if _api.map.get_entities_at(h):
            continue
            
        agent_name = f"Goal Guard {spawn_count + 1}"
        new_agent = Agent(name=agent_name)
        new_agent.set_attribute("side", "Defender")
        new_agent.set_attribute("type", "DefenderAgent")
        new_agent.set_attribute("home_hex", center_hex)
        
        _api.entities.register_entity(new_agent)
        _api.map.place_entity(new_agent.id, h)
        
        event_bus.emit("entity_placed", {
            "id": new_agent.id, "q": h.q, "r": h.r, 
            "name": agent_name, "side": "Defender"
        })
        spawn_count += 1

def add_objective(hex_coord, name="Strategic Objective", color="#FFD700") -> ServiceResult:
    """Add a Goal Area zone at a specific hex."""
    return add_zone([hex_coord], {
        "name": name,
        "type": "Goal Area",
        "subtype": "Goal",
        "color": color
    }, auto_spawn_defenders=True)

def scatter_mines(count=None) -> ServiceResult:
    """Scatter random mine obstacles on the map."""
    guard = _require_api()
    if guard: return guard
    import random
    from engine.core.hex_math import Hex
    
    if count is None:
        count = random.randint(5, 10)
        
    created = 0
    for i in range(count):
        q = random.randint(-5, 5)
        r = random.randint(-5, 5)
        m_hex = Hex(q, r, -q-r)
        
        res = add_zone([m_hex], {
            "name": "Minefield",
            "type": "Obstacle",
            "subtype": "mine",
            "color": "#555555"
        })
        if res.ok: created += 1
        
    return ok({"count": created})


def add_attack_area(hex_coord) -> ServiceResult:
    """Adds a 4-hex 'Initial Attack Area' and spawns the attack force."""
    # Generate a small 4-hex cluster
    hexes = [hex_coord]
    for i in range(3):
        hexes.append(HexMath.neighbor(hex_coord, i))
        
    return add_zone(hexes, {
        "name": "Initial Attack Area",
        "type": "Designated Area",
        "subtype": "Attack Area",
        "side": "Attacker",
        "color": "#FF5555"
    }, auto_spawn_defenders=True)


def _spawn_attackers(zone_hexes: list):
    """Spawns the specialized attack force within the zone."""
    if not zone_hexes: return
    
    from services import entity_service
    entity_service.spawn_attack_force(zone_hexes[0])
