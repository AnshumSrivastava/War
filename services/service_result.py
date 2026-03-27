"""
FILE:    services/service_result.py
LAYER:   Middle-End
ROLE:    Standardized return type for all service calls.

DESCRIPTION:
    Every public function in every service returns a ServiceResult.
    This guarantees:
    - No exceptions escape from the services layer to the UI.
    - The UI always has a consistent way to check for success.
    - Errors have a human-readable message suitable for display or logging.
    - The UI can show a placeholder instead of crashing on any error.

    USAGE (service side):
        from services.service_result import ServiceResult, ok, err
        return ok({"entities": [...]})
        return err("Map not loaded yet")

    USAGE (UI side):
        result = entity_service.get_all_entities()
        if result.ok:
            self.render(result.data)
        else:
            self.show_placeholder(f"[Missing: {result.error}]")

    USAGE (terminal / headless side):
        result = entity_service.get_all_entities()
        if not result.ok:
            print(f"[entity_service] WARNING: {result.error}")

DOES NOT IMPORT FROM:
    - engine/ (any)
    - ui/ or web_ui/
    - PyQt5 / Flask
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ServiceResult:
    """
    The standard return value for every service call.

    Attributes:
        ok:     True if the operation succeeded; False on any error.
        data:   The result data on success. None on failure.
        error:  Human-readable error description. Empty string on success.
        code:   Optional machine-readable error code (e.g. "NOT_FOUND").
    """
    ok:    bool
    data:  Any           = field(default=None)
    error: str           = field(default="")
    code:  Optional[str] = field(default=None)


def ok(data: Any = None) -> ServiceResult:
    """
    Convenience constructor for a successful result.

    Args:
        data: The payload to return to the caller.

    Returns:
        ServiceResult with ok=True.
    """
    return ServiceResult(ok=True, data=data)


def err(message: str, code: str = None, data: Any = None) -> ServiceResult:
    """
    Convenience constructor for a failed result.

    Args:
        message: Human-readable description of what went wrong.
        code:    Optional machine-readable error code.
        data:    Optional partial data (e.g. for partial-success scenarios).

    Returns:
        ServiceResult with ok=False.
    """
    return ServiceResult(ok=False, error=message, code=code, data=data)
