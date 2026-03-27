"""
FILE: engine/api.py
ROLE: The Single Domain Facade.

DESCRIPTION:
This acts as the API Gateway for the Engine (Domain layer).
The Services layer interacts solely with this class, preventing them
from importing deep engine internals directly. This isolates the tech-agnostic 
business logic from structural changes in the domain.
"""

class DomainAPI:
    """Provides unified access to the WorldState sub-systems."""
    
    def __init__(self, state):
        self._state = state
        self._map = state.map
        self._entities = state.entity_manager
        
    @property
    def map(self):
        return self._map
        
    @property
    def entities(self):
        return self._entities
        
    @property
    def config(self):
        return self._state.data_controller
        
    @property
    def undo_stack(self):
        return getattr(self._state, 'undo_stack', None)
        
    # --- FACADE METHODS ---
    
    def simulate_step(self):
        """Advances the simulation by one full step."""
        # For now, simulation service still builds ActionModel
        pass
