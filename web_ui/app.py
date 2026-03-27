"""
FILE:    web_ui/app.py
LAYER:   Frontend (Web)
ROLE:    Flask web interface for the war game engine.

DESCRIPTION:
    A lightweight HTTP API that exposes engine state and actions via REST.
    This is one of potentially many frontends (the desktop PyQt app is another).

    The web UI uses the same services/ layer as the desktop UI.
    It does NOT maintain its own in-memory state — all state lives in
    the engine and is accessed through services/.

    To run:
        python web_ui/app.py
        Then open http://localhost:8080 in a browser.

    DOES NOT IMPORT FROM:
    - engine/ directly
    - ui/ (desktop PyQt code)
    - PyQt5
"""

import sys
import os

from flask import Flask, render_template, jsonify, request

# ---------------------------------------------------------------------------
# BOOTSTRAP: Initialize the WorldState and wire all services.
# This is done once at startup, just like in main.py.
# ---------------------------------------------------------------------------
from engine.state.world_state import WorldState
import services.map_service        as map_svc
import services.entity_service     as entity_svc
import services.simulation_service as sim_svc
import services.scenario_service   as scenario_svc
import services.rules_service      as rules_svc
import services.data_service       as data_svc
import services.zone_service       as zone_svc
import services.path_service       as path_svc

_state = WorldState.create()

map_svc.init(_state)
entity_svc.init(_state)
sim_svc.init(_state)
scenario_svc.init(_state)
rules_svc.init(_state)
data_svc.init(_state)
zone_svc.init(_state)
path_svc.init(_state)

# ---------------------------------------------------------------------------
# FLASK APP
# ---------------------------------------------------------------------------
app = Flask(__name__)


# =============================================================================
# PAGES
# =============================================================================

@app.route("/")
def index():
    """Serve the main web UI page."""
    return render_template("index.html")


# =============================================================================
# MAP API
# =============================================================================

@app.route("/api/map")
def get_map():
    """Return basic map info."""
    result = map_svc.get_map_info()
    if result.ok:
        return jsonify(result.data)
    return jsonify({"error": result.error}), 500


@app.route("/api/map/hex/<int:q>/<int:r>")
def get_hex(q, r):
    """Return terrain data for a specific hex."""
    result = map_svc.get_hex(q, r)
    if result.ok:
        return jsonify(result.data)
    return jsonify({"error": result.error, "code": result.code}), 404


@app.route("/api/map/zones")
def get_zones():
    """Return all zone definitions."""
    result = map_svc.get_zones()
    if result.ok:
        return jsonify(result.data)
    return jsonify({"error": result.error}), 500


# =============================================================================
# ENTITY API
# =============================================================================

@app.route("/api/entities")
def get_entities():
    """Return all entities currently on the map."""
    result = entity_svc.get_all_entities()
    if not result.ok:
        return jsonify({"error": result.error}), 500
    entities = result.data or []
    out = []
    for e in entities:
        pos_result = entity_svc.get_entity_position(e.id)
        pos = pos_result.data if pos_result.ok else {"q": 0, "r": 0}
        out.append({
            "id":        e.id,
            "name":      e.name,
            "side":      e.get_attribute("side", "?"),
            "type":      e.get_attribute("type", "?"),
            "personnel": e.get_attribute("personnel", 0),
            "q":         pos.get("q"),
            "r":         pos.get("r"),
        })
    return jsonify(out)


@app.route("/api/entities", methods=["POST"])
def place_entity():
    """Place a new agent on the map."""
    data = request.get_json() or {}
    q         = data.get("q")
    r         = data.get("r")
    side      = data.get("side", "Attacker")
    unit_type = data.get("type", "Infantry")
    name      = data.get("name")

    if q is None or r is None:
        return jsonify({"error": "q and r coordinates are required."}), 400

    result = entity_svc.place_entity(q=q, r=r, side=side, unit_type=unit_type, name=name)
    if result.ok:
        return jsonify(result.data), 201
    return jsonify({"error": result.error}), 400


@app.route("/api/entities/<entity_id>", methods=["DELETE"])
def remove_entity(entity_id):
    """Remove an entity from the map."""
    result = entity_svc.remove_entity(entity_id)
    if result.ok:
        return jsonify({"status": "removed", "id": entity_id})
    return jsonify({"error": result.error}), 404


# =============================================================================
# SIMULATION API
# =============================================================================

@app.route("/api/simulation/step", methods=["POST"])
def simulation_step():
    """Advance the simulation by one tick."""
    data = request.get_json() or {}
    step_number    = data.get("step_number", 1)
    episode_number = data.get("episode_number", 1)
    max_steps      = data.get("max_steps", 50)
    result = sim_svc.step(step_number, episode_number, max_steps)
    if result.ok:
        check = rules_svc.check_terminal_conditions(step_number, max_steps)
        response = {"tick": result.data}
        if check.ok and check.data:
            response["game_over"] = check.data
        return jsonify(response)
    return jsonify({"error": result.error}), 500


@app.route("/api/simulation/reset", methods=["POST"])
def simulation_reset():
    """Reset the simulation state for a new episode."""
    rules_svc.reset()
    result = sim_svc.reset()
    if result.ok:
        return jsonify({"status": "reset"})
    return jsonify({"error": result.error}), 500


# =============================================================================
# SCENARIO API
# =============================================================================

@app.route("/api/scenarios")
def list_scenarios():
    """List all available scenarios."""
    result = scenario_svc.list_scenarios()
    if result.ok:
        return jsonify(result.data)
    return jsonify({"error": result.error}), 500


@app.route("/api/scenarios/load", methods=["POST"])
def load_scenario():
    """Load a scenario by file path."""
    data = request.get_json() or {}
    path = data.get("path")
    if not path:
        return jsonify({"error": "path is required."}), 400
    result = scenario_svc.load_scenario(path)
    if result.ok:
        return jsonify(result.data)
    return jsonify({"error": result.error, "code": result.code}), 400


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
