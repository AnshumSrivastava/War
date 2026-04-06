from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QLineF, QTimer
from engine.core.hex_math import HexMath
from collections import deque
import time

class Visualizer:
    def __init__(self, hex_widget):
        self.hex_widget = hex_widget
        self.fire_events = [] # Now stores (start, end, color, expiry_time)
        self.movement_trails = {} 
        self.texts = [] # Now stores (hex, text, color, expiry_time)
        
        # Event Queue for staggered playback
        self.event_queue = deque()
        
        # Heartbeat timer for sequential processing
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self._process_next_event)
        self.process_interval = 200 # ms between events
        
        # Refresh timer specifically for transient cleanup
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_expired_events)
        self.cleanup_timer.start(50) # Check every 50ms
        
        # Visibility Flags
        self.show_trails = True
        self.show_fire = True
        self.show_text = True
        
    def clear_transients(self):
        # We don't clear immediately anymore; we let them expire
        pass

    def reset(self):
        self.fire_events = []
        self.movement_trails = {}
        self.texts = []
        self.event_queue.clear()
        self.process_timer.stop()

    def enqueue_batch(self, events):
        """Add a whole tick's worth of events to the staggered queue."""
        if not events:
            return
            
        for evt in events:
            self.event_queue.append(evt)
            
        if not self.process_timer.isActive():
            self.process_timer.start(self.process_interval)

    def _process_next_event(self):
        """Pops one event from the queue and makes it 'active' on the map."""
        if not self.event_queue:
            self.process_timer.stop()
            return

        evt = self.event_queue.popleft()
        now = time.time()
        lifetime = 0.8 # Seconds an effect stays visible
        
        # LOGGING: If the event has a log message, display it in the UI log now.
        if 'log' in evt:
            try:
                mw = getattr(self.hex_widget, 'mw', None)
                if mw and hasattr(mw, 'log_info'):
                    mw.log_info(evt['log'])
            except Exception as e:
                print(f"Error logging event: {e}")

        etype = evt.get('type')
        if etype == 'fire':
            color = QColor(255, 50, 50) if evt.get('hit') else QColor(255, 150, 0)
            self.fire_events.append({
                'start': evt['source_hex'],
                'end': evt['target_hex'],
                'color': color,
                'expiry': now + lifetime
            })
        elif etype == 'move':
            # Trails are handled cumulatively for now
            self.add_move_event(evt['agent_id'], evt['from'], evt['to'])
        elif etype == 'reward' or etype == 'text':
            color = evt.get('color', QColor(255, 255, 255))
            val = evt.get('value', evt.get('text', ""))
            if isinstance(val, float): val = f"{val:+.0f}"
            self.texts.append({
                'hex': evt['hex'],
                'text': str(val),
                'color': color,
                'expiry': now + lifetime
            })

        # Tell UI to redraw with the new active effect
        self.hex_widget.update()

    def _cleanup_expired_events(self):
        """Removes old shots and text effects."""
        now = time.time()
        orig_len = len(self.fire_events) + len(self.texts)
        
        self.fire_events = [e for e in self.fire_events if e['expiry'] > now]
        self.texts = [t for t in self.texts if t['expiry'] > now]
        
        if len(self.fire_events) + len(self.texts) < orig_len:
            self.hex_widget.update()

    def add_move_event(self, agent_id, from_hex, to_hex):
        if agent_id not in self.movement_trails:
             self.movement_trails[agent_id] = [from_hex]
        
        if self.movement_trails[agent_id][-1] != to_hex:
            self.movement_trails[agent_id].append(to_hex)

    def draw(self, painter):
        if self.show_trails:
            self._draw_trails(painter)
            
        if self.show_fire:
            self._draw_arrows(painter)
            
        if self.show_text:
            self._draw_texts(painter)

    def _get_screen_pos(self, hex_obj):
        wx, wy = HexMath.hex_to_pixel(hex_obj, self.hex_widget.hex_size)
        cx = self.hex_widget.width() / 2
        cy = self.hex_widget.height() / 2
        sx = wx - self.hex_widget.camera_x + cx
        sy = wy - self.hex_widget.camera_y + cy
        return QPointF(sx, sy)

    def _draw_trails(self, painter):
        painter.save()
        for aid, trail in self.movement_trails.items():
            if len(trail) < 2: continue
            
            # --- 1. THE MAIN TRAIL (Prominent Line) ---
            color = QColor(0, 255, 255, 120)  # Brighter Cyane
            if hasattr(self.hex_widget, 'theme'):
                color = QColor(0, 210, 255, 180) # More tactical blue
                
            pen = QPen(color, 3, Qt.DashLine) # Thick Dashed line
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush) # FIX: Prevent filled polygon bounding
            
            points = [self._get_screen_pos(h) for h in trail]
            if points:
                painter.drawPolyline(QPolygonF(points))

            # --- 2. BREADCRUMBS (Dots at hex centers) ---
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            for pt in points:
                painter.drawEllipse(pt, 4, 4)
        painter.restore()

    def _draw_arrows(self, painter):
        painter.save()
        for evt in self.fire_events:
            start_pt = self._get_screen_pos(evt['start'])
            end_pt = self._get_screen_pos(evt['end'])
            color = evt['color']
            
            # --- TACTICAL FIRE LINE ---
            # Using a thicker SolidLine for the main stream, with a glow effect if possible.
            # For now, a 3px Wide Solid Line with alpha.
            line_color = QColor(color)
            line_color.setAlpha(200)
            
            pen = QPen(line_color, 3, Qt.SolidLine)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(start_pt, end_pt)
            
            # Add a secondary "spark" or "bullet" trail (Dotted)
            pen_spark = QPen(QColor(255, 255, 255, 180), 1, Qt.DotLine)
            painter.setPen(pen_spark)
            painter.drawLine(start_pt, end_pt)
            
            self._draw_arrowhead(painter, start_pt, end_pt, color)
        painter.restore()


    def _draw_arrowhead(self, painter, start, end, color):
        line = QLineF(start, end)
        angle = line.angle()
        
        arrow_size = 10
        p1 = end
        
        v = line.unitVector()
        v.setLength(arrow_size)
        v.setAngle(angle + 150)
        p2 = v.p2()
        
        v.setAngle(angle - 150)
        p3 = v.p2()
        
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygonF([p1, p2, p3]))

    def _draw_texts(self, painter):
        painter.save()
        font = painter.font()
        font.setBold(True)
        font.setPointSize(11)
        painter.setFont(font)
        
        for evt in self.texts:
            pt = self._get_screen_pos(evt['hex'])
            pt.setY(pt.y() - 15)
            
            painter.setPen(QPen(evt['color']))
            painter.drawText(pt, evt['text'])
            
        painter.restore()
