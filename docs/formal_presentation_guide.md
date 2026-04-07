# **Hex Grid Tactical Simulation System**
## **Structured Presentation Document (Stakeholder / Investor – Formal Guide)**

---

## **0. How to Use This Document**
This document is intentionally modular. Each section can be read independently or followed as a linear narrative.

**Tracks:**
*   **[FLOW]** User journey and interface.
*   **[AI]** Reinforcement learning and decision system.
*   **[ARCH]** System architecture and backend.
*   **[DEEP]** Mathematical and advanced technical detail.

---

## **1. Executive Overview [FLOW]**

### **1.1 System Definition**
A hex-grid based tactical simulation environment designed to model strategy formation and execution using dual-layer reinforcement learning.

### **1.2 Problem Context**
Traditional tactical systems rely on "Scripted Logic" (Finite State Machines):
*   **Deterministic**: AI follows predictable IF-THEN patterns.
*   **Non-adaptive**: Cannot react to creative or unforeseen human maneuvers.
*   **Unable to generalize**: Strategy for Map A rarely works on Map B.

### **1.3 Core Shift**
*   **From Fixed Logic**: $f(x) = k$ (Hardcoded response).
*   **To Adaptive Policy**: $\pi(a|s)$ (Probabilistic decision based on value).

### **1.4 Objective**
Maximize the Cumulative Reward ($G_t$):
$G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1}$

---

## **2. System Overview [ARCH]**

### **2.1 High-Level Components**
*   **UI Layer (PyQt5)**: Real-time state visualization, tactical design language, and scenario control.
*   **Simulation Engine (ActionModel)**: The execution environment governing the temporal step logic and movement/combat physics.
*   **Data Layer (JSON/Persistent)**: A distributed sharded database architecture for AI knowledge and scenario state.

### **2.2 System Diagram [ARCH]**
*(Visualization: UI Layer ↔ ActionModel ↔ Feature Encoder ↔ Q-Table Database)*

---

# **TRACK A — USER FLOW**

---

## **3. Entry & Scenario Selection [FLOW]**

### **Description**
The landing interface acts as the "Command Center," allowing users to initialize new tactical environments or resume existing training sessions via the Project Explorer.

### **Purpose**
Minimize setup friction, specifically decoupling map data from simulation rules to allow for rapid scenario switching.

---

## **4. Terrain Editor (Map Construction) [FLOW]**

### **Description**
Users define the geometric state space using a flat-top hexagonal grid.
*   **Terrain Types**: Rivers, Mountains, Urban Centers, and Forests.
*   **Attributes**: Each hex contains cost ($\text{move\_cost}$) and cover ($\text{defense\_bonus}$) scalars.

### **System Role**
Terrain attributes directly modify the **Reward Function** and the **Transition Probability**, forcing the AI to evaluate risk vs. speed.

---

## **5. Scenario Rules Configuration [FLOW]**

### **Description**
Defines operational constraints:
*   **Hierarchies**: Section (10), Platoon (30), Company (110).
*   **Roster**: Automatic indexing (e.g., `A/Company1`, `B/Company1`).
*   **Stacking**: Max units allowed per hex.

### **System Role**
Determines the boundaries of the **Action Space** and the capacity of the **State Vector**.

---

## **6. Defender Strategy Design [FLOW]**

### **Description**
Spatial intent encoding:
*   **Obstacle Zones**: High-cost regions ($C = \infty$ for pathfinding).
*   **Goal Areas**: Mathematical sinks providing positive Reward ($+R$) for occupancy.

### **System Role**
Converts human tactical intuition into numerical "Gravity Wells" that guide AI training.

---

## **7. Defender Deployment [FLOW]**

### **Description**
Manual assignment of roster agents into defined defensive zones. The system validates placement against roster rules and zone boundaries.

---

## **8. Attacker Strategy & Deployment [FLOW]**

### **Description**
Mirror process for the attacking force. Attacker zones determine the "Entry Vector" for the AI, while deployment sets the initial state of the simulation.

---

## **9. Simulation Control [FLOW]**

### **Description**
The "Play" environment featuring:
*   **Training Mode**: High-speed execution with $\epsilon$-greedy exploration.
*   **Observe Mode**: Real-time visualization of agent "Thoughts" (Top-3 Q-values) and health trends.

---

# **TRACK B — INTELLIGENCE SYSTEM**

---

## **10. Reinforcement Learning Overview [AI]**

### **Concept**
The system uses **Value-Based learning**. Agents don't have a map of the world; they have a "Value Map" of actions.

### **Key Idea**
Agents map states ($S$) to actions ($A$) to maximize a reward scalar ($R$). This is solved by iteratively improving the Action-Value function $Q(s, a)$.

---

## **11. MDP Formalism [AI]**

### **Definition**
$MDP = \langle S, A, P, R, \gamma \rangle$

### **Mapping**
*   **$S$**: Hex coordinates, health, ammo, and distance to objective.
*   **$A$**: 11 discrete tactical actions (8 Directional Move, Fire, Melee, Hold).
*   **$P$**: Transition function (Physics of the hex grid).
*   **$R$**: Reward Engine (Hit/Miss, Reach Goal, Survival).
*   **$\gamma$**: Discount factor ($0.99$), prioritizing future success over immediate gain.

---

## **12. Q-Learning Mechanism [AI]**

### **Update Rule (Bellman Equation)**
$Q(s, a) \leftarrow (1 - \alpha) Q(s, a) + \alpha [R + \gamma \max_{a'} Q(s', a')]$

### **Policy**
**$\epsilon$-greedy Strategy**:
*   $\epsilon$ chance to explore (random action).
*   $1-\epsilon$ chance to exploit (best known action).
*   $\epsilon$ decays over time to stabilize the strategy.

---

## **13. Reward System [AI]**

### **Components**
*   **Mission Reward**: $+400$ for objective completion (decays with time).
*   **Combat Reward**: $+50$ for engagement hit $+ 10 \cdot \text{casualties}$.
*   **Efficiency Penalties**: $-1.0$ per step; $-10.0$ for revisiting the same hex (looping).

### **Purpose**
Translates high-level mission success into a singular optimization target for the AI's gradient ascent.

---

## **14. Feature Encoding [DEEP]**

### **Method**
**Tile Coding & Hashing**:
*   8 overlapping $10 \times 10$ tilings.
*   Hashing state into a 4096-dimensional sparse index.

### **Purpose**
Enables the AI to **Generalize**. If an AI learns that "Woods = Cover" in one area, it applies that knowledge to all wooded areas across the state space.

---

## **15. Dual-Layer AI Architecture [AI]**

### **Commander Layer (Strategic)**
*   Assigns intermediate high-level goals.
*   Global Q-table for trajectory optimization.

### **Agent Layer (Tactical)**
*   Executes localized movement and combat.
*   Individual Q-tables for role-specific survival.

### **Benefit**
Reduces the "Curse of Dimensionality" and mimics modern military Mission Command.

---

## **16. Combat & Tactical Modeling [DEEP]**

### **Lethality Calculation**
$L = \frac{\text{BaseLethality} \cdot \text{Accuracy} \cdot \text{AttrRatio}}{\text{CoverBonus}}$

### **Probabilistic Modeling**
Attrtiton is sampled from a **Poisson Distribution**:
$P(X=k) = \frac{\lambda^k e^{-\lambda}}{k!}$ where $\lambda = L / 10$.

---

# **TRACK C — ARCHITECTURE & BACKEND**

---

## **17. Technology Stack [ARCH]**

*   **Python**: Core ML logic and scripting.
*   **PyQt5**: Native high-performance UI rendering.
*   **Gymnasium**: Environment standard for RL algorithm compatibility.

---

## **18. Data Layer (Current) [ARCH]**

### **JSON Sharding**
Data is sharded across discrete JSON files:
*   `maps/`: Geometric data.
*   `training/`: Q-value sparse arrays.
*   `scenarios/`: Rule definitions.

### **Benefit**
Maximum transparency, human-auditable knowledge, and zero-RAM disk-based persistence.

---

## **19. Data Layer (Future) [ARCH]**

### **PostgreSQL**
Structured storage for episode history and analytical querying.

### **Redis**
Extreme high-speed in-memory key-value lookups for $Q(s, a)$ during massive parallel training runs.

---

## **20. CRUD System [ARCH]**

### **Extensibility**
Full management interface for:
*   **Weapons**: Modifying lethality, range, and rate-of-fire.
*   **Units**: Defining speed and base personnel.
*   **Terrain**: Adjusting movement costs and defense bonuses.

---

# **TRACK D — SYSTEM EVALUATION**

---

## **21. Strengths**
*   **Adaptive Intelligence**: Emergent tactics (flanking, suppression).
*   **Modular Design**: Swap AI algorithms without changing maps or rules.
*   **Mathematical Transparency**: Every action is traceable to a specific Reward scalar.

---

## **22. Limitations**
*   **Training Time**: High-entropy scenarios require many episodes to converge.
*   **JSON Bottleneck**: Disk I/O limits parallel thread scaling (Target for Future SQL).

---

## **23. Future Roadmap**
*   **Distributed Training**: Multi-node reinforcement learning.
*   **Real-time Simulation**: Moving from discrete steps to continuous-time events.
*   **Scenario Marketplace**: User-contributed tactical challenges.

---

## **24. Closing Summary**
The Hex Grid Tactical Simulation System bridges the gap between human-defined strategic intent and machine-optimized execution, providing a sandbox for discovering high-fidelity tactical solutions.

---

## **Appendix: Advanced Mathematical Deep Dive**

### **Hexagonal Metric Math**
*   **Coordinate Constraint**: $q + r + s = 0$
*   **Hex-to-Pixel**:
    $x = \frac{3}{2} \cdot size \cdot q$
    $y = \sqrt{3} \cdot size \cdot (\frac{q}{2} + r)$
*   **Manhattan Distance (Hex)**:
    $d(A, B) = \max(|A_q - B_q|, |A_r - B_r|, |A_s - B_s|)$

### **Reinforcement Learning Formalism**
*   **Bellman Update**: $Q_{new}(s, a) = (1 - \alpha) Q(s, a) + \alpha [R + \gamma \max_{a'} Q(s', a')]$
*   **State Encoding**: $O(8 \text{ tilings} \cdot \Theta(\text{hash\_lookup}))$ complexity.
