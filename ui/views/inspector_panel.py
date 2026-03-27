"""
FILE: ui/views/inspector_panel.py
ROLE: The "Magnifying Glass" (Inspector Panel).

DESCRIPTION:
This panel is located on the right side of the screen. Its job is to show you 
the specific details of whatever you have clicked on (a hex or a unit).

It allows you to:
1. See the terrain type of a hex.
2. Change the properties of a unit (like its name or personnel).
3. Manage the different "Layers" of the map (Visual units vs Logic zones).
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QFormLayout, QDockWidget
from PyQt5.QtCore import Qt

class InspectorPanel(QWidget):
    """
    The panel that displays details for selected map elements.
    """
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.main_window = parent
        self.state = state
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignTop)
        
        # --- TOOL OPTIONS GROUP ---
        # This part changes depending on which tool you have selected (Paint, Place, etc.).
        self.tool_opts_group = QFrame()
        self.tool_opts_group.setObjectName("InspectorGroup")
        self.tool_opts_group.setFrameShape(QFrame.StyledPanel)
        self.tool_opts_layout = QFormLayout(self.tool_opts_group)
        layout.addWidget(self.tool_opts_group)
        self.tool_opts_group.hide() 
        
        # --- LAYER MANAGER ---
        # A tree view that shows all the 'Things' (Units, Zones, Paths) on the map.
        from ui.components.layer_manager_widget import LayerManagerWidget
        self.layer_manager = LayerManagerWidget(self.main_window)
        layout.addWidget(self.layer_manager)

    def update_selection(self, hex_obj):
        """Called when a hex is clicked; tells the LayerManager to highlight it."""
        if hasattr(self, 'layer_manager'):
            self.layer_manager.select_by_hex(hex_obj)
