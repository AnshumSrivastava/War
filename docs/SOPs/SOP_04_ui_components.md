# SOP-04: Creating UI Components

**Version:** 1.0 | **Owner:** Core Team | **Applies to:** All new UI widgets and views

---

## 1. Purpose

This SOP defines how to create consistent, maintainable UI components in the wargame engine. Following this ensures all new widgets look and behave consistently with the rest of the application.

---

## 2. Component Anatomy

Every reusable widget follows this structure:

```python
"""
FILE: ui/components/my_widget.py
ROLE: [One-line description]
...
"""
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, ...
from PyQt5.QtCore import Qt, pyqtSignal
from ui.styles.theme import Theme

log = logging.getLogger(__name__)

# ── CONFIG BLOCK ────────────────────────────────────────────────────────
# All user-visible strings and styles live here — NEVER inline in widgets.
STR_TITLE     = "Widget Title"
STR_BTN_OK    = "✓  Confirm"
STYLE_PANEL   = f"background: {Theme.BG_PANEL}; border-radius: 4px;"
# ────────────────────────────────────────────────────────────────────────

class MyWidget(QWidget):
    # Signals at the class level
    something_happened = pyqtSignal(str)

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.mw = main_window  # Reference to MainWindow for cross-widget comms
        self._setup_ui()

    def _setup_ui(self):
        """ONE-TIME widget construction. Called once from __init__."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        ...

    def refresh(self):
        """REBUILD: Repopulate from fresh data. Called when data changes."""
        ...

    def on_data_updated(self, data: dict):
        """Signal handler — updates display without full rebuild."""
        ...
```

---

## 3. Theme Usage

Always use `Theme.*` constants for colors, never raw hex codes in widget files:

```python
# ✅ CORRECT
label.setStyleSheet(f"color: {Theme.ACCENT_GOOD}; font-size: 12px;")

# ❌ WRONG — breaks when theme changes
label.setStyleSheet("color: #4caf50; font-size: 12px;")
```

### Key Theme Constants

| Constant | Use For |
|---|---|
| `Theme.BG_DARK` | Main background |
| `Theme.BG_PANEL` | Panel/card backgrounds |
| `Theme.TEXT_PRIMARY` | Primary readable text |
| `Theme.TEXT_DIM` | Secondary, hint, or disabled text |
| `Theme.ACCENT_GOOD` | Success, positive values, health |
| `Theme.ACCENT_BAD` | Errors, warnings, damage |
| `Theme.ACCENT_ALLY` | Blue team / allied units |
| `Theme.ACCENT_ENEMY` | Red team / enemy units |

---

## 4. Layout Conventions

```python
# Standard panel margins: 8px all sides
layout.setContentsMargins(8, 8, 8, 8)
layout.setSpacing(6)

# Compact control rows (Timeline, toolbars): 4px margins, 4px spacing
layout.setContentsMargins(4, 4, 4, 4)
layout.setSpacing(4)

# Modal dialogs: 16px margins for breathing room
layout.setContentsMargins(16, 16, 16, 16)
```

---

## 5. Button Taxonomy

Use the `TacticalButton` hierarchy from `ui/styles/theme.py` for consistent button appearance:

| Class | Visual | Used For |
|---|---|---|
| Primary | Filled accent color | Main actions (Play, Save) |
| Secondary | Outlined | Supporting actions (Step, Reset) |
| Warning | Orange fill | Destructive but reversible (Clear Log) |
| Danger | Red fill | Irreversible actions (Delete Scenario) |
| Ghost | Transparent | Toolbar/inline actions |

```python
from ui.styles.theme import Theme
btn = QPushButton(STR_BTN_PLAY)
btn.setObjectName("primary-btn")  # Picked up by QSS
```

---

## 6. Placing a New Widget in the Layout

### As a Dock (sidebar/bottom panel):
```python
# In main_window.py → _build_docks()
dock = QDockWidget("My Panel", self)
dock.setWidget(MyWidget(self, main_window=self))
dock.setAllowedAreas(Qt.BottomDockWidgetArea)
self.addDockWidget(Qt.BottomDockWidgetArea, dock)
self.my_panel_dock = dock  # Store reference for visibility control
```

### Controlling visibility with mode:
```python
# In ui/core/mode_state_machine.py → switch_mode()
is_sim_mode = new_mode in ("play", "learning")
self.mw.my_panel_dock.setVisible(is_sim_mode)
```

---

## 7. Signal/Slot Best Practices

```python
# ✅ Connect in _setup_ui(), after widgets are created
btn.clicked.connect(self.action_do_thing)

# ✅ Disconnect before destruction (prevents dangling refs in long-running apps)
def closeEvent(self, event):
    btn.clicked.disconnect(self.action_do_thing)
    super().closeEvent(event)

# ✅ Use pyqtSignal for communicating upward to parent
class MyWidget(QWidget):
    save_requested = pyqtSignal()
    
    def action_save(self):
        self.save_requested.emit()

# In parent:
widget.save_requested.connect(self.on_child_save_requested)
```

---

## 8. Performance Checklist for Live-Updating Widgets

For widgets that refresh every simulation tick (live agent table, event log):

- [ ] Use `blockSignals(True)` during updates
- [ ] Update only changed rows, not full rebuild (`setItem` not `clearContents + rebuild`)
- [ ] Use `resizeColumnsToContents()` at most once per episode, not every tick  
- [ ] Auto-scroll only if user is at the bottom (check `scrollBar().value() == scrollBar().maximum()`)
- [ ] Cap displayed items (e.g., keep only last 500 log entries)
