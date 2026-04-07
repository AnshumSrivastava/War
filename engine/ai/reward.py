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
        # We will use the config loader if available, otherwise fallback to these
        from engine.ai.config_loader import ConfigLoader

        
        # --- REWARD SYSTEM ---
        rl_conf = ConfigLoader.get("rl_config", "rewards", {})
        
        self.REWARD_EVASION_SUCCESS = rl_conf.get("evasion_success", 5.0)
        self.REWARD_CLOSING = rl_conf.get("closing", 30.0)
        self.REWARD_GOAL_COMPLETED = rl_conf.get("goal_reached", 400.0)
        self.REWARD_ACTION_INCENTIVE = 0.0
        
        # --- FIRE REWARDS (tunable via config/rl_config.json) ---
        self.FIRE_HIT_REWARD   = rl_conf.get("fire_hit", 120.0)
        self.FIRE_KILL_REWARD  = rl_conf.get("fire_kill", 400.0)
        self.FIRE_DAMAGE_MULT  = rl_conf.get("fire_damage_mult", 10.0)
        self.FIRE_MISS_PENALTY = rl_conf.get("fire_miss", -5.0)
        
        # --- PENALTY SYSTEM ---
        self.PENALTY_UNIT_LOST = rl_conf.get("eliminated", -400.0)
        self.PENALTY_DAMAGE_TAKEN = rl_conf.get("damage_taken", -2.0)
        self.PENALTY_PER_STEP = rl_conf.get("step_penalty", -1.0)
        self.PENALTY_RETREATING = rl_conf.get("retreat_penalty", -40.0)
        self.PENALTY_REVISITING_HEX = rl_conf.get("revisit_penalty", -10.0)

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
                    reward += abs(command_dist_delta) * self.REWARD_CLOSING * 1.5 
                elif command_dist_delta > 0:
                    reward -= abs(command_dist_delta) * self.REWARD_CLOSING * 1.5 

                # Target reached - REMOVED the "Hold / End Turn" restriction so they get rewarded purely for arriving
                if command_dist == 0:
                    reward += decayed_goal_reward 

            # --- CAPTURING A ZONE ---
            elif cmd.command_type == "CAPTURE":
                if command_dist_delta < 0:
                    reward += self.REWARD_CLOSING
                if command_dist == 0:
                    reward += decayed_goal_reward * 1.5

            # --- DEFENDING A POSITION ---
            elif cmd.command_type == "DEFEND":
                obj_type = getattr(cmd, "objective_type", "DEFAULT")
                
                if obj_type == "HOLD_POST":
                    dist_to_home = command_dist
                    if dist_to_home == 0:
                        reward += 50.0
                        if action_type == "FIRE":
                            reward += 40.0
                    else:
                        reward -= dist_to_home * 10.0
                
                elif obj_type == "IDLE_PATROL":
                    if command_dist > 1 and command_dist_delta < 0:
                        reward += self.REWARD_CLOSING
                    elif command_dist <= 1 and action_type == "FIRE":
                        reward += 30.0
                    elif command_dist == 0:
                        reward += decayed_goal_reward

        # 4. COMBAT: Did the unit engage an enemy?
        if action_type == "FIRE" and combat_result:
            casualties = combat_result.get("casualties", 0)
            remaining = combat_result.get("remaining", 1)

            # Pull from config (set in config/rl_config.json) via RewardModel.__init__
            FIRE_HIT_REWARD   = getattr(self, 'FIRE_HIT_REWARD', 120.0)
            FIRE_DAMAGE_MULT  = getattr(self, 'FIRE_DAMAGE_MULT', 10.0)
            FIRE_MISS_PENALTY = getattr(self, 'FIRE_MISS_PENALTY', -5.0)
            FIRE_KILL_REWARD  = getattr(self, 'FIRE_KILL_REWARD', 400.0)

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
