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
        super().__init__(widget)
        self.painting = False          # True while mouse button is held to paint.
        self.current_mouse_hex = None  # Hex currently under the cursor.
        self.brush_radius = 1          # 1 = single hex, up to 5 = wide brush.

    def get_cursor(self):
        return Qt.CrossCursor
        
    def get_options_widget(self):
        """
        THE SETTINGS BOX: Build the small menu that appears in the sidebar
        when this tool is active.  Includes terrain pickers and a brush-size slider.
        """
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QSlider, QHBoxLayout
        from PyQt5.QtCore import Qt as _Qt

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # --- Terrain Selection ---
        lbl_type = QLabel("Terrain Type")
        self.combo_terrain = QComboBox()

        lbl_sub = QLabel("Subtype / ID")
        self.combo_sub = QComboBox()

        t_types = []
        if hasattr(self.state, 'terrain_controller'):
            t_types = self.state.terrain_controller.get_available_terrains()
        if not t_types:
            t_types = ["Vegetation", "Water", "Mountain"]
        self.combo_terrain.addItems(t_types)

        self.combo_terrain.currentTextChanged.connect(self.update_terrain_subtypes)
        self.combo_sub.currentTextChanged.connect(lambda t: setattr(self.state, 'zone_opt_subtype', t))

        layout.addWidget(lbl_type)
        layout.addWidget(self.combo_terrain)
        layout.addWidget(lbl_sub)
        layout.addWidget(self.combo_sub)

        # --- Brush Size ---
        brush_row = QHBoxLayout()
        lbl_brush = QLabel("Brush:")
        self.brush_size_label = QLabel(f"{self.brush_radius}")
        self.brush_slider = QSlider(_Qt.Horizontal)
        self.brush_slider.setRange(1, 5)
        self.brush_slider.setValue(self.brush_radius)
        self.brush_slider.setPageStep(1)

        def _on_brush_changed(val):
            self.brush_radius = val
            self.brush_size_label.setText(str(val))
            self.widget.update()

        self.brush_slider.valueChanged.connect(_on_brush_changed)

        brush_row.addWidget(lbl_brush)
        brush_row.addWidget(self.brush_slider)
        brush_row.addWidget(self.brush_size_label)
        layout.addLayout(brush_row)

        # Initialise state
        self.combo_terrain.setCurrentText(getattr(self.state, 'zone_opt_type', "Vegetation"))
        self.update_terrain_subtypes(self.combo_terrain.currentText())

        widget.setLayout(layout)
        return widget

    def update_terrain_subtypes(self, t_type):
        """Updates the second dropdown menu based on the first one."""
        self.state.zone_opt_type = t_type
        if hasattr(self, 'combo_sub'):
            self.combo_sub.clear()
            # Define specific options for each category.
            subtypes = []
            if t_type == "Vegetation": subtypes = ["Forest", "Scrub", "Orchard"]
            elif t_type == "Water": subtypes = ["River", "Lake", "Stream"]
            elif t_type == "Mountain": subtypes = ["High", "Low", "Pass"]
            else: subtypes = ["Generic"]
            self.combo_sub.addItems(subtypes)

    def mousePressEvent(self, event):
        """Starts the painting process when the mouse is clicked."""
        if event.button() == Qt.LeftButton:
            self.painting = True
            
            # Identify which hexagon was clicked and paint it immediately.
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            self.apply_paint(click_hex)
            self.widget.refresh_map() # Redraw the map to show the new land.

    def mouseMoveEvent(self, event):
        """Continues painting as the mouse moves."""
        self.current_mouse_hex = self.widget.screen_to_hex(event.x(), event.y())
        if self.painting:
            # If the user is holding the button down, paint every hex the mouse touches.
            self.apply_paint(self.current_mouse_hex)
        self.widget.refresh_map() # Redraw for the hover highlight or the new paint.

    def mouseReleaseEvent(self, event):
        """Stops painting when the user lets go of the button."""
        if event.button() == Qt.LeftButton:
            self.painting = False
            self.widget.refresh_map()

    def apply_paint(self, hex_obj):
        """The core logic: changes terrain for hex_obj and all hexes within brush_radius."""
        if not hex_obj:
            return

        z_type = getattr(self.state, 'zone_opt_type', "Vegetation")
        z_sub  = getattr(self.state, 'zone_opt_subtype', "Forest")

        # Resolve terrain type string
        t_type    = "plain"
        candidate = z_sub.lower()
        avail     = []
        if hasattr(self.state, 'terrain_controller'):
            avail = self.state.terrain_controller.get_available_terrains()

        if candidate in avail:
            t_type = candidate
        elif z_type in avail:
            t_type = z_type
        elif z_type.lower() in avail:
            t_type = z_type.lower()
        else:
            if z_type == "Vegetation":
                if "Forest" in z_sub:    t_type = "forest"
                elif "Scrub" in z_sub:   t_type = "scrub"
            elif z_type == "River":      t_type = "water"
            elif z_type == "Mountain":   t_type = "mountain"

        new_data = {"type": t_type}

        # Paint all hexes within brush radius (spiral covers center + N rings)
        targets = HexMath.spiral(hex_obj, self.brush_radius - 1)
        for target_hex in targets:
            current = self.state.map.get_terrain(target_hex)
            if not current or current.get("type") != t_type:
                self.state.map.set_terrain(target_hex, new_data)

    def draw_preview(self, painter):
        """GHOST HIGHLIGHT: Draws brush-radius highlight over hovered hexes."""
        if not self.current_mouse_hex:
            return

        cx = self.widget.width() / 2
        cy = self.widget.height() / 2

        targets = HexMath.spiral(self.current_mouse_hex, self.brush_radius - 1)
        highlight_color = QColor(255, 255, 255, 40)
        painter.setBrush(QBrush(highlight_color))
        painter.setPen(QPen(QColor(255, 255, 255, 180), 2))

        for h in targets:
            wx, wy = HexMath.hex_to_pixel(h, self.widget.hex_size)
            sx = wx - self.widget.camera_x + cx
            sy = wy - self.widget.camera_y + cy
            corners = HexMath.get_corners(sx, sy, self.widget.hex_size)
            poly = QPolygonF([QPointF(pt[0], pt[1]) for pt in corners])
            painter.drawPolygon(poly)

