# War Game Simulator — Tactical Simulation Engine

Welcome to the **War Game Simulator**. This is the `currentActive` iteration of the project: a multi-agent reinforcement learning (MARL) engine with a fully-featured PyQt5 tactical interface.

## Architecture

The application is strictly layered — violations of this hierarchy are tracked in `docs/comprehensive_analysis.md`.

```
engine/ → services/ → ui/
```

1. **Engine** (`/engine`): Pure simulation logic — Q-learning, hex math, pathfinding, combat. Zero UI dependencies.
2. **Services** (`/services`): The only permitted bridge between UI and Engine. All functions return `ServiceResult` objects.
3. **UI** (`/ui`): PyQt5 presentation layer. Reads from `services/`, never from `engine/` directly.
4. **Config** (`/config`): All tunable parameters (RL hyperparameters, reward values, episode limits). No magic numbers in code.

For full architectural detail, see:
- `docs/comprehensive_analysis.md` — Complete audit of the codebase (issues, priorities, SOPs)
- `docs/SOPs/` — Developer standard operating procedures

## Quick Start (NixOS / Nix Shell)

```bash
cd scripts/
./run_nix.sh
```

## Quick Start (Manual)

**Dependencies:**
```bash
pip install -r requirements.txt
```

> **Font Note:** For the best visual experience, install `Inter` and `JetBrains Mono` from Google Fonts or your package manager. The UI falls back to system fonts if unavailable.

**Run:**
```bash
python main.py
```

## Developer SOPs

| SOP | Topic |
|---|---|
| [SOP-01](docs/SOPs/SOP_01_project_structure.md) | Project structure & file placement |
| [SOP-02](docs/SOPs/SOP_02_adding_new_feature.md) | Adding a new feature end-to-end |
| [SOP-03](docs/SOPs/SOP_03_coding_standards.md) | Coding standards & naming conventions |
| [SOP-04](docs/SOPs/SOP_04_ui_components.md) | Creating UI components |
| [SOP-05](docs/SOPs/SOP_05_rl_configuration.md) | RL training configuration |

## Key Files

| File | Role |
|---|---|
| `main.py` | Entry point — HiDPI setup, app init |
| `engine/simulation/act_model.py` | Core simulation loop (one tick per call) |
| `engine/ai/reward.py` | Reward model (config-driven via `config/rl_config.json`) |
| `services/simulation_service.py` | Service bridge for simulation state |
| `ui/views/main_window.py` | Main application window |
| `ui/views/timeline_panel.py` | Simulation control buttons |
| `ui/components/event_log_widget.py` | Live action feed |
| `config/rl_config.json` | RL hyperparameters and reward constants |
