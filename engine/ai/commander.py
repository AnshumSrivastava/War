"""
FILE: engine/ai/commander.py
ROLE: The "General" of the AI forces.

DESCRIPTION:
While the RL 'ActionModel' controls how a unit takes a single step, the StrategicCommander
determines the high-level objectives (e.g., "Attack that group of enemies", "Defend this bridge").
It assesses the physical map and assigns `AgentCommand` objects to autonomous units.
"""

import random
from engine.core.hex_math import Hex, HexMath
from engine.simulation.command import AgentCommand
from engine.core.pathfinding import Pathfinder
from engine.ai.commander_rl import CommanderRLAgent

# Global RL Instance for the commander
_commander_brain = CommanderRLAgent()

def get_commander_brain():
    return _commander_brain

def set_commander_model(path):
    global _commander_brain
    _commander_brain.load_model(path)

class StrategicCommander:
    """Evaluates the battlefield and issues macro-level orders to AI units."""
    
    @staticmethod
    def assign_mission(entity, global_state):
        """
        Assigns high-level objectives (Missions) to units based on their side and status.
        Unlike the Resolution Agent, the Commander does NOT calculate the exact path.
        """
        side = str(entity.get_attribute("side", "")).lower()
        my_pos = global_state.map.get_entity_position(entity.id)
        
        if not my_pos:
            return  # Unit is not on map

        # --- DEFENDER LOGIC ---
        if side == "defender":
            # Set Home Hex (where they were initially dropped)
            home = entity.get_attribute("home_hex")
            if not home:
                # Resilience: Ensure my_pos is a formal Hex before saving as attribute
                home_h = Hex(my_pos[0], my_pos[1], my_pos[2]) if isinstance(my_pos, (list, tuple)) else my_pos
                entity.set_attribute("home_hex", home_h)
                home = home_h
            else:
                # Resilience: attributes from JSON might be lists, convert back to Hex
                home = Hex(home[0], home[1], home[2]) if isinstance(home, (list, tuple)) else home
            
            # DEFAULT: Protect the Home area.
            # Only move if the commander decides a reinforcement is critical (Sequencing logic)
            entity.current_command = AgentCommand(
                "DEFEND",
                home,
                is_user_assigned=False,
                objective_type="HOLD_POST"
            )
            entity.current_command.domain_hex = home
            return

        # --- ATTACKER LOGIC ---
        # Find the most logical target area/enemy.
        target_tuple = StrategicCommander._find_best_offensive_target(my_pos, entity, global_state)
        
        if target_tuple:
            target_hex, is_goal = target_tuple
            # --- STRATEGIC RL CHOICE ---
            # Commander decides which 'Axis' (routing tactic) to use.
            pathfinder = Pathfinder(global_state.map)
            _, stats = StrategicCommander._generate_movement_axes(my_pos, target_hex, pathfinder, global_state, side)
            
            # Select axis using RL Brain
            axis_idx, state_idx = get_commander_brain().select_axis(stats, is_training=True)
            
            # Record decision for future learning (Trajectory support)
            if not hasattr(entity, "commander_trajectory"):
                entity.commander_trajectory = []
            entity.commander_trajectory.append((state_idx, axis_idx))

            # Resilience: converter back if find_best_offensive_target returned a list
            target_h = Hex(target_hex[0], target_hex[1], target_hex[2]) if isinstance(target_hex, (list, tuple)) else target_hex

            entity.current_command = AgentCommand(
                "CAPTURE" if is_goal else "MOVE",
                target_h,
                is_user_assigned=False,
                objective_type="REACH_TARGET",
                axis=axis_idx
            )
        else:
            # If no enemies are left, hold position but stay alert.
            entity.current_command = AgentCommand(
                "DEFEND",
                my_pos,
                is_user_assigned=False,
                objective_type="IDLE_PATROL"
            )

    @staticmethod
    def _generate_movement_axes(start_hex: Hex, target_hex: Hex, pathfinder: Pathfinder, state, faction: str):
        """
        Creates 3 different strategic routes to the objective:
        0: Direct (Standard terrain-only path)
        1: Safe (Heavy penalty for enemy line-of-fire)
        2: Fast (Ignores terrain penalties completely to find raw geometric shortest path)
        """
        axes = {}
        stats = {}
        
        # Helper to calculate threat
        def get_threat(h):
            if hasattr(state, "threat_map"):
                return state.threat_map.get_threat_for_faction(h, faction)
            return 0.0

        def direct_cost(h):
            t = state.map.get_terrain(h)
            return t.get("cost", 1.0) if t else float('inf')
            
        # Axis 0: DIRECT
        axes[0] = pathfinder.get_path(start_hex, target_hex, cost_fn=direct_cost)
        
        # Axis 1: SAFE
        def safe_cost(h):
            t = state.map.get_terrain(h)
            if not t: return float('inf')
            base = t.get("cost", 1.0)
            threat = get_threat(h)
            return base + (threat * 5.0) # Massive penalty for danger
        axes[1] = pathfinder.get_path(start_hex, target_hex, cost_fn=safe_cost)
        
        # Axis 2: FAST (Ignore terrain costs - assume flat 1.0, but still respect map bounds)
        axes[2] = pathfinder.get_path(start_hex, target_hex, cost_fn=lambda h: 1.0 if state.map.get_terrain(h) else float('inf'))
        
        # Calculate stats for the RL Agent
        for i in range(3):
            path = axes.get(i)
            if not path:
                # If a path isn't possible (e.g. walled in), heavily penalize its stats
                stats[i] = {"avg_threat": 99.0, "length": 99}
                continue
                
            total_threat = sum(get_threat(h) for h in path)
            avg_threat = total_threat / len(path) if len(path) > 0 else 0.0
            stats[i] = {"avg_threat": avg_threat, "length": len(path)}
            
        return axes, stats

    @staticmethod
    def _find_best_offensive_target(my_pos: Hex, entity, global_state) -> (Hex, bool):
        """Locates the optimal enemy or objective and returns the best firing position to engage them."""
        my_side = entity.get_attribute("side", "Neutral")
        
        # --- NEW GOAL AREA PRIORITIZATION ---
        goal_hexes = []
        zones = global_state.map.get_zones()
        for zone_id, zone in zones.items():
            if zone.get("type") == "Goal Area" and zone.get("side") != my_side:
                goal_hexes.extend(zone.get("hexes", []))
        
        target_pos = None
        is_goal = False
        if goal_hexes:
            # If there's a goal, target the closest hex of that goal
            goal_hexes.sort(key=lambda h: HexMath.distance(my_pos, h))
            target_pos = goal_hexes[0]
            is_goal = True
            # print(f"Commander prioritizing Goal Area at {target_pos}")
        else:
            # Fallback to closest enemy or defender "Home" logic
            best_fallback = None
            best_dist = float('inf')
            
            for other in global_state.entity_manager.get_all_entities():
                other_side = other.get_attribute("side", "Neutral")
                if other_side != my_side and other_side != "Neutral" and int(other.get_attribute("personnel", 0)) > 0:
                    # Prefer the defender's 'home_hex' if they have one (the "capture defenders hex" request)
                    other_pos = global_state.map.get_entity_position(other.id)
                    home_hex = other.get_attribute("home_hex")
                    
                    candidate = home_hex or other_pos
                    if candidate:
                        dist = HexMath.distance(my_pos, candidate)
                        if dist < best_dist:
                            best_dist = dist
                            best_fallback = candidate
                            
            if not best_fallback:
                return None, False
            target_pos = best_fallback
        
        # --- UNIT TYPE SPECIALIZATION ---
        u_type = entity.get_attribute("type", "")
        
        # Close Combat and Defenders go directly to the target/goal
        if u_type in ["CloseCombatAgent", "DefenderAgent"] or is_goal:
            if u_type == "FiringAgent" and is_goal:
                # Firing Agent targeting a goal should still maintain distance
                pass 
            else:
                return target_pos, is_goal
        
        # --- OPTIMAL POSITION LOGIC (Firing Agents / Others) ---
        # Find the closest hex that is EXACTLY at our intended engagement range
        fire_range = int(entity.get_attribute("fire_range", 0))
        if fire_range <= 0:
            if u_type == "FiringAgent": fire_range = 6
            else: fire_range = 3
        
        # If we are already at or near range, and can see/fire, stay put? 
        # For now, let's just find the best hex on the ring.
        firing_ring = StrategicCommander._get_hex_ring(target_pos, fire_range)
        
        candidates = []
        for candidate_hex in firing_ring:
            # Check if this hex is a valid, passable terrain piece on our map
            if global_state.map.get_terrain(candidate_hex):
                travel_dist = HexMath.distance(my_pos, candidate_hex)
                candidates.append((travel_dist, candidate_hex))
        
        if not candidates or is_goal:
            # For Goals, we want to go DIRECTLY to the hex.
            # For others, if no firing ring exists, move directly.
            return target_pos, is_goal
            
        # Sort by travel distance and pick one of the top 3 randomly to prevent clustering
        candidates.sort(key=lambda x: x[0])
        top_n = candidates[:3]
        return random.choice(top_n)[1], is_goal

    @staticmethod
    def _get_hex_ring(center: Hex, radius: int) -> list:
        """Returns all hexes exactly `radius` distance from the center hex."""
        results = []
        if radius <= 0:
            return [center]
            
        # Start at a known hex on the radius (one step left, then radius steps down-left)
        # Or more simply using our flat-top directions: Start by moving direction 4 (SW) 'radius' times
        hex_idx = center
        for _ in range(radius):
            hex_idx = HexMath.neighbor(hex_idx, 4)
            
        # Then walk the ring: 6 sides, each `radius` hexes long
        for i in range(6):
            for j in range(radius):
                results.append(hex_idx)
                # To trace the perimeter, we must walk in the 'next' direction
                hex_idx = HexMath.neighbor(hex_idx, i)
                
        return results
