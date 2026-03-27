"""
Direct Fire Module.

Calculates combat attrition and personnel losses.
Works with BaseEntity objects via get_attribute() API.
"""
import math
import random


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
        
        Args:
            attacker: BaseEntity with attributes (side, personnel, unit_type, etc.)
            target:   BaseEntity with attributes (side, personnel, unit_type, etc.)
            game_map: Optional Map object (for range checks)
            
        Returns:
            dict: {
                "hit": bool,
                "casualties": int (personnel lost),
                "suppression_dealt": int (amount of suppression added to target),
                "remaining": int (target's personnel after damage),
                "weapon": str (weapon name used),
                "attacker_id": str,
                "target_id": str,
            }
        """
        # Get configs via the data_controller if provided
        if data_controller:
            atk_config = data_controller.resolve_unit_config(attacker)
            tgt_config = data_controller.resolve_unit_config(target)
        else:
            # Fallback for tests that might not have a controller yet
            atk_config = attacker.attributes
            tgt_config = target.attributes
        
        weapon = atk_config["weapon"]
        target_personnel = int(target.get_attribute("personnel", tgt_config["personnel"]))
        
        # --- Range check (if map provided) ---
        if game_map:
            from engine.core.hex_math import HexMath
            atk_pos = game_map.get_entity_position(attacker.id)
            tgt_pos = game_map.get_entity_position(target.id)
            if atk_pos and tgt_pos:
                distance = HexMath.distance(atk_pos, tgt_pos)
                if isinstance(weapon, dict): w_max_range = weapon.get('max_range', 3)
                else: w_max_range = getattr(weapon, 'max_range', 3)

                if distance > w_max_range:
                    w_name = getattr(weapon, 'name', weapon.get('name', 'Weapon')) if not isinstance(weapon, dict) else weapon.get('name', 'Weapon')
                    return {
                        "hit": False,
                        "casualties": 0,
                        "suppression_dealt": 0,
                        "remaining": target_personnel,
                        "weapon": w_name,
                        "attacker_id": attacker.id,
                        "target_id": target.id,
                    }
                    
        # --- Cover Logic ---
        # Cover significantly mitigates personnel casualties, but the sheer volume of 
        # incoming fire will still heavily suppress the unit.
        cover_defense_bonus = 1.0
        if game_map and tgt_pos:
            target_terrain = game_map.get_terrain(tgt_pos)
            if target_terrain:
                # E.g., Trench might have a cost of 2.0 (representing 2x defense multiplier)
                cover_defense_bonus = max(1.0, float(target_terrain.get("cost", 1.0)))
        
        # Expected casualties = lethality * combat_factor_ratio / cover
        atk_factor = atk_config["combat_factor"]
        tgt_factor = tgt_config["combat_factor"]
        factor_ratio = atk_factor / max(tgt_factor, 1.0)
        
        # Support new modular 'lethality' attribute vs legacy 'damage * rof'
        if isinstance(weapon, dict):
            base_lethality = weapon.get('lethality') or (weapon.get('damage', 1) * weapon.get('rate_of_fire', 1))
            w_accuracy = weapon.get('accuracy', 0.5)
            base_suppression = weapon.get('suppression') or (weapon.get('damage', 1) * weapon.get('rate_of_fire', 1))
        else:
            base_lethality = getattr(weapon, 'lethality', getattr(weapon, 'damage', 1) * getattr(weapon, 'rate_of_fire', 1))
            w_accuracy = getattr(weapon, 'accuracy', 0.5)
            base_suppression = getattr(weapon, 'suppression', getattr(weapon, 'damage', 1) * getattr(weapon, 'rate_of_fire', 1))

        lethality = (base_lethality * w_accuracy * factor_ratio) / cover_defense_bonus
        suppression_power = base_suppression * factor_ratio
        
        # Poisson sample: lambda = lethality / 10
        lam = max(lethality / 10.0, 0.5)
        raw_casualties = self._poisson_sample(lam)
        
        # Suppression sample: Lambda usually translates to 10-40 suppression points
        supp_lam = max(suppression_power / 2.0, 5.0)
        raw_suppression = self._poisson_sample(supp_lam) * 10 
        
        # Clamp to target's remaining personnel
        final_casualties = min(raw_casualties, target_personnel)
        remaining = target_personnel - final_casualties
        
        return {
            "hit": final_casualties > 0 or raw_suppression > 0,
            "casualties": final_casualties,
            "suppression_dealt": raw_suppression,
            "remaining": remaining,
            "weapon": weapon.name,
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