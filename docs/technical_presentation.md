# The War Project: Complete Technical Reference

> A comprehensive document for anyone who knows how to code and wants to fully understand every layer of this system — from state management and mathematics to how an episode plays out and what each UI tab does.

---

## Part I: What This System Is

The **War** project is a **Multi-Agent Reinforcement Learning (MARL)** research environment built on a hexagonal tactical map. It is not a game in the entertainment sense. It is a **simulation engine** where:
- Multiple autonomous agents exist on a map, each belonging to a faction (`Attacker` or `Defender`).
- Each agent independently perceives its surroundings, reasons using a learned Q-table, and executes actions (Move, Fire, Close Combat, Hold).
- A two-tier AI hierarchy guides both *macro-level strategy* (the Commander) and *micro-level tactics* (each agent).
- The system learns through thousands of episodes, saving Q-tables to disk so that learned knowledge carries over between sessions.

The environment can run **fully headlessly** (no screen) via `xvfb-run` on servers for high-speed training, or with a full **PyQt5 desktop UI** for human analysis and scenario editing.

---

## Part II: Technology Stack

| Component | Technology | Why |
|---|---|---|
| Core Language | **Python 3.12** | Rapid iteration, strong NumPy ecosystem |
| Desktop UI | **PyQt5 + PyQtWebEngine** | Cross-platform, mature widget library |
| Web UI | **Flask** | Lightweight REST/streaming server for browser-based access |
| Math & RL Memory | **NumPy** | Q-tables stored as `.npy` matrices; tile coding uses vectorized ops |
| RL Storage | **MemoryDatabase** (Redis-compatible) | Rapid read/write during training episodes |
| Backend Platform | **Supabase** | Optional cloud data sync |
| Dev Environment | **Nix (`shell.nix`)** | Hermetic, reproducible builds; eliminates "works on my machine" |
| Testing | **pytest** | Unit and integration tests in `/test/` |

---

## Part III: Directory Architecture

The entire project enforces a **strict three-layer boundary**. No layer may import above itself.

```
/currentActive
  /engine           ← Backend: pure math, simulation, AI, state
    /ai             ← Q-tables, encoder, commander, reward models
    /combat         ← Direct fire, mine negotiation, weapon data
    /core           ← Hex math, map, entity manager, pathfinding, undo
    /data           ← Data loaders, content paths, memory database
    /simulation     ← ActionModel (sim loop), move/fire/commit actions
    /state          ← WorldState, GlobalState, ThreatMap, UISettings
  /services         ← Middle-End: the only bridge between UI and engine
  /ui               ← Frontend: PyQt5 widgets, tools, canvas, views
  /web_ui           ← Alternate Frontend: Flask routes + browser canvas
  /content          ← JSON: unit definitions, weapon stats, terrain, zones
  /data/models      ← Persisted AI Q-tables (.npy + .json)
  /infra            ← Nix environment files
  /test             ← pytest test suite
  main.py           ← Entry point: launches PyQt5 app
```

### The Three Hard Rules

1. `engine/` never imports from `services/`, `ui/`, or `web_ui/`.
2. `services/` never imports from `ui/` or `web_ui/`.
3. `ui/` never imports from `engine/` directly — it always calls `services/`.

---

## Part IV: State Architecture

### 4.1 Agent State

Every agent (`BaseEntity → Agent`) tracks a 4-component state that drives all RL decisions.

| Component | Storage | Description |
|---|---|---|
| **x, y (Spatial)** | `Map._entity_positions[entity.id] → Hex(q, r, s)` | Position in cube coordinates, displayed as offset `(col, row)` to the user |
| **Time (Temporal)** | `step_number * time_per_step` (default: `10 min/step`) | Total elapsed simulation time, e.g., Step 5 = 50 game-world minutes |
| **Status** | `entity.get_attribute("suppression")`, `entity.tokens`, `entity.get_attribute("personnel")` | Combat condition: Normal / Suppressed (50+ supp) / Pinned (100+ supp) / Dead (personnel = 0) |
| **Abstraction** | `entity.attributes: AttributeDict` | All other properties (side, type, ammo, weight, fire_range, home_hex) encapsulated via dot-access dictionary |

The `AttributeDict` is a `dict` subclass that allows `entity.attributes.side` instead of `entity.attributes["side"]`, providing clean attribute access while remaining JSON-serializable.

### 4.2 Global State (Singleton)

`GlobalState` is a **Singleton** that acts as the shared notebook for the entire application.

```
GlobalState (Singleton)
  ├── map: Map                      ← terrain, zones, entity positions
  ├── entity_manager: EntityManager ← all active agents by ID
  ├── threat_map: ThreatMap         ← danger overlay per faction per hex
  ├── data_controller: DataManager  ← loaded JSON definitions (cache)
  ├── ui: UISettings                ← selected tool, theme, grid mode
  ├── undo_stack: UndoStack         ← Command Pattern history (50 steps)
  ├── project_path                  ← currently loaded .json scenario
  ├── time_per_step = 10            ← minutes per simulation tick
  └── is_learning = False           ← True during training loops
```

**Why Singleton?** Any module in the codebase — the map renderer, a PyQt widget, or a simulation step — can call `GlobalState()` and get the exact same object. This eliminates redundant state passing while maintaining a single source of truth.

**WorldState (Successor):** For new code, `WorldState` is a plain `@dataclass` (not a singleton) injected via constructor arguments. This enables multiple simultaneous scenarios and parallel training. The migration is ongoing; `GlobalState` remains as a compatibility shim.

### 4.3 Threat Map

Every simulation tick, the `ThreatMap` scans all active units and marks every hex within their firing range along the 6 hex axes with a threat score.

- `faction_threats["Attacker"][hex_tuple] += 1.0` per enemy unit that can fire on that hex.
- Used by the **Safe axis pathfinder** to add `threat * 5.0` penalty to route costs.
- Used by the **Tactical Agent encoder** to represent danger in the state vector.

---

## Part V: The Mathematics

### 5.1 Hexagonal Geometry (Cube Coordinates)

The hex grid uses `(q, r, s)` cube coordinates with the hard constraint:
$$q + r + s = 0$$

This allows hex math to behave like 3D integer arithmetic.

**Distance** between two hexes A and B:
$$d(A, B) = \frac{|A_q - B_q| + |A_r - B_r| + |A_s - B_s|}{2}$$

**Hex → Pixel** conversion (Flat-Top orientation):
$$\begin{pmatrix} x \\ y \end{pmatrix} = \text{size} \cdot \begin{pmatrix} \frac{3}{2} & 0 \\ \frac{\sqrt{3}}{2} & \sqrt{3} \end{pmatrix} \begin{pmatrix} q \\ r \end{pmatrix}$$

**Pixel → Hex** (inverse, for mouse clicks):
$$q = \frac{2x}{3 \cdot \text{size}}, \quad r = \frac{-x + x\sqrt{3}y}{3 \cdot \text{size}}$$
Then rounded via the cube-rounding algorithm that preserves $q+r+s=0$.

**Line of Sight**: Uses linear interpolation across cube coordinates from `start` to `end`, sampling $d$ intermediate points.

**Ring Generation**: To find all hexes exactly $k$ steps away (used for firing rings), the system walks $k$ steps in one direction, then traces the perimeter of the hexagon.

### 5.2 A* Pathfinding

The `Pathfinder` uses a priority queue (`heapq`) implementing classic **A***.

$$f(n) = g(n) + h(n)$$

where:
- $g(n)$ = accumulated terrain cost from start to node $n$.
- $h(n)$ = hex distance heuristic from $n$ to goal (admissible, never over-estimates).

Three cost functions are supported, each defining a different **movement axis**:
1. **Direct**: Cost from terrain JSON (`{"cost": 1.0}` for clear, `2.0` for rough).
2. **Safe**: `cost + threat * 5.0` — heavily penalizes hexes in enemy firing arcs.
3. **Fast**: Uniform cost of `1.0` — ignores terrain, finds geometric shortest path.

### 5.3 Combat Attrition: Poisson Distribution

All damage in this system is derived from the **Poisson distribution**, which models the number of independent events (hits) in a fixed interval given a known average rate.

**Direct Fire** (ranged combat):
$$\lambda_{\text{cas}} = \frac{(\text{Damage} \times \text{ROF} \times \text{Accuracy}) \times \text{Combat Ratio}}{\text{Cover} \times 10}$$

Where `Combat Ratio = Attacker Factor / Max(Defender Factor, 1)`.

**Suppression** follows the same logic with a separate lambda:
$$\lambda_{\text{supp}} = \frac{\text{Suppression Power} \times \text{Combat Ratio}}{2}$$

Casualties are **sampled** (not deterministic) using Knuth's algorithm:
```
L = exp(-λ); k = 0; p = 1.0
while p > L: k += 1; p *= random()
return k - 1
```

For large $\lambda \geq 30$ (rare, large formations), a **Gaussian approximation** is used:
$$k \sim \mathcal{N}(\lambda, \sqrt{\lambda})$$

**Mine Negotiation** uses the same Poisson mechanism:
$$\lambda_{\text{mine}} = \text{density} \times \text{base\_damage}$$

### 5.4 Suppression Mechanics

Suppression is a continuous float value on each agent:
- Decays by `20.0` per tick naturally.
- At `>= 50`: unit is **Suppressed** → receives half tokens.
- At `>= 100`: unit is **Pinned** → receives zero tokens.
- At `personnel <= 0`: unit is **Destroyed**.

---

## Part VI: The Reinforcement Learning System

### 6.1 State Encoding (Tile Coding)

Raw hex positions are encoded into a fixed-size feature vector using **Tile Coding** — a classical RL technique for generalizing across continuous or large discrete spaces.

**Architecture**: 8 overlapping tilings over the map, each with a 10×10 grid.

For a given `(col, row)` position, each tiling generates an `(idx_x, idx_y)` index:
$$\text{tile\_id} = \text{hash}(i, \text{idx}_x, \text{idx}_y)$$

The 8 active tile hashes are then **XORed** with attribute states `(casualty_level, reward_level)`:
$$\text{feature\_idx} = (\text{tile\_hash} \oplus \text{hash}(\text{cas\_state}, \text{rew\_state})) \mod 4096$$

This creates a **4096-dimensional sparse binary feature vector** per agent per step, where only 8 indices are active. The Q-table is indexed by these features.

**Casualty encoding** (4 buckets):
- `> 75%` personnel → Healthy (0)
- `> 50%` → Light (1)
- `> 25%` → Moderate (2)
- `≤ 25%` → Critical (3)

### 6.2 The Action Space

There are **11 discrete actions** (the `RL_ACTION_MAP`):

| Index | Action | Description |
|---|---|---|
| 0–5 | MOVE [direction] | Move to one of 6 neighboring hexes (E, NE, NW, W, SW, SE) |
| 6 | FIRE | Shoot at nearest visible enemy |
| 7 | HOLD / END TURN | Consume all remaining tokens, end turn |
| 8 | CLOSE_COMBAT | Melee attack on adjacent enemy |
| 9–10 | COMMIT_[ROLE] | Commit to a strategic role (e.g., suppression support) |

### 6.3 Q-Learning (Tactical Agent)

The tactical brain is a **tabular Q-Learning** agent stored as a `NumPy` matrix `Q[state_size × action_size]` (4096 × 11).

**Bellman Update Rule:**
$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]$$

| Hyperparameter | Value | Meaning |
|---|---|---|
| $\alpha$ (learning rate) | `0.1` | How strongly new experience overwrites old |
| $\gamma$ (discount factor) | `0.99` | Future rewards are nearly as important as immediate |
| $\epsilon$ (exploration) | `1.0 → 0.05` | Probability of choosing a random action; decays by 0.995/episode |

**Two Brains**: Each unit can use one of two Q-table managers:
- **Ephemeral**: Starts empty, explores actively. Used for training.
- **Persistent**: Loads from disk. Used for "veteran" AI difficulty.

**Experience Replay**: All `(state, action, reward, next_state, done)` tuples are stored in a `ReplayBuffer` (capacity 5000). Every 10 steps and at every episode end, a random **batch of 32** is sampled for training, improving stability.

### 6.4 The Commander (Strategic RL)

The Commander uses a **simpler Q-table** (12 states × 3 actions) because strategic decisions are lower-frequency and more interpretable.

**State discretization** uses two features:
- `threat_bucket`: 0–3 based on avg threat along Direct path.
- `dist_bucket`: 0–2 based on distance to objective (short/medium/far).
$$\text{state\_idx} = (\text{threat\_bucket} \times 3) + \text{dist\_bucket}$$

**Actions**: Choose between Direct (0), Safe (1), and Fast (2) axes.

**Learning**: Uses **trajectory-based discounted reward** propagated backwards through the sequence of Commander decisions made during an episode:
$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha(G_t - Q(s_t, a_t)), \quad G_t = \gamma \cdot G_{t+1}$$

This connects early routing decisions to late-episode outcomes — a key advantage over single-step updates.

### 6.5 The Reward Model

The reward function shapes the AI's behavior by assigning numerical values to outcomes:

| Event | Reward |
|---|---|
| Fire hit (per casualty) | `+50 + casualties * 10` |
| Kill (personnel → 0) | `+150` |
| Fire miss | `-5` |
| Moving closer to objective | `+22.5 per hex` |
| Moving away from objective | `-22.5 per hex` |
| Arriving at objective | `+400 × decay_multiplier` |
| Unit takes personnel losses | `-2 per lost` |
| Unit destroyed | `-400` |
| Revisiting a hex | `-10` |
| Moving under fire (evasion) | `+5` |
| Per step (time pressure) | `-1` |

The **goal reward** decays over time: `multiplier = max(0.1, 1 - step/max_steps)`, incentivizing speed.

---

## Part VII: The Simulation Lifecycle (One Episode)

An **episode** is one complete engagement from setup to terminal condition.

### 7.1 Episode Startup

1. `SimulationService.reset()` is called → `ActionModel.reset_episode()`.
2. All agent `visited_hexes` are cleared (prevents backtracking penalties from previous episode).
3. Episode counter increments; epsilons are decayed.
4. Batch training runs on the Replay Buffer.
5. Knowledge is auto-saved to disk.

### 7.2 A Single Simulation Step (The Tick)

`SimulationService.step(step_number)` → `ActionModel.step_all_agents(step_number)`:

**Phase 0 — Environmental Update**
- `ThreatMap.update()`: Scans all entities, projects firing lines along all 6 hex axes out to `fire_range`, increments `faction_threats[side][hex]` by 1.0.

**Phase 1 — Token Generation**
- Each agent receives tokens equal to its movement speed (capped at `2.0`).
- Suppression modifiers clamp this: Suppressed → `speed/2`, Pinned → `0`.
- Suppression itself decays by `20.0` points this tick.

**Phase 2 — Sense** (per agent)
- Agent scans all entities within its `vision_range` (hex distance).
- The closest visible enemy becomes the `target`.

**Phase 3 — Command (Strategic)**
- If the agent has no active command, or has reached its current goal, `StrategicCommander.assign_mission()` is called.
- The Commander generates 3 route options (Direct/Safe/Fast), gathers their stats (length, avg threat), and uses its RL brain to select an **axis**.
- An `AgentCommand` (`MOVE`/`CAPTURE`/`DEFEND`) with the chosen `axis` is assigned.

**Phase 4 — Decide (Tactical RL)**
- `StateActionEncoder.get_features()` creates the sparse 8-active-index feature vector from the agent's position and health.
- The Q-table returns Q-values for all available actions.
- $\epsilon$-greedy selection: with probability $\epsilon$, pick random; otherwise, `argmax Q(s, a)`.

**Phase 5 — Act (Execution)**
- Token cost is deducted: MOVE = 1.0 (or 2.0 in rough terrain), FIRE/COMBAT = 2.0, HOLD = all remaining.
- If insufficient tokens, the agent's turn ends.
- The selected action is dispatched to its handler (`MoveAction`, `FireAction`, `CloseCombatAction`, `CommitAction`).
- **Move**: Validates direction, terrain, weight limit → updates map position → checks for mine zones.
- **Fire**: Calls `DirectFire.calculate_attrition()` → Poisson sample → applies casualties and suppression.
- **Close Combat**: Similar to fire but at melee range.
- Events (visual) are appended to the event list for the UI renderer.

**Phase 6 — Learn**
- New state features are computed (`next_state`).
- `RewardModel.calculate_reward()` scores the action.
- The `(state, action, reward, next_state, done)` transition is pushed to `ReplayBuffer`.
- Every 10 steps, a batch of 32 is sampled and `QTableManager.update_batch()` is called.

**Phase 7 — Terminal Check**
- `check_terminal_conditions()`:
  - `step > max_steps` → timeout, episode over.
  - Only one side has `personnel > 0` → elimination, episode over.
- Events + logs are returned to the UI via `event_bus.emit("tick_complete", payload)`.

---

## Part VIII: The Services Layer

The **Services Layer** is the only permitted bridge between UI and Engine. All public functions return a `ServiceResult(ok: bool, data: Any, error: str, code: str)` — they never raise exceptions to the caller.

| Service | Responsibility |
|---|---|
| `map_service` | Create maps, load/save terrain, query hex data |
| `entity_service` | Place/remove/query agents |
| `simulation_service` | `step()`, `reset()`, `run_episodes()`, terminal checks |
| `scenario_service` | Load/save full scenario JSON (Golden State snapshots) |
| `data_service` | Unit definitions, weapon catalogs, terrain configs |
| `ai_service` | Read/write epsilon values, Q-table states |
| `rules_service` | Validate moves, check win/loss conditions |
| `path_service` | Expose pathfinding results to the UI |

Events flow via the **Event Bus** (`event_bus.emit("tick_complete", payload)`), allowing the UI to subscribe without polling. The UI never calls engine internals.

---

## Part IX: The UI — Tabs, Tools, and Software Behavior

### 9.1 Main Window Structure (`main_window.py`)

The application opens as a **PyQt5 docked-panel layout** with:
- A central **Hex Canvas** (`hex_widget.py`) rendering the map.
- Multiple **dockable panels** around it.
- A **toolbar** with tool buttons and simulation controls.

### 9.2 The Hex Canvas (`hex_widget.py`)

The primary interactive area. It uses a `QGraphicsView` / `QGraphicsScene` to render:
- **Hexagonal tiles** painted based on terrain type and color.
- **Zone overlays**: Goal Areas (gold), Obstacle Zones (mine fields), Side Boundaries.
- **Agent icons**: Color-coded by faction; moving units animate their icon sliding between hexes.
- **Movement Trails**: Historical path lines traced across the hexes the agent has visited.
- **Combat Lasers**: Animated line drawn from attacker to target during fire.
- **Reward Labels**: Floating `+/-` numbers above agents toggled on/off.
- **AI Thinking Bubbles**: The Inspector shows the top 3 Q-values the agent considered.

Mouse input is routed through a `CanvasController` which dispatches clicks to the **active tool**.

### 9.3 Map Editor Tools (`ui/tools/`)

| Tool | Behavior |
|---|---|
| `paint_tool.py` | Left-click paints terrain type onto hovered hex; right-click erases |
| `place_agent_tool.py` | Places a new agent of the configured type at the clicked hex |
| `zone_tool.py` | Click-and-drag to draw zones (Goal Area, Obstacle, Side Boundary) |
| `edit_tool.py` | Click to select entities; shows Inspector properties for editing |
| `path_tool.py` | Draws custom named path lines across a sequence of hexes |
| `erase_tool.py` | Removes terrain, agents, or zones from the map |

All tools write to state only through `services/`, never touching the engine directly.

### 9.4 Panels and Tabs

#### **Inspector Panel** (`object_properties_widget.py`)
Contextually shows editable form fields for the currently selected object:
- For **agents**: name, side, type, personnel count, suppression level, status, AI debug info.
- For **tiles**: terrain type, movement cost.
- For **zones**: zone type, subtype, assigned side.

#### **Scene Hierarchy** (`scene_hierarchy_widget.py`)
A tree-view listing every agent and zone on the map. Supports:
- Click to select and focus the camera on an entity.
- Toggle visibility of individual objects.

#### **Event Log** (`event_log_widget.py`)
A scrolling HTML ticker showing live combat events per step, e.g.:
```
[Step 5] Bravo Squad: FIRE → R:+60.0 (Alpha Platoon D:3)
[Step 5] Alpha Platoon: MINE STRIKE! -12 pers
```

#### **Dashboard** (`dashboard_widget.py`)
Analytics charts showing:
- Action distribution over time (MOVE vs FIRE vs HOLD bar chart).
- Explore vs Exploit ratio (how often agents pick random vs best-known action).
- Epsilon decay curve.
- Personnel over time per unit.

#### **Simulation Controls** (`workflow_bar.py`)
Buttons for:
- **Step** (⏭): Advance one tick.
- **Play/Pause** (▶/⏸): Auto-advance at configured speed.
- **Learn** (🧠): Run N episodes headlessly.
- **Reset** (🔄): Restore agents to starting positions.
- **Save Knowledge** (💾): Force-write Q-tables to disk.

#### **Master Data Widget** (`master_data_widget.py`)
Database browser for the content JSON files. Allows viewing and editing:
- Unit definitions (type, personnel, speed, weapons, vision).
- Weapon catalog (damage, rate of fire, accuracy, suppression, range).
- Terrain templates (cost, cover bonus, color).

#### **Scenario Manager** (`scenario_manager_widget.py`)
Load/save complete scenario files (map + entities + zones). Implements the **Golden State** snapshot pattern: when entering simulation mode, the scenario state is frozen into a snapshot; on reset, it is restored exactly — no simulation-time changes persist back to the editor.

#### **Maps Widget** (`maps_widget.py`)
Browse, create, and load different map files. Map dimensions are configurable; changing them re-initializes the encoder and pathfinder.

#### **Rules Widget** (`rules_widget.py`)
Configure per-scenario gameplay rules (max steps per episode, stacking limits per hex, etc.). These values feed directly into the `check_terminal_conditions()` function.

#### **Timeline Panel** (`timeline_panel.py`)
Displays a scrollable history of past steps in the current episode, allowing the user to replay and inspect any historical state.

---

## Part X: Data Definitions (Content Layer)

All unit, weapon, and terrain data lives in `/content/` as JSON files and is loaded at startup by `DataManager`.

### Unit Definition Example
```json
{
  "name": "FireAgent",
  "type": "FiringAgent",
  "personnel": 100,
  "combat_factor": 5,
  "vision_range": 6,
  "fire_range": 6,
  "speed": 2,
  "learned": false,
  "weapon": {
    "name": "Assault Rifle",
    "damage": 3,
    "rate_of_fire": 5,
    "accuracy": 0.65,
    "suppression": 15,
    "max_range": 6
  }
}
```

`learned: true` causes the engine to assign the **Persistent** (veteran) Q-table to that unit instead of the Ephemeral (explorer) one.

### Terrain Definition Example
```json
{
  "name": "Forest",
  "cost": 2.0,
  "color": "#2d6a4f"
}
```
A `cost` of `2.0` means it takes 2 movement tokens to enter and doubles as the **cover defense bonus** in the combat formula.

---

## Part XI: Persistence — How the AI Remembers

After each training episode, `save_knowledge()` writes two files:

| File | Format | Purpose |
|---|---|---|
| `data/models/q_table.npy` | NumPy binary | Fast load; the persistent (veteran) Q-table |
| `data/models/q_table.json` | Sparse JSON | Human-readable; debug/inspect individual state-action values |
| `data/models/ephemeral_q_table.npy` | NumPy binary | Explorer brain in progress |
| `data/models/commander_q_table.json` | JSON 12×3 | Strategic Commander's learned routing preferences |

On startup, both Q-tables are loaded from disk. If no file exists, they start from all zeros (uniformly uninformed).

---

## Appendix: Running the System

```bash
# Desktop App
python main.py

# Headless (server training)
xvfb-run python main.py

# Run all tests
python -m pytest test/ -v

# Nix dev shell (reproducible env)
nix-shell infra/shell.nix
```
