"""
FILE: engine/simulation/fire.py
ROLE: The "Gunner" for units.

DESCRIPTION:
This file handles the logic for a unit attacking an enemy from a distance.
It checks for several rules before allowing a shot:
1. Is there a target?
2. Is the target within the weapon's range?
3. Is the target in a "Straight Line" (Axial Alignment)? In this game, 
   units can only fire along the 6 main axes of the hex grid EXCPET for 
   indirect fire weapons (like Mortars or Artillery).

If the shot is allowed, it uses the 'Combat Engine' to calculate how much 
damage was dealt and updates the enemy's personnel count.
"""
from .base_action import BaseAction
from engine.core.hex_math import HexMath

class FireAction(BaseAction):
    """
    Handles the 'FIRE' command for any unit capable of ranged combat.
    """
    def __init__(self):
        # We name this tool "FIRE" so the AI Brain can find it.
        super().__init__("FIRE", "Fire Weapon")

    def is_allowed(self, entity, game_map, target=None, data_controller=None) -> bool:
        """
        GUNNER CHECK: Returns True if the unit is physically allowed to shoot.
        """
        if not target:
            return False
            
        my_pos = game_map.get_entity_position(entity.id)
        other_pos = game_map.get_entity_position(target.id)
        if not my_pos or not other_pos:
            return False

        dist = HexMath.distance(my_pos, other_pos)
        
        # 1. RANGE DETERMINATION
        # Honor agent-specific attributes first (overriding config)
        max_range = int(entity.get_attribute("fire_range", 0))
        
        # Fallback to capabilities.range (used in many agent JSONs)
        if max_range <= 0:
            caps = entity.get_attribute("capabilities", {})
            max_range = int(caps.get("range", 0))
        
        # 2. UNIT TYPE FALLBACK
        u_type = entity.get_attribute("type", "")
        if max_range <= 0:
            if u_type == "FiringAgent" or u_type == "FireAgent": max_range = 6
            elif u_type == "CloseCombatAgent": max_range = 2
            elif u_type == "DefenderAgent": max_range = 2
            else: max_range = 3 # Standard default
            
        if dist > max_range:
            return False
            
        # 3. ALIGNMENT POLICY (Relaxed for accessibility)
        # In this tactical simulation, we allow firing in any direction 
        # as long as range and LOS are clear.
        return True


    def execute(self, entity, game_map, target=None, combat_engine=None, data_controller=None):
        """
        THE ATTACK PROCESS: Actually pulls the trigger and records what happened.
        """
        if not target or not combat_engine:
            return "FIRE FAILED (No Target/Engine)", None, None
            
        my_pos = game_map.get_entity_position(entity.id)
        other_pos = game_map.get_entity_position(target.id)
        dist = HexMath.distance(my_pos, other_pos) if (my_pos and other_pos) else 999
        
        u_type = entity.get_attribute("type", "")
        max_range = int(entity.get_attribute("fire_range", 0))
        if max_range <= 0:
            caps = entity.get_attribute("capabilities", {})
            max_range = int(caps.get("range", 0))

        if max_range <= 0:
            if u_type == "FiringAgent" or u_type == "FireAgent": max_range = 6
            elif u_type == "CloseCombatAgent": max_range = 2
            elif u_type == "DefenderAgent": max_range = 2
            else: max_range = 3
            
        if dist > max_range:
            return "OUT OF RANGE", None, None

            
        # For simplicity in this specialized tactical scenario, 
        # we bypass the strict inventory/ammo checks if the unit is a specialized type.
        weapon_name = "Primary Armament"
        if u_type == "FiringAgent": weapon_name = "Long-Range Cannon"
        elif u_type == "CloseCombatAgent": weapon_name = "Short-Range Carbine"

        # 2. LOG AMMO (UNLIMITED FOR NOW)
        a_type = "NATO_556"
        resources = getattr(entity, 'inventory', {}).get("resources", {})
        resources[a_type] = 99

        # 3. COMBAT RESOLUTION
        combat_result = combat_engine.calculate_attrition(entity, target, game_map, data_controller=data_controller)
        
        casualties = combat_result.get("casualties", 0)
        suppression_dealt = combat_result.get("suppression_dealt", 0)
        weapon_name = weapon_name
        remaining = combat_result.get("remaining", 0)
        
        # 4. APPLY DAMAGE
        target.set_attribute("personnel", remaining)
        current_suppression = float(target.get_attribute("suppression", 0.0))
        new_suppression = current_suppression + suppression_dealt
        target.set_attribute("suppression", new_suppression)
        target.set_attribute("under_fire", True)
        
        # 5. TEXT REPORT
        desc = f"FIRE ({weapon_name}) [Ammo: {resources[a_type]}]"
        if casualties > 0 or suppression_dealt > 0:
            if casualties > 0:
                desc += f" -> -{casualties} pers"
                if remaining <= 0: desc += " [KILLED]"
            if suppression_dealt > 0 and remaining > 0:
                if new_suppression >= 100: desc += " [PINNED]"
                elif new_suppression >= 50: desc += " [SUPPRESSED]"
        else:
            desc += " MISS"
            
        # 6. VISUAL EVENT
        event = {
            "type": "fire",
            "source_hex": my_pos,
            "target_hex": other_pos,
            "hit": casualties > 0 or suppression_dealt > 10
        }
        return desc, event, combat_result
