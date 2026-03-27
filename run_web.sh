#!/usr/bin/env bash

# ======================================================================
# Wargame Engine - Web UI Launcher
# ======================================================================

echo "Starting Wargame Web UI..."

# Get the directory of this script (project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Auto-enter Nix shell if not already inside one
if [ -z "$IN_NIX_SHELL" ]; then
    echo "Entering Nix shell to retrieve Flask dependency..."
    exec nix-shell "$PROJECT_ROOT/infra/shell_light.nix" --run "$PROJECT_ROOT/run_web.sh"
    exit 0
fi

# Launch the Web UI backend
echo "Launching Flask backend server..."
echo "The interface will be available at http://localhost:8080"
echo "Press Ctrl+C to stop."

cd "$PROJECT_ROOT/web_ui"
python3 app.py
