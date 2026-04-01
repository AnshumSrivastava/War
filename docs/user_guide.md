# Wargame Engine: Comprehensive User Guide

Welcome to the Wargame Engine. This application functions as both an interactive map editor and a robust Research & Development (R&D) sandbox where autonomous Reinforcement Learning (RL) agents learn military tactics.

This guide is designed for both non-technical stakeholders looking to run a simulation and technical developers configuring AI experiments.

---

## 1. Initial Setup & Launch

The engine requires a specific environment to run its Reinforcement Learning memory (in-memory Q-tables) and UI (PyQt5) smoothly. We have provided automated scripts to handle this.

### Windows Users
1. **Prerequisites**: Ensure **Python 3.10+** is installed on your machine.
2. In the project's root folder, run `python setup_windows.py`.
3. The script will automatically create an isolated Python environment (`venv`), install all required dependencies without cluttering your system, and verify the environment.
4. Once complete, activate the environment and launch:
   ```cmd
   .\venv\Scripts\activate
   python main.py
   ```

### Linux (NixOS) Users
The application utilizes Nix to guarantee a perfectly reproducible environment.
1. Launch the application via the Nix shell wrapper: `./scripts/run_nix.sh`

---

## 2. Navigating the Interface

The interface features a professional, high-contrast dark theme designed to minimize eye strain during long analytical sessions. The workspace is divided into critical zones:

### 2.1 The Map Canvas (Center)
The primary viewport. It renders the hexagonal grid, the terrain properties of each tile, and the real-time position of combat units.
*   **Pan**: Click and drag your Middle Mouse Button.
*   **Zoom**: Scroll the Mouse Wheel.

### 2.2 The Command Toolbox (Left Dock)
Your primary interaction tools for modifying the state of the simulation.
*   **Cursor Tool**: Used for inspecting elements. Clicking a unit or hexagon automatically populates the right-hand Inspector with its live data.
*   **Pan Tool**: An alternative way to move the map without using the middle mouse button.
*   **Assign Team & Goal**: Used to manually assign macro-objectives to the AI Commander (e.g., "Take this hill").
*   **Draw Terrain/Zones/Paths**: Painting tools for constructing the battlefield environment, mission boundaries, or logical routing lines.
*   **Place Agent Tool**: Used to deploy actual combat units (e.g., Snipers, Tanks) onto the battlefield.
*   **Eraser Tool**: Removes units or terrain features from the active hex.

### 2.3 The Inspector & Scene Hierarchy (Right Docks)
These docks provide granular control over the data on your map.
*   **Scene Hierarchy**: Functions identically to a layer panel in Photoshop. It is a complete directory of every Zone, Path, and Unit currently deployed. It allows you to rapidly locate specific elements in massive engagements.
*   **Object Properties (Inspector)**: A dynamic form that changes based on your current selection.
    *   *If a Tool is selected*: It displays the configuration options for that tool before you use it (e.g., selecting the "Red Faction" before using the Place Agent brush).
    *   *If a Unit is clicked*: It displays the live, mid-simulation statistics of that unit (Health, Action Tokens, Suppression level).

### 2.4 The Master Data Database (Top Tabs)
The engine stores unit and weapon definitions in highly modular, customizable JSON files. You do not need to edit code to create new units. Simply switch the main window tab at the top of the application from the **"Simulation"** view to the **"Master Data"** view.
*   **Agent Types**: Create custom soldiers alongside their fundamental attributes—Base Speed, Vision Range, and Default Weaponry.
*   **Weapons**: Define the mathematical properties of new armaments. You can tweak Effective Range, Lethality (Casualty probability), and Suppression capability. For example, high-fire-rate machine guns inherently cause massive Suppression compared to a rifle.

---

## 3. Running a Simulation

Once your forces (Red vs. Blue) are deployed, you can begin the active RL training loop.

### 3.1 The Execution Phase
1. Locate the **Simulation Control Bar** at the top of the window.
2. Click the **Play** button to transition the engine from "Edit" to "Run" mode.
3. The internal tick-clock will begin. The speed of the simulation can be adjusted via the slider.

### 3.2 Real-Time Feedback
As the simulation ticks forward, you will observe the following:
*   **Combat Animations**: Lasers represent direct fire rules. A solid red line indicates a confirmed casualty attack, while a dashed gray line signifies a missed shot.
*   **The Event Log**: Located at the bottom of the screen, this ticker creates a permanent, chronologically ordered log of all battlefield results exactly as they occur.
*   **Floating Text**: Rapid damage identification (e.g., `-12 KIA`) will float off victims on the map canvas.

### 3.3 Status Halos
Units project colored halos to immediately communicate their combat status to the human observer:
*   **No Halo**: The unit is healthy and possesses maximum Action Tokens.
*   **Orange Halo**: The unit is **Suppressed**. They possess 50% max Action Tokens. They must choose between moving or shooting; they cannot do both in a single turn.
*   **Red Halo**: The unit is **Pinned**. They have suffered overwhelming suppressing fire and possess 0 Action Tokens. They will automatically skip their turn and hug the dirt until the incoming fire ceases.

---

## 4. Understanding AI Behavior & Learning (Reinforcement Learning)
The units in the engine are autonomous. You do not micro-manage their movement.

If a unit's profile in the Master Database is set to `learned: false`, it is currently an "Explorer." In the first few episodes (resets) of a simulation, Exporers will behave irrationally, wander aimlessly, or fire randomly.

However, behind the scenes, their actions (and subsequent rewards or deaths) are continuously updating the in-memory Q-tables. Over the course of dozens of episodes, you will witness the units naturally discarding suicidal tactics in favor of cover-utilization, focused firing, and objective capture—demonstrating the core capability of the Reinforcement Learning engine.
