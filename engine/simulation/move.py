"""
FILE: engine/simulation/move.py
ROLE: The "Navigator" for units.

DESCRIPTION:
This file handles the logic for moving a unit from one hexagon to another.
It checks for several rules before allowing a move:
1. Is the direction valid? (North, South, East, West, etc.)
2. Is there actually ground (terrain) there, or is it the edge of the world?
3. Is another unit already blocking the way? (Using Weight-based Stacking Limits).

If all checks pass, the unit's position is updated on the map, and the action 
is recorded in the history log for 'Undo' purposes.
"""
from .base_action import BaseAction
from engine.core.hex_math import Hex, HexMath, DIRECTION_MAP


class MoveAction(BaseAction):
    """
    Handles the 'MOVE' command for any unit.
    """
    def __init__(self):
        # We name this tool "MOVE" so the AI Brain can find it.
        super().__init__("MOVE", "Move Unit")

    def is_allowed(self, entity, game_map, target=None) -> bool:
        """
        Basic capability check. (Always True for now, unless the unit is broken).
        """
        return True

    def execute(self, entity, game_map, direction=None, **kwargs):
        """
        THE MOVEMENT PROCESS: 
        Slides a unit into a neighboring hexagon if the path is clear.
        """
        # 1. DIRECTION CHECK: Is the direction one of the 6 valid hexagonal directions?
        if not direction or direction not in DIRECTION_MAP:
            return f"MOVE FAILED (Invalid Dir: {direction})", None, None
            
        current_pos = game_map.get_entity_position(entity.id)
        if not current_pos:
            return "MOVE FAILED (Unit not on map)", None, None
            
        # 2. CALCULATION: Figure out the coordinates of the hexagon we want to enter.
        dq, dr, ds = DIRECTION_MAP[direction]
        new_hex = Hex(current_pos.q + dq, current_pos.r + dr, current_pos.s + ds)
        
        # 3. TERRAIN CHECK: Does the destination actually exist? (No 'Void' or map edges).
        terrain = game_map.get_terrain(new_hex)
        if terrain is None:
             return f"MOVE BLOCKED ({direction} -> edge of world)", None, None
             
        # 4. STACKING CHECK (V3 WEIGHT SYSTEM): 
        # Instead of a simple count, we check how HEAVY the units are.
        # A bridge or a 100m hex can only hold so many tons of steel/personnel.
        entity_manager = kwargs.get("entity_manager")
        if entity_manager:
            # Get the weight of the moving unit.
            agent_weight = float(entity.get_attribute("weight", 1))
            # Ask the map if there's enough room for this specific weight.
            if hasattr(game_map, 'can_place_agent') and not game_map.can_place_agent(new_hex, agent_weight, entity_manager):
                return f"MOVE BLOCKED (Weight Limit Exceeded)", None, None
        else:
            # Fallback for simple simulations: Maximum 3 units per hex.
            limit = game_map.active_scenario.rules.get("max_agents_per_hex", 3)
            if len(game_map.get_entities_at(new_hex)) >= limit:
                return f"MOVE BLOCKED (Hex is crowded)", None, None
            
        # 5. UNDO SYSTEM (V3 RESTORE): Log this move so we can 'Rewind' time.
        from engine.state.global_state import GlobalState
        state = GlobalState()
        if hasattr(state, 'undo_stack'):
            from engine.core.undo_system import MoveEntityCommand
            # Create a 'Movement Message' for the history book.
            cmd = MoveEntityCommand(game_map, entity.id, new_hex, current_pos)
            state.undo_stack.push(cmd)

        # 6. SUCCESS: Physically update the map, moving the unit to its new home.
        game_map.place_entity(entity.id, new_hex)
        
        # Status message
        status_msg = f"MOVE {direction.upper()}"

        # FEEDBACK: Create an event so the graphics window knows to slide the unit's icon.
        event = {
            "type": "move",
            "agent_id": entity.id,
            "from": current_pos,
            "to": new_hex
        }

        # --- MINE STRIKE CHECK ---
        zones = game_map.get_zones()
        from engine.state.global_state import GlobalState
        state = GlobalState()
        
        for zone_id, zone_data in zones.items():
            if zone_data.get("type") == "Obstacle":
                # Check if this hex is in the obstacle zone
                if any(tuple(new_hex) == tuple(h) for h in zone_data.get("hexes", [])):
                    # Get the specific obstacle properties (e.g. "mine")
                    obs_subtype = zone_data.get("subtype", "mine")
                    catalog = state.data_controller.obstacle_types
                    obs_properties = catalog.get(obs_subtype, {})
                    
                    if "mine" in obs_subtype.lower() or "mine" in obs_properties.get("name", "").lower():
                        from engine.combat.mine_negotiation import MineNegotiation
                        casualties = MineNegotiation.negotiate_minefield(entity, obs_properties)
                        
                        if casualties > 0:
                            current_p = int(entity.get_attribute("personnel", 100))
                            new_p = max(0, current_p - casualties)
                            entity.set_attribute("personnel", new_p)
                            status_msg += f" | <b>MINE STRIKE!</b> -{casualties} pers"
                            if new_p <= 0:
                                status_msg += " [DETROYED]"
                        break # Only one mine strike per movement step
                
        # Moving units are harder to hit, so we clear the 'under fire' status.
        entity.set_attribute("under_fire", False)
        
        return status_msg, event, None
