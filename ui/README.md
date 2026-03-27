# `ui/` — Frontend Layer (Desktop)

The desktop UI built with PyQt5. It knows nothing about how data is stored or computed — it only calls `services/`.

## Who works here

**UI Team** — you write PyQt5 widgets and layouts. You never touch `engine/`. You call `services/` for all data and actions.

## Rules

1. **No `from engine.*` imports.** Ever. Use `services.*` instead.
2. When a service returns `ServiceResult(ok=False)`, show a placeholder (`ui/utils/fallback.py`) — never crash.
3. All colors and fonts come from `ui/styles/theme.py`. No inline stylesheet strings in widgets.
4. UI settings (selected tool, grid mode, theme) live in `ui/styles/ui_state.py` — not in the engine.
5. One tool file = one responsibility (see `ui/tools/`).

## Sub-packages

| Package | Contents |
|---|---|
| `views/` | Top-level window assembly |
| `panels/` | ToolbarPanel, SimulationPanel, ScenarioPanel (WIP) |
| `canvas/` | HexWidget map renderer + CanvasController input routing |
| `tools/` | One file per drawing/editing tool |
| `components/` | Reusable dumb widgets (no state) |
| `styles/` | Theme colors, QSS stylesheets, font tokens, UIState |
| `utils/` | Helpers including `fallback.py` stub data |
| `dialogs/` | Modal dialogs |

## Graceful degradation pattern

Every widget that shows real data must follow this pattern:

```python
from services import map_service
from ui.utils.fallback import STUB_MAP, warn_missing

result = map_service.get_map_info()
if result.ok:
    self.update_display(result.data)
else:
    warn_missing(result, context="MapPanel")
    self.update_display(STUB_MAP)   # Show stub — no crash
```
