"""
FILE:    engine/state/world_state.py
LAYER:   Backend → State
ROLE:    Runtime world state container — NOT a singleton.

DESCRIPTION:
    WorldState holds all mutable game data for a running session:
    the map, entities, threat map, undo stack, and loaded data.

    KEY DIFFERENCE from the old GlobalState:
    - This is a plain dataclass, not a singleton. One instance is created
      in main.py or engine/cli.py and passed down via dependency injection.
    - Multiple WorldState instances can coexist (e.g. for parallel training,
      or running two scenarios side-by-side in the future).
    - No UI settings live here. See ui/styles/ui_state.py for those.

    MIGRATION NOTE:
    - Old code used `GlobalState()` (singleton call). New code receives
      `state: WorldState` as a constructor argument.
    - GlobalState still works as a compatibility shim while migration is
      in progress. Do not add new features to GlobalState.

DOES NOT IMPORT FROM:
    - Any UI code (ui/, web_ui/)
    - services/
    - PyQt5 / Flask
"""

from dataclasses import dataclass, field
from typing import Optional

from engine.core.map import Map
from engine.core.entity_manager import EntityManager
from engine.state.threat_map import ThreatMap
from engine.core.undo_system import UndoStack


@dataclass
class WorldState:
    """
    Container for all mutable simulation state in one session.

    Create one instance at startup and pass it into every service and
    engine component that needs it. Do NOT re-instantiate mid-session.

    Attributes:
        map:            The hex map — tiles, terrain, zones, paths.
        entity_manager: Manages all placed agents and objects.
        threat_map:     Derived danger-zone overlay per faction per tick.
        undo_stack:     History of reversible edit commands (editor mode).
        data_controller: Loaded game data (unit definitions, terrain configs).
        project_path:   File path of the currently open project/scenario, if any.
        current_project: Name of the loaded project/scenario.
        current_map:    Name of the loaded map file.
        time_per_step:  Simulated minutes per engine tick.
        is_learning:    True while the RL training loop is running.
    """
    map:            Map            = field(default_factory=Map)
    entity_manager: EntityManager  = field(default_factory=EntityManager)
    threat_map:     ThreatMap      = field(default_factory=ThreatMap)
    undo_stack:     UndoStack      = field(default_factory=lambda: UndoStack(limit=50))

    # Loaded data controller — injected after construction via create()
    data_controller: Optional[object] = field(default=None)

    # Session context
    project_path:    Optional[str] = field(default=None)
    current_project: Optional[str] = field(default=None)
    current_map:     Optional[str] = field(default=None)

    # Simulation settings
    time_per_step:   int  = field(default=10)   # minutes per tick
    is_learning:     bool = field(default=False)

    @classmethod
    def create(cls, content_root: Optional[str] = None) -> "WorldState":
        """
        Factory method — creates a fully-initialized WorldState.

        Use this in main.py and engine/cli.py instead of calling __init__
        directly, so the data_controller is always set up correctly.

        Args:
            content_root: Path to the content/ directory. If None, the
                          engine.data.content_path resolver is used.

        Returns:
            A ready-to-use WorldState instance.
        """
        from engine.data.content_path import get_content_root
        from engine.data.loaders.data_manager import DataManager

        root = content_root or get_content_root()
        state = cls()
        state.data_controller = DataManager(content_root=root)
        # terrain_controller is the same object (backward compat alias)
        state.terrain_controller = state.data_controller
        return state
