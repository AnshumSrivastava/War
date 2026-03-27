#!/usr/bin/env bash
# Wrapper to run the application inside the Nix shell environment
# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"
# Check if xvfb-run is needed (e.g., if DISPLAY is not set and we are on Linux)
if [[ -z "$DISPLAY" && "$OSTYPE" == "linux-gnu"* ]]; then
    echo "No DISPLAY detected, using xvfb-run..."
    RUN_CMD="xvfb-run python3 -u main.py"
else
    RUN_CMD="python3 -u main.py"
fi

nix-shell "$PROJECT_ROOT/infra/shell_ultralight.nix" --run "$RUN_CMD"
