"""
FILE: ui/core/ui_settings_persistence.py
LAYER: Frontend
ROLE: Save and restore dock panel layout between sessions.

DESCRIPTION:
    Uses QSettings to persist the QMainWindow geometry and dock/toolbar
    state between application runs.  Call save() in closeEvent and
    restore() at the end of _init_ui().

DOES NOT IMPORT FROM:
    - engine/ (anything)
    - services/
"""

from PyQt5.QtCore import QSettings


class UISettingsPersistence:
    """
    Saves and restores QMainWindow layout to/from the OS settings store.
    Usage:
        # At end of _init_ui():
        UISettingsPersistence.restore(self)

        # In closeEvent():
        UISettingsPersistence.save(self)
    """

    _ORG  = "WarGame"
    _APP  = "MainWindow"

    @classmethod
    def save(cls, main_window) -> None:
        """Persist current window geometry and dock/toolbar state."""
        try:
            settings = QSettings(cls._ORG, cls._APP)
            settings.setValue("geometry",    main_window.saveGeometry())
            settings.setValue("windowState", main_window.saveState())
            # Save theme preference
            theme_mode = getattr(main_window.state, "theme_mode", "dark")
            settings.setValue("themeMode", theme_mode)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Could not save window state: %s", exc)

    @classmethod
    def restore(cls, main_window) -> None:
        """Restore previously saved geometry and dock/toolbar state."""
        try:
            settings = QSettings(cls._ORG, cls._APP)
            geometry = settings.value("geometry")
            state    = settings.value("windowState")
            if geometry:
                main_window.restoreGeometry(geometry)
            if state:
                main_window.restoreState(state)
            # Restore theme preference
            theme_mode = settings.value("themeMode", "dark")
            if hasattr(main_window.state, "theme_mode"):
                main_window.state.theme_mode = theme_mode
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Could not restore window state: %s", exc)
