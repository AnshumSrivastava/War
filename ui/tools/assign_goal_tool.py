"""
FILE: ui/tools/assign_goal_tool.py
ROLE: The "Commander" (Mission Assignment Tool).

DESCRIPTION:
This tool allows you to give direct orders to units on the map.
1. First, you click on a unit (Agent) to select them.
2. Then, you choose an action from the menu (like "MOVE" or "FIRE").
3. Finally, you click on a target hexagon to assign that goal.

The unit's AI will then process this order during the next simulation turn.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QGroupBox, QFrame
from PyQt5.QtGui import QPen, QColor, QBrush
from engine.simulation.command import AgentCommand
from engine.core.hex_math import HexMath

class AssignGoalTool(MapTool):
    """
    Handles the user interaction for assigning tactical goals to individual entities.
    """
    def __init__(self, widget):
        super().__init__(widget)
        self.selected_entity_id = None # Keeps track of which soldier you have currently clicked.
        self.lbl_selected = None
        self.combo_type = None
        self._active = False

    def activate(self):
        self._active = True
        super().activate()

    def deactivate(self):
        self._active = False
        super().deactivate()

    def get_options_widget(self):
        """
        COMMAND CONSOLE: Builds the UI in the sidebar where you pick 
        the order type.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Header
        header = QLabel("<b>COMBAT ORDERS</b>")
        header.setStyleSheet(f"color: {Theme.ACCENT_ALLY}; font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # --- Selected Agent Display ---
        self.lbl_selected = QLabel("Selected Agent: <b>None</b>")
        self.lbl_selected.setStyleSheet(f"background-color: {Theme.BG_INPUT}; padding: 8px; border: 1px solid {Theme.BORDER_STRONG}; border-radius: 4px;")
        layout.addWidget(self.lbl_selected)
        
        # --- Command Type Selection ---
        group = QGroupBox("Order Configuration")
        v_layout = QVBoxLayout()
        v_layout.setSpacing(8)
        
        v_layout.addWidget(QLabel("Primary Action:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["MOVE", "DEFEND", "FIRE", "CAPTURE", "HOLD / END TURN"])
        
        current_cmd = getattr(self.state, "goal_opt_type", "MOVE")
        self.combo_type.setCurrentText(current_cmd)
        self.combo_type.currentTextChanged.connect(
            lambda t: setattr(self.state, 'goal_opt_type', t)
        )
        
        v_layout.addWidget(self.combo_type)
        
        # Instructions Label
        instr = QLabel("<i>1. Click Agent to select them<br>2. Pick action above<br>3. Click Hex to assign destination</i>")
        instr.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        v_layout.addWidget(instr)
        
        group.setLayout(v_layout)
        layout.addWidget(group)
        
        # Spacer at bottom
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def mousePressEvent(self, event):
        """Handles selecting units and assigning targets."""
        if event.button() == Qt.LeftButton:
            # Convert the mouse click into map coordinates.
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            entities_at_hex = self.state.map.get_entities_at(click_hex)
            
            # 1. SELECTING: If you clicked on a hex with a unit, pick that unit.
            if entities_at_hex:
                for eid in entities_at_hex:
                    ent = self.state.entity_manager.get_entity(eid)
                    if ent: 
                        self.selected_entity_id = eid
                        # Update the sidebar text to show the unit's name.
                        if self.lbl_selected:
                            try:
                                self.lbl_selected.setText(f"Selected: <b>{ent.name}</b>")
                            except RuntimeError:
                                pass
                        self.log(f"Selected Entity: {ent.name}")
                        self.widget.update()
                        return
            
            # 2. ASSIGNING: If you have a unit already selected, assign the goal to 
            # the hexagon you just clicked.
            if self.selected_entity_id:
                ent = self.state.entity_manager.get_entity(self.selected_entity_id)
                if not ent:
                    # If the unit is gone (e.g. destroyed), clear selection.
                    self.selected_entity_id = None
                    try:
                        if self.lbl_selected:
                            self.lbl_selected.setText("Selected: <b>None</b>")
                    except RuntimeError:
                        pass
                    return
                
                # Fetch whichever command type (MOVE, FIRE, etc.) is currently in the sidebar.
                try:
                    cmd_type = self.combo_type.currentText()
                except (RuntimeError, AttributeError):
                    cmd_type = getattr(self.state, "goal_opt_type", "MOVE")
                
                # STAMP THE ORDER: Physically attach the command to the unit's memory.
                ent.current_command = AgentCommand(
                    command_type=cmd_type, 
                    target_hex=click_hex, 
                    is_user_assigned=True # Flags that a HUMAN gave this order, not the AI.
                )
                
                self.log(f"Assigned Goal '{cmd_type}' to {ent.name} at {click_hex.q},{click_hex.r}")
                
                # Redraw the screen to show any visual command indicators.
                self.widget.update()
                
    def draw_preview(self, painter):
        """VISUAL FEEDBACK: Draws a dashed selection ring around the unit."""
        if not self.selected_entity_id:
            return
            
        ent = self.state.entity_manager.get_entity(self.selected_entity_id)
        if not ent:
            return
            
        # Find where the unit is currently standing.
        hex_obj = self.state.map.get_entity_position(self.selected_entity_id)
        if not hex_obj:
            return
            
        # Convert map hex to screen pixels.
        wx, wy = HexMath.hex_to_pixel(hex_obj, self.widget.hex_size)
        sx = wx - self.widget.camera_x + self.widget.width() / 2
        sy = wy - self.widget.camera_y + self.widget.height() / 2
        
        # Draw a bright Yellow dashed ring.
        pen = QPen(QColor(255, 255, 0, 200), 3, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        radius = self.widget.hex_size * 0.7
        painter.drawEllipse(QPointF(sx, sy), radius, radius)
