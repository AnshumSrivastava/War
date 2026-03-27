# `services/` — Middle-End Layer

The services layer is the **only** bridge between the Frontend (UI) and the Backend (engine). It handles all interaction so that neither side needs to know the other exists.

## Who works here

**Services Team** — you write pure Python. No PyQt, no Flask, no file I/O (use `data_service.py` for that). You call `engine/` and you speak to the UI via the event bus.

## Files

| File | Responsibility |
|---|---|
| `__init__.py` | Public API — UI imports from here |
| `event_bus.py` | Pub/sub system replacing PyQt signals |
| `service_result.py` | `ServiceResult` type — all services return this |
| `map_service.py` | Create, load, query, modify map and terrain |
| `entity_service.py` | Place, remove, query agents |
| `simulation_service.py` | Run ticks, episodes, reset (no Qt) |
| `rules_service.py` | Win/loss/draw terminal conditions, move validation |
| `scenario_service.py` | Load/save scenarios, list available scenarios |
| `data_service.py` | Unit definitions, terrain configs from `content/` |
| `ai_service.py` | Read/write AI brain state (epsilon, Q-values) |

## Rules

1. Every public function returns `ServiceResult` — never raises to the caller.
2. Use `event_bus.emit()` to notify the UI of state changes.
3. Never import from `ui/`, `web_ui/`, PyQt5, or Flask.
4. Never maintain your own state — use the injected `WorldState`.

## Example pattern

```python
# Service side
from services.service_result import ok, err
from services import event_bus

def do_thing(q, r):
    try:
        result = _state.map.whatever(q, r)
        event_bus.emit("thing_done", {"q": q, "r": r})
        return ok(result)
    except Exception as e:
        return err(f"Could not do thing: {e}")
```

```python
# UI side
result = map_service.do_thing(3, 5)
if result.ok:
    self.render(result.data)
else:
    self.show_placeholder(f"Missing: {result.error}")
```
