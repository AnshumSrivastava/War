"""
Direct Fire Module.

Calculates combat attrition and personnel losses.
Works with BaseEntity objects via get_attribute() API.
"""
import math
import random
from engine.core.hex_math import HexMath


class DirectFire:
    """
    Computes combat attrition between two BaseEntity agents.
    
    Uses weapon lethality (damage * rate_of_fire * accuracy) to derive an
    expected casualty rate, then samples from a Poisson distribution.
    Returns a result dict — the caller is responsible for applying damage.
    """

    def calculate_attrition(self, attacker, target, game_map=None, data_controller=None):
        """
        Calculate attrition from attacker firing on target.
        """
        # 1. CONFIG RESOLUTION
        if data_controller:
            atk_config = data_controller.resolve_unit_config(attacker)
            tgt_config = data_controller.resolve_unit_config(target)
        else:
            atk_config = getattr(attacker, 'attributes', {})
            tgt_config = getattr(target, 'attributes', {})
        
        # 2. WEAPON RESOLUTION
        # weapon can be a string ID, a dict, or a specialized weapon object
        weapon_val = atk_config.get("weapon", "Standard")
        weapon_name = "Tactical Weapon"
        w_max_range = 3
        base_lethality = 10
        base_suppression = 10
        w_accuracy = 0.5

        if isinstance(weapon_val, dict):
            weapon_name = weapon_val.get("name", "Custom Weapon")
            w_max_range = int(weapon_val.get("max_range", 3))
            base_lethality = float(weapon_val.get("lethality") or (weapon_val.get("damage", 1) * weapon_val.get("rate_of_fire", 1)))
            w_accuracy = float(weapon_val.get("accuracy", 0.5))
            base_suppression = float(weapon_val.get("suppression") or base_lethality)
        elif isinstance(weapon_val, str) and data_controller:
            # Look up in catalog
            catalog = getattr(data_controller, 'weapons', {})
            w_info = catalog.get(weapon_val, {})
            if w_info:
                weapon_name = w_info.get("name", weapon_val)
                w_max_range = int(w_info.get("max_range", 3))
                base_lethality = float(w_info.get("lethality") or (w_info.get("damage", 1) * w_info.get("rate_of_fire", 1)))
                w_accuracy = float(w_info.get("accuracy", 0.5))
                base_suppression = float(w_info.get("suppression") or base_lethality)
        
        target_personnel = int(target.get_attribute("personnel", tgt_config.get("personnel", 10)))
        
        # 3. RANGE CHECK
        if game_map:
            atk_pos = game_map.get_entity_position(attacker.id)
            tgt_pos = game_map.get_entity_position(target.id)
            if atk_pos and tgt_pos:
                distance = HexMath.distance(atk_pos, tgt_pos)
                if distance > w_max_range:
                    return {
                        "hit": False, "casualties": 0, "suppression_dealt": 0,
                        "remaining": target_personnel, "weapon": weapon_name,
                        "attacker_id": attacker.id, "target_id": target.id,
                    }
                    
        # 4. COVER & DEFENSE
        cover_defense_bonus = 1.0
        if game_map and 'tgt_pos' in locals() and tgt_pos:
            target_terrain = game_map.get_terrain(tgt_pos)
            if target_terrain:
                # Use get_attribute for terrain objects to be safe
                if hasattr(target_terrain, 'get_attribute'):
                    cover_defense_bonus = max(1.0, float(target_terrain.get_attribute("cost", 1.0)))
                elif isinstance(target_terrain, dict):
                    cover_defense_bonus = max(1.0, float(target_terrain.get("cost", 1.0)))
        
        # 5. ATTRITION MATH
        atk_factor = float(atk_config.get("combat_factor", 1.0))
        tgt_factor = float(tgt_config.get("combat_factor", 1.0))
        factor_ratio = atk_factor / max(tgt_factor, 1.0)
        
        lethality = (base_lethality * w_accuracy * factor_ratio) / cover_defense_bonus
        suppression_power = base_suppression * factor_ratio
        
        # Poisson sample: lambda = lethality / 10
        lam = max(lethality / 10.0, 0.5)
        raw_casualties = self._poisson_sample(lam)
        
        # Suppression sample
        supp_lam = max(suppression_power / 2.0, 5.0)
        raw_suppression = self._poisson_sample(supp_lam) * 10 
        
        final_casualties = min(raw_casualties, target_personnel)
        remaining = target_personnel - final_casualties
        
        return {
            "hit": final_casualties > 0 or raw_suppression > 0,
            "casualties": final_casualties,
            "suppression_dealt": raw_suppression,
            "remaining": remaining,
            "weapon": weapon_name,
            "attacker_id": attacker.id,
            "target_id": target.id,
        }

    @staticmethod
    def _poisson_sample(lam):
        """Sample from Poisson distribution using Knuth's algorithm."""
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1