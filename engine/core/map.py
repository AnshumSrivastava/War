"""
FILE: engine/core/map.py
ROLE: The "Universe" manager for the game world and missions.

DESCRIPTION:
This file defines two major structures that hold the entire game state:
1. Scenario: This is like a 'Mission Layer'. It sits on top of the terrain and 
   remembers where units are stationed, what the victory zones are, and 
   the specific rules for that battle (e.g., maximum turns allowed).
2. Map: This represents the physical earth. It stores the terrain types 
   (mountains, water, plains) and keeps track of which Scenario is active.

These classes are responsible for "Serialization" - the process of turning 
complex computer objects into simple text (JSON) so they can be saved to a file 
and loaded back exactly as they were.
"""
from engine.core.hex_math import Hex, HexMath
from typing import List, Tuple, Optional, Any, Set, Dict

class Scenario:
    """
    A 'Mission' or 'Battle' configuration. 
    It doesn't care about the terrain (mountains/grass), but it cares about:
    - Where the soldiers (Entities) are standing.
    - Where the special zones (like Objectives) are.
    - The specific rules for this engagement.
    """
    def __init__(self, name: str = "Default Scenario"):
        self.name = name
        
        # Spatial Map: A dictionary that lets us quickly find who is standing on a specific hex.
        # Format: {(q,r,s): [list of unit IDs]}
        self._spatial_map: Dict[Tuple[int, int, int], List[str]] = {}
        
        # Entity Positions: The reverse of the above. Quickly find WHERE a unit is by its ID.
        # Format: {unitID: (q,r,s)}
        self._entity_positions: Dict[str, Tuple[int, int, int]] = {}
        
        # Zones: Areas of interest (e.g., 'Deployment Zone', 'Victory Point').
        self._zones: Dict[str, Dict] = {}
        
        # Paths: Lines drawn on the map (e.g., 'Retreat Route', 'Main Road').
        self._paths: Dict[str, Dict] = {}
        
        # Game Rules: Customizable settings that change how the AI or players behave.
        self.rules = {
            "max_agents_per_hex": 3,      # How many soldiers can squeeze into one hexagon.
            "max_turns": 30,             # When the game automatically ends.
            "attacker_max_force": 10,     # Troop limit for the red side.
            "defender_max_force": 10,     # Troop limit for the blue side.
        }
        
    def to_dict(self) -> Dict:
        """
        CONVERSION: Turns this entire scenario into a dictionary for saving to a file.
        It converts internal 'Cube' coordinates (difficult for humans) into 
        simple 'Offset' coordinates (like 'column 10, row 5') which are easier to read.
        """
        data = {
            "name": self.name,
            "rules": self.rules,
            "zones": {},
            "paths": {},
            "entity_positions": {}
        }
        
        # Save where every entity is standing
        for eid, coords in self._entity_positions.items():
            h = Hex(*coords)
            col, row = HexMath.cube_to_offset(h)
            key = f"{col},{row}"
            data["entity_positions"][eid] = key 
        
        # Save all the special zones
        for zid, zdata in self._zones.items():
            z_copy = zdata.copy()
            if 'hexes' in z_copy:
                # Convert the internal hex list to a simple list of [col, row] numbers
                z_copy['hexes'] = [list(HexMath.cube_to_offset(h)) for h in z_copy['hexes']]
            if 'vertices' in z_copy:
                 # Handle the corners of the zone shape
                 verts = []
                 for h in z_copy['vertices']:
                     if isinstance(h, list) or isinstance(h, tuple):
                         verts.append(list(h))
                     else:
                         verts.append(list(HexMath.cube_to_offset(h)))
                 z_copy['vertices'] = verts
            data["zones"][zid] = z_copy
            
        # Save all the path lines
        for pid, pdata in self._paths.items():
            p_copy = pdata.copy()
            if 'hexes' in p_copy:
                p_copy['hexes'] = [list(HexMath.cube_to_offset(h)) for h in p_copy['hexes']]
            data["paths"][pid] = p_copy
            
        return data
    
    def to_dict_with_entities(self, entity_manager) -> Dict:
        """
        Works like to_dict(), but ALSO includes all the stats (health, names) 
        of the units from the EntityManager.
        """
        data = self.to_dict()
        
        # Package up every entity's internal data
        entities_data = {}
        for eid in self._entity_positions:
             ent = entity_manager.get_entity(eid)
             if ent:
                 # Construct a basic dictionary of the unit's current state
                 ent_data = {
                     "id": ent.id,
                     "name": ent.name,
                     "components": ent.components,
                     "attributes": ent.attributes.copy()
                 }
                 
                 # If the unit was in the middle of a command (like moving), save that too
                 if getattr(ent, 'current_command', None):
                     cmd = ent.current_command
                     ent_data["current_command"] = {
                         "type": cmd.command_type,
                         "target_hex": list(cmd.target_hex) if cmd.target_hex else None,
                         "is_user_assigned": cmd.is_user_assigned
                     }
                      
                 entities_data[eid] = ent_data
        
        data["entities"] = entities_data
        return data

    def load_from_dict(self, data: Dict):
        """
        LOADING: Takes a dictionary (from a file) and rebuilds the scenario.
        It translates those simple 'Offset' coordinates back into 'Cube' math.
        """
        self.name = data.get("name", "Unnamed Scenario")
        self.rules = data.get("rules", {
            "max_agents_per_hex": 3,
            "max_turns": 30,
            "attacker_max_force": 10,
            "defender_max_force": 10,
        })
        self._zones = {}
        self._entity_positions = {}
        self._spatial_map = {}
        
        # Put every entity back where it belongs
        pos_raw = data.get("entity_positions", {})
        for eid, pos_val in pos_raw.items():
            try:
                # Support both string "col,row" and legacy list [col, row]
                if isinstance(pos_val, str):
                    c_str, r_str = pos_val.split(',')
                    col, row = int(c_str), int(r_str)
                elif isinstance(pos_val, list) and len(pos_val) >= 2: 
                    col, row = pos_val[0], pos_val[1]
                else:
                    continue
                    
                h = HexMath.offset_to_cube(col, row)
                t_coords = (h.q, h.r, h.s)
                
                self._entity_positions[eid] = t_coords
                # Update the spatial map so the engine knows this hex is occupied
                if t_coords not in self._spatial_map:
                    self._spatial_map[t_coords] = []
                self._spatial_map[t_coords].append(eid)
            except ValueError:
                continue
            
        # Rebuild all path lines
        paths_raw = data.get("paths", {})
        for pid, pdata in paths_raw.items():
            hexes_raw = pdata.get('hexes', [])
            hexes = []
            for h_raw in hexes_raw:
                if len(h_raw) >= 2:
                    hexes.append(HexMath.offset_to_cube(h_raw[0], h_raw[1]))
            
            p_fixed = pdata.copy()
            p_fixed['hexes'] = hexes
            self._paths[pid] = p_fixed

        # Rebuild all special zones
        zones_raw = data.get("zones", {})
        for zid, zdata in zones_raw.items():
            z_fixed = zdata.copy()
            
            # Rebuild the list of hexagons inside the zone
            hexes_raw = zdata.get('hexes', [])
            hexes = []
            for h_raw in hexes_raw:
                if len(h_raw) >= 2:
                    hexes.append(HexMath.offset_to_cube(h_raw[0], h_raw[1]))
            z_fixed['hexes'] = hexes
            
            # Rebuild the corner points of the zone
            verts_raw = zdata.get('vertices', [])
            verts = []
            for v_raw in verts_raw:
                if len(v_raw) >= 2:
                    verts.append(HexMath.offset_to_cube(v_raw[0], v_raw[1]))
            z_fixed['vertices'] = verts
            
            self._zones[zid] = z_fixed

    def capture_state(self, entity_manager):
        """Save a complete snapshot of the current 'Design' state (units, positions, etc.)."""
        # This captures positions, zones, paths, and unit attributes
        self._snapshot = self.to_dict_with_entities(entity_manager)

    def restore_state(self, entity_manager):
        """Restore the Scenario to exactly how it was when last captured."""
        if not hasattr(self, '_snapshot'):
            return # Nothing to restore
            
        # 1. Clear existing tactical state
        entity_manager.clear()
        
        # 2. Reload everything from the snapshot
        # load_from_dict_with_entities handles positions, spatial_map, AND manager hydration
        self.load_from_dict_with_entities(self._snapshot, entity_manager)
    
    def load_from_dict_with_entities(self, data: Dict, entity_manager):
        """Load scenario data and restore entities."""
        self.load_from_dict(data)
        
        # Restore Entities
        entities_raw = data.get("entities", {})
        for eid, edata in entities_raw.items():
            # Create or Update Entity
            # If it already exists in manager?
            # Usually we clear old ones or overwrite.
            # Let's create new instance for safety or update existing
            
            # We need to know class type (Agent or BaseEntity). 
            # For now, default to Agent if has components, or BaseEntity
            # Simple heuristic: Always Agent? Or check components?
            
            # Assuming Agent for now if simple wargame
            # Import locally to avoid circular import issues if top-level moved
            from engine.core.entity_manager import Agent, BaseEntity
            
            new_ent = Agent(agent_id=eid, name=edata.get("name", "Unknown"))
            new_ent.components = edata.get("components", [])
            new_ent.attributes.update(edata.get("attributes", {}))
            
            cmd_data = edata.get("current_command")
            if cmd_data:
                from engine.simulation.command import AgentCommand
                from engine.core.hex_math import Hex
                tgt = cmd_data.get("target_hex")
                tgt_hex = Hex(*tgt) if tgt else None
                new_ent.current_command = AgentCommand(
                    command_type=cmd_data.get("type", "MOVE"),
                    target_hex=tgt_hex,
                    is_user_assigned=cmd_data.get("is_user_assigned", False)
                )
            
            entity_manager.register_entity(new_ent)
            
        # Also populate cache so we can switch away and back without losing data if we didn't edit anything
        self._cached_entities_dict = entities_raw.copy()


class Map:
    """
    The ROOT of the game world. 
    It manages the physical terrain and coordinates which 'Scenario' is being played.
    """
    def __init__(self):
        # Default size of the world (50x50 hexagons)
        self.width = 50 
        self.height = 50
        
        # Terrain data: Stores what is at every hex (e.g., 'This hex is a mountain').
        # Key is (q,r,s) cube coordinates.
        self._terrain: Dict[Tuple[int, int, int], Dict] = {}
        
        # Scenario management
        self.scenarios: Dict[str, Scenario] = {}
        self.active_scenario = Scenario("Default")
        self.scenarios["Default"] = self.active_scenario
        
        # Map Boundaries & Side Assignments (Red territory vs Blue territory)
        self.border_path: List[Hex] = [] # The line of hexes that divides the map
        self.hex_sides: Dict[Tuple[int, int, int], str] = {} # Remembers which side owns which hex

    def set_terrain(self, hex_obj: Hex, data: Dict):
        """Sets the terrain type for a specific hexagon."""
        self._terrain[tuple(hex_obj)] = data

    def get_terrain(self, hex_obj: Hex) -> Dict:
        """
        GEOGRAPHY: Returns the terrain stats for a specific hexagon.
        Checks if the location is within the world boundaries first.
        """
        # First, convert to simple column/row to check if it's on the map
        col, row = HexMath.cube_to_offset(hex_obj)
        if not (0 <= col < self.width and 0 <= row < self.height):
            return None # Out of bounds (The 'Void')
            
        # If no terrain is defined, we treat it as a 'plain' field
        return self._terrain.get(tuple(hex_obj), {"type": "plain", "elevation": 0, "cost": 1.0})

    # --- Delegated to Active Scenario ---

    def place_entity(self, entity_id: str, hex_obj: Hex):
        """
        DEPLOYMENT: Places a unit (soldier/vehicle) onto a specific hexagon.
        It handles removing them from their old spot and checking the 'Stacking' rules.
        """
        scen = self.active_scenario
        coords = tuple(hex_obj)
        
        # 1. If the unit was already somewhere else, remove them from the old spot first
        if entity_id in scen._entity_positions:
            old_coords = scen._entity_positions[entity_id]
            if old_coords in scen._spatial_map:
                if entity_id in scen._spatial_map[old_coords]:
                    scen._spatial_map[old_coords].remove(entity_id)

        # 2. Update their record to show they are at the new location
        scen._entity_positions[entity_id] = coords
        if coords not in scen._spatial_map:
            scen._spatial_map[coords] = []
            
        # 3. Check the 'Stacking Limit' (How many units can fit in one hex?)
        stack_limit = scen.rules.get("max_agents_per_hex", 3)
        if len(scen._spatial_map[coords]) >= stack_limit:
             # If too many units are here, we print a warning. 
             # In a strict battle, this might be forbidden.
             print(f"Warning: Stacking limit ({stack_limit}) reached at {coords}. Placement might be invalid.")

        # 4. Finalize the unit's position in the spatial lookup system
        scen._spatial_map[coords].append(entity_id)

    def get_entities_at(self, hex_obj: Hex) -> List[str]:
        return self.active_scenario._spatial_map.get(tuple(hex_obj), [])

    def get_entity_position(self, entity_id: str) -> Optional[Hex]:
        coords = self.active_scenario._entity_positions.get(entity_id)
        if coords:
            return Hex(*coords)
        return None

    def remove_entity_pos(self, entity_id: str):
        scen = self.active_scenario
        if entity_id in scen._entity_positions:
            old_coords = scen._entity_positions.pop(entity_id)
            if old_coords in scen._spatial_map:
                if entity_id in scen._spatial_map[old_coords]:
                    scen._spatial_map[old_coords].remove(entity_id)

    def clear_hex(self, hex_obj: Hex):
        """Clear terrain (static) and entities (scenario-specific)."""
        coords = tuple(hex_obj)
        if coords in self._terrain:
            del self._terrain[coords]
            
        # Also clear entities from active scenario at this hex?
        # Typically "clearing" might mean resetting the tile.
        # For now, let's just clear terrain as before, 
        # but if we want to remove entities we should access active_scenario.
        pass 

    def add_zone(self, zone_id: str, data: Dict):
        self.active_scenario._zones[zone_id] = data

    def get_zones(self) -> Dict:
        return self.active_scenario._zones

    def remove_zone(self, zone_id: str):
        if zone_id in self.active_scenario._zones:
            del self.active_scenario._zones[zone_id]

    def add_path(self, path_id: str, data: Dict):
        self.active_scenario._paths[path_id] = data

    def get_paths(self) -> Dict:
        return self.active_scenario._paths

    def remove_path(self, path_id: str):
         if path_id in self.active_scenario._paths:
            del self.active_scenario._paths[path_id]

    # --- Persistence (Map = Terrain Only + Ref to scenarios?) ---
    # For now, let's keep to_dict saving ONLY terrain and dimensions, 
    # OR we can save the *current session* (Map + Scenario).
    # Based on user request, we want separate files. 
    # So map.to_dict() should generally serve "Terrain" saving.
    
    def to_dict(self, include_scenarios=False, entity_manager=None) -> Dict:
        """
        SAVING TERRAIN: Converts the static map (mountains/plains) into a dictionary.
        This is what gets saved to '.json' files.
        """
        data = {
            "width": self.width,
            "height": self.height,
            "terrain": {},
            "file_type": "project" if include_scenarios else "terrain"
        }
        
        # Save every terrain tile using easy-to-read 'column,row' coordinates
        for hex_tuple, t_data in self._terrain.items():
            h = Hex(*hex_tuple)
            col, row = HexMath.cube_to_offset(h)
            key = f"{col},{row}"
            data["terrain"][key] = t_data
        
        # Save which side (Red/Blue) has been assigned to each hexagon
        data["hex_sides"] = {}
        if hasattr(self, 'hex_sides'):
            for hex_tuple, side_id in self.hex_sides.items():
                 h = Hex(*hex_tuple)
                 col, row = HexMath.cube_to_offset(h)
                 key = f"{col},{row}"
                 data["hex_sides"][key] = side_id
        
        return data

    def load_from_dict(self, data: Dict):
        """Restore Terrain Data from Offset Coordinates."""
        if "width" in data: self.width = data.get("width", 50)
        if "height" in data: self.height = data.get("height", 50)
        
        terrain_raw = data.get("terrain")
        if terrain_raw is not None:
            self._terrain = {}
            for key, t_data in terrain_raw.items():
                try:
                    # Key is "col,row"
                    if ',' in key:
                        c_str, r_str = key.split(',')
                        col, row = int(c_str), int(r_str)
                        h = HexMath.offset_to_cube(col, row)
                        self._terrain[(h.q, h.r, h.s)] = t_data
                    else: 
                        # Fallback for old "q,r,s" if mixed?
                        parts = list(map(int, key.split(',')))
                        if len(parts) == 3: # Legacy Cube
                             self._terrain[(parts[0], parts[1], parts[2])] = t_data
                except ValueError:
                    continue
        
        if data.get("file_type") == "project" and "scenarios" in data:
            scenarios_data = data["scenarios"]
            self.scenarios = {} # Clear existing? Or merge? Clear is safer for Project Load.
            
            # We need an entity manager passed in, or we can't restore entities.
            # Map.load_from_dict signature doesn't have it.
            # We should overload or check kwargs if we want to be clean, 
            # but python allows us to add `entity_manager=None` to the signature.
            pass
    
    def load_project_data(self, data: Dict, entity_manager):
        """Full project load with scenarios and entities."""
        self.load_from_dict(data) # Loads terrain + dimensions
        
        if "scenarios" in data:
            self.scenarios = {}
            # Clear entities from manager too? Yes, new project.
            entity_manager._entities = {} 
            
            for name, s_data in data["scenarios"].items():
                scen = Scenario(name)
                scen.load_from_dict_with_entities(s_data, entity_manager)
                self.scenarios[name] = scen
                
            active_name = data.get("active_scenario", "Default")
            if active_name in self.scenarios:
                self.active_scenario = self.scenarios[active_name]
            elif self.scenarios:
                 self.active_scenario = list(self.scenarios.values())[0]
            else:
                 self.active_scenario = Scenario("Default")
                 self.scenarios["Default"] = self.active_scenario

    def detect_sections(self) -> List[dict]:
        """
        FLOOD FILL: This is a clever algorithm that identifies distinct 'zones' on the map.
        It's like pouring paint onto the map: the paint spreads until it hits 
        the 'Border Line'. This tells us which hexagons belong to 'Side A' vs 'Side B'.
        """
        sections = []
        visited = set()
        border_set = set(tuple(h) for h in self.border_path)
        
        section_id_counter = 0
        
        # Scan every hex on the map
        for col in range(self.width):
            for row in range(self.height):
                h = HexMath.offset_to_cube(col, row)
                t_h = tuple(h)
                
                # Skip if we already checked it or if it's the border itself
                if t_h in visited or t_h in border_set:
                    continue
                
                # We found a new, unvisited hexagon! Start a 'Flood Fill' from here.
                section_hexes = set()
                queue = [h]
                visited.add(t_h)
                section_hexes.add(t_h)
                
                while queue:
                    curr = queue.pop(0)
                    # Check all 6 neighbors
                    for i in range(6):
                        n = HexMath.neighbor(curr, i)
                        t_n = tuple(n)
                        
                        # Stop if out of map bounds
                        c, r = HexMath.cube_to_offset(n)
                        if not (0 <= c < self.width and 0 <= r < self.height):
                            continue
                        
                        # If neighbor isn't visited and isn't a border, add it to this section
                        if t_n not in visited and t_n not in border_set:
                            visited.add(t_n)
                            section_hexes.add(t_n)
                            queue.append(n)
                
                # Once the paint stops spreading, we save this section
                if section_hexes:
                    sections.append({'id': section_id_counter, 'hexes': section_hexes})
                    section_id_counter += 1
                    
        return sections
