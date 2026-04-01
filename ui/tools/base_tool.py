"""
FILE: ui/tools/base_tool.py
ROLE: The "Blueprint" for all map tools.

DESCRIPTION:
This file defines the base class for every tool you use on the map (like the 
Paintbrush, the Eraser, or the Unit Placer). It acts as a standard set of 
instructions so every tool knows how to talk to the map.

Think of this as the "Generic Tool Handle" that all specific tools attach to.
"""

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtGui import QMouseEvent, QPainter, QCursor
import logging

log = logging.getLogger(__name__)

class MapTool(QObject):
    """
    ABSTRACTION: The template for any tool that interacts with the Hex Map.
    Provides lifecycle methods (activate/deactivate) and mouse event placeholders.
    """
    def __init__(self, widget):
        """
        Initializes the tool and links it to the map widget.
        """
        super().__init__(widget)
        # Reference to the HexWidget (the map canvas) this tool is currently being used on.
        self.widget = widget
        # Reference to the GlobalState (the application's shared notebook).
        self.state = widget.state

    def mousePressEvent(self, event: QMouseEvent):
        """Called the moment you click a mouse button on the map."""
        pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Called when you let go of the mouse button."""
        pass

    def mouseMoveEvent(self, event: QMouseEvent):
        """Called constantly as you move the mouse across the map."""
        pass

    def draw_preview(self, painter: QPainter):
        """
        GHOST DRAWING: Override this to show a 'preview' of what the tool will do 
        (like showing a translucent hex where you're about to paint).
        """
        pass

    def get_options_widget(self, parent=None):
        """
        ABSTRACTION: Returns a QWidget containing the tool's settings.
        If parent is provided, the widget will be linked to it to prevent popups.
        """
        return None

    def activate(self):
        """Called when you select this tool from the toolbar."""
        pass

    def deactivate(self):
        """Called when you switch away from this tool to another one."""
        pass
    
    def commit(self):
        """
        FINALIZE: Called to finish an operation, like when you press Enter 
        or Right-Click to complete a path.
        """
        pass

    def get_cursor(self) -> Qt.CursorShape:
        """
        Override this to specify a custom cursor for the tool.
        Returns the cursor shape to be used when this tool is active.
        """
        return Qt.ArrowCursor

    def log(self, message):
        """
        MESSENGER: A helper function that sends a message to the application's
        information log at the bottom of the screen.
        """
        mw = self.widget.window() # Get the main application window.
        if hasattr(mw, 'log_info'):
            mw.log_info(message) # Send the message to the log.
        else:
            log.info(message) # Use standard logging instead of print.

