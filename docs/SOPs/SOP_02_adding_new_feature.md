# SOP-02: Adding a New Feature End-to-End

**Version:** 1.0 | **Owner:** Core Team | **Applies to:** All new gameplay or AI features

---

## 1. Purpose

This SOP describes the canonical workflow for adding a new feature to the system. Following this prevents layer violations and ensures the feature is testable, configurable, and maintainable.

---

## 2. Example: "Add a Suppression System" (used as illustration)

We'll trace adding a hypothetical "suppression" attribute that grows when a unit is fired on and reduces their action tokens.

---

## 3. Step-by-Step Workflow

### Step 1 — Define Config Values (if tuneable)
Add any magic numbers to the appropriate config file first:

```json
// config/simulation_config.json
{
    "suppression": {
        "gain_per_hit": 10,
        "decay_per_step": 2,
        "max_value": 100,
        "token_reduction_factor": 0.5
    }
}
```

### Step 2 — Implement Engine Logic
Create or modify engine files. Engine code must be pure Python with zero UI imports.

```python
# engine/combat/suppression.py
from engine.ai.config_loader import ConfigLoader

class SuppressionModel:
    def __init__(self):
        conf = ConfigLoader.get("simulation_config", "suppression", {})
        self.GAIN_PER_HIT = conf.get("gain_per_hit", 10)
        self.DECAY_PER_STEP = conf.get("decay_per_step", 2)
        self.MAX_VALUE = conf.get("max_value", 100)

    def apply_hit(self, entity):
        current = entity.get_attribute("suppression", 0)
        entity.set_attribute("suppression", min(current + self.GAIN_PER_HIT, self.MAX_VALUE))

    def decay(self, entity):
        current = entity.get_attribute("suppression", 0)
        entity.set_attribute("suppression", max(current - self.DECAY_PER_STEP, 0))
```

### Step 3 — Wire into Simulation Loop
Call the engine logic from `engine/simulation/act_model.py`:

```python
# In step_all_agents(), after combat resolution:
from engine.combat.suppression import SuppressionModel
suppression_model = SuppressionModel()

# After fire event:
suppression_model.apply_hit(target_entity)

# Each step for all entities:
suppression_model.decay(entity)
```

### Step 4 — Expose via Service Layer
Add a function in the appropriate service to make the data accessible to UI:

```python
# services/entity_service.py
def get_entity_suppression(entity_id: str) -> int:
    """Returns the current suppression level for an entity (0-100)."""
    entity = _state().entity_manager.get_entity(entity_id)
    if not entity:
        return 0
    return int(entity.get_attribute("suppression", 0))
```

### Step 5 — Display in UI
Import from services, never from engine:

```python
# ui/components/event_log_widget.py
import services.entity_service as entity_svc

def update_agent_row(self, entity_id: str, row: int):
    suppression = entity_svc.get_entity_suppression(entity_id)
    self.table.setItem(row, COL_SUPPRESSION, QTableWidgetItem(str(suppression)))
```

### Step 6 — Write a Test

```python
# test/test_suppression.py
from engine.combat.suppression import SuppressionModel
from engine.core.entity import Entity

def test_suppression_apply_and_decay():
    e = Entity()
    e.set_attribute("suppression", 0)
    model = SuppressionModel()
    
    model.apply_hit(e)
    assert e.get_attribute("suppression") == model.GAIN_PER_HIT
    
    model.decay(e)
    assert e.get_attribute("suppression") == model.GAIN_PER_HIT - model.DECAY_PER_STEP
```

---

## 4. Checklist

Before submitting a feature for review:

- [ ] Config values added to `config/*.json` (no magic numbers in code)
- [ ] Engine module tests pass without PyQt5 installed
- [ ] Services function added to expose data to UI
- [ ] UI reads data via `services.*`, not `engine.*`
- [ ] No `print()` statements — use `logging.getLogger(__name__)`
- [ ] String literals use `STR_` prefix or are defined as config constants
- [ ] `blockSignals(True)` used when programmatically populating QTableWidgets

---

## 5. Anti-Patterns to Avoid

| ❌ Don't Do This | ✅ Do This Instead |
|---|---|
| `from engine.ai.q_table import QTableManager` in a widget | Call `services.simulation_service.get_agent_brain_stats()` |
| `magic_number = 50` inline in a function | Add to `config/rl_config.json`, load via `ConfigLoader` |
| `print(f"Agent moved to {pos}")` | `log.debug(f"Agent moved to {pos}")` |
| `table.setItem(row, col, ...)` without `blockSignals(True)` | Wrap in `table.blockSignals(True)` / `table.blockSignals(False)` |
| `from PyQt5 import ...` inside `engine/` | Never — engine must be UI-agnostic |
