"""
FILE: engine/state/threat_map.py
ROLE: Risk Assessment module for the hex grid map.

DESCRIPTION:
This module evaluates the battlefield to determine which locations are "dangerous" (i.e., currently under enemy observation or in their line of fire). 
It calculates a "Threat Score" for each hex, which is used by the Pathfinder to find safer routes.
"""

from typing import Dict, Tuple
from engine.core.hex_math import Hex, HexMath
from engine.core.map import Map
from engine.core.entity_manager import EntityManager

class ThreatMap:
    """
    Evaluates and caches the danger level of every hex on the map based on 
    enemy positions and capabilities.
    """
    def __init__(self):
        # A dictionary mapping a hex coordinate tuple (q, r, s) to a float Threat Score.
        # Example: {(0, 0, 0): 2.0} means two enemies can currently fire upon the origin hex.
        self.threat_scores: Dict[Tuple[int, int, int], float] = {}
        # Separate fields by faction for granular threat assessment.
        self.faction_threats: Dict[str, Dict[Tuple[int, int, int], float]] = {
            "Attacker": {}, "Defender": {}, "Neutral": {}
        }
        
    def clear(self):
        """Reset the threat map."""
        self.threat_scores.clear()
        
    def get_threat(self, hex_coord: Hex) -> float:
        """Get the current threat penalty for a specific hexagon."""
        return self.threat_scores.get((hex_coord.q, hex_coord.r, hex_coord.s), 0.0)

    def update(self, entity_manager: EntityManager, game_map: Map, data_controller=None):
        """
        Recalculate the entire threat map. 
        This should be called at the beginning of every turn/tick.
        """
        self.clear()
        
        # Get all active units capable of fighting
        active_entities = [e for e in entity_manager.get_all_entities() if int(e.get_attribute("personnel", 0)) > 0]
        
        # For this tactical level, we consider ALL active entities.
        # A fully robust version would calculate Threat *relative to the querying unit's side*
        # (i.e., Attacker Threat Map vs Defender Threat Map).
        # For simplicity in pathfinding, we calculate an absolute "Activity Zone" or 
        # separate fields by faction. Here, we'll build separate faction maps.
        
        self.faction_threats = {"Attacker": {}, "Defender": {}, "Neutral": {}}

        for entity in active_entities:
            side = entity.get_attribute("side", "Neutral")
            if side not in self.faction_threats:
                self.faction_threats[side] = {}
                
            my_pos = game_map.get_entity_position(entity.id)
            if not my_pos:
                continue
                
            if data_controller:
                config = data_controller.resolve_unit_config(entity)
                # Use fire_range if available, then fallback to vision, then default
                fire_range = int(entity.get_attribute("fire_range", config.get("range_of_fire", config.get("vision_range", 3))))
            else:
                fire_range = int(entity.get_attribute("fire_range", 3))
            
            # Simplified line-of-fire: Mark every hex in range along the 6 hex axes
            for direction_idx in range(6):
                current_hex = my_pos
                for dist in range(1, fire_range + 1):
                    current_hex = HexMath.neighbor(current_hex, direction_idx)
                    
                    # We want to map threats even if the hex is "empty" space on the theoretical map grid,
                    # but typically we only care about valid map spaces. 
                    # Use get_terrain to safely check if the hex exists on the map.
                    if game_map.get_terrain(current_hex):
                        coord_tuple = (current_hex.q, current_hex.r, current_hex.s)
                        
                        # Add +1.0 Threat to this faction's projection for this hex
                        current_threat = self.faction_threats[side].get(coord_tuple, 0.0)
                        self.faction_threats[side][coord_tuple] = current_threat + 1.0

    def get_threat_for_faction(self, hex_coord: Hex, querying_faction: str) -> float:
        """
        Returns how dangerous a hex is for 'querying_faction'.
        It sums the threat projected by all *other* opposing factions.
        """
        coord_tuple = (hex_coord.q, hex_coord.r, hex_coord.s)
        total_danger = 0.0
        
        for faction, threat_dict in self.faction_threats.items():
            if faction != querying_faction and faction != "Neutral":
                total_danger += threat_dict.get(coord_tuple, 0.0)
                
        return total_danger
