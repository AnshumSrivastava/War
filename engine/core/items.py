"""
FILE: engine/core/items.py
ROLE: The "Armory" (Inventory and Equipment Definitions).

DESCRIPTION:
This module defines the modular components that make up an agent's loadout.
"""

class Resource:
    """Consumable items like Ammo, Fuel, or Medical Supplies."""
    def __init__(self, name: str, weight: float = 0.01, description: str = ""):
        self.name = name
        self.weight = weight
        self.description = description

    def __repr__(self):
        return f"<Resource {self.name}>"

class Weapon:
    """
    A modular weapon system that can be assigned to any agent.
    """
    def __init__(self, 
                 name: str, 
                 weapon_type: str, # "Direct", "Indirect", "Melee"
                 max_range: float,
                 lethality: float, 
                 suppression: float, 
                 accuracy: float,
                 rate_of_fire: int,
                 ammo_type: str,
                 ammo_consumption: int = 1,
                 weight: float = 5.0,
                 damage: float = None): # For legacy compatibility
        self.name = name
        self.weapon_type = weapon_type
        self.max_range = max_range
        self.lethality = lethality or (damage * rate_of_fire if damage else 0)
        self.suppression = suppression or self.lethality
        self.accuracy = accuracy
        self.rate_of_fire = rate_of_fire
        self.ammo_type = ammo_type
        self.ammo_consumption = ammo_consumption
        self.weight = weight
        self.damage = damage or (lethality / rate_of_fire if rate_of_fire else 0)

    def __repr__(self):
        return f"<Weapon {self.name} ({self.weapon_type})>"
