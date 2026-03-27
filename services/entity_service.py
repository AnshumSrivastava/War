"""
FILE:    services/entity_service.py
LAYER:   Middle-End
ROLE:    All agent/entity operations — place, remove, move, query.

DESCRIPTION:
    This service is the ONLY way the UI places, removes, or queries agents.
    The UI never imports engine.core.entity_manager directly.

    Events emitted:
    - "entity_placed"   payload: {"id": str, "q": int, "r": int, "side": str}
    - "entity_removed"  payload: {"id": str}
    - "entity_selected" payload: {"id": str} or None
    - "entities_cleared" payload: None

DOES NOT IMPORT FROM:
    - ui/ or web_ui/
    - PyQt5 / Flask
"""

from typing import Optional, List
from services.service_result import ServiceResult, ok, err
from services import event_bus
from engine.api import DomainAPI

_state = None
_api = None
_selected_entity_id: Optional[str] = None


def init(state) -> None:
    """Inject WorldState. Must be called once at app startup."""
    global _state, _api
    _state = state
    _api = DomainAPI(state)


def _require_api() -> Optional[ServiceResult]:
    if _api is None:
        return err("Entity service not initialized.", code="NOT_INITIALIZED")
    return None


# =============================================================================
# QUERY OPERATIONS
# =============================================================================

def get_all_entities() -> ServiceResult:
    """
    Return all entities currently on the map.

    Returns:
        ServiceResult with data=list of entity objects.
    """
    guard = _require_api()
    if guard: return guard
    try:
        entities = _api.entities.get_all_entities()
        return ok(entities or [])
    except Exception as e:
        return err(f"Could not retrieve entities: {e}")


def get_entities_at(q: int, r: int) -> ServiceResult:
    """Return all entities at a specific hex."""
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)
        entities = _api.map.get_entities_at(hex_coord)
        return ok(entities or [])
    except Exception as e:
        return err(f"Could not get entities at ({q},{r}): {e}")


def get_entity_position(entity_id: str) -> ServiceResult:
    """
    Return the map position of an entity as (q, r).

    Returns:
        ServiceResult with data={"q": int, "r": int} or error if not on map.
    """
    guard = _require_api()
    if guard: return guard
    try:
        pos = _api.map.get_entity_position(entity_id)
        if pos is None:
            return err(f"Entity '{entity_id}' not found on map.", code="NOT_FOUND")
        return ok({"q": pos.q, "r": pos.r})
    except Exception as e:
        return err(f"Error finding entity '{entity_id}': {e}")


def get_selected_entity() -> ServiceResult:
    """Return the currently selected entity, or error if none."""
    guard = _require_api()
    if guard: return guard
    if _selected_entity_id is None:
        return err("No entity selected.", code="NONE_SELECTED")
    try:
        entity = _api.entities.get_entity(_selected_entity_id)
        if entity is None:
            return err(f"Selected entity '{_selected_entity_id}' no longer exists.",
                       code="NOT_FOUND")
        return ok(entity)
    except Exception as e:
        return err(f"Error retrieving selected entity: {e}")


# =============================================================================
# SELECTION
# =============================================================================

def select_entity(entity_id: Optional[str]) -> ServiceResult:
    """
    Set the selected entity. Pass None to clear selection.

    Args:
        entity_id: ID of entity to select, or None to deselect.
    """
    global _selected_entity_id
    _selected_entity_id = entity_id
    event_bus.emit("entity_selected", {"id": entity_id})
    return ok({"id": entity_id})


# =============================================================================
# MUTATION OPERATIONS
# =============================================================================

def place_entity(q: int, r: int, side: str, unit_type: str,
                 name: str = None, entity_data: dict = None) -> ServiceResult:
    """
    Place a new agent on the map.

    Args:
        q:           Hex axial column.
        r:           Hex axial row.
        side:        Side constant (SIDE_ATTACKER or SIDE_DEFENDER).
        unit_type:   Unit type key (maps to content/ definition).
        name:        Optional display name, auto-generated if None.
        entity_data: Optional additional attributes to set on the entity.

    Returns:
        ServiceResult with data={"id": str, "q": int, "r": int, "side": str}
    """
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        hex_coord = HexMath.create_hex(q, r)

        # Delegate to entity_manager for creation
        entity = _api.entities.create_entity(
            unit_type=unit_type,
            side=side,
            name=name,
            extra_attrs=entity_data or {}
        )
        _api.map.place_entity(entity.id, hex_coord)

        payload = {"id": entity.id, "q": q, "r": r, "side": side,
                   "name": entity.name, "type": unit_type}
        event_bus.emit("entity_placed", payload)
        return ok(payload)
    except Exception as e:
        return err(f"Could not place entity at ({q},{r}): {e}")


def remove_entity(entity_id: str) -> ServiceResult:
    """
    Remove an entity from the map and the entity manager.

    Args:
        entity_id: ID of the entity to remove.
    """
    guard = _require_api()
    if guard: return guard
    try:
        _api.map.remove_entity(entity_id)
        _api.entities.remove_entity(entity_id)
        event_bus.emit("entity_removed", {"id": entity_id})
        return ok({"id": entity_id})
    except Exception as e:
        return err(f"Could not remove entity '{entity_id}': {e}")


def spawn_defenders_around(center_hex, count: int = 4) -> ServiceResult:
    """
    Spawn defender agents in a ring around a target hex.
    
    Args:
        center_hex: The Hex coordinate or (q,r,s) tuple around which to spawn.
        count:      Number of defenders to spawn.
    """
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        from engine.core.entity_manager import Agent
        
        # Normalize center_hex if it's a tuple
        if hasattr(center_hex, 'q'):
            center_hex = HexMath.create_hex(center_hex.q, center_hex.r)
        elif isinstance(center_hex, (list, tuple)):
            center_hex = HexMath.create_hex(center_hex[0], center_hex[1])

        neighbors = [HexMath.neighbor(center_hex, i) for i in range(6)]
        valid_hexes = [h for h in neighbors if _api.map.get_terrain(h)]
        
        spawn_count = 0
        for h in valid_hexes:
            if spawn_count >= count: break
            if _api.map.get_entities_at(h): continue
            
            agent_name = f"Guard {spawn_count + 1} ({datetime.datetime.now().microsecond})"
            new_agent = Agent(name=agent_name)
            new_agent.set_attribute("side", "Defender")
            new_agent.set_attribute("type", "DefenderAgent")
            
            _api.entities.register_entity(new_agent)
            _api.map.place_entity(new_agent.id, h)
            
            event_bus.emit("entity_placed", {
                "id": new_agent.id, "q": h.q, "r": h.r, 
                "name": agent_name, "side": "Defender"
            })
            spawn_count += 1
            
        return ok({"spawned_count": spawn_count})
    except Exception as e:
        return err(f"Failed to spawn defenders: {e}")


def spawn_attack_force(center_hex) -> ServiceResult:
    """Spawns a balanced attack force (2 CC, 1 Fire, 1 Reserve)."""
    guard = _require_api()
    if guard: return guard
    try:
        from engine.core.hex_math import HexMath
        from engine.core.entity_manager import Agent
        import datetime
        
        if hasattr(center_hex, 'q'):
            center_hex = HexMath.create_hex(center_hex.q, center_hex.r)
        elif isinstance(center_hex, (list, tuple)):
            center_hex = HexMath.create_hex(center_hex[0], center_hex[1])

        neighbors = [center_hex] + [HexMath.neighbor(center_hex, i) for i in range(6)]
        valid_hexes = [h for h in neighbors if _api.map.get_terrain(h)]
        
        force_mix = [
            ("CloseCombatAgent", "Close Combat 1"),
            ("CloseCombatAgent", "Close Combat 2"),
            ("FiringAgent", "Firing Agent"),
            ("ReserveAgent", "Reserve Support")
        ]
        
        spawn_count = 0
        for h in valid_hexes:
            if spawn_count >= len(force_mix): break
            if _api.map.get_entities_at(h): continue
            
            u_type, u_name = force_mix[spawn_count]
            new_agent = Agent(name=u_name)
            new_agent.set_attribute("side", "Attacker")
            new_agent.set_attribute("type", u_type)
            
            # Set ranges
            if u_type == "FiringAgent": new_agent.set_attribute("fire_range", 6)
            elif u_type == "CloseCombatAgent": new_agent.set_attribute("fire_range", 2)
            
            _api.entities.register_entity(new_agent)
            _api.map.place_entity(new_agent.id, h)
            
            event_bus.emit("entity_placed", {
                "id": new_agent.id, "q": h.q, "r": h.r, 
                "name": u_name, "side": "Attacker"
            })
            spawn_count += 1
            
        return ok({"spawned_count": spawn_count})
    except Exception as e:
        return err(f"Failed to spawn attack force: {e}")
