"""
FILE: ui/core/shortcut_registry.py
ROLE: The "Keyboard Manager".

DESCRIPTION:
This registry centralizes all application shortcuts, making them easier 
to manage, rebind, and document (e.g., for a Hotkeys Help Dialog).
"""
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QObject

class ShortcutRegistry(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.shortcuts = {}
        
    def register(self, key_sequence, description, callback, context=None):
        """Registers a new shortcut and binds it to a callback."""
        shortcut = QShortcut(QKeySequence(key_sequence), self.mw)
        shortcut.activated.connect(callback)
        
        self.shortcuts[key_sequence] = {
            "description": description,
            "callback": callback,
            "context": context,
            "shortcut_obj": shortcut
        }
        return shortcut

    def setup_default_shortcuts(self):
        """Binds all standard application hotkeys."""
        # --- Mode Switching ---
        self.register("Ctrl+1", "Switch to Maps Gallery", lambda: self.mw.mode_tabs.setCurrentIndex(0), "Navigation")
        self.register("Ctrl+2", "Switch to Terrain Editor", lambda: self.mw.mode_tabs.setCurrentIndex(1), "Navigation")
        self.register("Ctrl+3", "Switch to Scenario Editor", lambda: self.mw.mode_tabs.setCurrentIndex(2), "Navigation")
        self.register("Ctrl+4", "Switch to Play Mode", lambda: self.mw.mode_tabs.setCurrentIndex(3), "Navigation")
        self.register("Ctrl+5", "Switch to Database", lambda: self.mw.mode_tabs.setCurrentIndex(4), "Navigation")
        
        # --- Tool Selection ---
        self.register("V", "Select Tool", lambda: self.mw.set_tool("cursor"), "Tools")
        self.register("E", "Edit Tool", lambda: self.mw.set_tool("edit"), "Tools")
        self.register("X", "Eraser Tool", lambda: self.mw.set_tool("eraser"), "Tools")
        self.register("A", "Place Agent Tool", lambda: self.mw.set_tool("place_agent"), "Tools")
        self.register("Z", "Draw Zone Tool", lambda: self.mw.set_tool("draw_zone"), "Tools")
        self.register("B", "Paint Tool", lambda: self.mw.set_tool("paint_tool"), "Tools")
        self.register("P", "Draw Path Tool", lambda: self.mw.set_tool("draw_path"), "Tools")
        self.register("G", "Assign Goal Tool", lambda: self.mw.set_tool("assign_goal"), "Tools")
        
        # --- Simulation Control ---
        self.register("F5", "Execute Mission", self.mw.start_simulation_loop, "Simulation")
        self.register("F6", "Pause Simulation", self.mw.pause_simulation, "Simulation")
        self.register("F10", "Step Simulation", self.mw.advance_simulation, "Simulation")
        
        # --- File Operations ---
        self.register("Ctrl+S", "Save Project", self.mw.action_save_project, "File")
        self.register("Ctrl+Shift+N", "New Project", self.mw.action_new_project, "File")
        self.register("Ctrl+Shift+O", "Open Project", self.mw.action_load_project, "File")
        self.register("Ctrl+Q", "Exit Application", self.mw.close, "File")
        self.register("Ctrl+R", "Restart Application", self.mw.restart_app, "File")
        
        # --- Window Control ---
        self.register("F11", "Toggle Fullscreen", self.toggle_fullscreen, "View")
        
    def toggle_fullscreen(self):
        if self.mw.isFullScreen():
            self.mw.showNormal()
        else:
            self.mw.showFullScreen()
            
    def get_shortcuts_by_context(self):
        """Returns shortcuts grouped by context for UI display."""
        grouped = {}
        for key, data in self.shortcuts.items():
            ctx = data["context"] or "General"
            if ctx not in grouped: grouped[ctx] = []
            grouped[ctx].append((key, data["description"]))
        return grouped
