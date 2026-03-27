"""
conftest.py — Pytest configuration for the war game test suite.

Applies a global PyQt5 mock BEFORE any test file is collected,
so engine modules that import PyQt at the top level (e.g. simulation_controller)
can be imported safely without a display server.

Every test file in this directory gets this mock automatically.
No per-file mock boilerplate needed.
"""
import sys
from unittest.mock import MagicMock
import os

# --- PyQt5 mock so engine imports don't blow up without a display ---
_mock_qt = MagicMock()
for _mod in [
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtWidgets",
    "PyQt5.QtGui",
    "PyQt5.QtWebEngine",
    "PyQt5.QtWebEngineWidgets",
]:
    sys.modules.setdefault(_mod, _mock_qt)

# --- Ensure the project root is on the path ---
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
