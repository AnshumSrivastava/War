"""
FILE: engine/action/commit.py
ROLE: The "Specialist" or "Reinforcement" logic.

DESCRIPTION:
In this game, some units start as 'ReserveAgents'. These are units that haven't 
yet chosen their specialty.
This file handles the 'COMMIT' action, which allows a Reserve unit to 
permanently transition into a specific role:
- FIRE: Becomes a FireAgent (Combat specialist).
- MOVE: Becomes a MoveAgent (Fast-moving specialist).

This is a one-time change that updates the unit's stats and capabilities mid-battle.
"""
from .base_action import BaseAction # Import the template for all actions.

class CommitAction(BaseAction):
    """
    Handles the 'COMMIT' command, turning recruiters into specialists.
    """
    def __init__(self):
        # Call the constructor of the BaseAction class.
        # We name this tool "COMMIT" so the AI Brain can find and use it.
        super().__init__("COMMIT", "Commit Reserve")

    def is_allowed(self, entity, game_map, target=None) -> bool:
        """
        ROLE CHECK: Can this unit actually specialize?
        """
        # The action is only allowed if the entity's 'type' attribute is "ReserveAgent".
        # If they are already a FireAgent or MoveAgent, they can't change again!
        return entity.get_attribute("type") == "ReserveAgent"

    def execute(self, entity, game_map, role=None, **kwargs):
        """
        THE SPECIALIZATION PROCESS: 
        Permanently transforms a general unit into a specialist.
        """
        # 1. VALIDATION: A unit can choose to become a "FIRE" combatant or a "MOVE" scout.
        if role not in ["FIRE", "MOVE"]:
            return "COMMIT FAILED (Invalid Role)", None, None
            
        # 2. ASSIGN NEW JOB: Change the 'Type' of the unit forever.
        # Determine the new unit type based on the chosen role.
        new_type = "FireAgent" if role == "FIRE" else "MoveAgent"
        # Update the unit's internal record.
        entity.set_attribute("type", new_type)
        
        # 3. ASSIGN NEW GEAR: Give them specialized equipment (Weaponry or Speed).
        if new_type == "FireAgent":
             # FireAgents are "Direct" combatants (High damage).
             entity.set_attribute("subtype", "Direct")
        else:
             # MoveAgents are "Fast" scouts (High speed).
             entity.set_attribute("subtype", "Fast")
             
        # 4. TEXT REPORT: A simple message for the dashboard log.
        desc = f"COMMIT -> {new_type}"
        
        # 5. VISUAL EVENT: Inform the screen so it can show a 'Level Up' effect.
        event = {
            "type": "commit", 
            "hex": game_map.get_entity_position(entity.id), 
            "role": new_type 
        }
        return desc, event, None
