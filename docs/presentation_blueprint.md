# **Hex Grid Tactical Simulation System**
### **Presentation Blueprint & Technical Manual**

---

## **0. Cover Slide**
*   **Product Name**: Wargame Engine v1.0
*   **Tagline**: *“A Reinforcement Learning–Driven Tactical Simulation Environment”*
*   **Context**: Leveraging Markov Decision Processes for Autonomous Combat Logic.

---

## **1. Executive Overview (Modern Tactical Simulation)**
**The Challenge**: Traditional tactical sims rely on "If-Then" scripts. They are predictable, brittle, and fail to adapt to creative human maneuvers.

**The Solution**: An environment where entities **learn** optimal behavior through interaction.
*   **Adaptive Intelligence**: RL-driven agents that discover flanking, suppression, and defensive positioning without being told "how."
*   **Multi-Layer Decision Architecture**: Separation of high-level strategic intent from low-level tactical execution.

---

## **2. System Architecture (The "Director" Pattern)**
The system is built on a clean decoupling of concerns:
*   **UI Layer (PyQt5)**: High-precision desktop control with a custom "Tactical CSS" design system (Zinc-Dark/Slate-Light).
*   **Simulation Engine (RL + MDP)**: The `ActionModel` (The "Clock") coordinates the Sense-Decide-Act loop.
*   **Data Layer (JSON)**: Distributed disk-persistent storage managed by a global `DataManager`.

---

## **3. User Journey: The Integrated Workflow**

### **3.1 Entry Point — Mission Control**
*   **Feature**: Dashboard for Project and Map management.
*   **Logic**: "Deep Link" loading allows users to jump directly into specific map states from the explorer.
*   **Intent**: Minimize friction between the idea phase and the simulation.

### **3.2 Terrain Construction (The State Space)**
*   **Elements**: Rivers, Canals, Forests, Obstacles.
*   **Technical Impact**: Every hex is an object with varying "Cost" and "Cover" attributes.
*   **Why It Matters**: Terrain directly modifies the **Reward Function**. Moving through a forest is "costly" in time (tokens) and score (punishing slow advance).

### **3.3 Scenario Rules (Operational Boundaries)**
*   **Configurations**:
    *   **Force Roster**: Automated tactical naming (e.g., `A/Company1`, `B/Platoon2`).
    *   **Unit Hierarchy**: Section (10), Platoon (30), Company (110).
    *   **Stack Limits**: Physical constraints on unit density per hex (prevents "Death Stacks").

### **3.4 Strategy Design (The "Zones" System)**
*   **Reserve Zones**: Areas where reinforcements wait.
*   **Obstacle Zones**: High-penalty regions for pathfinding.
*   **Goal Areas**: Dynamic reward anchors. If an agent stays in a Goal Area, its **Reward Accumulator** ticks up positive points.

---

## **4. Reinforcement Learning: Core Intelligence**

### **4.1 Why RL?**
Traditional AI (A* or FSM) just follows paths. RL **evaluates** paths.
*   **State-Action Mapping**: `(Situation X) -> (Action Y) = Reward Z`.
*   **Emergent Behavior**: Agents learn to wait for fire support before advancing if the reward for "Surviving" is balanced against "Reaching Goal."

### **4.2 MDP Framework (The Math)**
*   **States**: 82-feature vector (Agent health, ammo, enemy distance, terrain cost, mission objective).
*   **Actions**: 11 discrete choices (Move N/S/E/W/NE/NW/SE/SW, Fire, Melee, Hold).
*   **Rewards**: 
    *   `+10.0` for hitting enemy.
    *   `-5.0` for backtracking (looping in circles).
    *   `-1.0` per step (time penalty).

### **4.3 Q-Learning Approach**
*   **Algorithm**: Discrete Q-Learning with Epsilon-Greedy exploration.
*   **Experience Replay**: Stores the last 5,000 actions. Learns in batches of 32 to ensure stable "Strategic Memory."

---

## **5. Dual-Layer AI Architecture (The Key Differentiator)**

### **5.1 Strategic Layer (The Commander)**
*   **Logic**: Single `StrategicCommander` brain.
*   **Role**: Assigns "Missions" to agents (e.g., "Take Hex 14,3").
*   **Scope**: Global trajectory optimization.

### **5.2 Tactical Layer (The Agent)**
*   **Logic**: Individual `QTableManager` per entity.
*   **Role**: Handles the "how" (Which direction? Should I fire?).
*   **Benefit**: Mimics military **Mission Command**: Give scientists/soldiers the *Goal*, let them solve the *Execution*.

---

## **6. Technology Stack**
| Component | Tech | Note |
| :--- | :--- | :--- |
| Framework | **PyQt5** | Robust desktop threading for heavy RL computation. |
| RL Registry | **Gymnasium** | Custom `Wargame-v0` environment registration. |
| Storage | **JSON DB** | Human-readable, disk-sharded persistent storage. |
| AI | **NumPy** | High-speed matrix math for state encoding. |

---

## **7. Backend Evolution (Roadmap)**
*   **Current State**: Sharded JSON files (Low RAM overhead, disk-persistent).
*   **Future Goal**: **Redis** for real-time state caching + **PostgreSQL** for massive multi-user scenario tracking.
*   **Why?**: JSON is great for prototyping; SQL is necessary for high-frequency distributed training.

---

## **8. Closing Summary**
Our system isn't just a game—it's a **Tactical Lab**. We have separated the *Math* from the *Map*, allowing for a fully extensible platform where AI learns the art of war through the science of rewards.
