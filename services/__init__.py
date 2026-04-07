"""
FILE:    services/__init__.py
LAYER:   Middle-End
ROLE:    Public API of the services layer — the only import target for the UI.

DESCRIPTION:
    The services/ package is the ONLY interface between the UI (ui/, ui/)
    and the engine (engine/). The UI must import from here exclusively.

    Service responsibilities:
    - map_service:        Create, load, save, query map state
    - zone_service:       Manage map zones (polygons)
    - path_service:       Manage map paths (lines)
    - entity_service:     Place, remove, move, query agents and objects
    - scenario_service:   Load/save scenarios, manage sides
    - simulation_service: Run ticks, episodes, reset (headless, no Qt)
    - rules_service:      Validate moves, check win/loss/draw
    - data_service:       Load unit definitions, terrain configs
    - ai_service:         Trigger AI decisions, query brain state
    - event_bus:          Subscribe and emit cross-layer events
    - service_result:     ServiceResult type used by all services

DEPENDENCY RULE:
    - May import from engine/ (it orchestrates the backend).
    - Must NOT import from ui/ or ui/.
    - Must NOT import PyQt5 or Flask.
    - Must NEVER raise exceptions to the caller — always return ServiceResult.
"""

from services.service_result import ServiceResult, ok, err
from services import event_bus

__all__ = ["ServiceResult", "ok", "err", "event_bus"]
