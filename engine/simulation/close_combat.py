"""
FILE: engine/action/close_combat.py
ROLE: The "Melee Combat" specialist.

DESCRIPTION:
This file handles the logic for a unit attacking an enemy that is right next 
to them (Distance = 1).
Rules for Melee:
1. The enemy must be in a neighboring hexagon.
2. It doesn't matter if the unit is 'aligned' or not - if you are adjacent, 
   you can strike.

Just like the 'Fire' action, this uses the Combat Engine to determine 
the damage and update the enemy units.
"""
from .base_action import BaseAction
from engine.core.hex_math import HexMath

class CloseCombatAction(BaseAction):
    """
    Handles the 'CLOSE_COMBAT' command, representing a melee attack.
    """
    def __init__(self):
        # We name this tool "CLOSE_COMBAT" so the AI Brain can find and use it.
        # The display name "Close Combat" is for user interfaces or logs.
        super().__init__("CLOSE_COMBAT", "Close Combat")

    def is_allowed(self, entity, game_map, target=None, data_controller=None) -> bool:
        """
        NEIGHBOR CHECK: Returns True if the enemy is in the immediate next hexagon.
        """
        # 1. TARGET CHECK: You must have an enemy in mind to strike!
        if not target: return False
        
        # 2. POSITION CHECK: Get the location of both units.
        my_pos = game_map.get_entity_position(entity.id)
        other_pos = game_map.get_entity_position(target.id)
        
        # 3. RANGE CHECK: If either unit is not on the map, we can't calculate distance.
        if not my_pos or not other_pos: return False
        
        # 4. ADJACENCY: Melee is only possible if the units are face-to-face (Distance = 1).
        # It doesn't matter if they are in a straight line or not.
        return HexMath.distance(my_pos, other_pos) == 1

    def execute(self, entity, game_map, target=None, combat_engine=None, data_controller=None):
        """
        THE MELEE PROCESS: High-risk, high-reward face-to-face combat.
        """
        # 1. SAFETY CHECK: Ensure we have both a target and a brain to calculate the result.
        if not target or not combat_engine:
            return "MELEE FAILED (No Target/Engine)", None, None
            
        # 2. CALCULATION: The combat engine calculates a brutal close-quarters strike.
        # It takes into account the units' personnel and any defensive positions.
        combat_result = combat_engine.calculate_attrition(entity, target, game_map, data_controller=data_controller)
        casualties = combat_result.get("casualties", 0)
        remaining = combat_result.get("remaining", 0)
        
        # 3. UNDO SYSTEM (V3 RESTORE): Log this strike so it can be 'Undone' in the UI.
        from engine.state.global_state import GlobalState
        state = GlobalState()
        if hasattr(state, 'undo_stack'):
            from engine.core.undo_system import DamageEntityCommand
            # Save the 'before and after' of this attack.
            cmd = DamageEntityCommand(state.entity_manager, target.id, casualties)
            state.undo_stack.push(cmd)

        # 4. APPLY DAMAGE: Update the target's personnel count based on the strike.
        # Note: We use 'personnel' to represent the number of soldiers remaining.
        target.set_attribute("personnel", remaining)
        # Mark the unit as 'under fire' so the UI knows to show a hit effect.
        target.set_attribute("under_fire", True)
        
        # 5. TEXT REPORT: Human-readable status update for the event log.
        desc = f"MELEE"
        if casualties > 0:
            desc += f" -> -{casualties} personnel"
            if remaining <= 0:
                desc += " [KILLED]"
        else:
            desc += " MISS"
            
        # 6. VISUAL EVENT: Send data to the graphics window. 
        # We reuse the 'fire' visual event but mark it with 'is_melee' 
        # so the screen knows to draw a sword/explosion at close range.
        event = {
            "type": "fire",
            "source_hex": game_map.get_entity_position(entity.id),
            "target_hex": game_map.get_entity_position(target.id),
            "hit": casualties > 0,
            "is_melee": True
        }
        return desc, event, combat_result
