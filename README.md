# War Game Simulator (v3 Structure)

Welcome to the **War Game Simulator**! This repository holds the `refactoredV3` iteration of the overarching War Game project, which integrates a robust multi-agent reinforcement learning (MARL) engine with a fully-featured, decoupled PyQt5 interface.

## Purpose

The main purpose of the V3 refactoring was to enforce **strict modularity** and completely decouple the simulation engine from the user interface. By separating the codebase into distinct layers (`engine`, `data`, and `ui`), the system is now exceptionally scalable and straightforward to navigate.

## Architecture Highlights

The application is structured around a central abstraction:

1. **Engine Layer** (`/engine`): Houses the pure simulation logic logic, Q-Learning modules, discrete event handlers, hex math, and pathfinding. The engine operates entirely independent of any visual display.
2. **Data Layer** (`/data`): Manages the loading and saving of definitions, including terrain templates, agent catalogs, zone descriptions, and static project files.
3. **UI Layer** (`/ui`): A pure presentation layer that queries the `engine` and `data` states and renders the map to a PyQt5 window, including interactive map tools, analytics, dashboards, and live agent feeds.

For a deeper dive into the exact module relationships, class diagrams, and design patterns utilized, please open the **Documentation** tab natively inside the application or view `docs/ARCHITECTURE.md`.

## Quick Start

### Installation

Ensure you have Python 3 and PyQt5 installed.
Additional requirements include `numpy` (for Q-table calculations) and `markdown` (for the internal documentation viewer).

```bash
pip install PyQt5 numpy markdown
```

### Running the Simulator

Launch the main entry point to open the dashboard interface:

```bash
python main.py
```

From there, you can explore the internal **Documentation** tab to learn the specifics of combat algorithms, map generation, and the reinforcement learning loops!
