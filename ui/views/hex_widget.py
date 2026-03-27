"""
FILE: ui/views/hex_widget.py
ROLE: The "Artist" (Map Renderer).

DESCRIPTION:
This is the most complex file in the UI. It is responsible for drawing the 
hexagonal grid, the terrain, the units, and the mission zones on your screen.

Think of this like a digital canvas:
1. It calculates where each hexagon should be drawn (Hex Math).
2. It paints the terrain colors (Green for grass, Blue for water, etc.).
3. It draws the units as circles with colors representing their side.
4. It handles 'Camera' movement (Panning and Zooming) so you can look around the map.
5. It handles 'Tools' like the Pencil (to draw terrain) or the Eraser.

Key Rendering Layers (in order of drawing):
1. Terrain Layer: Base colors and elevation.
2. Overlay Layer: Special features like Rivers or Roads.
3. Zone Layer: Mission zones (Capture points, Obstacles).
4. Unit Layer: The actual agents/units.
"""
from PyQt5.QtWidgets import QWidget, QApplication, QPinchGesture, QToolTip
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRectF, QEvent
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPolygonF, QLinearGradient, QPixmap, QCursor

from engine.core.hex_math import HexMath, Hex
from ui.core.hex_context_menu import HexContextMenu
from engine.state.global_state import GlobalState
from ui.styles.theme import Theme
from ui.core.icon_painter import VectorIconPainter
from ui.tools.selection_tool import SelectionTool
from ui.tools.draw_path_tool import DrawPathTool
from ui.tools.draw_zone_tool import DrawZoneTool
from ui.tools.place_agent_tool import PlaceAgentTool
from ui.tools.eraser_tool import EraserTool
from ui.tools.edit_tool import EditTool
from ui.tools.paint_tool import PaintTool
from ui.tools.assign_goal_tool import AssignGoalTool
from ui.core.arrow_painter import TacticalArrowPainter

class HexWidget(QWidget):
    """
    The main interactive map area. It handles drawing everything and 
    responding to mouse clicks/drags.
    """
    hex_clicked = pyqtSignal(object)  # Signal sent when a user clicks a hexagon

    def __init__(self, parent=None, state=None):
        """THE CONSTRUCTOR: Prepares the digital canvas."""
        super().__init__(parent)
        self.mw = parent
        if state is None:
             from engine.state.global_state import GlobalState
             self.state = GlobalState()
        else:
             self.state = state
        
        # --- CAMERA & VIEW SETTINGS ---
        self.hex_size = 50.0  # The current zoom level (pixel radius of a hexagon).
        self.camera_x = 0.0   # Where the camera is looking (horizontal).
        self.camera_y = 0.0   # Where the camera is looking (vertical).
        
        # --- THEME COLORS ---
        # Default colors for the grid and background.
        self.background_color = QColor(30, 30, 35)
        self.grid_color = QColor(60, 60, 65)
        self.void_color = QColor(20, 20, 25) 
        
        self.show_coords = getattr(state, "show_coords", False) # Show map coordinates
        self.show_threat_map = getattr(state, "show_threat_map", False) # Show AI Danger Zones

        # INTERACTION TRACKING: Keep track of mouse movement.
        self.last_mouse_pos = None # Used for dragging the map.
        self.panning = False        # True if the user is currently 'dragging' the view.
        self.hovered_hex = None    # The hexagon currently under the mouse cursor.
        
        self.setMouseTracking(True) # Tell the window to listen to all mouse moves.
        self.setFocusPolicy(Qt.StrongFocus) # Allow capturing keys like 'Esc' or 'Delete'.
        
        # ENABLE PINCH-TO-ZOOM: For users with trackpads or touchscreens.
        self.grabGesture(Qt.PinchGesture)
        
        # --- TOOLBOX ---
        # Each 'Tool' is a separate class that handles a specific way of interacting with the map.
        self.tools = {
            "cursor": SelectionTool(self),
            "draw_path": DrawPathTool(self),
            "draw_zone": DrawZoneTool(self),
            "place_agent": PlaceAgentTool(self),
            "paint_tool": PaintTool(self),
            "assign_goal": AssignGoalTool(self),
            "eraser": EraserTool(self),
            "edit": EditTool(self)
        }

        self.active_tool = self.tools["cursor"]
        self.update_theme() 

        self.editing_zone_id = None
        self.editing_path_id = None
        
        # --- CACHING (Quick Win #9) ---
        self.terrain_cache = None
        self.cache_valid = False
        
        # --- ANIMATIONS (Phase 6) ---
        from PyQt5.QtCore import QTimer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(33) # 30 FPS for smooth movement
        
        self.agent_anim_state = {} # {agent_id: {"x": float, "y": float, "target_x": float, "target_y": float}}
        self.selection_pulse = 0.0
        self.pulse_dir = 1
        self.agent_movement_queues = {} # {agent_id: [Hex1, Hex2, ...]}
        
        # --- OVERLAYS ---
        self.show_rewards = False
        self.recent_rewards = {} # {agent_id: (reward_val, time_added)}
        
    def clear_animations(self):
        """Purge all simulation-time movement and visual caches."""
        self.agent_anim_state = {}
        self.agent_movement_queues = {}
        self.recent_rewards = {}
        self.update()

    def clear_selection(self):
        """Clears active object selection when switching tools."""
        self.editing_zone_id = None
        self.editing_path_id = None
        if getattr(self.active_tool, 'dragging_vertex_idx', None) is not None:
             self.active_tool.dragging_vertex_idx = None
        self.update()

    def update_animations(self):
        """Advances all unit animations by one frame."""
        # 1. Pulse the selection highlight
        self.selection_pulse += 0.05 * self.pulse_dir
        if self.selection_pulse >= 1.0: self.pulse_dir = -1
        elif self.selection_pulse <= 0.0: self.pulse_dir = 1
        
        # 2. Smoothly move agents towards their actual hex positions
        delta = 1.0 # Instant snap to prevent linear floating over void space
        changed = False
        
        for aid, state in list(self.agent_anim_state.items()):
            # A. Sequential Queue Advance
            queue = self.agent_movement_queues.get(aid, [])
            if queue:
                # If we are very close to current target, pop next hex from queue
                if abs(state["target_x"] - state["x"]) < 2.0 and abs(state["target_y"] - state["y"]) < 2.0:
                    next_hex = queue.pop(0)
                    from engine.core.hex_math import HexMath
                    wx_next, wy_next = HexMath.hex_to_pixel(next_hex, self.hex_size)
                    state["target_x"] = wx_next
                    state["target_y"] = wy_next
                    changed = True

            # B. Move towards target
            diff_x = state["target_x"] - state["x"]
            if abs(diff_x) > 0.1:
                state["x"] += diff_x * delta
                changed = True
            else:
                state["x"] = state["target_x"]
                
            # Move Y
            diff_y = state["target_y"] - state["y"]
            if abs(diff_y) > 0.1:
                state["y"] += diff_y * delta
                changed = True
            else:
                state["y"] = state["target_y"]
        
        # 3. Request a redraw if something is moving or pulsing
        if changed or self.pulse_dir != 0: 
            self.update()

    def enqueue_agent_move(self, agent_id, to_hex):
        """Adds a new destination to the agent's movement pipeline."""
        if agent_id not in self.agent_movement_queues:
            self.agent_movement_queues[agent_id] = []
        self.agent_movement_queues[agent_id].append(to_hex)

    def refresh_map(self):
        """Forces a full re-render of the terrain layer."""
        self.cache_valid = False
        self.update()

    def event(self, event):
        """Standard Qt event handler, used here to catch touch gestures."""
        if event.type() == QEvent.Gesture:
            return self.gesture_event(event)
        return super().event(event)

    def gesture_event(self, event):
        """Handles Pinch-to-Zoom gestures on laptops or tablets."""
        pinch = event.gesture(Qt.PinchGesture)
        if pinch:
            scale = pinch.scaleFactor()
            self.hex_size *= scale
            self.hex_size = max(10, min(200, self.hex_size)) # Clamp zoom range
            self.cache_valid = False # Invalidate cache on zoom change
            self.update() # Redraw the screen
            return True
        return False

    def showEvent(self, event):
        """Automatically centers the map when it first appears on screen."""
        super().showEvent(event)
        self.recenter_view()

    def recenter_view(self):
        """Calculates the center of the map and moves the camera there."""
        if hasattr(self.state, 'map'):
             mid_col = self.state.map.width // 2
             mid_row = self.state.map.height // 2
             
             center_hex = HexMath.offset_to_cube(mid_col, mid_row)
             cx, cy = HexMath.hex_to_pixel(center_hex, self.hex_size)
             
             self.camera_x = cx
             self.camera_y = cy
             self.cache_valid = False # New camera pos
             self.update()
    
    @property
    def current_tool(self):
        """Returns the tool currently being used by the user."""
        return self.active_tool

    def set_tool(self, tool_id):
        """Switches the cursor to a new tool (e.g. from Pointer to Eraser)."""
        new_tool = self.tools.get(tool_id)
        if not new_tool:
            new_tool = self.tools["cursor"]
            
        if self.active_tool != new_tool:
            self.clear_selection()
            self.active_tool.deactivate()
            self.active_tool = new_tool
            self.active_tool.activate()
            self.state.selected_tool = tool_id 
            self.setCursor(self.active_tool.get_cursor())
            
            # If switching to paint tool, we might want to clear cache eventually, 
            # but for now, we'll invalidate on each terrain change.
            self.update()
            
    def keyPressEvent(self, event):
        """Handles keyboard shortcuts (like ESC to reset the tool)."""
        if event.key() == Qt.Key_Escape:
             self.set_tool("cursor")
             mw = self.window()
             if hasattr(mw, 'update_tools_visibility'):
                 mw.update_tools_visibility()
        else:
             super().keyPressEvent(event)

    def update_theme(self):
        """Changes colors when switching between Dark Mode and Light Mode."""
        mode = getattr(self.state, "theme_mode", "dark")
        if mode == "light":
            self.background_color = QColor(240, 240, 240)
            self.grid_color = QColor(180, 180, 180)
            self.text_color = QColor(20, 20, 20)
            self.void_color = QColor(220, 220, 220)
        else:
            self.background_color = QColor(Theme.BG_DEEP)
            self.grid_color = QColor(Theme.BORDER_STRONG)
            self.text_color = QColor(Theme.TEXT_DIM)
            self.void_color = QColor(Theme.BG_DEEP)

    def paintEvent(self, event):
        """
        THE MASTER PAINTING FUNCTION: 
        This is the "Engine Room" for graphics. It is called every time a pixel 
        on the map needs to change (e.g., when you move the camera or a unit steps).
        
        It draws the world in organized LAYERS, like a digital oil painting:
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # Makes lines and circles look smooth.
        
        # --- LAYER 0: THE VOID (Background) ---
        # Fill the entire window with a dark color so there are no "empty" white spots.
        painter.fillRect(self.rect(), self.void_color)
        
        # Calculate the mathematical center of your screen.
        viewport_width = self.width()
        viewport_height = self.height()
        cx = viewport_width / 2
        cy = viewport_height / 2
        
        # --- LAYER 1: THE TERRAIN (The Foundation) ---
        # 1. Check if we need to update the cache
        if not self.cache_valid or not self.terrain_cache or self.terrain_cache.size() != self.size():
            self.render_terrain_cache(cx, cy, viewport_width, viewport_height)
            self.cache_valid = True
            
        # 2. Draw the cached terrain
        painter.drawPixmap(0, 0, self.terrain_cache)
        
        # --- LAYER 1.5: HOVER HIGHLIGHT (Live Overlay) ---
        if self.hovered_hex:
            self.draw_hex_hover(painter, cx, cy)
        
        # --- LAYER 2: THE MAP DETAILS (The Features) ---
        # Draws roads, rivers, and borders on top of the land.
        self.draw_terrain_overlays(painter, cx, cy)
        
        # --- LAYER 2.5: THREAT HEATMAP (The Danger Zones) ---
        if getattr(self, "show_threat_map", False):
            self.draw_threat_heatmap(painter, cx, cy, viewport_width, viewport_height)
        
        # --- LAYER 3: MISSION ELEMENTS (The Scenario) ---
        # These only appear when we are setting up a mission or playing.
        app_mode = getattr(self.state, "app_mode", "terrain")
        if app_mode != "terrain":
            # Draw the semi-transparent "Capture Zones" and "Obstacles".
            self.draw_zone_layer(painter, cx, cy)
            # Draw the units (Agents) as colored circles.
            self.draw_entity_layer(painter, cx, cy, viewport_width, viewport_height)
        
        # --- LAYER 3.5: TRANSIENT EFFECTS (Fire, Move Trails) ---
        if hasattr(self, 'visualizer') and self.visualizer:
            self.visualizer.draw(painter)
            
        # --- LAYER 4: THE CURSOR (The Preview) ---
        # Draw whatever tool you are currently holding (e.g., a "ghost" unit or a path line).
        if self.active_tool:
            self.active_tool.draw_preview(painter)
            
        # --- LAYER 5: DATA OVERLAY (The Librarian) ---
        # Draw things like coordinate numbers (0,0) if you've turned them on.
        if self.show_coords:
            self.draw_debug_coords(painter, cx, cy, viewport_width, viewport_height)

    def render_terrain_cache(self, cx, cy, vw, vh):
        """Pre-renders the terrain layer into a QPixmap."""
        if not self.terrain_cache or self.terrain_cache.size() != self.size():
            self.terrain_cache = QPixmap(self.size())
            
        cache_painter = QPainter(self.terrain_cache)
        cache_painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background
        cache_painter.fillRect(self.rect(), self.background_color)
        
        # Reuse existing draw_hex_layer logic
        self.draw_hex_layer(cache_painter, cx, cy, vw, vh)
        cache_painter.end()

    def draw_hex_layer(self, painter, cx, cy, vw, vh):
        grid_mode = getattr(self.state, "grid_mode", "infinite")
        
        def draw_hex(q, r):
             """Inner helper to draw a single hexagon."""
             hex_obj = Hex(q, r, -q-r)
             
             # Convert the "Hex Coordinate" into "Screen Pixels".
             wx, wy = HexMath.hex_to_pixel(hex_obj, self.hex_size)
             sx = wx - self.camera_x + cx
             sy = wy - self.camera_y + cy
             
             # PERFORMANCE BOOST (Culling):
             # If a hexagon is completely off-screen, we skip drawing it 
             # to keep the app running fast.
             margin = self.hex_size * 2
             if sx < -margin or sx > vw + margin or sy < -margin or sy > vh + margin: return
 
             # 1. SHAPE: Calculate the 6 corners that make the hexagon.
             corners = HexMath.get_corners(sx, sy, self.hex_size - 1)
             poly = QPolygonF([QPointF(x, y) for x, y in corners])
             
             # 2. TERRAIN COLOR: Ask the database what the land looks like here.
             attrs = self.state.terrain_controller.get_hex_full_attributes(hex_obj, self.state.map)
             color_code = attrs.get("color", "#1E1E23") 
             elevation = attrs.get("elevation", 0)
             
             brush_color = QColor(color_code)
             
             # 3. ELEVATION (Depth/Height) & SHADING:
             alpha_val = 40 + (abs(elevation) * 0.1)
             alpha_val = max(30, min(180, int(alpha_val)))
             brush_color.setAlpha(alpha_val)
             
             painter.setBrush(QBrush(brush_color))
             
             # 5. GRID & RELIEF
             pen_color = QColor(Theme.BORDER_STRONG)
             pen_color.setAlpha(100)
             pen = QPen(pen_color)
             pen.setWidthF(0.5)
             painter.setPen(pen)
             painter.drawPolygon(poly)
             
             # Draw a subtle "highlight" on the top-left edges for 3D effect
             if elevation > 0:
                relief_pen = QPen(QColor(255, 255, 255, 40), 2)
                painter.setPen(relief_pen)
                painter.drawLine(QPointF(corners[5][0], corners[5][1]), QPointF(corners[0][0], corners[0][1]))
                painter.drawLine(QPointF(corners[0][0], corners[0][1]), QPointF(corners[1][0], corners[1][1]))
             
             # 6. TERRAIN DECALS (The "Aesthetic" part)
             t_type = attrs.get("type", "plain").lower()
             painter.setOpacity(0.6)
             
             if "forest" in t_type or "wood" in t_type:
                 # Draw small "tree" silhouettes
                 tree_color = QColor(Theme.BG_DEEP).darker(150)
                 painter.setPen(QPen(tree_color, 1))
                 painter.setBrush(QBrush(tree_color))
                 for i in range(3):
                     tx = sx + (i-1) * (self.hex_size * 0.3)
                     ty = sy + (i%2) * (self.hex_size * 0.1)
                     r = self.hex_size * 0.15
                     painter.drawEllipse(QPointF(tx, ty-r), r, r)
                     painter.drawLine(QPointF(tx, ty-r), QPointF(tx, ty+r))
                     
             elif "water" in t_type or "sea" in t_type:
                 # Draw "ripple" lines
                 painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
                 for i in range(2):
                     ry = sy + (i-0.5) * (self.hex_size * 0.4)
                     rw = self.hex_size * 0.4
                     painter.drawLine(QPointF(sx - rw, ry), QPointF(sx + rw, ry))
                     
             elif "urban" in t_type or "city" in t_type or "town" in t_type:
                 # Draw small "building" boxes
                 painter.setPen(QPen(QColor(Theme.BG_DEEP), 1))
                 painter.setBrush(QBrush(QColor(Theme.BG_DEEP)))
                 for i in range(2):
                      bx = sx + (i-0.5) * (self.hex_size * 0.4)
                      by = sy + (i-0.5) * (self.hex_size * 0.2)
                      bw, bh = self.hex_size * 0.25, self.hex_size * 0.3
                      painter.drawRect(QRectF(bx - bw/2, by - bh/2, bw, bh))
                      
             painter.setOpacity(1.0)
             
             # 7. FRONT LINE (Borders)
             if getattr(self.state, 'show_borders', True) and self.state.map.border_path:
                 if tuple(hex_obj) in self.state.map.border_path:
                     bounds = poly.boundingRect()
                     gradient = QLinearGradient(bounds.topLeft(), bounds.topRight())
                     gradient.setColorAt(0.0, QColor(Theme.ACCENT_ENEMY))
                     gradient.setColorAt(1.0, QColor(Theme.ACCENT_ALLY))
                     painter.setBrush(QBrush(gradient))
                     painter.setPen(Qt.NoPen)
                     painter.drawPolygon(poly)
             
             # 8. TERRITORY OWNERSHIP
             if getattr(self.state, 'show_sections', True) and hasattr(self.state.map, 'hex_sides'):
                 side = self.state.map.hex_sides.get(tuple(hex_obj))
                 
                 # Logic for filtering which territories are shown based on the current tab.
                 app_mode = getattr(self.state, "app_mode", "scenario")
                 active_scen_side = getattr(self.state, "active_scenario_side", "Attacker")
                 
                 show_side = True
                 if app_mode == "scenario" and active_scen_side != "Combined":
                     # Hide the "Other Side" if you are currently setting up just one team.
                     role_map = getattr(self.state, "role_allocation", {"Red": "Defender", "Blue": "Attacker"})
                     if side and role_map.get(side) != active_scen_side:
                         show_side = False
                 
                 if show_side:
                     if side == "Red":
                         painter.setBrush(QBrush(QColor(Theme.ACCENT_ENEMY))) 
                         painter.setOpacity(0.15)
                         painter.setPen(Qt.NoPen)
                         painter.drawPolygon(poly)
                         painter.setOpacity(1.0)
                     elif side == "Blue":
                         painter.setBrush(QBrush(QColor(Theme.ACCENT_ALLY))) 
                         painter.setOpacity(0.15)
                         painter.setPen(Qt.NoPen)
                         painter.drawPolygon(poly)
                         painter.setOpacity(1.0)
 
        # --- VIEWPORT NAVIGATION ---
        center_hex = HexMath.pixel_to_hex(self.camera_x, self.camera_y, self.hex_size)
        if not center_hex: return
 
        # Calculate how many hexagons fit in the window so we don't draw hidden ones.
        draw_radius = int(max(vw, vh) / (self.hex_size * 1.5)) + 2
        center_q, center_r = center_hex.q, center_hex.r
        
        if grid_mode == "bounded":
             # Hard limits on how far the world reaches.
             map_width = self.state.map.width
             map_height = self.state.map.height
             c_col, c_row = HexMath.cube_to_offset(center_hex)
             
             min_col = max(0, c_col - draw_radius)
             max_col = min(map_width, c_col + draw_radius + 1)
             min_row = max(0, c_row - draw_radius)
             max_row = min(map_height, c_row + draw_radius + 1)
             
             for col in range(min_col, max_col):
                 for row in range(min_row, max_row):
                     q, r, _ = HexMath.offset_to_cube(col, row)
                     draw_hex(q, r)
        else:
            # Infinite Mode: Draw everything in a circular radius around the camera.
            for q in range(center_q - draw_radius, center_q + draw_radius + 1):
                for r in range(center_r - draw_radius, center_r + draw_radius + 1):
                     if HexMath.distance(center_hex, Hex(q, r, -q-r)) > draw_radius: continue
                     draw_hex(q, r)
    def draw_hex_hover(self, painter, cx, cy):
        """Draws a highlight over the hexagon currently under the mouse."""
        if not self.hovered_hex: return
        
        wx, wy = HexMath.hex_to_pixel(self.hovered_hex, self.hex_size)
        sx = wx - self.camera_x + cx
        sy = wy - self.camera_y + cy
        
        # Check if hovered hex is on screen
        vw, vh = self.width(), self.height()
        margin = self.hex_size
        if sx < -margin or sx > vw + margin or sy < -margin or sy > vh + margin: return
        
        corners = HexMath.get_corners(sx, sy, self.hex_size - 1)
        poly = QPolygonF([QPointF(x, y) for x, y in corners])
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 50))) # Semi-Transparent white
        painter.setPen(QPen(QColor(Theme.ACCENT_ALLY), 2))
        painter.drawPolygon(poly)

    def draw_terrain_overlays(self, painter, cx, cy):
        """Draws roads, canals, and other lines on top of the terrain."""
        self.draw_global_paths(painter, cx, cy)

    def draw_zone_layer(self, painter, cx, cy):
        """Draws the semi-transparent rectangles or regions for mission zones."""
        app_mode = getattr(self.state, "app_mode", "terrain")
        active_side = getattr(self.state, "active_scenario_side", "Attacker")
        
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            # Filter zones so you only see the ones relevant to your current side.
            if app_mode == "scenario":
                z_side = zdata.get("side", "Neutral")
                role_map = getattr(self.state, "role_allocation", {"Red": "Defender", "Blue": "Attacker"})
                resolved_active_side = active_side
                mapped_z_side = role_map.get(z_side, z_side)
                
                if mapped_z_side != "Neutral" and active_side not in ["All", "Combined"] and mapped_z_side != resolved_active_side:
                    continue
                
                # Neutral obstacles are always visible
                zone_type = zdata.get("type", "")
                if "Obstacle" in zone_type:
                    if z_side != "Neutral" and active_side not in ["All", "Combined"] and mapped_z_side != resolved_active_side:
                        continue
            
            hexes = zdata.get('hexes', [])
            if not hexes: continue
            
            color = QColor(zdata.get('color', '#FFFFFF'))
            color.setAlpha(80) # Semi-Transparent
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            for h in hexes:
                wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
                sx = wx - self.camera_x + cx
                sy = wy - self.camera_y + cy
                corners = HexMath.get_corners(sx, sy, self.hex_size - 1)
                poly = QPolygonF([QPointF(x, y) for x, y in corners])
                painter.drawPolygon(poly)

    def draw_entity_layer(self, painter, cx, cy, vw, vh):
        """THE UNIT LAYER: Draws all units (agents) with smooth movement and grounding."""
        app_mode = getattr(self.state, "app_mode", "terrain")
        active_side = getattr(self.state, "active_scenario_side", "Attacker")
        selected_id = getattr(self.active_tool, 'selected_entity_id', None)
        
        for eid, ent in self.state.entity_manager._entities.items():
             side = ent.get_attribute("side", "Neutral")
             
             # --- SIDE FILTERING ---
             if app_mode == "scenario" and active_side not in ["All", "Combined"]:
                 if side == "Attacker" and active_side != "Attacker": continue
                 if side == "Defender" and active_side != "Defender": continue
             
             hex_obj = self.state.map.get_entity_position(eid)
             if not hex_obj: continue
             
             # SYNC ANIMATION TARGET: Get current hex position in world coordinates
             wx_target, wy_target = HexMath.hex_to_pixel(hex_obj, self.hex_size)
             
             if eid not in self.agent_anim_state:
                 # Initial placement (no animation)
                 self.agent_anim_state[eid] = {"x": wx_target, "y": wy_target, "target_x": wx_target, "target_y": wy_target}
             else:
                 # ONLY poll from map if NO queue exists and we aren't moving to a queued target
                 queue = self.agent_movement_queues.get(eid, [])
                 state = self.agent_anim_state[eid]
                 if not queue and abs(state["x"] - state["target_x"]) < 1.0 and abs(state["y"] - state["target_y"]) < 1.0:
                     # Update target for smooth interpolation in update_animations()
                     self.agent_anim_state[eid]["target_x"] = wx_target
                     self.agent_anim_state[eid]["target_y"] = wy_target

             # Get the currently ANIMATED position
             anim = self.agent_anim_state[eid]
             sx = anim["x"] - self.camera_x + cx
             sy = anim["y"] - self.camera_y + cy
             
             # Culling: Don't draw if the unit is off-screen.
             margin = self.hex_size
             if sx < -margin or sx > vw + margin or sy < -margin or sy > vh + margin: continue
             
             # --- 1. SELECTION GLOW (Pulse) ---
             radius = self.hex_size * 0.5
             if eid == selected_id:
                 glow_color = QColor(Theme.ACCENT_ALLY)
                 glow_color.setAlpha(int(100 + 100 * self.selection_pulse))
                 painter.setBrush(Qt.NoBrush)
                 painter.setPen(QPen(glow_color, 4 + 2 * self.selection_pulse))
                 painter.drawEllipse(QPointF(sx, sy), radius * 1.25, radius * 1.25)

             # --- 2. DROP SHADOW (Grounding) ---
             # Draw a slightly offset dark ellipse to look like it's on the ground.
             shadow_color = QColor(0, 0, 0, 80)
             painter.setBrush(QBrush(shadow_color))
             painter.setPen(Qt.NoPen)
             painter.drawEllipse(QPointF(sx + 4, sy + 4), radius, radius)

             # --- 3. TEAM COLORS ---
             agent_color = QColor(Theme.TEXT_PRIMARY)
             if side in ["Attacker", "Red"]: agent_color = QColor(Theme.ACCENT_ENEMY)
             elif side in ["Defender", "Blue"]: agent_color = QColor(Theme.ACCENT_ALLY)
             
             health = int(ent.get_attribute("health", 100))
             alpha = int((max(0, min(120, health)) / 120.0) * 255)
             alpha = max(100, alpha)
             agent_color.setAlpha(alpha)
             
             # --- SUPPRESSION HALOS ---
             suppression = float(ent.get_attribute("suppression", 0.0))
             if suppression >= 50:
                 halo_color = QColor(Theme.ACCENT_ENEMY) if suppression >= 100 else QColor(Theme.ACCENT_WARN)
                 halo_color.setAlpha(180)
                 painter.setBrush(Qt.NoBrush)
                 painter.setPen(QPen(halo_color, 4))
                 painter.drawEllipse(QPointF(sx, sy), radius * 1.3, radius * 1.3)
             
             painter.setBrush(QBrush(agent_color))
             painter.setPen(QPen(Qt.black, 1))
             painter.drawEllipse(QPointF(sx, sy), radius, radius)
             
             atype = ent.get_attribute("type", "").lower()
             icon_type = "nato_infantry"
             if "mg" in atype or "machine" in atype: icon_type = "nato_mg"
             elif "recon" in atype or "cavalry" in atype: icon_type = "nato_recon"

             icon_rect = QRectF(sx - radius*0.7, sy - radius*0.7, radius * 1.4, radius * 1.4)
             VectorIconPainter.draw_vector_icon(painter, icon_rect, icon_type, color="white")
             
             # --- 4. REWARD OVERLAY ---
             if self.show_rewards and hasattr(self, 'action_model'):
                  # Fetch recent rewards for this agent
                  reward_val = 0
                  for r_step, r_eid, r_val, r_act in reversed(self.action_model.episode_rewards):
                      if r_eid == eid:
                          reward_val = r_val
                          break
                  
                  if reward_val != 0:
                      painter.setPen(QPen(QColor(Theme.ACCENT_ALLY) if reward_val > 0 else QColor(Theme.ACCENT_ENEMY)))
                      font_reward = painter.font()
                      font_reward.setBold(True)
                      font_reward.setPointSize(max(10, int(self.hex_size / 3)))
                      painter.setFont(font_reward)
                      
                      sign = "+" if reward_val > 0 else ""
                      painter.drawText(
                          QRectF(sx - self.hex_size, sy - radius - self.hex_size*0.5, self.hex_size*2, self.hex_size),
                          Qt.AlignCenter | Qt.AlignBottom,
                          f"{sign}{reward_val:g}"
                      )

             # --- UNIT LABEL ---
             painter.setPen(QPen(Qt.white))
             font = painter.font()
             font.setPointSize(max(8, int(self.hex_size / 4)))
             painter.setFont(font)
             painter.drawText(
                 QRectF(sx - self.hex_size, sy + radius, self.hex_size * 2, self.hex_size), 
                 Qt.AlignCenter | Qt.AlignTop, 
                 ent.name
             )
             
             # --- COMMAND VISUALS (Dashed Lines) ---
             cmd = getattr(ent, 'current_command', None)
             if cmd and getattr(cmd, 'target_hex', None):
                 wx_tgt, wy_tgt = HexMath.hex_to_pixel(cmd.target_hex, self.hex_size)
                 sx_tgt = wx_tgt - self.camera_x + cx
                 sy_tgt = wy_tgt - self.camera_y + cy
                 
                 cmd_color = QColor(255, 255, 255, 150)
                 if cmd.command_type == "MOVE": cmd_color = QColor(Theme.ACCENT_ALLY)
                 elif cmd.command_type == "CAPTURE": cmd_color = QColor(Theme.ACCENT_WARN)
                 elif cmd.command_type == "DEFEND": cmd_color = QColor(0, 100, 255, 150)
                 elif cmd.command_type == "FIRE": cmd_color = QColor(Theme.ACCENT_ENEMY)
                 
                 width = 3 if getattr(cmd, 'is_user_assigned', False) else 2
                 TacticalArrowPainter.draw_arrow(painter, QPointF(sx, sy), QPointF(sx_tgt, sy_tgt), cmd_color, width=width, style=Qt.DashLine)
                 
                 painter.setBrush(Qt.NoBrush)
                 painter.setPen(QPen(cmd_color, 2))
                 painter.drawEllipse(QPointF(sx_tgt, sy_tgt), radius * 0.8, radius * 0.8)
                 
                 if getattr(cmd, 'is_user_assigned', False):
                     painter.setBrush(QBrush(cmd_color))
                     painter.drawEllipse(QPointF(sx_tgt, sy_tgt), radius * 0.3, radius * 0.3)

    def draw_debug_coords(self, painter, cx, cy, vw, vh):
         """Displays coordinate numbers on each hexagon for developers."""
         center_hex = HexMath.pixel_to_hex(self.camera_x, self.camera_y, self.hex_size)
         if not center_hex: return
         
         radius = int(max(vw, vh) / self.hex_size) + 2
         painter.setPen(QPen(self.text_color))
         font = painter.font()
         font.setPointSize(max(8, int(self.hex_size / 3)))
         painter.setFont(font)
         
         grid_mode = getattr(self.state, "grid_mode", "infinite")
         map_width = self.state.map.width
         map_height = self.state.map.height
         
         for q in range(center_hex.q - radius, center_hex.q + radius):
             for r in range(center_hex.r - radius, center_hex.r + radius):
                 h = Hex(q, r, -q-r)
                 col, row = HexMath.cube_to_offset(h)
                 
                 # Bounds check for 'Bounded' map mode
                 if grid_mode == "bounded":
                     if col < 0 or col >= map_width or row < 0 or row >= map_height:
                         continue
                 
                 # Draw text if on-screen
                 wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
                 sx = wx - self.camera_x + cx
                 sy = wy - self.camera_y + cy
                 if 0 < sx < vw and 0 < sy < vh:
                     painter.drawText(QRectF(sx-self.hex_size, sy-self.hex_size/2, self.hex_size*2, self.hex_size), 
                              Qt.AlignCenter, f"{col},{row}")

    def draw_threat_heatmap(self, painter, cx, cy, vw, vh):
         """Displays semi-transparent red zones for tactical danger."""
         if not hasattr(self.state, 'threat_map'): return
         
         center_hex = HexMath.pixel_to_hex(self.camera_x, self.camera_y, self.hex_size)
         if not center_hex: return
         
         draw_radius = int(max(vw, vh) / (self.hex_size * 1.5)) + 2
         grid_mode = getattr(self.state, "grid_mode", "infinite")
         map_width = self.state.map.width
         map_height = self.state.map.height
         active_side = getattr(self.state, "active_scenario_side", "Attacker")
         
         for q in range(center_hex.q - draw_radius, center_hex.q + draw_radius + 1):
             for r in range(center_hex.r - draw_radius, center_hex.r + draw_radius + 1):
                 h = Hex(q, r, -q-r)
                 col, row = HexMath.cube_to_offset(h)
                 
                 if grid_mode == "bounded":
                     if col < 0 or col >= map_width or row < 0 or row >= map_height:
                         continue
                 elif HexMath.distance(center_hex, h) > draw_radius:
                     continue
                 
                 # Only colorize hexes that actually exist on the map (no void overlays)
                 if not self.state.map.get_terrain(h):
                     continue
                 
                 # The AI pathfinder uses getting threat relative to the querying faction.
                 threat_score = self.state.threat_map.get_threat_for_faction(h, active_side)
                 
                 if threat_score > 0:
                     wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
                     sx = wx - self.camera_x + cx
                     sy = wy - self.camera_y + cy
                     
                     if 0 < sx < vw and 0 < sy < vh:
                         # Scale alpha based on danger (e.g. 1 threat = light red, 5 threat = solid red)
                         alpha_val = min(150, int(threat_score * 30))
                         threat_color = QColor(255, 0, 0, alpha_val)
                         
                         corners = HexMath.get_corners(sx, sy, self.hex_size - 1)
                         poly = QPolygonF([QPointF(x, y) for x, y in corners])
                         
                         painter.setBrush(QBrush(threat_color))
                         painter.setPen(Qt.NoPen)
                         painter.drawPolygon(poly)

    def draw_global_paths(self, painter, cx, cy):
        """THE ROAD BUILDER: Draws long lines like Borders, Rivers, and Roads."""
        app_mode = getattr(self.state, "app_mode", "terrain")
        active_side = getattr(self.state, "active_scenario_side", "Attacker")
        
        paths = self.state.map.get_paths()
        for pid, pdata in paths.items():
            # Filter: Don't show enemy territory lines unless in 'Combined' view.
            if app_mode == "scenario":
                p_side = pdata.get("side", "Neutral")
                if pdata.get("type") != "Border":
                    if p_side != "Neutral" and active_side not in ["All", "Combined"] and p_side != active_side:
                        continue

            # User setting: Hide borders if requested.
            if pdata.get("type") == "Border" and not getattr(self.state, "show_borders", True):
                continue
                
            hexes = pdata.get('hexes', [])
            if len(hexes) < 2: continue
            
            color = QColor(pdata.get('color', '#CCCCCC'))
            pen = QPen(color, 5)
            pen.setJoinStyle(Qt.RoundJoin) # Makes corners smooth.
            painter.setPen(pen)
            
            path_mode = pdata.get('mode', getattr(self.state, 'path_mode', "Center-to-Center"))
            
            # --- EDGE-ALIGNED MODE (Complex Border Drawing) ---
            # This logic 'walks' around the perimeter of the hexagons to draw a continuous jagged line.
            if path_mode == "Edge-Aligned":
                all_path_hexes = []
                for i in range(len(hexes)):
                    if i == 0: all_path_hexes.append(hexes[i])
                    else:
                        line_hexes = HexMath.line(hexes[i-1], hexes[i])
                        if line_hexes and len(line_hexes) > 1: all_path_hexes.extend(line_hexes[1:])
                        else: all_path_hexes.append(hexes[i])

                points = []
                # Walk the line and determine which specific edges of the hex to "paint".
                if len(all_path_hexes) >= 2:
                    h0, h1 = all_path_hexes[0], all_path_hexes[1]
                    dir_idx = HexMath.get_neighbor_direction(h0, h1)
                    wx, wy = HexMath.hex_to_pixel(h0, self.hex_size)
                    corners = HexMath.get_corners(wx, wy, self.hex_size)
                    
                    # Store the two corners that form the edge between the first two hexagons.
                    c1, c2 = corners[dir_idx], corners[(dir_idx + 1) % 6]
                    points.append(QPointF(c1[0] - self.camera_x + cx, c1[1] - self.camera_y + cy))
                    points.append(QPointF(c2[0] - self.camera_x + cx, c2[1] - self.camera_y + cy))
                    current_tip_world = c2
                
                # Iterate through the rest of the path, finding connected corners.
                for i in range(1, len(all_path_hexes) - 1):
                    curr_h, prev_h, next_h = all_path_hexes[i], all_path_hexes[i-1], all_path_hexes[i+1]
                    dir_from_prev = HexMath.get_neighbor_direction(curr_h, prev_h)
                    dir_to_next = HexMath.get_neighbor_direction(curr_h, next_h)
                    
                    wx, wy = HexMath.hex_to_pixel(curr_h, self.hex_size)
                    corners = HexMath.get_corners(wx, wy, self.hex_size)
                    
                    idx_entry_start, idx_entry_end = dir_from_prev, (dir_from_prev + 1) % 6
                    
                    # Find which corner on the new hex matches where our line currently ends.
                    m_s = (corners[idx_entry_start][0] - current_tip_world[0])**2 + (corners[idx_entry_start][1] - current_tip_world[1])**2
                    m_e = (corners[idx_entry_end][0] - current_tip_world[0])**2 + (corners[idx_entry_end][1] - current_tip_world[1])**2
                    current_idx = idx_entry_end if m_e < m_s else idx_entry_start
                    
                    idx_exit_1, idx_exit_2 = dir_to_next, (dir_to_next + 1) % 6
                    
                    # Determine shortest path around the perimeter to get to the next shared edge.
                    d_cw1, d_ccw1 = (idx_exit_1 - current_idx) % 6, (current_idx - idx_exit_1) % 6
                    d_cw2, d_ccw2 = (idx_exit_2 - current_idx) % 6, (current_idx - idx_exit_2) % 6
                    
                    best_diff, best_target, direction = 100, -1, 0
                    if d_cw1 < best_diff: best_diff, best_target, direction = d_cw1, idx_exit_1, 1
                    if d_ccw1 < best_diff: best_diff, best_target, direction = d_ccw1, idx_exit_1, -1
                    if d_cw2 < best_diff: best_diff, best_target, direction = d_cw2, idx_exit_2, 1
                    if d_ccw2 < best_diff: best_diff, best_target, direction = d_ccw2, idx_exit_2, -1
                    
                    curr = current_idx
                    for _ in range(best_diff):
                        curr = (curr + direction) % 6
                        c = corners[curr]
                        points.append(QPointF(c[0] - self.camera_x + cx, c[1] - self.camera_y + cy))
                        current_tip_world = c
                
                if len(points) > 1:
                    painter.drawPolyline(*points)
            else:
                # --- CENTER-TO-CENTER MODE ---
                # Simple mode: the line goes straight through the middle of each hexagon.
                all_path_hexes = []
                for i in range(len(hexes)):
                    if i == 0: all_path_hexes.append(hexes[i])
                    else:
                        line_hexes = HexMath.line(hexes[i-1], hexes[i])
                        if line_hexes and len(line_hexes) > 1: all_path_hexes.extend(line_hexes[1:])
                        else: all_path_hexes.append(hexes[i])

                points = []
                for h in all_path_hexes:
                    wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
                    points.append(QPointF(wx - self.camera_x + cx, wy - self.camera_y + cy))
                
                if len(points) > 1:
                    painter.drawPolyline(*points)
                elif len(points) == 1:
                    painter.drawEllipse(points[0], 5, 5)

    def draw_path_preview(self, painter, cx, cy):
        if not self.current_path or len(self.current_path) == 0:
            return
            
        path_mode = getattr(self.state, 'path_mode', "Center-to-Center")
        
        pen = QPen(QColor("#FFFF00"), 3, Qt.DashLine)
        painter.setPen(pen)
        
        if path_mode == "Edge-Aligned":
            # Border Line: Walker (Perimeter Following)
            if len(self.current_path) < 2:
                 # Just a dot if single point
                 h = self.current_path[0]
                 wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
                 sx = wx - self.camera_x + cx
                 sy = wy - self.camera_y + cy
                 painter.drawEllipse(QPointF(sx, sy), 5, 5)
                 return

            # 1. Full hex list via interpolation
            all_path_hexes = []
            for i in range(len(self.current_path)):
                if i == 0:
                    all_path_hexes.append(self.current_path[i])
                else:
                    start = self.current_path[i-1]
                    goal = self.current_path[i]
                    line_hexes = HexMath.line(start, goal)
                    if line_hexes and len(line_hexes) > 1:
                        all_path_hexes.extend(line_hexes[1:])
                    else:
                        all_path_hexes.append(goal)

            if len(all_path_hexes) < 2:
                return

            points = []
            current_tip_world = (0, 0)

            # Init First Segment
            h0 = all_path_hexes[0]
            h1 = all_path_hexes[1]
            dir_idx = HexMath.get_neighbor_direction(h0, h1)
            
            wx, wy = HexMath.hex_to_pixel(h0, self.hex_size)
            corners = HexMath.get_corners(wx, wy, self.hex_size)
            
            c1 = corners[dir_idx]
            c2 = corners[(dir_idx + 1) % 6]
            
            sx1 = c1[0] - self.camera_x + cx
            sy1 = c1[1] - self.camera_y + cy
            sx2 = c2[0] - self.camera_x + cx
            sy2 = c2[1] - self.camera_y + cy
            
            points.append(QPointF(sx1, sy1))
            points.append(QPointF(sx2, sy2))
            
            current_tip_world = c2

            # Walk the rest
            for i in range(1, len(all_path_hexes) - 1):
                curr_h = all_path_hexes[i]
                prev_h = all_path_hexes[i-1]
                next_h = all_path_hexes[i+1]
                
                dir_from_prev = HexMath.get_neighbor_direction(curr_h, prev_h)
                dir_to_next = HexMath.get_neighbor_direction(curr_h, next_h)
                
                wx, wy = HexMath.hex_to_pixel(curr_h, self.hex_size)
                corners = HexMath.get_corners(wx, wy, self.hex_size)
                
                # Determine traversal on current hex perimeter
                # We enter from 'dir_from_prev' edge
                # We exit to 'dir_to_next' edge
                
                # Entry corner is the one we are sitting on (current_tip_world)
                # It corresponds to one of the corners of the entry edge.
                
                idx_entry_start = dir_from_prev
                idx_entry_end = (dir_from_prev + 1) % 6
                
                match_start = (corners[idx_entry_start][0] - current_tip_world[0])**2 + (corners[idx_entry_start][1] - current_tip_world[1])**2
                match_end = (corners[idx_entry_end][0] - current_tip_world[0])**2 + (corners[idx_entry_end][1] - current_tip_world[1])**2
                
                current_idx = idx_entry_end if match_end < match_start else idx_entry_start
                
                idx_exit_1 = dir_to_next
                idx_exit_2 = (dir_to_next + 1) % 6
                
                # Calculate shortest rotation (CW or CCW) to either exit corner
                diff_cw_1 = (idx_exit_1 - current_idx) % 6
                diff_ccw_1 = (current_idx - idx_exit_1) % 6
                diff_cw_2 = (idx_exit_2 - current_idx) % 6
                diff_ccw_2 = (current_idx - idx_exit_2) % 6
                
                best_diff = 100
                best_target = -1
                direction = 0
                
                # Minimal turn logic
                if diff_cw_1 < best_diff:
                    best_diff = diff_cw_1
                    best_target = idx_exit_1
                    direction = 1
                if diff_ccw_1 < best_diff:
                    best_diff = diff_ccw_1
                    best_target = idx_exit_1
                    direction = -1
                if diff_cw_2 < best_diff:
                    best_diff = diff_cw_2
                    best_target = idx_exit_2
                    direction = 1
                if diff_ccw_2 < best_diff:
                    best_diff = diff_ccw_2
                    best_target = idx_exit_2
                    direction = -1
                
                steps = best_diff
                curr = current_idx
                for _ in range(steps):
                    curr = (curr + direction) % 6
                    c = corners[curr]
                    sx = c[0] - self.camera_x + cx
                    sy = c[1] - self.camera_y + cy
                    points.append(QPointF(sx, sy))
                    current_tip_world = c
                
                # Ensure we end exactly on the specific exit corner we targeted
                other_exit_corner_idx = idx_exit_2 if best_target == idx_exit_1 else idx_exit_1
                c_other = corners[other_exit_corner_idx] # This might not be used, handled by loop?
                
                # Actually, the loop brings us to 'best_target'.
                # But the edge has 2 corners. We walked to ONE of them.
                # Now we need to cross the edge to the OTHER corner? No.
                # The 'best_target' corner IS the corner we are at.
                # Wait, the edge to next hex is 'dir_to_next'.
                # We need to land on a corner of 'dir_to_next'.
                # Once there, that corner IS shared with 'next_h'?
                # The shared edge has 2 corners. We land on one.
                # The next iteration starts from that SAME point (which corresponds to a potentially different corner index on next_h).
                
                # So we update current_tip_world only.
                pass 
                
            if len(points) > 1:
                painter.drawPolyline(*points)
                
        else:
            # Center-to-Center mode: Connect all hex centers along the path
            # For each pair of clicked hexes, find all hexes between them
            all_path_hexes = []
            
            for i in range(len(self.current_path)):
                if i == 0:
                    all_path_hexes.append(self.current_path[i])
                else:
                    # Get all hexes on line from previous to current
                    start = self.current_path[i-1]
                    goal = self.current_path[i]
                    
                    # Use hex line interpolation
                    line_hexes = HexMath.line(start, goal)
                    
                    if line_hexes and len(line_hexes) > 1:
                        # Add all hexes except the first (already added)
                        all_path_hexes.extend(line_hexes[1:])
                    else:
                        # Fallback: just add the goal hex
                        all_path_hexes.append(goal)
            
            # Now draw lines connecting all these hex centers
            points = []
            for h in all_path_hexes:
                wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
                sx = wx - self.camera_x + cx
                sy = wy - self.camera_y + cy
                points.append(QPointF(sx, sy))
            
            if len(points) > 1:
                painter.drawPolyline(*points)
            elif len(points) == 1:
                # Single hex - show a dot
                painter.drawEllipse(points[0], 5, 5)
        
    def draw_polygon_preview(self, painter, cx, cy):
        # 1. Calculate and draw filled preview hexes
        if len(self.current_polygon) >= 3:
            # Get hexes inside current polygon
            preview_hexes = HexMath.get_hexes_in_polygon(self.current_polygon)
            
            # Draw filled preview
            for hex_obj in preview_hexes:
                wx, wy = HexMath.hex_to_pixel(hex_obj, self.hex_size)
                sx = wx - self.camera_x + cx
                sy = wy - self.camera_y + cy
                
                corners = HexMath.get_corners(sx, sy, self.hex_size - 1)
                poly = QPolygonF([QPointF(x, y) for x, y in corners])
                
                # Semi-transparent fill
                color = QColor("#00FF00")
                color.setAlpha(60)
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawPolygon(poly)
        
        # 2. Draw vertex line loop
        pen = QPen(QColor("#00FF00"), 3, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        points = []
        for h in self.current_polygon:
             wx, wy = HexMath.hex_to_pixel(h, self.hex_size)
             sx = wx - self.camera_x + cx
             sy = wy - self.camera_y + cy
             points.append(QPointF(sx, sy))
        
        # Draw the lines connecting the points.
        if len(points) > 1:
            painter.drawPolyline(*points)
            # If it's a closed shape (Polygon), connect the last point to the first.
            if len(points) > 2:
                painter.drawLine(points[-1], points[0])
    
    def draw_edit_vertices(self, painter, cx, cy, mode):
        """Draw editable vertices for zones or paths"""
        if mode == "zone" and self.editing_zone_id:
            zone_data = self.state.map.get_zones().get(self.editing_zone_id)
            if not zone_data:
                return
            # Use vertices if available, otherwise fall back to hexes
            vertices = zone_data.get('vertices', zone_data.get('hexes', []))
            color = QColor("#FFFF00")  # Yellow for zone vertices
            
        elif mode == "path" and self.editing_path_id:
            path_data = self.state.map.get_paths().get(self.editing_path_id)
            if not path_data:
                return
            vertices = path_data.get('hexes', [])  # Paths use hexes as vertices
            color = QColor("#FF00FF")  # Magenta for path vertices
        else:
            return
        
        if not vertices:
            return
        
        # Draw connecting lines between vertices
        painter.setPen(QPen(color, 3, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        
        points = []
        for vertex in vertices:
            wx, wy = HexMath.hex_to_pixel(vertex, self.hex_size)
            sx = wx - self.camera_x + cx
            sy = wy - self.camera_y + cy
            points.append(QPointF(sx, sy))
        
        if len(points) > 1:
            painter.drawPolyline(*points)
            if mode == "zone" and len(points) > 2:
                painter.drawLine(points[-1], points[0])  # Close polygon
        
        # Draw vertex markers (Large dots you can click and drag)
        for i, vertex in enumerate(vertices):
            wx, wy = HexMath.hex_to_pixel(vertex, self.hex_size)
            sx = wx - self.camera_x + cx
            sy = wy - self.camera_y + cy
            
            # Draw outer ring (The 'handle')
            painter.setPen(QPen(color, 3))
            painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
            radius = self.hex_size * 0.5
            painter.drawEllipse(QPointF(sx, sy), radius, radius)
            
            # Draw inner dot (The center)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(sx, sy), radius * 0.4, radius * 0.4)
            
            # Draw vertex number so the user knows the order
            painter.setPen(QPen(Qt.white))
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QPointF(sx - 5, sy + 5), str(i))
    
    def get_clicked_vertex(self, screen_x, screen_y):
        """Check if click is on a vertex, return vertex index or None"""
        vertices = []
        if self.editing_zone_id:
            zone_data = self.state.map.get_zones().get(self.editing_zone_id)
            if zone_data:
                vertices = zone_data.get('vertices', [])
        elif self.editing_path_id:
            path_data = self.state.map.get_paths().get(self.editing_path_id)
            if path_data:
                vertices = path_data.get('hexes', [])
        
        if not vertices:
            return None
        
        cx = self.width() / 2
        cy = self.height() / 2
        click_radius = self.hex_size * 0.5  # Same as vertex marker radius
        
        for i, vertex in enumerate(vertices):
            wx, wy = HexMath.hex_to_pixel(vertex, self.hex_size)
            sx = wx - self.camera_x + cx
            sy = wy - self.camera_y + cy
            
            # Check distance from click to vertex center
            dist = ((screen_x - sx) ** 2 + (screen_y - sy) ** 2) ** 0.5
            if dist <= click_radius:
                return i
        
        return None


    # --- INTERACTION & INPUT HANDLING ---

    def mousePressEvent(self, event):
        """
        Detects when a user clicks the mouse on the map.
        1. Middle Click: Centers the camera.
        2. Ctrl + Left Click: Starts 'Panning' (dragging the map).
        3. Simple Left Click: Passes the click to the active TOOL (e.g. Paint or Select).
        4. Right Click: Opens a menu of commands for the selected unit.
        """
        self.setFocus() # Make sure the map captures keyboard shortcuts
        self.last_mouse_pos = event.pos()

        # 1. Middle Click to Recenter
        if event.button() == Qt.MidButton:
             self.recenter_view()
             return

        # 2. Panning Check (Dragging the camera)
        modifiers = QApplication.keyboardModifiers()
        if (event.button() == Qt.LeftButton and (modifiers & Qt.ControlModifier)) or \
           (self.panning): 
            self.panning = True
            self.setCursor(Qt.ClosedHandCursor) # Change cursor to a 'grabbing' hand
            return

        # 3. Tool Logic (Paint, Select, etc.)
        if self.active_tool:
            self.active_tool.mousePressEvent(event)
            
        # 4. Right Click: Context Menus 
        if event.button() == Qt.RightButton:
            click_hex = self.screen_to_hex(event.x(), event.y())
            if not click_hex: 
                return
            
            # Show the new modular context menu
            menu_ctrl = HexContextMenu(self.mw, self.state, click_hex)
            menu_ctrl.show(event.globalPos())
            return


    def _show_command_menu(self, global_pos, agent, target_hex):
        """Creates the pop-up menu when you right-click with an agent selected."""
        from PyQt5.QtWidgets import QMenu
        from engine.simulation.command import AgentCommand
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #444; }
            QMenu::item:selected { background-color: #3d3d3d; }
        """)
        
        # Header showing agent name and target
        title = menu.addAction(f"Command [{agent.name}] targets ({target_hex.q},{target_hex.r})")
        title.setEnabled(False)
        menu.addSeparator()
        
        # Function to actually assign the order
        def assign(cmd_type):
            agent.current_command = AgentCommand(cmd_type, target_hex, is_user_assigned=True)
            mw = self.window()
            if hasattr(mw, 'log_info'):
                mw.log_info(f"Assigned <b>{cmd_type}</b> Command to {agent.name} at Hex({target_hex.q},{target_hex.r})")
            self.update()
            
        # List of available orders
        menu.addAction("Move to Hex").triggered.connect(lambda: assign("MOVE"))
        menu.addAction("Capture Hex").triggered.connect(lambda: assign("CAPTURE"))
        menu.addAction("Defend Hex").triggered.connect(lambda: assign("DEFEND"))
        menu.addAction("Fire on Hex").triggered.connect(lambda: assign("FIRE"))
        
        if getattr(agent, 'current_command', None):
            menu.addSeparator()
            def clear_cmd():
                agent.current_command = None
                mw = self.window()
                if hasattr(mw, 'log_info'): mw.log_info(f"Cleared Command for {agent.name}")
                self.update()
            menu.addAction("Clear Command").triggered.connect(clear_cmd)
            
        menu.exec_(global_pos)

    def mouseReleaseEvent(self, event):
        """Called when the user lets go of the mouse button."""
        if self.active_tool:
            self.active_tool.mouseReleaseEvent(event)
            
        if self.panning:
            # Revert cursor back to normal
            self.setCursor(Qt.OpenHandCursor if self.space_held else Qt.ArrowCursor)
            if not self.space_held:
                self.panning = False
        
        self.last_mouse_pos = None

    def mouseDoubleClickEvent(self, event):
        """Passes double-clicks to the active tool."""
        if self.active_tool and hasattr(self.active_tool, 'mouseDoubleClickEvent'):
            self.active_tool.mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        """Called constantly as the mouse moves across the map."""
        # 1. Panning (Dragging the Camera)
        if self.panning and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.camera_x -= delta.x()
            self.camera_y -= delta.y()
            self.last_mouse_pos = event.pos()
            self.refresh_map() # Invalidate cache during pan
            return
            
        # 2. Tool Logic (e.g. updating the brush highlight)
        if self.active_tool:
            self.active_tool.mouseMoveEvent(event)
            
        # 3. Update 'Hovered' Hex (which hex is under the cursor)
        hex_obj = self.screen_to_hex(event.x(), event.y())
        if hex_obj != self.hovered_hex:
            self.hovered_hex = hex_obj
            self._update_hover_tooltip(event.globalPos(), hex_obj)
            self.update() # Redraw to show the highlight on the new hex

    def _update_hover_tooltip(self, screen_pos, hex_obj):
        """Builds and shows a rich tooltip for the hexagon under the cursor."""
        if not hex_obj:
            QToolTip.hideText()
            return

        # Basic Info
        lines = [f"<b>Hex:</b> {hex_obj.q}, {hex_obj.r}"]
        
        # Terrain Info
        terrain = self.state.map.get_terrain(hex_obj)
        if terrain:
            t_type = terrain.get("type", "plains").capitalize()
            elev   = terrain.get("elevation", 0)
            lines.append(f"<b>Terrain:</b> {t_type} (Elev: {elev})")
        
        # Entities Info
        entities = self.state.map.get_entities_at(hex_obj)
        for ent_id in entities:
            ent = self.state.entity_manager.get_entity(ent_id)
            if ent:
                side = ent.get_attribute("side", "Unknown")
                lines.append(f"<b>Unit:</b> {ent.name} ({side})")
        
        # Zones Info
        zones = self.state.map.get_zones()
        for zid, zdata in zones.items():
            if hex_obj in zdata.get("hexes", []):
                name = zdata.get("name", zid[:8])
                lines.append(f"<b>Zone:</b> {name}")

        QToolTip.showText(screen_pos, "<br>".join(lines), self)

    def keyPressEvent(self, event):
        """Handles single key presses (Space to pan, R to recenter)."""
        if event.key() == Qt.Key_Space:
            if not event.isAutoRepeat():
                self.space_held = True
                self.panning = True
                self.setCursor(Qt.OpenHandCursor)
        elif event.key() == Qt.Key_R:
             self.recenter_view()
        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            # Finish creating a Path or Zone
            self.commit_drawing()
        else:
            super().keyPressEvent(event)
            
    def keyReleaseEvent(self, event):
        """Detects when a key (like Space) is released."""
        if event.key() == Qt.Key_Space:
            if not event.isAutoRepeat():
                self.space_held = False
                self.panning = False
                self.setCursor(Qt.ArrowCursor)
                self.last_mouse_pos = None
            self.update()

    def zoom_by(self, factor, anchor_point=None):
        """
        Advanced Zooming: Zooms into the exact point where your cursor is, 
        rather than just zooming into the center of the screen.
        """
        if anchor_point is None:
            anchor_point = QPointF(self.width() / 2, self.height() / 2)
            
        old_hex_size = self.hex_size
        new_hex_size = old_hex_size * factor
        new_hex_size = max(10, min(200, new_hex_size))
        
        cx = self.width() / 2
        cy = self.height() / 2
        
        # Calculate world position under the anchor (e.g. cursor)
        wx = anchor_point.x() - cx + self.camera_x
        wy = anchor_point.y() - cy + self.camera_y
        
        self.hex_size = new_hex_size
        actual_factor = new_hex_size / old_hex_size
        
        # Adjust Camera so the point under the cursor stays fixed in screen space
        new_wx = wx * actual_factor
        new_wy = wy * actual_factor
        
        self.camera_x = new_wx - (anchor_point.x() - cx)
        self.camera_y = new_wy - (anchor_point.y() - cy)

        # Scale Animated Positions to prevent 'drifting' during zoom
        for aid, anim in self.agent_anim_state.items():
            anim["x"] *= actual_factor
            anim["y"] *= actual_factor
            anim["target_x"] *= actual_factor
            anim["target_y"] *= actual_factor
        
        self.refresh_map()

    def wheelEvent(self, event):
        """Handles mouse wheel zooming and panning."""
        modifiers = QApplication.keyboardModifiers()
        
        # 1. ZOOMING: If there's a vertical scroll delta, we zoom!
        # This is standard for most map/wargame applications.
        if event.angleDelta().y() != 0:
            zoom_speed = 1.15 if not (modifiers & Qt.ShiftModifier) else 1.05 # Precision zoom if Shift is held
            if event.angleDelta().y() > 0:
                factor = zoom_speed
            else:
                factor = 1.0 / zoom_speed
            
            self.zoom_by(factor, event.pos())
            return # Handled
            
        # 2. PANNING: If there's a horizontal scroll delta, we pan the camera.
        pixel_delta = event.pixelDelta()
        angle_delta = event.angleDelta()
        
        if not pixel_delta.isNull():
            # Smooth Trackpad Panning
            self.camera_x -= pixel_delta.x()
            self.camera_y -= pixel_delta.y()
        else:
            # Standard Mouse Wheel (Horizontal notches)
            scroll_step_x = angle_delta.x() / 2.0
            self.camera_x -= scroll_step_x
            
        self.update()

    def screen_to_hex(self, sx, sy):
        """
        MATH: Converts a pixel position (x, y) on your monitor into 
        the specific (Q, R) coordinates of a hexagon on the map.
        """
        cx = self.width() / 2
        cy = self.height() / 2
        wx = sx - cx + self.camera_x
        wy = sy - cy + self.camera_y
        return HexMath.pixel_to_hex(wx, wy, self.hex_size)

    def commit_drawing(self):
        """
        THE 'FINISH' BUTTON (Enter key): 
        Takes the lines or shapes you've drawn and permanently adds them 
        to the map as a Zone (Area) or Path (Road/River).
        """
        tool = self.state.selected_tool
        import uuid
        
        # --- FINALIZE A ZONE (POLYGON) ---
        if tool == "draw_zone" and hasattr(self, 'current_polygon') and self.current_polygon:
            zid = str(uuid.uuid4())[:8] # Generate a short, unique ID (like 'a1b2c3d4')
            
            # Read options selected in the UI sidebar
            z_type = getattr(self.state, 'zone_opt_type', "Area")
            z_sub = getattr(self.state, 'zone_opt_subtype', f"Area {zid}")
            z_terrain = getattr(self.state, 'zone_terrain_type', "Plains")
            
            # AUTO-COLOR: Pick a color based on the name of the zone.
            color = "#FFA500" # Default Orange
            if "Red" in z_sub or "Attacker" in z_type: color = "#FF0000"
            elif "Blue" in z_sub or "Defender" in z_type: color = "#0000FF"
            elif "Goal" in z_type or "Goal" in z_sub: color = "#00FF00" # Green for Goals
            elif "Obstacle" in z_type or "O" in z_sub: color = "#555555" # Grey for Obstacles
            
            # FIND THE FILL: Identify every hexagon that sits inside the drawn shape.
            hexes_inside = HexMath.get_hexes_in_polygon(self.current_polygon)
            
            # TERRAIN OVERWRITE: Change the land type for every hex inside this area.
            for hex_obj in hexes_inside:
                self.state.map.set_terrain(hex_obj, {"type": z_terrain.lower()})
            
            # SAVE THE ZONE: Permanently record this area in the map data.
            self.state.map.add_zone(zid, {
                "name": z_sub,
                "type": z_type,
                "color": color,
                "hexes": hexes_inside,
                "vertices": list(self.current_polygon) 
            })
            self.current_polygon = [] # Clear the temporary drawing line.
            
        # --- FINALIZE A PATH (LINE) ---
        elif tool == "draw_path" and hasattr(self, 'current_path') and self.current_path:
            pid = str(uuid.uuid4())[:8]
            p_mode = getattr(self.state, 'path_mode', "Center-to-Center")
            
            self.state.map.add_path(pid, {
                "name": f"Path {pid}", 
                "hexes": list(self.current_path),
                "mode": p_mode, 
                "color": "#CCCCCC"
            })
            self.current_path = [] # Reset for the next line.
            
        # Refresh the map to show the changes.
        self.update()
