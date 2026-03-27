import heapq
from typing import Dict, List, Optional, Tuple, Set
from engine.core.hex_math import Hex, HexMath
from engine.core.map import Map

"""
Pathfinding Module.

This module implements A* pathfinding and Dijkstra-based range searching for the
hexagonal grid system.
"""

class Pathfinder:
    """
    A* Pathfinding implementation for Hex Grid.
    
    Provides methods to find the shortest path between two hexes and to find all
    reachable hexes within a certain movement cost/range.
    """
    def __init__(self, game_map: Map):
        self.game_map = game_map

    def get_path(self, start: Hex, end: Hex, max_cost: float = float('inf'), cost_fn=None, max_iterations: int = 2000) -> Optional[List[Hex]]:
        """
        Find shortest path from start to end using A* algorithm.
        
        Args:
            start (Hex): Starting hex.
            end (Hex): Destination hex.
            max_cost (float): Maximum allowed path cost.
            cost_fn (callable): Optional function taking (Hex) -> float for customized costs.
            max_iterations (int): Safety cap to prevent infinite search on infinite maps.
            
        Returns:
            Optional[List[Hex]]: List of Hexes [start, ..., end] or None if unreachable.
        """
        frontier = []
        heapq.heappush(frontier, (0, start))
        
        came_from: Dict[Tuple[int,int,int], Optional[Hex]] = {}
        cost_so_far: Dict[Tuple[int,int,int], float] = {}
        
        start_tuple = tuple(start)
        came_from[start_tuple] = None
        cost_so_far[start_tuple] = 0
        
        iterations = 0
        while frontier:
            iterations += 1
            if iterations > max_iterations:
                return None # Safety break
                
            _, current = heapq.heappop(frontier)
            
            if current == end:
                break
            
            for i in range(6):
                neighbor = HexMath.neighbor(current, i)
                
                # Determine terrain cost
                if cost_fn:
                    try:
                        move_cost = cost_fn(neighbor)
                    except:
                        move_cost = float('inf')
                else:
                    # Check bounds/validity if map was finite, but it's infinite.
                    # Just check terrain cost.
                    terrain = self.game_map.get_terrain(neighbor)
                    
                    # If terrain is impassable (e.g. infinite cost or specific type)
                    move_cost = terrain.get("cost", 1.0) if terrain else float('inf')
                
                if move_cost == float('inf'):
                    continue
                
                new_cost = cost_so_far[tuple(current)] + move_cost
                
                if new_cost > max_cost:
                    continue
                
                neighbor_tuple = tuple(neighbor)
                if neighbor_tuple not in cost_so_far or new_cost < cost_so_far[neighbor_tuple]:
                    cost_so_far[neighbor_tuple] = new_cost
                    priority = new_cost + HexMath.distance(neighbor, end) # Heuristic
                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor_tuple] = current
                    
        # Reconstruct path
        path = []
        current_node = end
        if tuple(end) not in came_from:
            return None # No path found
            
        while current_node != start:
            path.append(current_node)
            current_node = came_from[tuple(current_node)]
        path.append(start)
        path.reverse()
        return path

    def get_reachable_hexes(self, start: Hex, range_budget: float, cost_fn=None) -> Set[Hex]:
        """
        Find all hexes reachable within a movement budget (Dijkstra/BFS).
        
        Args:
            start (Hex): Starting hex.
            range_budget (float): Maximum movement cost allowed.
            cost_fn (callable): Optional function taking (Hex) -> float for customized costs.
            
        Returns:
            Set[Hex]: A set of reachable Hex coordinates.
        """
        frontier = []
        heapq.heappush(frontier, (0, start))
        
        cost_so_far: Dict[Tuple[int,int,int], float] = {}
        start_tuple = tuple(start)
        cost_so_far[start_tuple] = 0
        
        reachable = set()
        
        while frontier:
            _, current = heapq.heappop(frontier)
            reachable.add(current)
            
            for i in range(6):
                neighbor = HexMath.neighbor(current, i)
                
                # Determine terrain cost
                if cost_fn:
                    move_cost = cost_fn(neighbor)
                else:
                    terrain = self.game_map.get_terrain(neighbor)
                    move_cost = terrain.get("cost", 1.0)
                
                if move_cost == float('inf'):
                    continue
                    
                new_cost = cost_so_far[tuple(current)] + move_cost
                
                if new_cost <= range_budget:
                    neighbor_tuple = tuple(neighbor)
                    if neighbor_tuple not in cost_so_far or new_cost < cost_so_far[neighbor_tuple]:
                        cost_so_far[neighbor_tuple] = new_cost
                        heapq.heappush(frontier, (new_cost, neighbor))
                        
        return reachable
