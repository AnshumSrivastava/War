"""
FILE: engine/action/base_action.py
ROLE: The "Blueprint" for every possible unit action.

DESCRIPTION:
This is an 'Abstract' file. It doesn't do anything on its own, but it sets 
the rules for what every other action file (like Fire, Move, or Commit) 
MUST be able to do. 
Every action in the game is like a tool in a Swiss Army knife - they all 
look different, but they all fit into the same handle.
"""
from abc import ABC, abstractmethod

class BaseAction(ABC):
    """
    The Base Class. If you want to add a new ability to the game (like 'Heal' or 'Scout'), 
    you must copy this template.
    """
    def __init__(self, action_id, name):
        """
        IDENTIFICATION: Every action needs a code name (ID) and a human name.
        """
        # The 'ID' is for the computer (e.g., "FIRE_WPN").
        self.action_id = action_id 
        # The 'Name' is for the human user (e.g., "Fire Weapon").
        self.name = name           

    @abstractmethod
    def is_allowed(self, entity, game_map, target=None) -> bool:
        """
        PRE-CHECK: This function must return True or False. 
        It asks: "In the current situation, is the unit physically allowed to do this?"
        For example: A unit cannot shoot if they are out of ammo or have no target.
        """
        pass

    @abstractmethod
    def execute(self, entity, game_map, target=None, **kwargs):
        """
        PERFORMANCE: This is where the actual work happens. 
        It returns a status report and data for the graphics window (events).
        """
        pass
