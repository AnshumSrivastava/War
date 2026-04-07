"""
FILE: data/services/master_data_service.py
ROLE: The "Sorting Office" (MasterDataService).

DESCRIPTION:
If the JSONDatabase is a pile of raw mail, this file is the sorting office. 
It takes all those raw JSON files and organizes them into logical categories:
- "This file is a Terrain definition (Forest, Desert, etc.)."
- "This file is a Unit definition (Infantry, Tank, etc.)."
- "This file is a Zone definition (Red Base, Blue Objective)."

It also ensures that if a file is missing some information, it fills in the 
blanks with sensible 'Default' values so the rest of the app doesn't crash.
"""

import os
from typing import Dict, Any, List, Optional
from engine.data.api.base_db import BaseDB
from engine.core.items import Weapon
from engine.core.naming_utils import NamingUtils
from engine.data.definitions.constants import ROLES, UNIT_TYPES

class MasterDataService:
    """
    The intelligence layer for the database. It knows HOW to interpret the files.
    """
    def __init__(self, db: BaseDB):
        self.db = db
        
        # --- THE MEMORY (Cache) ---
        # We store the most important data here so we don't have to keep 
        # reading from the slow hard drive every second.
        self.catalogs: Dict[str, Any] = {
            "defaults": {},
            "terrain_types": {},
            "agent_types": {"Attacker": {}, "Defender": {}},
            "zone_types": {"Attacker": {"Red Area 1": {}}, "Defender": {"Blue Area 1": {}}},
            "obstacle_types": {},
            "hierarchy": {},
            "weapons": {}
        }
        self.reload_catalogs()

    def reload_catalogs(self):
        """
        THE UPDATER:
        Goes through the 'content' folders and builds a fresh catalog of everything.
        """
        # 1. Load the "Defaults" (The baseline for a blank map)
        defs = self.db.get("Master Database/defaults") or self.db.get("config/defaults")
        if defs: self.catalogs["defaults"] = defs
            
        # 2. Load the "Terrain Types" (Plains, Forest, Mountains)
        terrain_catalog = {}
        terrain_keys = self.db.keys("Master Database/Terrain/*.json")
        for key in terrain_keys:
            data = self.db.get(key)
            if data and "type" in data:
                terrain_catalog[data["type"]] = data
        
        if terrain_catalog:
            self.catalogs["terrain_types"] = terrain_catalog
        else:
            t_types = self.db.get("Master/TerrainTypes")
            if t_types: self.catalogs["terrain_types"] = t_types
            
        # 3. Load the "Agent Types" (Soldiers, Tanks, etc.)
        new_agent_types = {"Attacker": {}, "Defender": {}}
        
        # We look in the new structured folders.
        agent_paths = ["Master Database/Agent/Attackers/*.json", "Master Database/Agent/Defenders/*.json"]
        for path_pattern in agent_paths:
            for key in self.db.keys(path_pattern):
                data = self.db.get(key)
                if data and "name" in data:
                    uid = data["name"].replace(" ", "_")
                    attrs = data.get("attributes", {})
                    caps = data.get("capabilities", {})
                    
                    # Merge attributes and capabilities (Capabilities take priority in military sims)
                    # Merge attributes and capabilities (Capabilities take priority in military sims)
                    role = data.get("role") or caps.get("role") or attrs.get("role", "attacker")
                    
                    # Determine Side (Side Catalog) based on path
                    if "Attacker" in path_pattern:
                        role_key = "Attacker"
                    elif "Defender" in path_pattern:
                        role_key = "Defender"
                    else:
                        # Fallback for legacy "config/agents/"
                        role_key = "Attacker" if "attack" in role.lower() else "Defender"
                    
                    agent_info = {
                        "name": data["name"],
                        "cost": data.get("cost", 100),
                        "personnel": data.get("personnel") or caps.get("personnel") or attrs.get("personnel", 100),
                        "icon": data.get("icon") or caps.get("icon") or attrs.get("icon", "agent.svg"),
                        "role": role.lower(),
                        "weight": data.get("weight") or caps.get("weight") or attrs.get("weight", 1),
                        "hierarchy": data.get("hierarchy") or caps.get("hierarchy") or attrs.get("hierarchy", "Platoon"),
                        "capabilities": {
                            "speed": caps.get("speed") or attrs.get("movement") or 5,
                            "range": caps.get("range") or attrs.get("attack_range") or 2,
                            "attack": caps.get("attack") or attrs.get("attack") or 25,
                            "defense": caps.get("defense") or attrs.get("defense") or 20,
                            "stealth": caps.get("stealth") or attrs.get("stealth") or 0
                        },
                        "actions": data.get("actions", caps.get("actions") or attrs.get("actions", ["FIRE", "MOVE", "HOLD"]))
                    }
                    new_agent_types[role_key][uid] = agent_info
        
        # If we successfully found units, update our catalog.
        if new_agent_types["Attacker"] or new_agent_types["Defender"]:
            self.catalogs["agent_types"] = new_agent_types
        else:
            u_cat = self.db.get("Master/UnitCatalog")
            if u_cat: self.catalogs["agent_types"] = {"Attacker": u_cat.copy(), "Defender": u_cat.copy()}

        # 4. Load Zones, Obstacles, Hierarchy, Weapons, and Resources
        self.catalogs["zone_types"] = self.db.get("Master Database/ZoneCatalog") or {}
        self.catalogs["obstacle_types"] = self.db.get("Master Database/ObstacleCatalog") or {}
        
        # WEAPONS SYSTEM: Load from new structured directory or legacy file.
        weapon_keys = self.db.keys("Master Database/Items/Weapons/*.json")
        if weapon_keys:
            all_weapons = {}
            for wk in weapon_keys:
                w_data = self.db.get(wk)
                if isinstance(w_data, dict): all_weapons.update(w_data)
            self.catalogs["weapons"] = all_weapons
        else:
            weapon_keys = self.db.keys("**/rules/weapons.json")
            if weapon_keys: self.catalogs["weapons"] = self.db.get(weapon_keys[0])

        # RESOURCES SYSTEM: Load the available resource types.
        resource_keys = self.db.keys("Master Database/Items/Resources/*.json")
        all_resources = {}
        for rk in resource_keys:
            r_data = self.db.get(rk)
            if isinstance(r_data, dict): all_resources.update(r_data)
        self.catalogs["resources"] = all_resources
        
        # MILITARY STRUCTURE: Load the hierarchy definitions (Squad -> Regiment)
        hier_keys = self.db.keys("**/rules/hierarchy.json")

    # --- READ ACCESS ---
    @property
    def defaults(self): return self.catalogs["defaults"]
    @property
    def terrain_types(self): return self.catalogs["terrain_types"]
    @property
    def agent_types(self): return self.catalogs["agent_types"]
    @property
    def zone_types(self): return self.catalogs["zone_types"]
    @property
    def obstacle_types(self): return self.catalogs["obstacle_types"]
    @property
    def hierarchy(self): return self.catalogs["hierarchy"]
    @property
    def weapons(self): return self.catalogs["weapons"]
    @property
    def resources(self): return self.catalogs["resources"]

    # --- DATA SAVING & LOADING ---
    # These wrap the low-level database calls with the correct folder paths.
    
    def save_terrain_data(self, data: Dict[str, Any], filename: str) -> bool:
        doc_name = os.path.splitext(filename)[0]
        return self.db.set(f"maps/terrain/{doc_name}", data)

    def load_terrain_data(self, filename: str) -> Optional[Dict[str, Any]]:
        doc_name = os.path.splitext(filename)[0]
        return self.db.get(f"maps/terrain/{doc_name}")
        
    def save_scenario_data(self, data: Dict[str, Any], filename: str) -> bool:
        doc_name = os.path.splitext(filename)[0]
        return self.db.set(f"maps/scenarios/{doc_name}", data)

    def load_scenario_data(self, filename: str) -> Optional[Dict[str, Any]]:
        doc_name = os.path.splitext(filename)[0]
        return self.db.get(f"maps/scenarios/{doc_name}")

    def save_scenario(self, filename: str, data: Dict[str, Any], project_path: Optional[str] = None) -> bool:
        """Saves a complete scenario to a specific project folder.
        
        DB keys are ALWAYS relative to root_dir (e.g. 'Projects/Foo/Maps/Bar/Scenarios/Name').
        project_path may be absolute or CWD-relative — we normalize it to be
        relative to db.root_dir so the key never contains the content prefix.
        """
        doc_name = NamingUtils.sanitize_filename(os.path.splitext(filename)[0])
        if project_path:
            # Compute key relative to DB root (both as absolute paths)
            db_root_abs = os.path.abspath(getattr(self.db, 'root_dir', 'content'))
            project_abs = os.path.abspath(project_path)
            try:
                rel_project = os.path.relpath(project_abs, db_root_abs)
            except ValueError:
                # Windows: different drives — fall back to just the scenario name
                rel_project = os.path.basename(project_abs)
            
            key = f"{rel_project}/Scenarios/{doc_name}"
            return self.db.set(key, data)
        return self.db.set(f"scenarios/{doc_name}", data)


    # --- PROJECTS ---
    
    def get_projects(self) -> List[str]:
        """Scans the 'Projects' folder for monolithic .json files."""
        # Check for new monolithic files
        json_keys = self.db.keys("Projects/*.json")
        projects = [os.path.basename(k) for k in json_keys]
        
        # Also check for legacy folders
        legacy_keys = self.db.keys("Projects/*/project_config.json")
        for k in legacy_keys:
            parts = k.split("/")
            if len(parts) >= 2 and parts[1] not in projects:
                projects.append(parts[1])
                
        return list(set(projects))

    def create_project(self, name: str) -> bool:
        """Creates a new monolithic project JSON (stub)."""
        key = f"Projects/{name}"
        if self.db.exists(key):
            return False
        return self.db.set(key, {"project_name": name, "version": "2.0"})

    def get_maps(self, project_name: str) -> List[str]:
        """Finds all the terrain maps that belong to a specific project."""
        keys = self.db.keys(f"Projects/{project_name}/Maps/*/Terrain.json")
        maps = []
        for k in keys:
            parts = k.split("/")
            if len(parts) >= 4 and parts[2] == "Maps":
                maps.append(parts[3])
        return list(set(maps))

    def create_new_map(self, project_name: str, map_name: str, width: int, height: int) -> bool:
        """Initializes the empty grid for a new map."""
        key = f"Projects/{project_name}/Maps/{map_name}/Terrain"
        if self.db.exists(key): return False
        
        terrain = {"dimensions": {"width": width, "height": height}, "grid": {"default": "plain"}, "layers": {}}
        return self.db.set(key, terrain)

    def resolve_unit_config(self, entity) -> Dict[str, Any]:
        """
        The Master Resolver: Given an entity, it determines its full stats, weapons, 
        and capabilities by checking the JSON catalogs first, then falling back to defaults.
        """
        # Resolve unit identity
        unit_type = entity.get_attribute("type", None)
        if not unit_type:
            unit_type = entity.get_attribute("unit_type", None)
            
        if not unit_type:
            # Infer from name
            name = getattr(entity, 'name', '')
            for ut in UNIT_TYPES:
                if ut in name:
                    unit_type = ut
                    break
                    
        side = entity.get_attribute("side", "Attacker")
        
        # 1. Primary Lookup: Try JSON Catalogs
        side_catalog = self.catalogs["agent_types"].get(side, {})
        template = side_catalog.get(unit_type, {})
        
        if template:
            caps = template.get("capabilities", {})
            role = template.get("role", "attacker").lower()
            
            # WEAPON RESOLUTION
            major_weapon_names = []
            if hasattr(entity, 'inventory') and entity.inventory.get("weapons"):
                major_weapon_names = [w.name if hasattr(w, 'name') else str(w) for w in entity.inventory["weapons"]]
            else:
                major_weapon_names = entity.get_attribute("weapons", [])
                
            if not major_weapon_names and "inventory" in template:
                major_weapon_names = template["inventory"].get("weapons", [])
                
            if not major_weapon_names:
                # Default weapon mapping
                if "Fire" in unit_type: major_weapon_names = ["LMG"]
                elif "Sniper" in unit_type: major_weapon_names = ["Sniper_Rifle"]
                elif "HeavyGunner" in unit_type: major_weapon_names = ["HMG"]
                else: major_weapon_names = ["INSAS"]
                
            equipped_weapons = []
            max_range = 1.0
            
            for w_name in major_weapon_names:
                w_info = self.catalogs["weapons"].get(w_name)
                if w_info:
                    w_obj = Weapon(
                        name=w_info["name"],
                        weapon_type=w_info["category"],
                        max_range=w_info["max_range"],
                        lethality=w_info.get("lethality"),
                        suppression=w_info.get("suppression"),
                        accuracy=w_info["accuracy"],
                        rate_of_fire=w_info["rate_of_fire"],
                        ammo_type=w_info["ammo_type"],
                        damage=w_info.get("damage")
                    )
                    equipped_weapons.append(w_obj)
            
            # Derive Personnel
            derived_personnel = template.get("personnel", 100)
            
            if equipped_weapons:
                max_range = max(w.max_range for w in equipped_weapons)
                weapon = equipped_weapons[0]
                combat_factor = weapon.lethality / 5.0 if weapon.lethality else 5.0
            else:
                weapon = None
                max_range = 2.0
                combat_factor = 5.0

            return {
                "unit_type": unit_type,
                "role": role,
                "personnel": derived_personnel,
                "weapon": weapon,
                "weapons": equipped_weapons,
                "vision_range": max_range + 3,
                "range_of_fire": max_range,
                "speed_of_action": template.get("speed") or caps.get("speed", 5.0),
                "combat_factor": combat_factor,
                "allowed_actions": template.get("actions", ["FIRE", "MOVE", "HOLD / END TURN"]),
                "icon": template.get("icon") or caps.get("icon") or "agent.svg"
            }

        # 2. Secondary Lookup: Hardcoded fallback
        type_info = UNIT_TYPES.get(unit_type, {"role": "attacker", "personnel": 100})
        role = type_info.get("role", "attacker")
        personnel = type_info.get("personnel", 100)
        role_params = ROLES.get(role, ROLES["attacker"])
        
        return {
            "unit_type": unit_type,
            "role": role,
            "personnel": personnel,
            "weapon": None,
            "ammo": 0,
            "vision_range": role_params["vision_range"],
            "range_of_fire": role_params["range_of_fire"],
            "speed_of_action": role_params["speed_of_action"],
            "combat_factor": role_params["combat_factor"],
            "allowed_actions": type_info.get("actions", ["FIRE", "MOVE", "HOLD / END TURN"])
        }
