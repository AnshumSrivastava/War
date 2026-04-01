"""
FILE: ui/tools/paint_tool.py
ROLE: The "Paintbrush" (Terrain Editing Tool).

DESCRIPTION:
This tool allows you to "paint" the land. 
1. You pick a terrain type (like Forest or Water).
2. You click and drag across the map.
3. Every hexagon you touch instantly transforms into that type of land.

It is useful for sculpting the environment before starting a simulation.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QPen, QBrush, QPolygonF
from engine.core.hex_math import HexMath

class PaintTool(MapTool):
    """
    A tool used to change the terrain of hexagons on the map.
    """
    def __init__(self, widget):
        """
        Initializes the Paintbrush tool.
        
        Args:
            widget: The HexWidget canvas where painting occurs.
        """
        super().__init__(widget)
        # Activation state: Is the user currently dragging to paint?
        self.painting = False          
        # Tracking: Which hex is the mouse currently hovering over?
        self.current_mouse_hex = None  
        # Brush Size: 1 = single hex, up to 5 = wide area brush.
        self.brush_radius = 1          

    def get_cursor(self):
        """Returns a 'Cross' cursor to indicate precision editing mode."""
        return Qt.CrossCursor
        
    def get_options_widget(self, parent=None):
        """
        THE SETTINGS BOX: Build the small menu that appears in the sidebar
        whenever the Paintbrush is active.  
        """
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QSlider, QHBoxLayout
        from PyQt5.QtCore import Qt as _Qt

        container = QWidget(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- TERRAIN CATEGORY SELECTION ---
        lbl_type = QLabel("CATEGORY")
        lbl_type.setStyleSheet("font-weight: bold; font-size: 9px; color: #a1a1aa;")
        self.combo_terrain = QComboBox()

        # Fetch dynamically from state
        t_types = []
        if hasattr(self.state, 'terrain_controller'):
            t_types = sorted([t.title() for t in self.state.terrain_controller.get_available_terrains()])
        if not t_types:
            t_types = ["Vegetation", "Water", "Mountain"]
        self.combo_terrain.addItems(t_types)

        # Connect UI interactions to state updates
        self.combo_terrain.currentTextChanged.connect(lambda t: setattr(self.state, 'zone_opt_type', t.lower()))

        layout.addWidget(lbl_type)
        layout.addWidget(self.combo_terrain)

        # --- BRUSH RADIUS SLIDER ---
        brush_row = QHBoxLayout()
        lbl_brush = QLabel("BRUSH RADIUS:")
        lbl_brush.setStyleSheet("font-size: 10px;")
        self.brush_size_label = QLabel(f"{self.brush_radius}")
        self.brush_slider = QSlider(_Qt.Horizontal)
        self.brush_slider.setRange(1, 5)
        self.brush_slider.setValue(self.brush_radius)
        self.brush_slider.setPageStep(1)

        def _on_brush_changed(val):
            """Internal handler for real-time brush resizing."""
            self.brush_radius = val
            self.brush_size_label.setText(str(val))
            # Trigging a widget update shows the new preview circle size
            self.widget.update()

        self.brush_slider.valueChanged.connect(_on_brush_changed)

        brush_row.addWidget(lbl_brush)
        brush_row.addWidget(self.brush_slider)
        brush_row.addWidget(self.brush_size_label)
        layout.addLayout(brush_row)

        # Sync initial state
        curr_type = getattr(self.state, 'zone_opt_type', "plain").title()
        if curr_type in [self.combo_terrain.itemText(i) for i in range(self.combo_terrain.count())]:
             self.combo_terrain.setCurrentText(curr_type)

        container.setLayout(layout)
        return container

    # Removed broken hardcoded update_terrain_subtypes

    def mousePressEvent(self, event):
        """Called when you click the left mouse button to start painting."""
        if event.button() == Qt.LeftButton:
            self.painting = True
            
            # Map the screen click to a mathematical hexagon coordinate
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            # Apply the initial 'splat' of paint
            self.apply_paint(click_hex)
            # Redraw to show changes immediately
            self.widget.refresh_map()

    def mouseMoveEvent(self, event):
        """Updates the hover ghost and applies paint if dragging."""
        self.current_mouse_hex = self.widget.screen_to_hex(event.x(), event.y())
        if self.painting:
            # Continue applying 'paint' to every hex the mouse enters while held
            self.apply_paint(self.current_mouse_hex)
        # Redraw to update the cursor preview and terrain visuals
        self.widget.refresh_map()

    def mouseReleaseEvent(self, event):
        """Called when you let go of the mouse button."""
        if event.button() == Qt.LeftButton:
            self.painting = False
            self.widget.refresh_map()

    def apply_paint(self, hex_obj):
        """
        THE ENGINE: Physically changes the Map Data.
        Changes the center hex (hex_obj) and all neighbors within brush_radius.
        """
        if not hex_obj:
            return

        # Fetch current UI settings for paint type
        z_type = getattr(self.state, 'zone_opt_type', "Vegetation")
        # RESOLUTION: Use exact selection from dropdown
        t_type = z_type.lower()
        if hasattr(self.state, 'terrain_controller'):
             avail = self.state.terrain_controller.get_available_terrains()
             if t_type not in avail:
                 t_type = "plain" # Fallback safeguard

        new_data = {"type": t_type}

        # CALCULATE TARGET AREA: Uses a SPIRAL algorithm to find all hexes in the brush circle.
        # radius-1 because spiral(R) includes center + R rings.
        targets = HexMath.spiral(hex_obj, self.brush_radius - 1)
        for target_hex in targets:
            current = self.state.map.get_terrain(target_hex)
            # Only apply change if the terrain is actually different (optimization)
            if not current or current.get("type") != t_type:
                self.state.map.set_terrain(target_hex, new_data)

    def draw_preview(self, painter):
        """
        PREVIEW CURSOR: Draws a translucent circle over the map showing 
        exactly where the paint will land and its currently selected size.
        """
        if not self.current_mouse_hex:
            return

        # Camera offset logic to draw at the correct screen position
        cx = self.widget.width() / 2
        cy = self.widget.height() / 2

        # Get all hexes that would be painted
        targets = HexMath.spiral(self.current_mouse_hex, self.brush_radius - 1)
        
        # Style the ghost highlight (faint white fill with stronger border)
        highlight_color = QColor(255, 255, 255, 40)
        painter.setBrush(QBrush(highlight_color))
        painter.setPen(QPen(QColor(255, 255, 255, 180), 2))

        # Render each hex in the preview area
        for h in targets:
            wx, wy = HexMath.hex_to_pixel(h, self.widget.hex_size)
            sx = wx - self.widget.camera_x + cx
            sy = wy - self.widget.camera_y + cy
            corners = HexMath.get_corners(sx, sy, self.widget.hex_size)
            poly = QPolygonF([QPointF(pt[0], pt[1]) for pt in corners])
            painter.drawPolygon(poly)


