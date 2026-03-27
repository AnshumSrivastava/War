# `engine/` — Backend Layer

The engine is a **pure Python library**. It knows nothing about any UI, any web framework, or any display system. It can run in a terminal with no screen attached.

## Who works here

**Infra / Data / AI Team** — you write pure Python algorithms, data models, and file loaders. No PyQt, no Flask. Your code is a library.

## Sub-packages

| Package | Contents |
|---|---|
| `core/` | Hex math, pathfinding, entity manager, map, undo system |
| `models/` | TypedDicts + canonical string constants (single source of truth) |
| `data/` | JSON file loaders, `content_path.py` path resolver |
| `ai/` | RL algorithms: encoder, Q-table, reward model, replay buffer, commanders |
| `simulation/` | Sense-Decide-Act engine: act_model, move, fire, combat |
| `state/` | `WorldState` dataclass (runtime state, not a singleton) |
| `combat/` | Direct fire, mine negotiation, close combat resolution |
| `cli.py` | Headless entry point — `python -m engine.cli run --scenario X` |

## Rules

1. **No PyQt**. The one exception is `simulation/simulation_controller.py` which is the Qt shim for the desktop UI timer — it should not grow.
2. **No Flask**.
3. **No imports from `services/` or `ui/`.**
4. All string constants go in `engine/models/constants.py`.
5. All data types go in `engine/models/` as TypedDicts.
6. The content/ path is always resolved via `engine/data/content_path.py`.

## Running headless

```bash
# Train 100 episodes with no display
python -m engine.cli run --scenario my_scenario --episodes 100

# Print current world state as JSON
python -m engine.cli state

# Validate a scenario file
python -m engine.cli validate --file content/Projects/Alpha.json
```
