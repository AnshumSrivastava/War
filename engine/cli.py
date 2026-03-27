"""
FILE:    engine/cli.py
LAYER:   Backend
ROLE:    Headless terminal entry point for the war game engine.

DESCRIPTION:
    Allows the engine to run completely without a GUI.
    Use this for:
    - Batch AI training sessions
    - Scenario validation
    - Automated testing / CI pipelines
    - Debugging engine state from a terminal

    USAGE:
        python -m engine.cli run --scenario <name> --episodes <N>
        python -m engine.cli state --map <file>
        python -m engine.cli validate --file <scenario_file>

    DOES NOT IMPORT FROM:
    - PyQt5 / Flask (no GUI dependency)
    - ui/ or web_ui/
    - services/ (CLI talks to engine directly, no middleware needed)
"""

import argparse
import json
import sys
from pathlib import Path

from engine.state.world_state import WorldState


# =============================================================================
# CLI COMMANDS
# =============================================================================

def cmd_run(args):
    """
    Run N training episodes headlessly and print progress to stdout.

    Args:
        args: Parsed argparse namespace with .scenario, .episodes, .steps.
    """
    print(f"[cli] Initializing world state...")
    state = WorldState.create()

    # Try to load the requested scenario
    scenario_name = args.scenario
    scenario_path = _find_scenario(state, scenario_name)
    if scenario_path is None:
        print(f"[cli] ERROR: Scenario '{scenario_name}' not found in content/Projects/.")
        sys.exit(1)

    print(f"[cli] Loading scenario: {scenario_path}")
    _load_scenario(state, scenario_path)

    from engine.simulation.act_model import ActionModel
    model = ActionModel(state)

    total_episodes = args.episodes
    max_steps = args.steps

    print(f"[cli] Starting {total_episodes} episodes x {max_steps} steps each.")
    state.is_learning = True

    for ep in range(1, total_episodes + 1):
        model.reset_episode()
        for step in range(1, max_steps + 1):
            events, logs = model.step_all_agents(
                step_number=step,
                table_mode=False,
                episode_number=ep,
                max_steps=max_steps
            )
        # Progress report every 10 episodes
        if ep % 10 == 0 or ep == total_episodes:
            eps = model.q_manager_ephemeral.epsilon
            print(f"[cli] Episode {ep:>4}/{total_episodes}  epsilon={eps:.4f}")

    state.is_learning = False
    model.save_knowledge()
    print(f"[cli] Training complete. Knowledge saved.")


def cmd_state(args):
    """Print the current world state as JSON to stdout."""
    state = WorldState.create()
    map_file = args.map
    if map_file:
        _load_map(state, map_file)

    entities = state.entity_manager.get_all_entities()
    output = {
        "map": {
            "width":  state.map.width,
            "height": state.map.height,
            "hex_count": len(state.map._hexes) if hasattr(state.map, '_hexes') else 0,
        },
        "entities": [
            {
                "id":   e.id,
                "name": e.name,
                "side": e.get_attribute("side", "?"),
                "type": e.get_attribute("type", "?"),
                "personnel": e.get_attribute("personnel", 0),
                "pos":  str(state.map.get_entity_position(e.id)),
            }
            for e in entities
        ]
    }
    print(json.dumps(output, indent=2))


def cmd_validate(args):
    """Validate a scenario file and report any issues."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[cli] ERROR: File not found: {file_path}")
        sys.exit(1)

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[cli] ERROR: Invalid JSON in {file_path}: {e}")
        sys.exit(1)

    issues = []
    if "sides" not in data:
        issues.append("Missing 'sides' key")
    if "rules" not in data:
        issues.append("Missing 'rules' key (will use defaults)")

    if issues:
        print(f"[cli] WARNINGS in {file_path.name}:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"[cli] OK: {file_path.name} looks valid.")


# =============================================================================
# HELPERS
# =============================================================================

def _find_scenario(state: WorldState, name: str):
    """Search content/Projects/ for a scenario matching `name`."""
    from engine.data.content_path import get_content_root
    projects_dir = Path(get_content_root()) / "Projects"
    # Try exact name, then with .json extension
    for candidate in [name, f"{name}.json"]:
        p = projects_dir / candidate
        if p.exists():
            return str(p)
    return None


def _load_scenario(state: WorldState, path: str):
    """Load a scenario JSON file into state (minimal, headless version)."""
    with open(path) as f:
        data = json.load(f)
    # Basic: just record the name; full loading handled by scenario_service
    state.current_project = data.get("name", Path(path).stem)


def _load_map(state: WorldState, map_file: str):
    """Load a map file into state.map (stub for now)."""
    # Actual loading delegated to map loader once services are fully wired
    state.current_map = map_file


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="python -m engine.cli",
        description="War Game Engine — Headless CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `run` command
    run_p = subparsers.add_parser("run", help="Run training episodes")
    run_p.add_argument("--scenario", required=True, help="Scenario name or path")
    run_p.add_argument("--episodes", type=int, default=100, help="Number of episodes")
    run_p.add_argument("--steps",    type=int, default=50,  help="Steps per episode")

    # `state` command
    state_p = subparsers.add_parser("state", help="Print current world state as JSON")
    state_p.add_argument("--map", default=None, help="Map file to load")

    # `validate` command
    val_p = subparsers.add_parser("validate", help="Validate a scenario file")
    val_p.add_argument("--file", required=True, help="Path to scenario JSON")

    args = parser.parse_args()

    commands = {
        "run":      cmd_run,
        "state":    cmd_state,
        "validate": cmd_validate,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
