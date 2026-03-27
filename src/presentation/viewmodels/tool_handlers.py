"""
FILE: src/presentation/viewmodels/tool_handlers.py
LAYER: Presentation
ROLE: Concrete Business Logic for Tools

DESCRIPTION:
These handlers implement the `IToolHandler` interface. They contain the PURE 
business logic for what happens when a user clicks the map with a tool active.
They MUST NOT contain any UI code (no Qt imports). They delegate entirely 
to the `services/` layer.
"""

from src.presentation.controllers.tool_controller import IToolHandler
import services.map_service as map_svc
import services.entity_service as entity_svc

class EraserHandler(IToolHandler):
    """Handles logic for deleting terrain and entities from a hex."""
    
    def on_click(self, q: int, r: int, button: str) -> None:
        if button == "left":
            # 1. Clear any terrain/zones
            map_svc.clear_hex(q, r)
            
            # 2. Clear any entities on that hex
            res = entity_svc.get_entities_at(q, r)
            if res.ok and res.data:
                for entity in res.data:
                    entity_svc.remove_entity(entity.id)
