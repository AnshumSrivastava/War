from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from engine.core.hex_math import Hex
from engine.core.map import Map
from engine.core.entity_manager import EntityManager

class Command(ABC):
    """
    THE BLUEPRINT: A standard 'Action' that the game knows how to do AND undo.
    Every command must have a 'Do' button (Redo) and a 'CTRL-Z' button (Undo).
    """
    
    @abstractmethod
    def undo(self):
        """Reverses the action (The CTRL-Z button)."""
        pass

    @abstractmethod
    def redo(self):
        """Re-performs the action (The CTRL-Y button)."""
        pass

class MacroCommand(Command):
    """
    THE BATCH: Grouping multiple tiny actions into one big step.
    For example, if you move 5 soldiers at once, this ensures they all 
    undo together if you press CTRL-Z.
    """
    def __init__(self, commands: List[Command]):
        self.commands = commands
        
    def redo(self):
        for cmd in self.commands:
            cmd.redo()
            
    def undo(self):
        for cmd in reversed(self.commands):
            cmd.undo()

class UndoStack:
    """
    THE HISTORY BOOK: Remembers everything you've done recently.
    It keeps two stacks: things in the past (History) and things you 
    accidentally undid (Future).
    """
    def __init__(self, limit: int = 50):
        self._history: List[Command] = []
        self._future: List[Command] = []
        self._limit = limit
        
        self._batch_mode = False
        self._current_batch: List[Command] = []

    def push(self, command: Command):
        """Adds a new action to the top of the history book."""
        if self._batch_mode:
            self._current_batch.append(command)
        else:
            self._history.append(command)
            # When you do something NEW, you can't 'Redo' anything old anymore.
            self._future.clear() 
            
            # Don't let the history book get too thick (memory limit).
            if len(self._history) > self._limit:
                self._history.pop(0)

    def undo(self):
        """Go one step back in time."""
        if not self._history:
            return
        cmd = self._history.pop()
        cmd.undo()
        self._future.append(cmd)

    def redo(self):
        """Move one step forward in time (re-do an action you just undid)."""
        if not self._future:
            return
        cmd = self._future.pop()
        cmd.redo()
        self._history.append(cmd)
        
    def begin_macro(self):
        """Start recording a 'Batch' of actions."""
        self._batch_mode = True
        self._current_batch = []

    def end_macro(self):
        """Stop recording and save the batch as one single step in history."""
        self._batch_mode = False
        if self._current_batch:
            if len(self._current_batch) == 1:
                self.push(self._current_batch[0])
            else:
                 self.push(MacroCommand(self._current_batch))
            self._current_batch = []

# --- Concrete Commands (The actual 'Tools') ---

class SetTerrainCommand(Command):
    """PAINTER: Changes the ground from grass to mountain (or vice versa)."""
    def __init__(self, game_map: Map, hex_obj: Hex, new_data: Dict, old_data: Dict):
        self.map = game_map
        self.hex_obj = hex_obj
        self.new_data = new_data
        self.old_data = old_data

    def redo(self):
        current = self.map.get_terrain(self.hex_obj)
        current.update(self.new_data)
        self.map.set_terrain(self.hex_obj, current)

    def undo(self):
        self.map.set_terrain(self.hex_obj, self.old_data)

class PlaceEntityCommand(Command):
    """DEPLOYER: Places a new unit or soldier onto the map."""
    def __init__(self, game_map: Map, entity_manager: EntityManager, entity_id: str, hex_obj: Hex, old_hex: Optional[Hex], data: Optional[Dict] = None):
        self.map = game_map
        self.em = entity_manager
        self.entity_id = entity_id
        self.hex_obj = hex_obj
        self.old_hex = old_hex
        self.data = data # Entity Data to recreate if needed

    def redo(self):
        # Ensure the unit actually exists in the game records.
        if hasattr(self.map, 'remove_entity_pos') and not self.em.get_entity(self.entity_id) and self.data:
             from engine.core.entity_manager import Agent
             agent = Agent(agent_id=self.entity_id, name=self.data.get("name","Unit"))
             agent.attributes = self.data.get("attributes", {})
             self.em.register_entity(agent)

        self.map.place_entity(self.entity_id, self.hex_obj)

    def undo(self):
        if self.old_hex:
            # Move them back to their previous hexagon.
            self.map.place_entity(self.entity_id, self.old_hex)
        else:
            # It was a brand new unit, so delete it entirely.
            if hasattr(self.map, 'remove_entity_pos'):
                self.map.remove_entity_pos(self.entity_id)
            self.em.remove_entity(self.entity_id)

class RemoveEntityCommand(Command):
    """BULLDOZER: Deletes a unit from the map."""
    def __init__(self, game_map: Map, entity_manager: EntityManager, entity_id: str, old_hex: Hex):
        self.map = game_map
        self.em = entity_manager
        self.entity_id = entity_id
        self.old_hex = old_hex
        # Keep a backup of the unit's stats so we can bring them back to life.
        ent = self.em.get_entity(entity_id)
        self.data = {
            "name": ent.name,
            "attributes": ent.attributes.copy()
        } if ent else {}

    def redo(self):
         if hasattr(self.map, 'remove_entity_pos'):
             self.map.remove_entity_pos(self.entity_id)
         pass 

    def undo(self):
        # Bring the unit back to the exact hexagon they were deleted from.
        if not self.em.get_entity(self.entity_id) and self.data:
             from engine.core.entity_manager import Agent
             agent = Agent(agent_id=self.entity_id, name=self.data.get("name","Unit"))
             agent.attributes = self.data.get("attributes", {})
             self.em.register_entity(agent)
             
        self.map.place_entity(self.entity_id, self.old_hex)


class ClearTerrainCommand(Command):
    """ERASER: Wipes everything off a specific hexagon."""
    def __init__(self, game_map: Map, hex_obj: Hex, old_data: Dict):
        self.map = game_map
        self.hex_obj = hex_obj
        self.old_data = old_data 

    def redo(self):
        self.map.clear_hex(self.hex_obj)

    def undo(self):
        self.map.set_terrain(self.hex_obj, self.old_data)

class AddZoneCommand(Command):
    """LAND SURVEYOR: Draws a new boundary label (like 'Victory Objective')."""
    def __init__(self, game_map: Map, zone_id: str, new_data: Dict):
        self.map = game_map
        self.zone_id = zone_id
        self.new_data = new_data

    def redo(self):
        self.map.add_zone(self.zone_id, self.new_data)

    def undo(self):
        self.map.remove_zone(self.zone_id)

class UpdateZoneCommand(Command):
    """REMODELER: Changes the settings of an existing zone."""
    def __init__(self, game_map: Map, zone_id: str, new_data: Dict, old_data: Dict):
        self.map = game_map
        self.zone_id = zone_id
        self.new_data = new_data
        self.old_data = old_data

    def redo(self):
        zones = self.map.get_zones()
        if self.zone_id in zones:
            zones[self.zone_id].update(self.new_data)

    def undo(self):
        zones = self.map.get_zones()
        if self.zone_id in zones:
             zones[self.zone_id] = self.old_data.copy()

class RemoveZoneCommand(Command):
    """ERASER: Deletes a boundary label."""
    def __init__(self, game_map: Map, zone_id: str, old_data: Dict):
        self.map = game_map
        self.zone_id = zone_id
        self.old_data = old_data

    def redo(self):
        self.map.remove_zone(self.zone_id)

    def undo(self):
        self.map.add_zone(self.zone_id, self.old_data)

class AddPathCommand(Command):
    """ROAD BUILDER: Draws a line or route on the map."""
    def __init__(self, game_map: Map, path_id: str, new_data: Dict):
        self.map = game_map
        self.path_id = path_id
        self.new_data = new_data

    def redo(self):
        self.map.add_path(self.path_id, self.new_data)

    def undo(self):
        self.map.remove_path(self.path_id)

class UpdatePathCommand(Command):
    """ROAD WORK: Changes the properties of a route."""
    def __init__(self, game_map: Map, path_id: str, new_data: Dict, old_data: Dict):
        self.map = game_map
        self.path_id = path_id
        self.new_data = new_data
        self.old_data = old_data

    def redo(self):
        paths = self.map.get_paths()
        if self.path_id in paths:
            paths[self.path_id].update(self.new_data)

    def undo(self):
         paths = self.map.get_paths()
         if self.path_id in paths:
             paths[self.path_id] = self.old_data.copy()

class MoveEntityCommand(Command):
    """TRANSPORTER: Relocates a unit from Hex A to Hex B."""
    def __init__(self, game_map: Map, entity_id: str, new_hex: Hex, old_hex: Hex):
        self.map = game_map
        self.entity_id = entity_id
        self.new_hex = new_hex
        self.old_hex = old_hex

    def redo(self):
        self.map.place_entity(self.entity_id, self.new_hex)

    def undo(self):
        self.map.place_entity(self.entity_id, self.old_hex)

class MoveZoneCommand(Command):
    """RELOCATOR: Moves an entire zone to a new coordinate."""
    def __init__(self, game_map: Map, zone_id: str, new_data: Dict, old_data: Dict):
        self.map = game_map
        self.zone_id = zone_id
        self.new_data = new_data
        self.old_data = old_data

    def redo(self):
        zones = self.map.get_zones()
        if self.zone_id in zones:
            zones[self.zone_id].update(self.new_data)
            
    def undo(self):
        zones = self.map.get_zones()
        if self.zone_id in zones:
            zones[self.zone_id] = self.old_data.copy()

class DamageEntityCommand(Command):
    """UNDO ACTION: Reverses the damage dealt to a unit's personnel count."""
    def __init__(self, entity_manager: EntityManager, entity_id: str, damage: int):
        self.em = entity_manager
        self.entity_id = entity_id
        self.damage = damage
        self.old_personnel = 0
        
        # We record the personnel count BEFORE the strike happened.
        ent = self.em.get_entity(entity_id)
        if ent:
            self.old_personnel = ent.get_attribute("personnel", 100)

    def redo(self):
        """RE-APPLY: Subtract the damage again."""
        ent = self.em.get_entity(self.entity_id)
        if ent:
            new_personnel = max(0, self.old_personnel - self.damage)
            ent.set_attribute("personnel", new_personnel)

    def undo(self):
        """RESTORE: Reset the personnel back to the original number."""
        ent = self.em.get_entity(self.entity_id)
        if ent:
            ent.set_attribute("personnel", self.old_personnel)
