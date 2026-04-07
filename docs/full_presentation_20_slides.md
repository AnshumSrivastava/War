# **Hex Grid Tactical Simulation System**
## **Detailed Technical Presentation Blueprint (v2.0 - Mathematical Edition)**

---

## **Slide 1: Cover Slide**
*   **Product Name**: Wargame Engine v1.0
*   **Tagline**: *“A Reinforcement Learning–Driven Tactical Simulation Environment”*
*   **Technical Core**: Multi-Agent MDP Optimization in an $O(k)$ Spatiotemporal Grid.

---

## **Slide 2: Executive Overview: The Problem Space**
*   **Context**: Traditional "Scripted" AI uses Finite State Machines (FSM).
*   **The Problem**:
    *   **Linearity**: $If(EnemyInRange) \rightarrow Fire()$.
    *   **Mathematical Brittleness**: Scripts don't handle the "Grey Space" of uncertainty effectively.
*   **The AI Shift**: Replacing $f(x) = k$ (static) with $\pi(a|s)$ (probabilistic policy) that adapts to the shifting entropy of the battlefield.

---

## **Slide 3: The Vision: Agentic Combat Logic**
*   **Concept**: We optimize for **Value ($V$)**, not for **Instructions**.
*   **Objective**: Transform human tactical intent into a **Reward Scalar ($R$)**.
*   **Goal**: Find the optimal policy $\pi^*$ that maximizes the expected return $G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1}$.

---

## **Slide 4: System Architecture Overview**
*   **UI (PyQt5)**: Renders the state $S$ at 60FPS.
*   **Engine (ActionModel)**: The execution environment for the transition function $P(s', r | s, a)$.
*   **Persistence (JSON)**: Serializing the Q-Table $Q(s, a)$ as a sparse matrix for disk-efficient learning.

---

## **Slide 5: UI UX: The Design System**
*   **Philosophy**: "Visualizing the Invisible Math."
*   **Design Tokens**:
    *   **Green/Red Paths**: Representing $Q$-value confidence intervals.
    *   **Confidence Meters**: Real-time display of $\epsilon$ (Exploration factor).
*   **Design**: Zinc-Dark theme tailored for high-contrast tactical data overlay.

---

## **Slide 6: Phase 1: Hexagonal Geometry (The Math of Space)**
*   **System**: Flat-Top Cube Coordinates ($q, r, s$).
*   **Primary Constraint**: $q + r + s = 0$ (Every hex is a slice of a 3D cube plane).
*   **Distance Formula**: 
    $d(A, B) = \frac{|A_q - B_q| + |A_r - B_r| + |A_s - B_s|}{2}$
*   **Pixel Projection**:
    $x = size \cdot \frac{3}{2}q$
    $y = size \cdot (\frac{\sqrt{3}}{2}q + \sqrt{3}r)$

---

## **Slide 7: Phase 2: Roster & Tactical Hierarchy**
*   **Scale Factors**:
    *   **Section**: $N=10$
    *   **Platoon**: $N=30$
    *   **Company**: $N=110$
*   **Lethality Mapping**: Units are assigned a **Combat Factor** $\beta$ based on their roster stats, which acts as a scalar in the attrition equation.

---

## **Slide 8: Phase 3 & 4: Strategic Zone Metrics**
*   **Obstacles**: Defined as "Hard Cost" modifiers ($C_{hex} = \infty$) in pathfinding.
*   **Goal Areas**: Mathematical sinks with a constant Reward $R_{step}$ that incentives "Occupancy" states.
*   **Area of Interest ($AoI$)**: Defined by a radius $r$ around a central hex $H_c$ using the Spiral Algorithm: 
    $Spiral(H_c, r) = \bigcup_{i=0}^{r} Ring(H_c, i)$

---

## **Slide 9: Phase 5 & 6: Deployment Logic**
*   **Border Collision**: Ray-casting algorithm used to determine if a Hex $H$ is valid within Polygon $P$.
*   **Status Indexing**: Every unit is assigned a Unique Global Identifier ($UUID$) that maps their deployment state to the JSON persistence layer $D(u)$.

---

## **Slide 10: Phase 7: The Simulation Step (Sense-Decide-Act)**
*   **Latency**: Yielding to the Qt Event Loop ensures $O(1)$ responsiveness for the user.
*   **The Loop**:
    1.  **Sense**: Update vision matrix $V_a$.
    2.  **Decide**: $a_t = \text{argmax}_a Q(s_t, a)$.
    3.  **Act**: Apply transition $s_{t+1}$.
    4.  **Reward**: Calculate $R_t$ and update brain.

---

## **11. Reinforcement Learning: The MDP Formalism**
*   **Formulation**: $MDP = \langle S, A, P, R, \gamma \rangle$:
    *   **$S$**: The 82-feature vector space.
    *   **$A$**: The discrete action space of 11 tactical moves.
    *   **$P$**: The environment transition (deterministic movement, stochastic combat).
    *   **$R$**: The Reward Engine.
    *   **$\gamma$**: The Discount Factor (currently $0.95-0.99$).

---

## **12. Feature Encoding: Tile Coding & Hashing**
*   **Technology**: Coarse Coding via overlapping Tilings.
*   **The Vector**: 8 tilings of $10 \times 10$ bins.
*   **Hashing Rule**: 
    $h(s) = (\sum_{i} w_i \cdot feature_i \oplus TilingID) \pmod{4096}$
*   **Result**: This allows the AI to generalize from a specific hex to "nearby similar situations."

---

## **13. The Action Space & Token Economy**
*   **Actions**:
    *   `MOVE` ($\Delta q, \Delta r$) for 8 directions.
    *   `FIRE` (Target $T$).
    *   `HOLD` (Energy conservation).
*   **Token Formula**: 
    $Tokens_{remaining} = Tokens_{initial} - (Cost_{base} \cdot Terrain_{multiplier} + Cost_{action})$
    *   Firing costs $2.0$ tokens; Moving costs $1.0 - 2.0$.

---

## **14. Reward Modeling: The Objective Function**
*   **Total Reward**: $R = R_{mission} + R_{combat} - P_{survival} - P_{movement}$
*   **Mission Decay**: $R_{goal} = 400 \cdot (1 - \frac{step}{step_{max}})$
*   **Combat Logic**:
    $R_{fire} = 50 + (10 \cdot casualties\_dealt)$
*   **Penalties**:
    $P_{loop} = -10.0$ (Backtracking).
    $P_{step} = -1.0$ (Time pressure).

---

## **15. Learning Equations: Bellman Update**
*   **The Goal**: Estimate the Action-Value Function $Q(s, a)$.
*   **Update Rule**:
    $Q(s, a) \leftarrow (1 - \alpha) Q(s, a) + \alpha [R + \gamma \max_{a'} Q(s', a')]$
*   **Epsilon-Greedy Policy**:
    $a = \begin{cases} \text{random} & \text{with prob } \epsilon \\ \text{argmax}_a Q(s, a) & \text{with prob } 1-\epsilon \end{cases}$

---

## **16. Dual-Layer AI: Strategic Command Architecture**
*   **Concept**: Decomposing a high-dimensional problem into two manageable sub-problems.
*   **Structure**:
    1.  **Commander (Macro)**: $MacroStates \rightarrow StrategicGoals$.
    2.  **Agent (Micro)**: $MicroStates \rightarrow TacticalActions$.
*   **Data**: Distinct Q-tables for Strategy vs. Execution.

---

## **17. Strategic Layer: The Commander Brain**
*   **Equation**: Operates on a lower frequency ($f_{step} / 10$).
*   **Logic**: Assigns a Mission Hex $H_{goal}$ to an agent. 
*   **Metric**: Evaluates the **Trajectory Reward** (the sum of all rewards an agent got while following a commanded path).

---

## **18. Tactical Layer: Combat Attrition (The Fire Engine)**
*   **Lethality Formula**:
    $L = \frac{BaseLethality \cdot Accuracy \cdot (AtkFactor / DefFactor)}{CoverBonus}$
*   **Casualty Sampling**: Poisson Distribution distribution logic.
    $P(X=k) = \frac{\lambda^k e^{-\lambda}}{k!}$ where $\lambda = L / 10$.
*   **Personnel Decay**: $N_{t+1} = N_t - X$.

---

## **19. Data Infrastructure: JSON Persistence**
*   **Serializing Intelligence**: 
    Knowledge is stored as `.npy` binaries for speed and `.json` sparse maps for auditability.
*   **Sparse Mapping**: 
    Only states with $\sum |Q| > 0$ are saved, reducing storage requirements by $>90\%$.

---

## **20. Evolution: Scaling to PostgreSQL & Redis**
*   **The Bottleneck**: File I/O during high-frequency parallel training.
*   **The Upgrade**:
    *   **PostgreSQL**: Structured historical analysis of episodes.
    *   **Redis**: In-memory KV-store for the Q-Table to enable $O(1)$ state lookups across multiple simulation instances.

---

## **21. System Strengths**
*   **Fidelity**: Non-scripted, emergent tactical intelligence.
*   **Math-First**: Decisions are derived from rigorous value-optimization, not arbitrary rules.
*   **Auditable**: Every decision can be traced back to a specific Q-Value in the database.

---

## **22. Summary**
*   **From Scenario to Solution**: A complete pipeline for training AI in complex physical environments.
*   **Legacy**: Moving wargaming from "Manual Probability" to "Machine Learning Adaptation."
*   **Final Call**: Tactical excellence via mathematical optimization.
