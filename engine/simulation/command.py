"""
FILE: engine/action/command.py
ROLE: The "Orders" given to units.

DESCRIPTION:
Units in this game don't just wander randomly - they follow high-level 
strategic goals. This file defines what a 'Command' looks like.
A command tells a unit: "Go to this specific spot and either Move, Capture, 
Defend, or Fire."
The AI Brain uses these commands to calculate whether a unit is doing a 
'Good' or 'Bad' job based on how well they follow orders.
"""
from typing import Optional, List
from engine.core.hex_math import Hex

class AgentCommand:
    """
    The Order Form. It contains the goal, the objective type,
    and whether a human assigned it.
    """
    def __init__(self, command_type: str, target_hex: Hex, is_user_assigned: bool = False, 
                 assigned_path: Optional[List[Hex]] = None, objective_type: str = "DEFAULT",
                 axis: int = 0):
        """
        CONSTRUCTOR: Create a new set of orders.
        
        Args:
            command_type: General category (e.g., "MOVE", "DEFEND", "CAPTURE").
            target_hex: The specific hexagon on the map where the goal is located.
            is_user_assigned: If True, the AI Commander won't give this unit new orders.
            assigned_path: Optional pre-calculated path (deprecated for Resolution Agents).
            objective_type: High-level tactical objective (e.g. "REINFORCE", "SUPPRESS").
        """
        self.command_type = command_type
        self.target_hex = target_hex
        self.is_user_assigned = is_user_assigned
        self.assigned_path = assigned_path or []
        self.objective_type = objective_type
        
        # Used for Defenders to remember their designated area
        self.domain_hex: Optional[Hex] = None 
        
    def __repr__(self):
        """A simple way to see the command in the computer's logs."""
        return f"AgentCommand({self.command_type}:{self.objective_type} @ {self.target_hex.q},{self.target_hex.r})"
