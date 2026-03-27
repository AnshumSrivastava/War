"""
FILE: engine/core/entity_manager.py
ROLE: The "Staff" manager for every unit and object in the game.

DESCRIPTION:
In a game, everything that isn't the ground (terrain) is an "Entity." 
This includes soldiers, tanks, obstacles, and even capture points.

This file handles:
1. Creating new units (Agents).
2. Giving them special abilities (Components).
3. Storing their stats like Health, Speed, and Side (Attributes).
4. Keeping a central list (the EntityManager) so the game can easily find 
   any unit by its ID.
"""

from typing import Any, Dict, List, Optional
import uuid

class AttributeDict(dict):
    """
    A fancy dictionary that allows you to access items using a dot (e.g., unit.health) 
    instead of square brackets (e.g., unit['health']). 
    It makes the code much cleaner and easier to read.
    """
    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError:
            # If the stat doesn't exist, we raise a clear error
            raise AttributeError(f"Attribute '{item}' not found.")

    def __setattr__(self, key: str, value: Any):
        self[key] = value

class BaseEntity:
    """
    The 'Generic' template for any object in the game.
    It doesn't have many rules yet - it just has a Name and an ID.
    Think of this as the 'Skeleton' that can become anything.
    """
    def __init__(self, entity_id: Optional[str] = None, name: str = "Unnamed"):
        """
        INITIALIZE: Create a new base structure for a unit or object.
        """
        # Every unit gets a unique ID (like a Fingerprint) so the game doesn't confuse them.
        self.id: str = entity_id or str(uuid.uuid4())
        self.name: str = name
        
        # 'Attributes' are the unit's stats (Health, Speed, Team, etc.)
        self.attributes: AttributeDict = AttributeDict()
        
        # 'Components' are the unit's abilities (Can it shoot? Can it move?)
        self.components: List[str] = [] 

    def set_attribute(self, key: str, value: Any):
        """Sets a specific entity attribute (e.g., personnel, status, side)."""
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Retrieves an entity attribute value."""
        return self.attributes.get(key, default)

    def has_component(self, component_name: str) -> bool:
        """Checks if the unit is capable of a specific action (e.g., 'Combat')."""
        return component_name in self.components

    def add_component(self, component_name: str):
        """Gives the unit a new capability (e.g., 'Movement')."""
        if component_name not in self.components:
            self.components.append(component_name)

    def load_from_dict(self, data: Dict[str, Any]):
        """
        RESTORATION: Takes data from a saved file and applies it to this unit.
        Used during game loading.
        """
        if "name" in data:
            self.name = data["name"]
        
        if "attributes" in data:
            for k, v in data["attributes"].items():
                self.attributes[k] = v
        
        if "components" in data:
            for comp in data["components"]:
                self.add_component(comp)

        if "inventory" in data:
            inv = data["inventory"]
            # weapons would normally be loaded via MasterDataService resolution
            # self.inventory is only initialized in Agent subclass, so check existence
            if hasattr(self, "inventory"):
                self.inventory["resources"] = inv.get("resources", {})
                self.inventory["weapons"] = []

class Agent(BaseEntity):
    """
    A specialized unit that is 'Alive'. 
    Unlike a simple rock or building, an Agent can Move, Fight, and make AI decisions.
    """
    def __init__(self, agent_id: Optional[str] = None, name: str = "Unknown Agent"):
        # We import this inside the function to avoid 'circular' errors
        from engine.simulation.command import AgentCommand
        super().__init__(agent_id, name)
        
        # The 'current_command' is what the agent is planning to do next.
        self.current_command: Optional[AgentCommand] = None
        
        # Every Agent starts with these three basic abilities:
        self.add_component("Movement")
        self.add_component("Combat")
        self.add_component("AI")
        
        # --- INVENTORY SYSTEM ---
        self.inventory: Dict[str, Any] = {
            "weapons": [],     # List of Weapon objects
            "resources": {},   # Dictionary: { "AmmoName": quantity_int }
            "equipment": []    # Passive items
        }
        
        # --- HIERARCHY ATTRIBUTES ---
        self.set_attribute("home_hex", None)
        self.set_attribute("vulnerability_score", 0.0)
        
        # Default settings
        if not self.get_attribute("type"):
             self.set_attribute("type", "FireAgent")
        if not self.get_attribute("subtype"):
             self.set_attribute("subtype", "Direct")

    def __repr__(self) -> str:
        """How the unit appears in the computer's logs."""
        return f"<Agent {self.name} ({self.id})>"

class EntityManager:
    """
    The 'Registry' for the game.
    Keeps a master list of every unit currently on the map.
    """
    def __init__(self):
        # A simple dictionary: { unitID : unitObject }
        self._entities: Dict[str, BaseEntity] = {}

    def register_entity(self, entity: BaseEntity):
        """Adds a new unit to the master game list."""
        self._entities[entity.id] = entity

    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """Finds and returns a unit based on its ID."""
        return self._entities.get(entity_id)

    def get_all_entities(self) -> List[BaseEntity]:
        """Returns a list of every unit in the game."""
        return list(self._entities.values())

    def remove_entity(self, entity_id: str):
        """Deletes a unit from the game."""
        if entity_id in self._entities:
            del self._entities[entity_id]

    def clear(self):
        """Wipes the list clean for a new game."""
        self._entities.clear()
