# Contributing to Tactical Engine

Welcome to the Tactical Engine development initiative! This document provides the guidelines and conventions we follow to maintain stability and modularity across the codebase.

## Code Standards
1. **No Magic Strings or Numbers**: Any value related to RL scaling, grid dimensions, or mathematical thresholds must be requested from the `ConfigLoader`. This includes items located in `/config/rl_config.json` and `simulation_config.json`.
2. **Pure Python Architecture**: The application strictly avoids HTML/JS/CSS bridging. We use fully native `PyQt5` UI layouts. Do not add WebKit elements unless explicitly approved for map rendering extensions.
3. **Save Sanitation**: Use `engine.core.naming_utils.NamingUtils.sanitize_filename()` for all strings that intend to become folder or file names. Windows compatibility is paramount.

## Architecture Guidelines
*   **Decoupled Logic**: The UI and Simulation layers are strictly decoupled. 
    *   Do not inject QWidgets into core `engine/` calculation areas.
    *   Send and receive signals via `ui/core/simulation_controller.py` if crossing between domains.

## Setting Up Your Environment
To get started:
1. Clone the repository.
2. Ensure you have Python >= 3.10.
3. Run `pip install -r requirements.txt`. For Nix users, shell setup rules are maintained in `infra/shell.nix`.
4. Boot the simulator using `scripts/run.sh` or `scripts/run.bat`.

## Reporting Bugs
If you find a bug, please check the Event Log and provide the Traceback originating from `engine/data/api`. Ensure reproducing steps detail the exact map scenario format loaded.
