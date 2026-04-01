# Wargame Engine: System Interaction & UML Diagrams

This document utilizes Mermaid.js to visually articulate the data flow, complex hierarchical relationships, and precise timing loops of the Wargame Engine. It is intended to bridge the conceptual gap between high-level architecture and the specific Python implementations.

## 1. Engine Architecture (Module Interactivity)
This diagram illustrates the strict Dependency Inversion principle employed by the engine. The Presentation Layer (`/ui/`) is entirely dependent on the Simulation and State layers. Conversely, the Mathematical Simulation (`/engine/`) is completely ignorant of the UI's existence.

```mermaid
graph TD
    classDef ui fill:#2b2b30,stroke:#3f3f46,stroke-width:2px,color:#fff;
    classDef logic fill:#0d2b45,stroke:#4dabf7,stroke-width:2px,color:#fff;
    classDef state fill:#2d1b1b,stroke:#ff6b6b,stroke-width:2px,color:#fff;
    classDef ext fill:#1b2d1b,stroke:#6bff6b,stroke-width:2px,color:#fff;

    Main[main.py Executable]:::ui --> MainWindow(MainWindow - PyQt5):::ui
    MainWindow --> GlobalState[(GlobalState Singleton)]:::state
    
    subgraph "Presentation Layer (/ui/)"
        MainWindow -.-> HexWidget(HexWidget - 2D Canvas Viewport):::ui
        MainWindow -.-> SceneHier(SceneHierarchy Tree Control):::ui
        MainWindow -.-> ObjProps(ObjectProperties Form Inspector):::ui
        HexWidget --> Visualizer(Animation Decoupling Queue):::ui
    end
    
    subgraph "Mathematical Simulation Layer (/engine/)"
        MainWindow -.-> SimCtrl[SimulationController Timekeeper]:::logic
        SimCtrl --> ActModel[ActionModel Logic Loop]:::logic
        ActModel -.-> Commander[StrategicCommander Macro-AI]:::logic
        ActModel -.-> Combat[DirectFire Probability Engine]:::logic
    end
    
    subgraph "State & Data Persistence Layer"
        GlobalState -.-> Map[(Hexagonal Map Geography)]:::state
        GlobalState -.-> EntityManager[(Unit Registry Database)]:::state
        GlobalState -.-> DataCtrl[(JSON Master Data Cache)]:::state
        
        ActModel --> QTable[(In-Memory Q-Tables)]:::ext
        Commander --> QTable
    end
```

---

## 2. The Reinforcement Learning (RL) Event Loop
This sequence diagram visualizes the exact chronological operations occurring within a fraction of a millisecond during a single Simulation "Tick". It highlights the authoritative dynamic between the Macro Commander and the Tactical Agent.

```mermaid
sequenceDiagram
    participant Main as SimulationController
    participant Cmdr as StrategicCommander (Macro)
    participant Model as ActionModel (Micro Engine)
    participant Unit as Tactical Agent (Physical Entity)
    participant Combat as DirectFireEngine (Math)
    participant QTable as In-Memory Q-Table Storage

    Main->>Cmdr: Prompt: Assign Core Missions (Pre-Tick)
    Cmdr-->>Unit: Issue Authoritative AgentCommand (Axis of Advance)
    
    Main->>Model: Execute Tick (step_all_agents)
    loop Every Active Unit in Registry
        Model->>Unit: Evaluate Action Economy (Available Tokens & Suppression)
        alt Pinned Status (Overwhelming Suppression)
            Unit-->>Model: Surrender Turn (0 Tokens Available)
        else Normal or Suppressed Status
            Model->>Model: SENSE: Raycast for hostile targets within Vision Hexes
            Model->>Model: FILTER: Restrict tactical options strictly to Commander's Axis OR Fire Actions
            Model->>QTable: DECIDE: Query Local Q-Table for Optimal Action
            QTable-->>Model: Return Chosen Action (e.g., MOVE, FIRE)
            
            alt Action == FIRE
                Model->>Combat: Request probability & lethality calculation
                Combat-->>Model: Apply Poisson-derived Casualties & Suppression damage
            else Action == MOVE
                Model-->>Unit: Update Internal Hex Coordinates
            end
            
            Model->>QTable: LEARN: Upload Reward modifier based on combat efficacy or mission progression
        end
    end
    Main->>Main: Conclude Tick & Update Global Episode Iterator
```

---

## 3. Core Class UML & Entity Relationships
This diagram represents the foundational Python Object relationships orchestrating the physical map geometry, static JSON configurations, and the live, active combat units deployed during a session.

```mermaid
classDiagram
    class Hex {
        +int q
        +int r
        +int s
        +tuple() coordinates
    }

    class Map {
        -dict _hexes
        -dict _entities
        +get_terrain(Hex)
        +get_entities_at(Hex)
        +move_entity(id, src, dst)
        +detect_sections()
    }

    class BaseEntity {
        +str id
        +str name
        +dict attributes
        +list components
        +get_attribute(key)
        +set_attribute(key, val)
    }

    class Agent {
        +AgentCommand current_command
        +Inventory inventory
        +__repr__()
    }

    class Inventory {
        -list weapons
        -dict resources
        -list equipment
    }

    class DataController {
        +dict agent_types
        +dict weapon_types
        +reload_configs()
        +get_weapon_stats(weapon_id)
    }
    
    BaseEntity <|-- Agent : Inherits Default Skeleton
    Map "1" *-- "many" Hex : Composes
    Map "1" o-- "many" Agent : Tracks Physical Location
    Agent "1" *-- "1" Inventory : Possesses
    Agent ..> DataController : References JSON Base Stats
```
