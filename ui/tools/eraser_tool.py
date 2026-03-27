"""
FILE: ui/tools/eraser_tool.py
ROLE: The "Bulldozer" (Cleanup Tool).

DESCRIPTION:
This tool is used to clear land and remove objects from the map.
When you click a hexagon with this tool, it wipes out any special terrain, 
buildings, or obstacles, resetting that spot to a plain, empty field.

It also records what was removed so you can 'Undo' the deletion if you 
make a mistake.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt

class EraserTool(MapTool):
    """
    Handles removing data from hexagons on the map.
    DELEGATES TO: Presentation Layer ToolController.
    """
    def mousePressEvent(self, event):
        """Called when you click on the map while the Eraser is active."""
        if event.button() == Qt.LeftButton:
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            
            # --- DISPATCH TO PURE LOGIC ---
            # We no longer do any engine math or undo stack manipulation here.
            mw = self.widget.window()
            if hasattr(mw, 'core_tool_controller'):
                # Ensure the controller knows we are the active tool
                mw.core_tool_controller.set_tool("eraser")
                mw.core_tool_controller.handle_click(click_hex.q, click_hex.r, "left")
            
            # Formally requested UI update
            self.widget.refresh_map()

