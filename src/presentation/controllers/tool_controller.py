"""
FILE: src/presentation/controllers/tool_controller.py
LAYER: Presentation
ROLE: Centralized Coordinator for all Map Interactions

DESCRIPTION:
This controller is tech-agnostic (contains no PyQt code). It is responsible 
for managing which tool is currently active and routing map click/hover events 
to the appropriate pure-logic IToolHandler.
"""

from typing import Dict, Optional
from services import event_bus

class IToolHandler:
    """Interface for pure-logic tool actions."""
    def on_click(self, q: int, r: int, button: str) -> None:
        pass
        
    def on_hover(self, q: int, r: int) -> None:
        pass


class ToolController:
    """The central authority on the active tool and its behavior."""
    
    def __init__(self):
        self._active_tool_id: str = "cursor"
        self._handlers: Dict[str, IToolHandler] = {}
        
    def register_handler(self, tool_id: str, handler: IToolHandler) -> None:
        """Register a pure-logic handler for a specific tool ID."""
        self._handlers[tool_id] = handler
        
    def set_tool(self, tool_id: str) -> None:
        """Change the active tool and notify the system."""
        if self._active_tool_id == tool_id:
            return
            
        self._active_tool_id = tool_id
        event_bus.emit("tool_changed", {"tool": tool_id})
        
    @property
    def active_tool(self) -> str:
        return self._active_tool_id
        
    def handle_click(self, q: int, r: int, button: str = "left") -> None:
        """Route a map click to the active tool's logic handler."""
        handler = self._handlers.get(self._active_tool_id)
        if handler:
            handler.on_click(q, r, button)
            
    def handle_hover(self, q: int, r: int) -> None:
        """Route a map hover to the active tool's logic handler."""
        handler = self._handlers.get(self._active_tool_id)
        if handler:
            handler.on_hover(q, r)
