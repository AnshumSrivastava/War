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
        """
        PERSISTENCE: Saves the current window layout, position, and user 
        preferences (like Theme) to the operating system's settings store.
        
        On Windows: This goes into the Registry.
        On Linux: This goes into a .conf file in ~/.config/
        On macOS: This goes into a .plist file.
        """
        try:
            # Initialize settings with unique Organization and App identifiers
            settings = QSettings(cls._ORG, cls._APP)
            
            # Save the raw binary state of the window (Geometry + Dock Layout)
            settings.setValue("geometry",    main_window.saveGeometry())
            settings.setValue("windowState", main_window.saveState())
            
            # Save visual preferences (Dark vs Light theme)
            theme_mode = getattr(main_window.state, "theme_mode", "dark")
            settings.setValue("themeMode", theme_mode)
            
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Layout persistence failed: %s", exc)

    @classmethod
    def restore(cls, main_window) -> None:
        """
        RECOVERY: Re-applies the window layout and preferences from the 
        last time the application was closed.
        
        This ensures buttons, sidebars, and theme stay where the user left them.
        """
        try:
            settings = QSettings(cls._ORG, cls._APP)
            
            # Fetch the saved binary blobs
            geometry = settings.value("geometry")
            state    = settings.value("windowState")
            
            # Apply them only if they exist (prevents errors on first run)
            if geometry:
                main_window.restoreGeometry(geometry)
            if state:
                main_window.restoreState(state)
                
            # Restore the user's preferred theme color
            theme_mode = settings.value("themeMode", "dark")
            if hasattr(main_window.state, "theme_mode"):
                main_window.state.theme_mode = theme_mode
                
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Layout recovery failed: %s", exc)

