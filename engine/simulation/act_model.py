"""
FILE: engine/simulation/act_model.py
ROLE: The "Brain" and "Clock" of the game simulation.

DESCRIPTION:
This is the most important file in the engine (The Controller). 
It runs the "Sense-Decide-Act" loop for every unit on the map. 
Every time the game takes a 'step' or 'tick' forward:
1. SENSE: Every unit looks around to see if any enemies are nearby (Vision).
2. DECIDE: Units use an AI 'Brain' (Q-Table) to choose an action.
3. ACT: Units actually move or shoot on the hexagonal map.
4. LEARN: After seeing the result, units remember if that was a good choice.

This file bridges the gap between the static Map/Units and the AI Learning brain.
"""
import random
import datetime
from typing import Optional, List, Callable
from PyQt5.QtCore import QCoreApplication

from engine.core.hex_math import Hex, HexMath, DIRECTION_MAP
from engine.core.map import Map
from engine.core.entity_manager import EntityManager

from engine.core.pathfinding import Pathfinder
from engine.data.definitions.constants import RL_ACTION_MAP, NUM_RL_ACTIONS
from engine.combat.direct_fire import DirectFire
from engine.ai.encoder import StateActionEncoder
from engine.ai.q_table import QTableManager
from engine.ai.reward import RewardModel
from engine.ai.replay_buffer import ReplayBuffer
from engine.core.logger import CombatLogger

# Modular Systems
import json
import os
from engine.simulation.fire import FireAction
from engine.simulation.move import MoveAction
from engine.simulation.close_combat import CloseCombatAction
from engine.simulation.commit import CommitAction
from engine.ai.commander import get_commander_brain


# DIRECTION_MAP is imported from engine.core.hex_math above — single canonical source.


class ActionModel:
    """
    The Simulation Controller. 
    It coordinates how every unit on the map thinks and behaves during a turn.
    """
    
    def __init__(self, state):
        # WORKSPACE: We store a reference to the 'GlobalState' which holds the map and units.
        # This is like the unit's "Briefing Folder" for the current mission.
        self.state = state
        self.map = state.map
        self.entity_manager = state.entity_manager

        # MISSION TIMING: How many minutes pass in the game world for every real-world 'click'.
        # Default is 10 minutes per step.
        self.time_per_step = getattr(state, 'time_per_step', 10)
        
        # WEAPONS EXPERT: This handles the mathematical 'dice rolls' for shooting and damage.
        self.fire_engine = DirectFire()
        
        # ABILITY KIT: All the different things units can do (FIRE, MOVE, MELEE, COMMIT).
        self.actions = {
            "FIRE": FireAction(),
            "MOVE": MoveAction(),
            "CLOSE_COMBAT": CloseCombatAction(),
            "COMMIT": CommitAction()
        }
        
        # SENSORY TRANSLATOR: This translates a unit's complex situation (Where am I? Who's near?)
        # into a simple set of numbers that the AI 'Brain' can process.
        rows = max(self.map.height, 10)
        cols = max(self.map.width, 10)
        self.encoder = StateActionEncoder(rows=rows, cols=cols)
        
        # --- THE TWO BRAINS ---
        # 1. Ephemeral (The Explorer): 
        #    This brain starts empty every session. It is used by units that are 
        #    actively learning and trying out new, unpredictable tactics.
        self.q_manager_ephemeral = QTableManager(
            state_size=self.encoder.state_size,
            action_size=NUM_RL_ACTIONS
        )
        self.q_manager_ephemeral.epsilon = 1.0 # 1.0 means 'always try something random'
        self.q_manager_ephemeral.load_q_table("data/models/ephemeral_q_table.npy")
        
        # 2. Persistent (The Veteran): 
        #    This brain loads previously saved knowledge from a file. 
        #    It is used by units that should behave like 'Hard' difficulty AI.
        self.q_manager_persistent = QTableManager(
            state_size=self.encoder.state_size,
            action_size=NUM_RL_ACTIONS
        )
        self.q_manager_persistent.load_q_table("data/models/q_table.npy")
        self.q_manager_persistent.epsilon = 0.01 # 0.01 means 'almost always use your experience'
        
        # BRAIN TRANSITION: 'Decay' makes the 'Explorer' brain slowly become a 'Veteran' brain over time.
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995 
        
        # We start with the Explorer brain by default.
        self.q_manager = self.q_manager_ephemeral
        
        # INSTRUCTOR: The 'Teacher'. It gives + points for good moves and - points for mistakes.
        self.reward_engine = RewardModel()
            
        # Helper for accurate terrain cost lookup (Risk-Aware)
        def get_true_cost(h: Hex, querying_faction: str = None) -> float:
            attrs = self.state.data_controller.get_hex_full_attributes(h, self.map)
            base_cost = float(attrs.get("cost", 1.0))
            
            # Add threat penalty. 2.0 extra tokens per enemy line-of-fire.
            threat_penalty = 0.0
            if querying_faction and hasattr(self.state, 'threat_map'):
                threat = self.state.threat_map.get_threat_for_faction(h, querying_faction)
                threat_penalty = threat * 2.0
                
            return base_cost + threat_penalty
            
        self.pathfinder = Pathfinder(self.map)
        
        # TRACKER: How many 'Score Points' each unit has earned in the current round.
        self.episode_rewards = {}   # unit_id -> total points
        self.episode_count = 0
        
        # ANALYTICS: Counts for the 'Dashboard' graphs in the UI.
        self.stats = {
            "actions": {},  # Counts how many times units chose to FIRE vs MOVE
            "modes": {"Exploit": 0, "Explore": 0} # Tracks if AI is using experience or guessing
        }
        
        # THINK TANK: Stores the internal thoughts of the AI for us to see in the Inspector.
        self.agent_debug_info = {} 
        
        # RECORD BOOK: A list of text descriptions of what's happening (e.g., "Unit A fired at Unit B").
        self.event_log = [] 
        
        # TACTICAL LOGGER: Persistent file-based logging for AAR and analysis.
        self.logger = CombatLogger()
        
        # EXPERIENCE REPLAY: Buffer for batch learning.
        self.replay_buffer = ReplayBuffer(capacity=5000)
        self.batch_size = 32

    
    # ------------------------------------------------------------------
    # PUBLIC: Called by MainWindow
    # ------------------------------------------------------------------
    
    def reinit_models(self):
        """Refreshes sub-systems that depend on map dimensions (Encoder, Pathfinder)."""
        # Re-sync references in case GlobalState replaced the objects
        self.map = self.state.map
        self.entity_manager = self.state.entity_manager
        
        rows = max(self.map.height, 10)
        cols = max(self.map.width, 10)
        self.encoder = StateActionEncoder(rows=rows, cols=cols)
        self.pathfinder = Pathfinder(self.map)
        print(f"ActionModel: Re-initialized models for map size {cols}x{rows}")

    def step_all_agents(self, step_number: int = 1, log_func: Optional[Callable] = None, table_mode: bool = True, episode_number: int = 1, max_steps: int = 50):
        """
        THE SIMULATION STEP: This function runs one 'Tick' of the game for every unit at once.
        It is called repeatedly by the Main Window when you press 'Play'.
        """
        events = []
        # Get a list of every single unit currently on the map.
        entities = self.entity_manager.get_all_entities()
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # TIME TALLY: Calculate how much 'Game Time' has passed (e.g., "10m", "20m").
        elapsed_minutes = step_number * self.time_per_step
        sim_time_str = f"{elapsed_minutes}m"

        # TACTICAL AWARENESS: Update the danger zones based on current enemy positions.
        if hasattr(self.state, 'threat_map'):
            self.state.threat_map.update(self.entity_manager, self.map, data_controller=self.state.data_controller)

        # REPORT ASSEMBLY: We collect info here to show a nice organized table in the 'Event Log'.
        step_data = [] 
        
        for entity in entities:
            # Initialize variables to avoid UnboundLocalError
            new_pos = None
            my_pos = None
            target = None
            terrain_cost = 0.0
            action_cost = 0.0
            
            # Yield to Qt event loop to prevent UI hangs on heavy computation
            QCoreApplication.processEvents()
            
            # 1. READINESS: Get the unit's configuration (how much personnel they should have).
            config = self.state.data_controller.resolve_unit_config(entity)
            
            if entity.get_attribute("personnel") is None:
                entity.set_attribute("personnel", config.get("personnel", 100))
            
            # --- SUPPRESSION TICK & DECAY ---
            # Suppression naturally decays over time if units aren't actively being shot at.
            current_supp = float(entity.get_attribute("suppression", 0.0))
            decay_rate = 20.0  # Lose 20 suppression points per turn naturally
            new_supp = max(0.0, current_supp - decay_rate)
            entity.set_attribute("suppression", new_supp)
            
            # --- TOKEN SYSTEM ---
            if getattr(entity, 'tokens', None) is None:
                # Enforce speed limit of 2 hexes per simulation step
                speed = 2.0
                
                # Apply Suppression Penalties to Token Generation
                if new_supp >= 100:
                    # PINNED: Unit cannot move or fire. It skips its turn.
                    entity.set_attribute("tokens", 0.0)
                    entity.tokens = 0.0
                elif new_supp >= 50:
                    # SUPPRESSED: Unit only receives half its usual action tokens.
                    # It can move slowly OR fire, but not both.
                    entity.set_attribute("tokens", speed / 2.0)
                    entity.tokens = speed / 2.0
                else:
                    # NORMAL
                    entity.set_attribute("tokens", speed)
                    entity.tokens = speed

        # --- SIMULATION LOOP ---
        # Agents take actions as long as they have remaining tokens.
        while True:
            active_entities = [e for e in entities if int(e.get_attribute("personnel", 0)) > 0 and getattr(e, 'tokens', 0) > 0]
            if not active_entities:
                break
                
            for entity in active_entities:
                # --- INITIALIZE SCRATCHPAD ---
                # These must be reset for every agent to avoid UnboundLocalError
                evt = None
                action_desc = "HOLD / END TURN"
                combat_result = None
                reward = 0.0
                thinking = {"mode": "Hold", "epsilon": 0.0, "q_values": {}}
                action_cost = 0.0
                terrain_cost = 0.0
                think_str = "HOLDING"
                
                config = self.state.data_controller.resolve_unit_config(entity)
            
                # 3. STATUS: If a unit's personnel count is 0, they are out of combat.
                personnel = int(entity.get_attribute("personnel", 100))
                if personnel <= 0 or entity.tokens <= 0:
                    continue
    
                # 4. LOCATION: If we can't find where the unit is on the map, skip their turn.
                my_pos = self.map.get_entity_position(entity.id)
                if my_pos is None: continue
                
                prev_personnel = personnel
                
                if entity.id not in self.episode_rewards:
                    self.episode_rewards[entity.id] = 0.0

                # Apply step penalty once per agent per simulation tick.
                tick_penalty_key = f"tick_penalty_{step_number}"
                if not getattr(entity, tick_penalty_key, False):
                    self.episode_rewards[entity.id] += self.reward_engine.PENALTY_PER_STEP
                    setattr(entity, tick_penalty_key, True)
                
                # --- PHASE 0: PREPARE ---
                my_pos = self.map.get_entity_position(entity.id)
                
                # --- PHASE 1: SENSE ---
                # Eyesight: The unit looks around to see if any enemies are within its 'Vision Range'.
                target = self._find_target(entity)
                config = self.state.data_controller.resolve_unit_config(entity)
                
                # --- PHASE 2: COMMAND (Orders) ---
                # If it's the very first 10 minutes (Step 0) of the game, give units their basic missions.
                from engine.simulation.command import AgentCommand
                from engine.ai.commander import StrategicCommander
                
                # 🚀 BEHAVIOR CHAINING: If no command or goal reached, assign a new mission!
                cmd = getattr(entity, 'current_command', None)
                arrived = False
                if cmd and my_pos:
                    if HexMath.distance(my_pos, cmd.target_hex) <= 0:
                        arrived = True

                # --- FIX: Wait for command to complete before assigning a new one ---
                # Previously, it would re-assign every step if not user-assigned.
                if not cmd or arrived:
                    # If they don't have a mission, or they've reached it, the AI Commander gives them one!
                    if not cmd or (arrived and not getattr(entity, 'mission_refreshed', False)):
                        StrategicCommander.assign_mission(entity, self.state)
                        setattr(entity, 'mission_refreshed', True) # Prevent infinite refresh in same step
                else:
                    setattr(entity, 'mission_refreshed', False)
                                    
                # DISTANCE TRACKING: Check how far the unit is from its goal BEFORE it takes a step.
                cmd_dist_before = float('inf')
                cmd = getattr(entity, 'current_command', None)
                if cmd:
                     my_pos = self.map.get_entity_position(entity.id)
                     if my_pos:
                          cmd_dist_before = HexMath.distance(my_pos, cmd.target_hex)
                
                # ENEMY TRACKING: Check how far the unit is from the nearest enemy BEFORE moving.
                dist_before = float('inf')
                if target:
                     my_pos = self.map.get_entity_position(entity.id)
                     tgt_pos = self.map.get_entity_position(target.id)
                     if my_pos and tgt_pos:
                          dist_before = HexMath.distance(my_pos, tgt_pos)
                
                # --- PHASE 3: DECIDE (The AI Brain) ---
                # TRANSLATE SITUATION: Convert the hex map and unit's status into numbers (Feature List).
                cum_reward = self.episode_rewards.get(entity.id, 0.0)
                state_features = self.encoder.get_features(entity, self.map, cum_reward, self.state.data_controller)
                
                # BRAIN SELECTION: Decide whether to use the 'Empty' brain or the 'Pre-trained' veteran brain.
                q_mgr = self._get_q_manager(entity)
                
                # OPTION SCAN: Figure out which actions (Move, Fire, etc.) are physically possible right now.
                allowed = self._get_allowed_actions(entity, target)
                
                # --- OVERRIDE LOGIC FOR USER GOALS ---
                action_idx = 7 # HOLD by default
                thinking = {"mode": "Override", "epsilon": 0.0, "q_values": {}}
                override_applied = False
                
                # If it's a USER-assigned command, we still want to give them some direct guidance
                # if they manually clicked a destination without RL training for that specific goal.
                if cmd and cmd.is_user_assigned and cmd.command_type == "MOVE":
                    if my_pos and HexMath.distance(my_pos, cmd.target_hex) > 0:
                        # RESPECT STRATEGIC AXIS
                        axis = getattr(cmd, "axis", 0)
                        if axis == 1: # SAFE
                            cost_fn = lambda h: self.get_true_cost(h, querying_faction=my_side)
                        elif axis == 2: # FAST
                            cost_fn = lambda h: 1.0 if self.map.get_terrain(h) else float('inf')
                        else: # DIRECT
                            def direct_cost(h):
                                t = self.map.get_terrain(h)
                                return t.get("cost", 1.0) if t else float('inf')
                            cost_fn = direct_cost

                        path_to_follow = self.pathfinder.get_path(
                            my_pos, cmd.target_hex,
                            cost_fn=cost_fn
                        )
                    
                        if path_to_follow and len(path_to_follow) > 1:
                            next_hex = path_to_follow[1]
                            direction_idx = HexMath.get_neighbor_direction(my_pos, next_hex)
                            
                            if direction_idx != -1:
                                direction_str = ["east", "northeast", "northwest", "west", "southwest", "southeast"][direction_idx]
                                for aidx, (atype, param) in RL_ACTION_MAP.items():
                                    if atype == "MOVE" and param == direction_str:
                                        if aidx in allowed:
                                            action_idx = aidx
                                            override_applied = True
                                            break

                elif cmd and cmd.is_user_assigned and cmd.command_type == "FIRE":
                    for aidx, (atype, param) in RL_ACTION_MAP.items():
                        if atype == "FIRE" and aidx in allowed:
                            action_idx = aidx
                            override_applied = True
                            break

                if not override_applied:
                    # THE MOMENT OF CHOICE: The AI picks an action index (0 to 10).
                    # For AI-assigned commands, the Resolution Agent is now FULLY AUTONOMOUS.
                    # It knows its target from `entity.current_command` and uses RL to get there.
                    action_idx, thinking = self._select_action(state_features, allowed, q_mgr)
                
                # TRANSLATION: Turn the choice (e.g., Index 2) into a real action command (e.g., MOVE NORTHEAST).
                action_type, direction = RL_ACTION_MAP.get(action_idx, ("HOLD / END TURN", None))
                
                # --- TOKEN COST CALCULATION ---
                action_cost = 1.0 # Base cost
                if action_type == "MOVE":
                    my_pos = self.map.get_entity_position(entity.id)
                    if my_pos and direction:
                        # DIRECTION_MAP is imported at module top from engine.core.hex_math
                        dq, dr, ds = DIRECTION_MAP.get(direction.lower(), (0, 0, 0))
                        next_hex = Hex(my_pos.q + dq, my_pos.r + dr, my_pos.s + ds)
                        # ANTICIPATORY COST: Check the destination terrain cost BEFORE moving.
                        next_attrs = self.state.data_controller.get_hex_full_attributes(next_hex, self.map)
                        raw_cost = float(next_attrs.get("cost", 1.0))
                        
                        # Apply Simplified Cost Rule: 1 for clear, 2 for terrain/obstacle
                        action_cost = 1.0 if raw_cost <= 1.0 else 2.0
                        
                        # REWARD ENGAGEMENT: Penalize or reward based on terrain type
                        terrain_cost = action_cost if action_cost > 1.0 else 0.0
                        if raw_cost == 99.0: # Destination is off-map or invalid
                            action_cost = 99.0
                elif action_type == "FIRE" or action_type == "CLOSE_COMBAT":
                    action_cost = 2.0
                elif action_type == "HOLD / END TURN":
                    action_cost = entity.tokens # Consumes all remaining tokens to end turn
                
                if entity.tokens < action_cost:
                    # If they can't afford it, end their turn
                    self._log(None, f"DEBUG: {entity.name} NO TOKENS (Need:{action_cost}, Have:{entity.tokens:.1f})")
                    entity.tokens = 0
                    continue
                
                self._log(None, f"DEBUG: {entity.name} {action_type} {direction or ''} (Cost:{action_cost})")
                entity.tokens -= action_cost
                
                # Report terrain cost specifically if it's high
                if action_type == "MOVE" and action_cost > 1.0:
                    self._log(None, f"<span style='color:#ff6b6b'>!!! {entity.name} PAYING {action_cost} for {direction}</span>")
    
                # --- PREPARE UI DEBUG INFO ---
                # We sort the top 3 actions the AI considered so the human can see its "Internal Monologue".
                q_vals = thinking.get("q_values", {})
                # Get the top 3 highest scores.
                sorted_q = sorted(q_vals.items(), key=lambda x: x[1], reverse=True)[:3]
                
                think_parts = []
                for aidx, qv in sorted_q:
                    aname, _ = RL_ACTION_MAP.get(aidx, ("?", None))
                    # Shorten the names for the UI 'Think Bubble'.
                    if aname.startswith("COMMIT"): aname = "C" + aname[6:]
                    think_parts.append(f"{aname}:{qv:.2f}")
                    
                # The 'Think Bubble' text shown in the Inspector panel.
                think_str = f"<b>{thinking['mode']}</b>(\u03b5={thinking['epsilon']:.2f})<br>" + ", ".join(think_parts)
                think_str += f"<br><span style='color: #61afef'>Cost:{action_cost} | Tokens:{entity.tokens:.1f}</span>"
                
                # STATS: Log whether the AI is 'Exploring' (guessing) or 'Exploiting' (using experience).
                mode = thinking.get("mode", "Exploit")
                self.stats["modes"][mode] = self.stats["modes"].get(mode, 0) + 1
                
                # GROUPING: Group specific moves like MOVE_NORTH into a single "MOVE" category for analytics.
                base_action_name = action_type 
                if "_" in base_action_name and not base_action_name.startswith("COMMIT"):
                     base_action_name = base_action_name.split("_")[0] 
                self.stats["actions"][base_action_name] = self.stats["actions"].get(base_action_name, 0) + 1
                
                # --- PHASE 4: ACT (Execution) ---
                # (Initializations moved to top of loop)
                
                # TOOL SELECTION: Pick the correct Action Tool (FIRE, MOVE, etc.) for the chosen action.
                base_type = action_type
                if action_type.startswith("COMMIT"): base_type = "COMMIT"
                
                action_obj = self.actions.get(base_type)
                
                if action_obj:
                     # DISPATCH: Tell the unit to actually perform the action on the map.
                     try:
                         # Each tool (FireAction, MoveAction, etc.) takes the current 'Map' and 'Unit' and does the work.
                         if base_type == "FIRE":
                             action_desc, evt, combat_result = action_obj.execute(entity, self.map, target=target, combat_engine=self.fire_engine, data_controller=self.state.data_controller)
                         elif base_type == "MOVE":
                             action_desc, evt, combat_result = action_obj.execute(entity, self.map, direction=direction)
                         elif base_type == "CLOSE_COMBAT":
                             action_desc, evt, combat_result = action_obj.execute(entity, self.map, target=target, combat_engine=self.fire_engine, data_controller=self.state.data_controller)
                         elif base_type == "COMMIT":
                             role = action_type.split("_")[1]
                             action_desc, evt, combat_result = action_obj.execute(entity, self.map, role=role)
                         else:
                             action_desc = "UNKNOWN"
                             evt = None
                             combat_result = None
                     except Exception as e:
                         # If something goes wrong (e.g., a bug in the code), report the error instead of crashing.
                         action_desc = f"ACTION ERROR ({e})"
                         evt = None
                         combat_result = None
                     # If the action created a visual effect (like a unit moving), add it to the 'Events' list for the screen.
                     if evt: events.append(evt)
                else:
                     action_desc = "HOLD / END TURN"
    
                # --- PHASE 5: LEARN (The Teacher) ---
                # Now we check how the unit's situation changed AFTER their action.
                dist_after = float('inf')
                target_after = self._find_target(entity)
                if target_after:
                     # Calculate the new distance to the enemy.
                     tgt_pos = self.map.get_entity_position(target_after.id)
                     if my_pos and tgt_pos:
                          dist_after = HexMath.distance(my_pos, tgt_pos)
                
                # Did they get closer or further away?
                delta = 0 
                if dist_before != float('inf') and dist_after != float('inf'):
                     delta = dist_after - dist_before
                     
                # Did they get closer to their strategic mission goal?
                cmd_dist_after = float('inf')
                cmd_delta = 0 
                if cmd:
                     if my_pos:
                          cmd_dist_after = HexMath.distance(my_pos, cmd.target_hex)
                          if cmd_dist_before != float('inf'):
                                cmd_delta = cmd_dist_after - cmd_dist_before
    
                # TERRAIN PENALTY: Moving through muddy slopes or dense forests is tiring (Costs points).
                terrain_cost = 0.0
                if my_pos:
                    terrain_data = self.map.get_terrain(my_pos)
                    if terrain_data:
                        terrain_cost = terrain_data.get("cost", 1) - 1 
    
                # BACKTRACKING PENALTY: We don't want units walking in circles, so they lose points 
                # for visiting the same hexagons over and over.
                revisit_penalty = 0.0
                if action_type.startswith("MOVE"):
                    new_pos = self.map.get_entity_position(entity.id)
                    if new_pos:
                        # Store a history of where the unit has been (JSON-safe list).
                        visited = entity.get_attribute("visited_hexes", [])
                        pos_tuple = [new_pos.q, new_pos.r, new_pos.s]
                        
                        cmd = getattr(entity, 'current_command', None)
                        goal_tuple = None
                        if cmd:
                            goal_tuple = [cmd.target_hex.q, cmd.target_hex.r, cmd.target_hex.s]
    
                        # If they step onto a tile they just left (or recently visited), penalize them.
                        # Using list search for small N is efficient enough and JSON-safe.
                        if pos_tuple in visited and pos_tuple != goal_tuple:
                            revisit_penalty = -5.0 
    
                        # Maintain list of unique recent locations
                        if pos_tuple not in visited:
                            visited.append(pos_tuple)
                            
                        # Only remember the last 6 steps to allow some flexibility.
                        visited = visited[-6:] 
                        entity.set_attribute("visited_hexes", visited)
    
                # CALCULATE REWARD: The AI 'Brain' gets points for success or loses points for failure.
                # Points are awarded for: Hitting enemies, reaching goals, and surviving.
                reward = self.reward_engine.calculate_reward(
                    entity, action_type,
                    combat_result=combat_result,
                    previous_personnel=prev_personnel, 
                    distance_delta=delta,
                    command_dist_delta=cmd_delta,
                    command_dist=cmd_dist_after,
                    terrain_cost=terrain_cost,
                    step_number=step_number,
                    max_steps=max_steps,
                    is_revisit=(revisit_penalty < 0)
                )
                
                # BRAIN UPDATE: Update the AI's internal spreadsheet (Q-Table) so it 'remembers' this result.
                self.episode_rewards[entity.id] += reward
                # WHAT HAPPENED NEXT: Note down where the unit ended up after acting.
                next_cum_reward = self.episode_rewards[entity.id]
                next_state_features = self.encoder.get_features(entity, self.map, next_cum_reward, self.state.data_controller)
                
                # DATA COLLECTION: Gather info for the big Step Report table in the UI.
                new_personnel = int(entity.get_attribute("personnel", 0))
                
                # EXPERIENCE COLLECTION: Store the transition for batch learning.
                done = (new_personnel <= 0 or step_number >= max_steps)
                self.replay_buffer.push(state_features, action_idx, reward, next_state_features, done)
                side = entity.get_attribute("side", "?")
                atype = entity.get_attribute("type", "Unit")
                
                # REVEAL STATE: Describe the agent's current situation for the UI inspector.
                c_idx = self.encoder.encode_casualty(new_personnel, int(entity.get_attribute("max_personnel", 100)))
                r_idx = self.encoder.encode_reward(next_cum_reward)
                
                c_str = {0: "Healthy", 1: "Light", 2: "Moderate", 3: "Critical"}.get(c_idx, "Unknown")
                r_str = {0: "Negative", 1: "Neutral", 2: "Positive"}.get(r_idx, "Unknown")
                
                state_desc = f"<b>{c_str} Situation</b> ({r_str})<br><span style='font-size: 0.85em; color: #aaa'>Features: {len(state_features)}</span>"
                
                # AGENT DEBUG INFO
                curr_p = my_pos
                pos_str = f"({curr_p.q}, {curr_p.r})" if curr_p else "Unknown"
                
                self.agent_debug_info[entity.name] = {
                     "state": state_desc,
                     "q_values": thinking.get("q_values", {}),
                     "action": action_desc,
                     "reward": reward,
                     "last_pos": pos_str,
                     "personnel": new_personnel,
                     "inventory": getattr(entity, 'inventory', {}),
                     "mode": thinking.get("mode", "Exploit")
                }
                
                # REWARD FORMATTING: Show the point change (e.g., "+10.00" or "-2.00").
                reward_str = f"{reward:.2f}"
                # If terrain cost was high, show it clearly
                if terrain_cost > 0.0:
                    base = reward + terrain_cost
                    reward_str = f"{reward:.2f}<br><span style='color: #888; font-size: 0.8em;'>(Base: {base:.1f} | Ter: -{terrain_cost:.1f})</span>"
                
                # Add token info to reward for debugging token deduction
                reward_str += f"<br><span style='color: #ae81ff; font-size: 0.8em;'>Cost {action_cost}</span>"
                
                # TARGET LOG: Show who the unit was looking at or attacking.
                tgt_info = "None"
                if target:
                    t_pos = self.map.get_entity_position(target.id)
                    t_dist = HexMath.distance(new_pos, t_pos) if (new_pos and t_pos) else -1
                    tgt_info = f"{target.name} (D:{t_dist})"
                
                # TABLE ROW: Add this unit's story to the big report table.
                step_data.append({
                    "Agent": entity.name,
                    "Type": atype,
                    "Personnel": str(new_personnel), # Terminology updated to 'Personnel'
                    "Tokens": f"{entity.tokens:.1f}",
                    "Pos": str(pos_str),
                    "Action": action_desc,
                    "Reward": reward_str,
                "Thinking": think_str
                })
                
                # LOG ENTRY: A simple text line for the scrolling history feed.
                log_entry = f"[{step_number}] {entity.name}: {action_desc} -> R:{reward:.1f} ({tgt_info})"
                
                # ATTACH LOG TO EVENT: This allows the Visualizer to log it in sync with the animation.
                if evt:
                    evt['log'] = log_entry
                
                self.event_log.append(log_entry)
                
                # FALLBACK: If HTML tables aren't working, log a simple text string.
                if not table_mode and log_func:
                     self._log(log_func, log_entry)
                
                # --- PERIODIC BATCH TRAINING ---
                # Learn from past experiences every 10 steps during the simulation
                if len(self.replay_buffer) >= self.batch_size and step_number % 10 == 0:
                     batch = self.replay_buffer.sample(self.batch_size)
                     self.q_manager_ephemeral.update_batch(batch)
            
        # MASTER REPORT: If units took turns, display them all in a polished HTML table.
        # Logic: Only show the big report table if we aren't in a high-speed learning phase.
        is_learning = getattr(self.state, 'is_learning', False)
        
        if step_data and table_mode and not is_learning:
            from engine.core.debug_utils import format_html_log
            table_str = format_html_log(f"EPISODE {episode_number} STEP {step_number} TIME {elapsed_minutes} REPORT", step_data)
            self._log(log_func, table_str, force_console=False)
        elif not step_data and table_mode and not is_learning:
             self._log(log_func, "No Active Agents.")
             
        # EPSILON DECAY: Decay is now handled at the end of each episode for more stability.
        # (Removed per-step decay to avoid overly aggressive exploration reduction).
        
        # --- RESET TOKENS FOR END OF TURN DURATION ---
        for entity in entities:
             if hasattr(entity, 'tokens'):
                  delattr(entity, 'tokens')
        
        # PERSISTENT LOGGING: Save the detailed tactical step data to disk.
        self.logger.log_step(episode_number, step_number, events)
        
        # Return both the visual events and the detailed tactical logs
        events.append({
            'type': 'time_update',
            'time': sim_time_str,
            'step': step_number
        })
        
        logs = self.event_log.copy()
        self.event_log.clear()
        return events, logs
    
    def reset_episode(self):
        """
        PREPARE NEXT ROUND: Wipes temporary memories and increments the round number.
        This is like clearing the chalkboard after a lesson.
        """
        self.episode_rewards.clear()
        self.event_log.clear()
        self.episode_count += 1

        # Units forget where they've walked so they don't get 'backtracking' penalties in a new round.
        for entity in self.entity_manager.get_all_entities():
            entity.set_attribute("visited_hexes", [])
        
        # New units slowly get more confident with every complete round.
        if self.q_manager_ephemeral.epsilon > self.epsilon_min:
            self.q_manager_ephemeral.epsilon = max(self.epsilon_min, self.q_manager_ephemeral.epsilon * self.epsilon_decay)
            
        # Veteran units stay focused on what they already know.
        self.q_manager_persistent.epsilon = 0.01

        # !!! STRATEGIC LEARNING !!!
        # Commander learns from the total journey of each unit.
        for entity in self.entity_manager.get_all_entities():
            if hasattr(entity, "commander_trajectory") and entity.commander_trajectory:
                reward_total = self.episode_rewards.get(entity.id, 0.0)
                get_commander_brain().learn_from_trajectory(entity.commander_trajectory, reward_total)
                # Reset trajectory for the next episode.
                entity.commander_trajectory = [] 
                
        # !!! BATCH TRAINING !!!
        # Experience Replay: Learn from a random batch of past tactical situations.
        if len(self.replay_buffer) >= self.batch_size:
            batch = self.replay_buffer.sample(self.batch_size)
            # We train the ephemeral (explorer) brain.
            self.q_manager_ephemeral.update_batch(batch)

        # !!! AUTO-SAVE !!!
        # This ensures the AI brain is written to the hard drive after every round.
        self.save_knowledge()

    def save_knowledge(self):
        """WRITE TO DISK: Saves both brains so they can be resumed later."""
        self.q_manager_persistent.save_q_table("data/models/q_table.npy")
        self.q_manager_ephemeral.save_q_table("data/models/ephemeral_q_table.npy")

    def _get_q_manager(self, entity):
        """AI SELECTOR: Picks whether this unit should use an 'Empty' or 'Veteran' brain."""
        config = self.state.data_controller.resolve_unit_config(entity)
        # If the unit's config file has 'learned: True', it will use the pre-trained veteran brain.
        if config.get("learned", False):
            return self.q_manager_persistent
        return self.q_manager_ephemeral
    
    # ------------------------------------------------------------------
    # SENSE HELPER METHODS (The unit's eyes and sensors)
    # ------------------------------------------------------------------
    
    def _find_target(self, entity):
        """
        VISION: Scans the map to find the closest enemy unit.
        Think of this as the unit's 'Eyes'. It can only see so far (Vision Range).
        """
        my_side = entity.get_attribute("side", "Neutral")
        my_pos = self.map.get_entity_position(entity.id)
        if my_pos is None:
            return None
        
        config = self.state.data_controller.resolve_unit_config(entity)
        vision = config["vision_range"]
        
        best_target = None
        best_dist = float('inf')
        
        # Look at every other unit in the game.
        for other in self.entity_manager.get_all_entities():
            if other.id == entity.id:
                continue # You can't target yourself.
            
            # Check if they are actually an enemy.
            other_side = other.get_attribute("side", "Neutral")
            if other_side == my_side or other_side == "Neutral":
                continue
            
            # Ignore units that are already destroyed (Personnel = 0).
            other_personnel = int(other.get_attribute("personnel", 0))
            if other_personnel <= 0:
                continue
            
            other_pos = self.map.get_entity_position(other.id)
            if other_pos is None:
                continue
            
            # Calculate physical distance between the two hexagons.
            dist = HexMath.distance(my_pos, other_pos)
            # If they are within sight AND they are the closest one found, pick them as the target.
            if dist <= vision and dist < best_dist:
                best_dist = dist
                best_target = other
        
        return best_target
    
    def _find_target_in_fire_range(self, entity):
        """
        FIRE RANGE CHECK: Finds an enemy that is close enough and aligned to be shot.
        Unlike 'Vision', this also checks 'Line of Fire' (straight axes).
        """
        my_pos = self.map.get_entity_position(entity.id)
        if my_pos is None:
            return None
        
        # RANGE DETERMINATION
        u_type = entity.get_attribute("type", "")
        fire_range = int(entity.get_attribute("fire_range", 0))
        if fire_range <= 0:
            if u_type == "FiringAgent": fire_range = 6
            elif u_type in ["CloseCombatAgent", "DefenderAgent"]: fire_range = 2
            else: fire_range = 3
            
        my_side = entity.get_attribute("side", "Neutral")
        
        for other in self.entity_manager.get_all_entities():
            if other.id == entity.id:
                continue
            other_side = other.get_attribute("side", "Neutral")
            if other_side == my_side or other_side == "Neutral":
                continue
            # Skip units with 0 personnel.
            if int(other.get_attribute("personnel", 0)) <= 0:
                continue
            
            other_pos = self.map.get_entity_position(other.id)
            if other_pos is None:
                continue
            
            dist = HexMath.distance(my_pos, other_pos)
            # To shoot, they must be in range AND in a straight line axis (Axial Alignment).
            if dist <= fire_range:
                if HexMath.is_aligned(my_pos, other_pos):
                    return other
        
        return None

    def _find_target_in_melee_range(self, entity):
        """HAND-TO-HAND check: Finds an enemy in an adjacent hexagon (distance = 1)."""
        my_pos = self.map.get_entity_position(entity.id)
        if my_pos is None: return None
        
        my_side = entity.get_attribute("side", "Neutral")
        
        for other in self.entity_manager.get_all_entities():
            if other.id == entity.id: continue
            # Check if the other unit is an enemy.
            other_side = other.get_attribute("side", "Neutral")
            if other_side == my_side or other_side == "Neutral": continue
            
            # Skip if they are already out of the fight.
            if int(other.get_attribute("personnel", 0)) <= 0: continue
            
            other_pos = self.map.get_entity_position(other.id)
            if not other_pos: continue
            
            # Close Combat (Melee) is only possible if they are in an ADJACENT hexagon (distance 1).
            if HexMath.distance(my_pos, other_pos) == 1:
                return other
        return None
    
    # ------------------------------------------------------------------
    # DECIDE (RL)
    # ------------------------------------------------------------------
    
    def _get_allowed_actions(self, entity, target):
        """
        RULES: Limits what actions a unit is allowed to try based on the game rules.
        For example:
        - Units can't move into walls.
        - Defenders are locked in place.
        - You can't shoot if you don't have a target in range.
        """
        side = str(entity.get_attribute("side", "")).lower()

        # --------------------------------------------------
        # 🔒 DEFENDER LOGIC: Units on defense are stuck in place!
        # --------------------------------------------------
        if side == "defender":
            allowed = [7]  # '7' is the code for 'HOLD/WAIT'
        
            # If an enemy is in line-of-fire, they are allowed to SHOOT back.
            fire_target = self._find_target_in_fire_range(entity)
            if fire_target:
                for idx, (atype, _) in RL_ACTION_MAP.items():
                    if atype == "FIRE":
                        allowed.append(idx)

            # If an enemy is in the next hexagon, they can perform MELEE combat.
            melee_target = self._find_target_in_melee_range(entity)
            if melee_target:
                for idx, (atype, _) in RL_ACTION_MAP.items():
                    if atype == "CLOSE_COMBAT":
                        allowed.append(idx)

            return allowed

        # --------------------------------------------------
        # ATTACKER LOGIC: Attackers are free to move and explore.
        # --------------------------------------------------
        allowed = []
        agent_type = entity.get_attribute("type", "DefenderAgent")
        side = entity.get_attribute("side", "Attacker")

        # Start with the basic list of things any unit can do.
        allowed_keys = ["FIRE", "MOVE", "CLOSE_COMBAT", "COMMIT", "HOLD / END TURN"]

        # If this specific unit type has a special list of abilities, use those instead.
        if hasattr(self.state, 'data_controller'):
            agent_catalog = self.state.data_controller.agent_types.get(side, {})
            config = agent_catalog.get(agent_type, {})
            if "actions" in config:
                allowed_keys = config["actions"]

        # You can ALWAYS choose to do nothing (HOLD).
        allowed.append(7)

        current_pos = self.map.get_entity_position(entity.id)

        # Loop through every possible move the AI brain knows about.
        for idx, (atype, param) in RL_ACTION_MAP.items():
            if idx == 7: continue # Already added above

            base_type = atype
            if atype.startswith("COMMIT"): base_type = "COMMIT"

            # If the unit's type isn't allowed to do this action, skip it.
            if base_type not in allowed_keys: continue

            # Pick the 'Tool' needed to check if this move is possible.
            action_obj = self.actions.get(base_type)
            if not action_obj: continue

            # ---- MOVE CHECK: Is the path clear? ----
            if base_type == "MOVE":
                dq, dr, ds = DIRECTION_MAP.get(param, (0, 0, 0))
                new_hex = Hex(current_pos.q + dq, current_pos.r + dr, current_pos.s + ds)

                # Check if the target hexagon exists and isn't a solid obstacle (like a wall).
                if self.map.get_terrain(new_hex) and not self._is_obstacle(new_hex):
                    # Check 'Stacking': Is there room for one more unit in that hexagon?
                    limit = self.map.active_scenario.rules.get("max_agents_per_hex", 3)
                    if len(self.map.get_entities_at(new_hex)) < limit:
                        allowed.append(idx)

            # ---- FIRE CHECK: Is the enemy in range? ----
            elif base_type == "FIRE":
                if action_obj.is_allowed(entity, self.map, target):
                    allowed.append(idx)

            # ---- CLOSE COMBAT CHECK: Is anyone next to me? ----
            elif base_type == "CLOSE_COMBAT":
                melee_target = self._find_target_in_melee_range(entity)
                if action_obj.is_allowed(entity, self.map, melee_target):
                    allowed.append(idx)

            # ---- COMMIT CHECK: Is it time to complete a mission? ----
            elif base_type == "COMMIT":
                if action_obj.is_allowed(entity, self.map):
                    allowed.append(idx)

        # If somehow nothing is allowed, at least let them HOLD.
        return allowed if allowed else [7]

    def _check_move_action(self, action_idx, current_pos, allowed_list):
        """Helper to validate move."""
        _, direction = RL_ACTION_MAP[action_idx]
        if direction and direction in DIRECTION_MAP:
            dq, dr, ds = DIRECTION_MAP[direction]
            new_hex = Hex(current_pos.q + dq, current_pos.r + dr, current_pos.s + ds)
            
            # Check: valid terrain (not void) and not an obstacle zone
            terrain = self.map.get_terrain(new_hex)
            if terrain is not None and not self._is_obstacle(new_hex):
                # Check Stacking? Validating strictly before move is good practice
                limit = self.map.active_scenario.rules.get("max_agents_per_hex", 3)
                entities_at = self.map.get_entities_at(new_hex)
                if len(entities_at) < limit:
                    allowed_list.append(action_idx)
    
    def _select_action(self, state, allowed_actions, q_manager=None):
        """
        THE CHOICE: Uses 'Epsilon-Greedy' logic to pick what to do next.
        - Sometimes, we pick something random (Explore).
        - Usually, we pick the smartest move we know (Exploit).
        """
        if q_manager is None:
            q_manager = self.q_manager_ephemeral
            
        epsilon = q_manager.epsilon
        
        # Look up what the AI is currently thinking about its possible moves.
        q_values = q_manager.get_q_values(state, allowed_actions)
        
        # Roll a 'Dice' (0.0 to 1.0). If it's less than Epsilon, the unit takes a random guess.
        # This is how the AI 'Learns' new tricks instead of doing the same thing forever.
        if random.random() < epsilon:
            choice = random.choice(allowed_actions)
            return choice, {"mode": "Explore", "epsilon": epsilon, "q_values": q_values}
        else:
            # Otherwise, use its 'Wisdom' to pick the move with the highest score.
            choice = q_manager.get_action(state, allowed_actions)
            return choice, {"mode": "Exploit", "epsilon": epsilon, "q_values": q_values}
    
    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    
    def _is_obstacle(self, hex_coords):
        """CHECKER: Returns True if a hexagon is blocked by a wall or obstacle zone."""
        zones = self.map.get_zones()
        for zid, zdata in zones.items():
            if zdata.get("type") == "Obstacle":
                if hex_coords in zdata.get('hexes', []):
                    return True
        return False
    
    @staticmethod  
    def _log(log_func, message, force_console=True):
        """MESSENGER: Prints a message to the Developer Console and the Visual Event Log."""
        # Detect HTML 
        is_html = message.strip().startswith("<")
        
        if force_console or not is_html:
            # Strip tags for console
            import re
            clean_msg = re.sub('<[^<]+?>', '', message).replace('&nbsp;', ' ').replace('<br>', ' | ')
            
            # For massive reports, just show a summary in terminal
            if is_html and len(clean_msg) > 200:
                title_match = re.search(r'<h3>(.*?)</h3>', message)
                title = title_match.group(1) if title_match else "Tactical Report"
                print(f"[REPORT] {title}")
            else:
                print(clean_msg)

        if log_func:
            log_func(message)