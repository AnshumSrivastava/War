"""
FILE: engine/ai/reward.py
ROLE: The "Incentive Coach" for the AI.

DESCRIPTION:
AI learns by getting 'Points' (Rewards) when it does something good and 'Penalties' 
when it does something bad. This file defines the 'Rulebook' for those points.

Examples:
- If a unit shoots and hits an enemy: Positive reward.
- If a unit moves closer to its mission goal: Positive reward.
- If a unit sustains personnel losses: Negative reward.
- If a unit remains idle: Step penalty.

By changing these numbers, we can change the personality of the AI (e.g., making 
it more aggressive or more cautious).
"""

class RewardModel:
    """
    This class is the "Judge". It evaluates everything a unit does and gives 
    it a Score (Reward) or takes points away (Penalty).
    """
    
    def __init__(self):
        # --- REWARD SYSTEM ---
        # NOTE: Fire hit/kill rewards are hardcoded constants in calculate_reward()
        # (150 per hit, 400 for elimination) rather than instance attributes, to keep
        # them close to the logic that uses them.
        self.REWARD_EVASION_SUCCESS = 5.0  # Moving while under fire.
        self.REWARD_CLOSING = 15.0         # Moving toward objective or enemy.
        self.REWARD_GOAL_COMPLETED = 400   # Arriving at a strategic objective.
        self.REWARD_ACTION_INCENTIVE = 0.0 # DISABLED: Don't reward jitter.
        
        # --- PENALTY SYSTEM ---
        self.PENALTY_UNIT_LOST = -400    # Normalized to match goal.
        self.PENALTY_DAMAGE_TAKEN = -2   # Reduced penalty.
        self.PENALTY_PER_STEP = -1.0     # Reduced step penalty.
        self.PENALTY_RETREATING = -20.0  # Heavy penalty for moving away.
        self.PENALTY_REVISITING_HEX = -10.0 # Discourage circular movement.

    def calculate_reward(self, entity, action_type, combat_result=None, previous_personnel=None, distance_delta=0, command_dist_delta=0, command_dist=float('inf'), terrain_cost=0.0, step_number=1, max_steps=50, is_revisit=False):
        """
        THE JUDGMENT: Takes everything that happened in the last 'step' and 
        returns the total score earned.
        """
        reward = 0.0
        
        # 1. THE CLOCK: Every second the unit spends alive, it loses a tiny bit 
        # of score. This forces the AI to be efficient and finish fast.
        # [REMOVED: Handled in act_model.py once per tick]
        
        # 2. TERRAIN: Moving over rough terrain like mud or mountains 'costs' points.
        if action_type == "MOVE":
            reward -= terrain_cost
            
        cmd = getattr(entity, 'current_command', None)

        # 3. MISSION OBJECTIVES: Is the unit following orders?
        if cmd:
            # We decay the mission reward over time. The longer you take, 
            # the fewer points the objective is worth.
            decay_multiplier = max(0.1, 1.0 - (step_number / max(1, max_steps)))
            decayed_goal_reward = self.REWARD_GOAL_COMPLETED * decay_multiplier
            
            # --- MOVING TO A HEX ---
            if cmd.command_type == "MOVE":
                if command_dist_delta < 0:
                    reward += abs(command_dist_delta) * self.REWARD_CLOSING * 1.5 # Normalized bonus
                elif command_dist_delta > 0:
                    reward -= abs(command_dist_delta) * self.REWARD_CLOSING * 1.5 # Normalized penalty

                # Massive bonus for actually arriving at the target hex!
                if command_dist == 0 and action_type == "HOLD / END TURN":
                    reward += decayed_goal_reward 

            # --- CAPTURING A ZONE ---
            elif cmd.command_type == "CAPTURE":
                if command_dist_delta < 0:
                    reward += self.REWARD_CLOSING
                if command_dist == 0 and action_type == "HOLD / END TURN":
                    reward += decayed_goal_reward * 1.5

            # --- DEFENDING A POSITION ---
            elif cmd.command_type == "DEFEND":
                obj_type = getattr(cmd, "objective_type", "DEFAULT")
                
                if obj_type == "HOLD_POST":
                    # Defenders should stay at their domain_hex (Home)
                    dist_to_home = command_dist # target_hex is home in HOLD_POST
                    if dist_to_home == 0:
                        reward += 50.0 # INCREASED: Bonus for staying strictly on post
                        if action_type == "FIRE":
                            reward += 40.0 # "Firing from cover/post" bonus
                    else:
                        # Penalty for being off-post without a specific MOVE order
                        reward -= dist_to_home * 10.0 # Reduced: Don't paralyze defenders.
                
                elif obj_type == "IDLE_PATROL":
                    if command_dist > 1 and command_dist_delta < 0:
                        reward += self.REWARD_CLOSING # Get back to patrol area
                    elif command_dist <= 1 and action_type == "FIRE":
                        reward += 30.0 # INCREASED: "Holding the Line" bonus
                    elif command_dist == 0 and action_type == "HOLD / END TURN":
                        reward += decayed_goal_reward # Successfully reached defense post

        # 4. COMBAT: Did the unit engage an enemy?
        if action_type == "FIRE" and combat_result:
            casualties = combat_result.get("casualties", 0)
            remaining = combat_result.get("remaining", 1)

            FIRE_HIT_REWARD  = 50   # Normalized reward (was 150)
            FIRE_DAMAGE_MULT = 10   # Per-casualty multiplier (was 20)
            FIRE_MISS_PENALTY = -5  # Penalty for a miss
            FIRE_KILL_REWARD  = 150  # Bonus for full elimination (was 400)

            if casualties > 0:
                reward += FIRE_HIT_REWARD + casualties * FIRE_DAMAGE_MULT
            else:
                reward += FIRE_MISS_PENALTY

            if remaining <= 0:
                reward += FIRE_KILL_REWARD

        # 5. MOVEMENT: Reward for aggression and evasion.
        elif action_type == "MOVE":
            # Reward for closing the gap to the nearest enemy.
            if distance_delta < 0:
                reward += self.REWARD_CLOSING
            elif distance_delta > 0:
                reward += self.PENALTY_RETREATING # Penality for running away
            
            # Bonus for moving safely through danger (being shot at).
            if entity.get_attribute("under_fire", False):
                reward += self.REWARD_EVASION_SUCCESS

        # 6. SURVIVAL: Penalize personnel losses.
        if previous_personnel is not None:
            current_personnel = int(entity.get_attribute("personnel", 0))
            if previous_personnel > current_personnel:
                # Calculate exactly how many personnel were lost.
                lost = previous_personnel - current_personnel
                reward += (lost * self.PENALTY_DAMAGE_TAKEN)
                
            # If personnel count reaches zero, the unit is destroyed.
            if previous_personnel > 0 and current_personnel <= 0:
                reward += self.PENALTY_UNIT_LOST

        if is_revisit:
            reward += self.PENALTY_REVISITING_HEX

        if action_type != "HOLD / END TURN" and self.REWARD_ACTION_INCENTIVE != 0:
            reward += self.REWARD_ACTION_INCENTIVE

        return reward
