# SOP-01: Project Structure & File Placement

**Version:** 1.0 | **Owner:** Core Team | **Applies to:** All new files and features

---

## 1. Purpose

This SOP defines where code and resources live, ensuring every developer can immediately find any piece of functionality without guessing. Violating this structure creates layer violations (the most common bug class in this codebase) and adds maintainability debt.

---

## 2. Top-Level Directory Map

```
currentActive/
├── config/              ← All tuneable parameters (NO code)
│   ├── rl_config.json      ← RL hyperparameters and reward values
│   └── simulation_config.json  ← Episode limits, token costs, step limits
│
├── content/             ← User-generated project data (NOT committed to git)
│   └── Projects/<name>/Maps/<map>/
│
├── data/                ← Runtime data: Q-tables, training logs (NOT committed)
│   ├── training/           ← Q-tables per agent and episode
│   └── models/             ← Saved strategic commander models
│
├── docs/                ← Technical documentation and SOPs
│   ├── SOPs/               ← Developer standard operating procedures
│   └── comprehensive_analysis.md  ← Architectural audit tracker
│
├── engine/              ← Pure Python simulation logic (NO PyQt5, NO UI code)
│   ├── ai/                 ← RL agent logic (Q-table, reward, encoder)
│   ├── combat/             ← Direct fire, melee resolution
│   ├── core/               ← Map, entity, pathfinding, utilities
│   ├── data/               ← Database adapters (JSONDatabase, MemoryDatabase)
│   └── simulation/         ← ActionModel step loop
│
├── infra/               ← Infrastructure: shell.nix, environment setup
├── scripts/             ← Launch and install scripts (install.sh, run_nix.sh)
├── services/            ← The BRIDGE between engine and UI
│   ├── map_service.py
│   ├── entity_service.py
│   ├── scenario_service.py
│   └── simulation_service.py
│
├── src/                 ← Optional MVVM presentation layer (currently minimal)
├── test/                ← Unit tests (mirrors engine/ and services/ structure)
├── ui/                  ← All PyQt5 display code (NO direct engine imports)
│   ├── components/         ← Reusable widgets
│   ├── core/               ← App-level controllers (modes, toolbar, simulation)
│   ├── dialogs/            ← Modal dialogs
│   ├── styles/             ← Theme, QSS, icon painter
│   ├── tools/              ← Interactive map tools (cursor, paint, zone)
│   └── views/              ← Full-screen views and docks
│
├── main.py              ← Entry point ONLY; no logic here
└── requirements.txt     ← Pin all dependencies here
```

---

## 3. The Three-Layer Rule

```
Engine → Services → UI
```

- **Engine** code may only import from other engine modules and Python stdlib.
  - ❌ NEVER import `from PyQt5...`
  - ❌ NEVER import `from ui...`
  - ❌ NEVER import `from services...`
  
- **Services** are the ONLY bridge. They translate engine objects into plain dicts/values the UI can consume.
  - ✅ May import from `engine/`
  - ❌ May NOT import from `ui/`

- **UI** displays data. It calls `services.*` functions, NEVER `engine.*` directly.
  - ✅ May import from `services/`
  - ❌ May NOT import from `engine/` (only exception: constants from `engine/data/definitions/`)

---

## 4. File Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Python modules | `snake_case.py` | `hex_widget.py` |
| Classes | `PascalCase` | `HexWidget` |
| Constants | `UPPER_SNAKE_CASE` | `TILE_SIZE`, `NUM_RL_ACTIONS` |
| UI string literals | `STR_` prefix | `STR_BTN_PLAY = "▶ Play"` |
| UI style strings | `STYLE_` prefix | `STYLE_SAVE_BTN_WARN` |
| Config keys | `snake_case` | `"epsilon_decay"` |

---

## 5. What Goes Where (Quick Reference)

| If you're adding... | It goes in... |
|---|---|
| New RL hyperparameter | `config/rl_config.json` |
| New reward constant | `config/rl_config.json` → loaded by `engine/ai/config_loader.py` |
| New game rule / combat logic | `engine/combat/` or `engine/simulation/` |
| New AI decision logic | `engine/ai/` |
| Data persistence / file I/O | `engine/data/api/` or `engine/data/services/` |
| Conversion between engine↔UI | `services/*.py` |
| New dialog | `ui/dialogs/` |
| Reusable widget | `ui/components/` |
| Full-page view | `ui/views/` |
| Interactive map tool | `ui/tools/` |
| App-level controller | `ui/core/` |
| Test for any of the above | `test/` (mirror the source path) |

---

## 6. Testing Requirements

- Every new service function must have an entry in `test/`
- Engine modules should be testable without PyQt5 being installed
- Run `python -m pytest test/` before every commit
