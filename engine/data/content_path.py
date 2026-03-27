"""
FILE:    engine/data/content_path.py
LAYER:   Backend → Data
ROLE:    Single resolver for the content/ root directory path.

DESCRIPTION:
    This is the ONLY place in the entire codebase that resolves the path
    to the `content/` directory. All data loaders, managers, and the CLI
    must call `get_content_root()` here instead of computing the path
    themselves via `os.path.dirname(os.path.dirname(...))` chains.

    Why this matters:
    - One place to change if the content directory ever moves.
    - Works correctly whether the app is run from the project root,
      a sub-directory, or packaged as a binary.
    - Testable: tests can call `set_content_root_override()` to point
      at a fixture directory without modifying any other file.

DOES NOT IMPORT FROM:
    - Any UI code
    - services/
    - engine.state
"""

import os
from pathlib import Path
from typing import Optional

# Internal override — set by tests or alternate frontends if needed.
_content_root_override: Optional[str] = None


def get_content_root() -> str:
    """
    Returns the absolute path to the content/ directory.

    Resolution order:
    1. Manual override (set via set_content_root_override) — used in tests.
    2. Environment variable WAR_CONTENT_ROOT — used for packaging/deployment.
    3. Default: two directories above this file (project root / content/).

    Returns:
        Absolute path string to the content/ directory.

    Raises:
        FileNotFoundError: If the resolved path does not exist on disk.
    """
    if _content_root_override is not None:
        return _content_root_override

    env_path = os.environ.get("WAR_CONTENT_ROOT")
    if env_path:
        return env_path

    # Default: this file is at engine/data/content_path.py
    # so the project root is two levels up.
    this_file = Path(__file__).resolve()
    project_root = this_file.parent.parent.parent   # engine/data/ -> engine/ -> project root
    content_path = project_root / "content"

    if not content_path.exists():
        raise FileNotFoundError(
            f"content/ directory not found at {content_path}. "
            "Set the WAR_CONTENT_ROOT environment variable to override."
        )

    return str(content_path)


def set_content_root_override(path: Optional[str]) -> None:
    """
    Override the content root path. Intended for tests and alternate deployments.

    Args:
        path: Absolute path to use as content root, or None to clear the override.
    """
    global _content_root_override
    _content_root_override = path
