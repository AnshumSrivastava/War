"""
FILE:    services/event_bus.py
LAYER:   Middle-End
ROLE:    Decoupled event system — replaces PyQt signals for cross-layer communication.

DESCRIPTION:
    A simple publish/subscribe bus. Services emit named events; UI panels
    subscribe to them. Neither side knows the other exists.

    This is what allows:
    - The simulation to emit "tick_complete" without knowing about Qt.
    - The UI to react to events without importing engine code.
    - The web UI and desktop UI to both subscribe to the same events.

    USAGE:
        # In a service (emit):
        from services.event_bus import emit
        emit("tick_complete", {"step": 42, "results": [...]})

        # In a UI panel (subscribe):
        from services.event_bus import subscribe
        subscribe("tick_complete", self.on_tick_complete)

    THREAD SAFETY:
        Callbacks are called synchronously on the thread that calls emit().
        For Qt UI, emit() should be called from the Qt main thread, or the
        subscriber should use Qt thread-safe mechanisms (e.g. QMetaObject.invokeMethod).

DOES NOT IMPORT FROM:
    - engine/ (any)
    - ui/ or web_ui/
    - PyQt5 / Flask
"""

from typing import Callable, Any

# Internal registry: event_name -> list of callback functions
_listeners: dict[str, list[Callable]] = {}


def subscribe(event: str, callback: Callable) -> None:
    """
    Register a callback to be called when `event` is emitted.

    Args:
        event:    Name of the event to listen for (e.g. "tick_complete").
        callback: Function to call. Receives one positional argument: the payload.
    """
    _listeners.setdefault(event, []).append(callback)


def unsubscribe(event: str, callback: Callable) -> None:
    """
    Remove a previously registered callback.

    Args:
        event:    Name of the event.
        callback: The exact function object that was passed to subscribe().
    """
    if event in _listeners:
        try:
            _listeners[event].remove(callback)
        except ValueError:
            pass  # Callback was not registered — ignore silently


def emit(event: str, payload: Any = None) -> None:
    """
    Emit an event, calling all registered subscribers in registration order.

    Args:
        event:   Name of the event to emit.
        payload: Optional data to pass to each subscriber.
    """
    for callback in _listeners.get(event, []):
        try:
            callback(payload)
        except Exception as e:
            # A broken subscriber must never crash the emitter or other subscribers.
            # Log the error and continue.
            print(f"[event_bus] ERROR in subscriber for '{event}': {e}")


def clear(event: str = None) -> None:
    """
    Remove all subscriptions. If `event` is given, clear only that event.
    Primarily used in tests to reset state between test cases.

    Args:
        event: Event name to clear, or None to clear all events.
    """
    if event is None:
        _listeners.clear()
    else:
        _listeners.pop(event, None)
