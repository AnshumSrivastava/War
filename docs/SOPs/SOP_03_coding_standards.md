# SOP-03: Coding Standards & Naming Conventions

**Version:** 1.0 | **Owner:** Core Team | **Applies to:** All Python source files

---

## 1. Method Naming Prefixes

Consistent prefixes make it immediately clear what a method does and who calls it:

| Prefix | Meaning | Example |
|---|---|---|
| `action_*` | User-triggered action (connected to a button or menu) | `action_save_project()` |
| `on_*` | Signal/event handler (response to a signal) | `on_sim_step_completed()` |
| `update_*` | Refreshes UI state from data | `update_live_data()` |
| `build_*` / `setup_*` | One-time construction (called in `__init__`) | `setup_left_toolbar()` |
| `mount_*` | Populates a widget with data (called during refresh) | `mount_agent_tab()` |
| `get_*` | Pure data accessor (no side effects) | `get_entity_suppression()` |
| `_*` | Private helper (should not be called externally) | `_find_target_in_fire_range()` |

---

## 2. String Literal Management

All user-visible strings must be defined as constants at the top of the file. No inline string literals in signal connections or widget creation.

```python
# ✅ CORRECT — Configuration block at top of file
STR_BTN_PLAY      = "▶  Play"
STR_BTN_PAUSE     = "⏸  Pause"
STR_BTN_STEP      = "↪ Step"
STR_TOOLTIP_PLAY  = "Start continuous simulation playback"
MSG_SIM_STARTED   = "Simulation <b>started</b>."

# ❌ WRONG — Inline string in widget
btn = QPushButton("Start Playing the Simulation")
btn.setToolTip("Click to start playing")
```

### String Naming Rules

| Prefix | Type |
|---|---|
| `STR_BTN_*` | Button labels |
| `STR_LBL_*` | Form labels |
| `STR_TAB_*` | Tab names |
| `STR_TITLE_*` | Dialog/section titles |
| `STR_HINT_*` | Hint/placeholder text |
| `MSG_*` | User-facing messages (log, dialogs) |
| `STR_ROLE_*` | Role labels (Attacker, Defender) |

---

## 3. Logging (Not Printing)

Use the standard `logging` module throughout. `print()` is only permitted in `main.py` and during prototype development.

```python
# At the top of every file:
import logging
log = logging.getLogger(__name__)

# Use levels correctly:
log.debug("Agent %s chose action %s", entity.id, action_type)   # Verbose tracing
log.info("Simulation started: %s episodes", episodes)             # Normal operation
log.warning("No scenario loaded — using empty map")              # Recoverable issue
log.error("Save failed: %s", str(e))                             # Non-fatal error
log.critical("Database corrupted — aborting")                    # Fatal
```

### Logging Level Guide

| Level | When to Use |
|---|---|
| `DEBUG` | Per-tick events, Q-value updates, pathfinding steps |
| `INFO` | Mode transitions, episode completions, file saves |
| `WARNING` | Missing config values (using fallback), deprecated calls |
| `ERROR` | Service call failures, bad JSON, IOError |
| `CRITICAL` | Unrecoverable state, should never happen in normal flow |

---

## 4. Comment Policy

Comments should explain **WHY**, not **WHAT**. The code already says what it does.

```python
# ❌ WRONG — restates the code
# Create a QSpinBox
self.episodes_spin = QSpinBox()

# ✅ CORRECT — explains the reason
# Episodes are capped at 1000 to prevent the UI from freezing during long batch runs
self.episodes_spin.setMaximum(1000)
```

---

## 5. Configuration vs. Hardcoded Values

**Rule**: If a value might change (reward weights, UI sizes, episode counts, time limits), it's a config value. If it's a true constant (math constants, enum values), it can live in `constants.py`.

```python
# ❌ WRONG — hardcoded
FIRE_HIT_REWARD = 120

# ✅ CORRECT — config-driven
from engine.ai.config_loader import ConfigLoader
conf = ConfigLoader.get("rl_config", "rewards", {})
self.FIRE_HIT_REWARD = conf.get("fire_hit", 120.0)
```

---

## 6. Signal/Slot Conventions

```python
# ✅ CORRECT: Lambda only for one-liners
btn.clicked.connect(lambda: self.on_mode_changed("terrain"))

# ✅ CORRECT: Named handler for anything more complex
btn.clicked.connect(self.action_save_project)

def action_save_project(self):
    """Saves the current project state to disk."""
    ...

# ❌ WRONG: Complex logic in lambda
btn.clicked.connect(lambda: (self.save(), self.update_visuals(), self.log_info("saved")) )
```

---

## 7. Widget Population (blockSignals)

When programmatically populating a `QTableWidget`, `QListWidget`, or `QComboBox`, always guard with `blockSignals` to prevent spurious signal emissions:

```python
table.blockSignals(True)
for row, item in enumerate(data):
    table.setItem(row, 0, QTableWidgetItem(str(item)))
table.blockSignals(False)
table.itemChanged.connect(self.on_item_changed)  # Connect AFTER population
```

---

## 8. File Headers

Every Python file must have a module docstring:

```python
"""
FILE: ui/components/event_log_widget.py
ROLE: Live action feed shown during simulation playback.

DESCRIPTION:
Displays a scrolling, structured list of simulation events (moves, fires, kills).
Supports episode tracking, color-coded severity, and a scroll-lock toggle.

DEPENDENCIES:
- services/simulation_service.py  (reads step results)
- ui/styles/theme.py              (colors for severity levels)
"""
```
