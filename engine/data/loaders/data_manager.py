"""
FILE: data/loaders/data_manager.py
ROLE: The "Library Clerk" (DataManager).

DESCRIPTION:
This file is the main interface for reading and writing data to the disk. 
Instead of every part of the app trying to figure out where "Scenario1.json" is 
hidden on the hard drive, they just ask the DataManager.

It acts as a "Facade" - a friendly face that hides the complexity of:
1. The low-level database (JSONDatabase).
2. The business rules for how terrain and units interact (MasterDataService).
"""

import os
from typing import Dict, Any, List, Optional
from engine.core.entity_manager import Agent
from engine.core.hex_math import Hex
from engine.data.api.json_db import JSONDatabase
from engine.data.services.master_data_service import MasterDataService

class DataManager:
    """
    The central hub for all file operations (Loading maps, saving agents, etc.).
    """
    def __init__(self, content_root: str = "content"):
        # The 'content' folder is where all the game data (maps, units, rules) lives.
        self.content_root = content_root
        
        # --- THE STORAGE LAYERS ---
        # Layer 1: The 'Warehouse' (Raw JSON reading/writing)
        self._db = JSONDatabase(content_root)
        
        # Layer 2: The 'Catalog' (Translates raw files into game objects)
        self._service = MasterDataService(self._db)

    def reload_configs(self):
        """Forces the app to re-read the JSON files from disk (Hot-reload)."""
        self._service.reload_catalogs()

    # --- THE DATA CATALOGS ---
    # These properties provide quick access to the standard libraries of things.
    @property
    def defaults(self): 
        """Standard default values for a new, empty hexagon."""
        return self._service.defaults
        
    @property
    def terrain_types(self): 
        """The list of all known terrains (Forest, Desert, etc.) and their stats."""
        return self._service.terrain_types
        
    @property
    def agent_types(self): 
        """The list of all known unit types (Infantry, Tank, etc.)."""
        return self._service.agent_types
        
    @property
    def zone_types(self): 
        """The list of different map areas (Red Base, Blue Base, etc.)."""
        return self._service.zone_types
        
    @property
    def obstacle_types(self): 
        """The list of things that block movement (Walls, Rivers)."""
        return self._service.obstacle_types

    @property
    def hierarchy(self):
        """The military structure definitions (Squad, Platoon, etc.)."""
        return self._service.hierarchy

    @property
    def weapons(self):
        """The weapons and lethality specifications."""
        return self._service.weapons

    @property
    def resources(self):
        """The available resource types (Ammo, Fuel, etc.)."""
        return self._service.resources

    def get_available_terrains(self):
        """Returns just the names of the terrain types for use in UI dropdowns."""
        return list(self.terrain_types.keys())

    def get_hex_full_attributes(self, hex_obj: Hex, map_instance) -> Dict[str, Any]:
        """
        Calculates the FINAL stats for a single hex.
        It starts with the defaults, then adds the terrain stats, 
        then adds any specific custom data for that exact hex.
        """
        final_attrs = self.defaults.copy()
        specific_data = map_instance.get_terrain(hex_obj)
        t_type = specific_data.get("type")
        if t_type and t_type in self.terrain_types:
            final_attrs.update(self.terrain_types[t_type])
        final_attrs.update(specific_data)
        return final_attrs

    # --- MAP & SCENARIO STORAGE ---
    # These functions handle the high-level 'Save Game' and 'Load Game' logic.
    
    def save_terrain_data(self, data: Dict[str, Any], filename: str) -> bool:
        """Saves the landscape (the hexes) of a map."""
        return self._service.save_terrain_data(data, filename)

    def load_terrain_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """Loads the landscape from a file."""
        return self._service.load_terrain_data(filename)
        
    def save_scenario_data(self, data: Dict[str, Any], filename: str) -> bool:
        """Saves a specific scenario (unit placement, objectives)."""
        return self._service.save_scenario_data(data, filename)

    def load_scenario_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """Loads a scenario and its units."""
        return self._service.load_scenario_data(filename)

    def list_scenarios(self) -> List[str]:
        """Returns a list of all saved scenarios."""
        # We look specifically in the maps/scenarios folder
        keys = self._db.keys("maps/scenarios/*.json")
        # Extract just the filenames
        return [os.path.basename(k) for k in keys]

    def save_scenario(self, filename: str, data: Dict[str, Any], project_path: Optional[str] = None) -> bool:
        """
        Saves a complete scenario, including its map data, to a specified file within a project.
        This method orchestrates the saving of both terrain and scenario-specific data.
        """
        return self._service.save_scenario(filename, data, project_path)

    # --- AGENT TEMPLATES ---
    
    def load_agent_template(self, filename: str) -> Optional[Agent]:
        """Loads a single unit preset (e.g., 'Standard Soldier') from a file."""
        data = self._service.load_agent_dict(filename)
        if not data: return None
        agent = Agent(name=data.get("name", "Unnamed Agent"))
        agent.load_from_dict(data)
        return agent

    def list_available_agents(self) -> List[str]:
        """Looks in the 'presets/agents' folder to see what units we can create."""
        path = os.path.join(self.content_root, "presets", "agents")
        if not os.path.exists(path): return []
        return [f for f in os.listdir(path) if f.endswith('.json')]
        
    # --- PROJECT MANAGEMENT ---
    
    def get_projects(self) -> List[str]:
        """Returns a list of all 'Project' folders in the content directory."""
        return self._service.get_projects()

    def create_project(self, name: str) -> bool:
        """Creates a new folder for a new project."""
        return self._service.create_project(name)

    def get_maps(self, project_name: str) -> List[str]:
        """Returns all the maps inside a specific project."""
        return self._service.get_maps(project_name)

    def create_new_map(self, project_name: str, map_name: str, width: int, height: int) -> bool:
        """Sets up the folder structure for a brand new map."""
        return self._service.create_new_map(project_name, map_name, width, height)

    def resolve_unit_config(self, entity) -> Dict[str, Any]:
        """Delegates unit configuration resolution to the MasterDataService."""
        return self._service.resolve_unit_config(entity)

# --- ALIASES ---
# These are just extra names for the same class, kept so that old code doesn't break.
TerrainController = DataManager
DataController = DataManager
DataLoader = DataManager
