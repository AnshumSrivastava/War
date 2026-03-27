# Wargame Engine: Architectural Overview & File Structure

This document provides a comprehensive overview of the Wargame Engine's architecture, design philosophy, and codebase structure. It is intended to serve as the primary onboarding document for developers, researchers, and project stakeholders.

## 1. Executive Summary

The Wargame Engine is a hexagon-based tactical simulation environment designed for Reinforcement Learning (RL) research. It provides a visual sandbox where autonomous agents learn and execute military tactics. 

The core design philosophy is strict **Separation of Concerns (SoC)**. The engine is divided into three distinct, decoupled layers:

1.  **State Layer (`/state/`, `/data/`)**: The absolute source of truth. It holds raw data—unit positions, terrain definitions, and health statistics—without executing any game logic.
2.  **Simulation Layer (`/simulation/`, `/core/`, `/ai/`)**: The deterministic mathematical engine. It calculates movement costs, line-of-sight, weapon lethality, and executes the AI's "Sense-Decide-Act" loops.
3.  **Presentation Layer (`/ui/`)**: A PyQt5-based reactive frontend. It reads the State Layer to draw the map and units, but it *never* bypasses the Simulation Layer to modify state directly.

This decoupling ensures that the simulation can be run "headlessly" (without a UI) on cloud servers for accelerated, massive-scale AI training, while still providing a robust graphical editor for human analysis.

---

## 2. Directory & File Structure Guide

The codebase is organized by architectural layer to ensure predictability and maintainability.

### 2.1 The Roots (Entry Points)
*   **`main.py`**: The application launcher. It initializes the PyQt5 application, boots the central `MainWindow`, and establishes connections to the Redis memory store.
*   **`setup_windows.py`**: An automated dependency manager and environment configuration script built to seamlessly onboard Windows developers without requiring manual virtual environment setup.

### 2.2 Mathematical Engine & Logic (`/engine/`)
This directory contains the core simulation systems. No UI dependencies (like PyQt5) are permitted within this folder.

#### `/engine/ai/` - Artificial Intelligence
*   **`commander.py`**: The Macro-Level AI. It acts as the "General," assessing the battlefield and issuing broad objective paths (Axes of Advance) to tactical units.
*   **`commander_rl.py`**: The Reinforcement Learning brain for the Commander. It decides between varying strategies (Direct Attack, Safe Approach, Flanking) based on historic success rates.
*   **`q_table.py`**: The interface for managing and synchronizing the AI's Q-Learning memory matrices.

#### `/engine/core/` - Foundational Systems
*   **`hex_math.py`**: The geometric bedrock of the engine. It handles all cube-coordinate mathematics required for hexagonal grids, including distance calculations, line-of-sight raycasting, and pixel-to-hex conversion algorithms.
*   **`map.py`**: Manages spatial relationships. It tracks terrain types and orchestrates scenarios, dictating where boundaries lie and which side controls specific zones.
*   **`entity_manager.py`**: The factory and registry for all active game objects. It manages the lifecycle of `Agent` classes, allowing the engine to query units by ID or retrieve all active participants.
*   **`pathfinding.py`**: An A* (A-Star) search implementation customized for hex grids, properly factoring in variable terrain movement penalties.
*   **`undo_system.py`**: Implements the Command Pattern, providing a stack-based history to allow users to undo or redo editor actions (like painting terrain or placing units).

#### `/engine/data/` - Static Configuration
*   **`data_controller.py`**: The singular entry point for reading JSON-based configuration files. It acts as a cache, ensuring disk reads are minimized during active simulations.
*   **`api/redis_db.py`**: The low-level socket connector to the external Redis server, providing rapid read/write access for the AI's memory systems.

#### `/engine/simulation/` - The Active Loop
*   **`act_model.py`**: The primary simulation heartbeat. The `ActionModel` iterates over all units, evaluates their action economy (Tokens/Suppression), queries their tactical brains (Redis), and enforces compliance with Commander-issued strategies.
*   **`simulation_controller.py`**: The timekeeper. It manages play/pause states, controls the simulation speed, and tracks episode iteration counters during RL training.
*   **`command.py`**: Defines data structures (e.g., `AgentCommand`) representing specific orders moving through the pipeline.
*   **`combat/direct_fire.py`**: The attrition calculator. It evaluates hit probabilities, calculates personnel casualties utilizing Poisson distributions, and processes suppression damage based on weapon fire rates and cover bonuses.

### 2.3 Presentation Layer (`/ui/`)
This directory contains all PyQt5 graphical components. It is responsible for translating the abstract simulation state into a human-readable, interactive interface.

#### `/ui/components/` - Embedded Panels
*   **`object_properties_widget.py`**: The dynamic "Inspector." It contextually generates form fields allowing the user to view and modify the statistics of whichever object or tool they currently have selected.
*   **`scene_hierarchy_widget.py`**: A tree-view directory listing every element on the map, allowing for rapid selection and visibility toggling of complex scenes.
*   **`event_log_widget.py`**: A scrolling combat ticker providing real-time text feedback of simulation events (e.g., casualties, suppression).

#### `/ui/core/` - Visual Utilities
*   **`visualizer.py`**: An animation decoupling system. It purposefully delays the UI rendering of instant simulation results (like weapons fire) to create readable, sequential animations for the human observer.
*   **`theme.py`**: Centralized style definitions enforcing a unified, high-contrast dark mode aesthetic across all Qt widgets.

#### `/ui/tools/` - Interactive Brushes
*   **`paint_tool.py`, `place_agent_tool.py`, `edit_tool.py`, etc.**: Object-oriented implementations of map editor tools. They intercept mouse clicks on the canvas and translate them into modifications of the `GlobalState`.

#### `/ui/views/` - Primary Application Shells
*   **`main_window.py`**: The overarching application shell. It manages widget docking, main menus, toolbars, and project serialization (saving/loading files).
*   **`hex_widget.py`**: The critical `QGraphicsView` canvas. It handles the actual rendering of the hexagonal grid, unit icons, and combat laser animations. 

### 2.4 External Dependencies (`/infra/` & `/data/`)
*   **`/infra/`**: Contains Nix environment configurations (`shell.nix`) ensuring perfect dependency replication for Linux/Docker environments.
*   **`/data/models/`**: The persistent storage location for the exported Reinforcement Learning memory matrices (`.npy` and `.json` files).
*   **`/content/` & `/data/db/`**: Directories containing the human-readable JSON files defining base unit stats, weaponry, and terrain attributes.
