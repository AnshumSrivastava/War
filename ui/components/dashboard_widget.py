"""
FILE: ui/components/dashboard_widget.py
ROLE: The "Mission Control" (Analytics & Intelligence).

DESCRIPTION:
This file creates the side panel that shows you what's happening 'under the hood' 
during a simulation. It's like a stock market ticker and medical monitor for your agents.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
                             QGridLayout, QFrame, QScrollArea, QProgressBar, QTextEdit, 
                             QListWidget, QComboBox, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QSplitter, QSizePolicy, QFormLayout)
from PyQt5.QtCore import Qt, QTimer, QRectF, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPen

import markdown
import os
from ui.styles.theme import Theme
from ui.components.themed_widgets import TacticalCard, TacticalHeader, TacticalTable, TacticalLogItem

# --- UI CONFIGURATION ---
# Tab Titles
STR_TAB_ANALYTICS = "Analytics"
STR_TAB_BRAIN = "Agent Brain (Live)"
STR_TAB_FEED = "Live Feed"
STR_TAB_LOGISTICS = "Logistics (Ammo)"
STR_TAB_REFERENCE = "Cheat Sheet"

# Card Titles
STR_CARD_ACTION_DIST = "ACTION DISTRIBUTION (TOTAL STEPS)"
STR_CARD_DECISION_MODE = "DECISION MODE (EXPLOIT VS EXPLORE)"
STR_CARD_TELEMETRY = "UNIT TELEMETRY"
STR_CARD_COGNITIVE = "COGNITIVE DESCRIPTOR"
STR_CARD_VAL_MATRIX = "ACTION VALUE MATRIX (EXPECTED UTILITY)"

# Labels & Form Fields
STR_LBL_ASSET_MONITOR = "ACTIVE ASSET MONITORING"
STR_LBL_PERSONNEL = "Personnel: {val}"
STR_LBL_HARDWARE = "Hardware: {val}"
STR_LBL_GRID_POS = "Grid Pos: {val}"
STR_LBL_OP_MODE = "Op Mode: {val}"
STR_LBL_ENV_STATE = "Env State: {val}"
STR_LBL_EFFICIENCY = "Efficiency: {val}"
STR_LBL_TYPE = "TYPE:"
STR_LBL_HULL = "HULL:"
STR_LBL_STATUS = "STATUS:"
STR_LBL_AMMO = "AMMO:"
STR_LBL_NO_DATA = "No Data Available"

# Table Columns
COLS_BRAIN = ["VECTOR", "SCORE", "TYPE"]

# Stylesheets
STYLE_TABS = f"""
    QTabWidget::pane {{ border: 1px solid {Theme.BORDER_STRONG}; background: {Theme.BG_SURFACE}; top: -1px; }}
    QTabBar::tab {{
        background: {Theme.BG_DEEP};
        color: {Theme.TEXT_DIM};
        padding: 10px 15px;
        border: 1px solid {Theme.BORDER_STRONG};
        border-bottom: none;
        margin-right: 2px;
        font-family: '{Theme.FONT_HEADER}';
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QTabBar::tab:selected {{
        background: {Theme.BG_SURFACE};
        color: {Theme.ACCENT_ALLY};
        border-top: 2px solid {Theme.ACCENT_ALLY};
    }}
    QTabBar::tab:hover:!selected {{
        background: rgba(255, 255, 255, 0.05);
    }}
"""
STYLE_SCROLL = "QScrollArea { border: none; background: transparent; }"
STYLE_PROGRESS_BAR = "QProgressBar {{ background: {bg}; border: 1px solid {border}; }} QProgressBar::chunk {{ background: {accent}; }}"
STYLE_MONO_LBL = f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;"
STYLE_COMBO = f"""
    QComboBox {{ 
        background-color: {Theme.BG_SURFACE}; color: white; border: 1px solid {Theme.BORDER_STRONG}; 
        padding: 8px; border-radius: 2px; font-family: '{Theme.FONT_HEADER}';
    }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
"""
STYLE_ASSET_LBL = f"color: {Theme.ACCENT_ALLY}; font-weight: bold; letter-spacing: 1.5px; font-size: 11px;"
STYLE_MONO_VITALS = f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px; padding: 2px;"
STYLE_FEED_SCROLL = f"QScrollArea {{ border: 1px solid {Theme.BORDER_STRONG}; background: {Theme.BG_DEEP}; }}"

# HTML Content
HTML_REFERENCE = f"""
<h2>RL Cheatsheet</h2>
<hr>
<h3>1. Bellman Equation (Q-Learning)</h3>
<p style='font-family: monospace; font-size: 14px; background-color: #222; padding: 10px;'>
Q(s,a) = (1-α)Q(s,a) + α[R + γ * max Q(s',a')]
</p>
<ul>
    <li><b>α (Alpha)</b>: Learning Rate (0.1) - How much new info overrides old.</li>
    <li><b>γ (Gamma)</b>: Discount Factor (0.9) - Importance of future rewards.</li>
    <li><b>R</b>: Immediate Reward.</li>
</ul>

<h3>2. State Space (Encoded)</h3>
<p>State = (Grid_Index * 12) + (Casualty_State * 3) + Reward_State</p>
<ul>
    <li><b>Grid Index</b>: Flat index of hex (Row * Cols + Col).</li>
    <li><b>Casualty State</b>: 0 (>75%), 1 (>50%), 2 (>25%), 3 (<25%).</li>
    <li><b>Reward State</b>: 0 (Negative), 1 (Neutral), 2 (Positive).</li>
</ul>

<h3>3. Rewards</h3>
<ul>
    <li><b>Fire Hit</b>: +200</li>
    <li><b>Kill</b>: +500</li>
    <li><b>Casualty Dealt</b>: +10 per unit</li>
    <li><b>Closing Distance</b>: +5</li>
    <li><b>Penalty (Miss)</b>: -5</li>
    <li><b>Penalty (Unit Lost)</b>: -200</li>
</ul>
"""
# -------------------------

class DashboardWidget(QWidget):
    """THE MISSION CONTROL HUB: Organizes the different data tabs."""
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # --- TAB NAVIGATION ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(STYLE_TABS)
        self.tabs.addTab(AnalyticsTab(), STR_TAB_ANALYTICS)            # Charts & Graphs
        self.tabs.addTab(AgentBrainTab(), STR_TAB_BRAIN)               # AI Thought Process
        self.tabs.addTab(LiveFeedTab(), STR_TAB_FEED)                  # Event Log
        self.tabs.addTab(LogisticsTab(state), STR_TAB_LOGISTICS)       # Resource Bars
        self.tabs.addTab(ReferenceTab(), STR_TAB_REFERENCE)           # RL Documentation
        
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        
    def refresh(self, action_model):
        """Called when switching to Dashboard tab."""
        # Update Analytics
        analytics_tab = self.tabs.widget(0)
        if hasattr(analytics_tab, 'update_stats'):
            analytics_tab.update_stats(action_model.stats)
            
        # Update White Box
        wb_tab = self.tabs.widget(1)
        if hasattr(wb_tab, 'update_info'):
            wb_tab.update_info(action_model.agent_debug_info)
            
        # Update Live Feed
        feed_tab = self.tabs.widget(2)
        if hasattr(feed_tab, 'update_log'):
            feed_tab.update_log(action_model.event_log)
            
        # Update Logistics
        logistics_tab = self.tabs.widget(3)
        if hasattr(logistics_tab, 'update_ammo'):
            logistics_tab.update_ammo(action_model)

class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(20)
        self.setStyleSheet(f"background-color: {Theme.BG_DEEP};")
        
        # 1. Action Distribution Module
        self.action_module = TacticalCard(STR_CARD_ACTION_DIST, accent_color=Theme.ACCENT_ALLY)
        self.action_chart = BarChart()
        self.action_module.addWidget(self.action_chart)
        self.layout.addWidget(self.action_module, 1)
        
        # 2. Decision Mode Module
        self.mode_module = TacticalCard(STR_CARD_DECISION_MODE, accent_color=Theme.ACCENT_ENEMY)
        self.mode_chart = BarChart(horizontal=True)
        self.mode_module.addWidget(self.mode_chart)
        self.layout.addWidget(self.mode_module, 1)
        
    def update_stats(self, stats):
        """Pushes new numbers into the charts."""
        self.action_chart.set_data(stats.get("actions", {})) # e.g. "Move: 50, Fire: 20"
        self.mode_chart.set_data(stats.get("modes", {}))     # e.g. "Explore: 10%, Exploit: 90%"

class LogisticsTab(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setStyleSheet(f"background-color: {Theme.BG_DEEP};")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(STYLE_SCROLL)
        
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(10)
        self.grid.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.container)
        self.layout.addWidget(scroll)
        
        self.cards = {} # agent_id -> TacticalCard
        
    def update_ammo(self, action_model):
        entities = action_model.entity_manager.get_all_entities()
        seen_ids = set()
        
        row, col = 0, 0
        max_cols = 2
        
        for entity in entities:
            aid = entity.id
            seen_ids.add(aid)
            
            side = entity.get_attribute("side", "Neutral")
            accent = Theme.ACCENT_ALLY if side == "Attacker" else Theme.ACCENT_ENEMY if side == "Defender" else Theme.TEXT_DIM
            
            if aid not in self.cards:
                # Create a new Tactical Card for this unit
                card = TacticalCard(title=f"{entity.name.upper()} [{side.upper()}]", accent_color=accent)
                card.setFixedWidth(280)
                
                # Vitals Layout
                vitals_layout = QFormLayout()
                vitals_layout.setLabelAlignment(Qt.AlignRight)
                vitals_layout.setSpacing(5)
                
                # Personnel Bar
                p_bar = QProgressBar()
                p_bar.setRange(0, 100)
                p_bar.setFixedHeight(12)
                p_bar.setTextVisible(False)
                p_bar.setStyleSheet(STYLE_PROGRESS_BAR.format(
                    bg=Theme.BG_DEEP, border=Theme.BORDER_STRONG, accent=accent))
                
                self.cards[aid] = {
                    'card': card,
                    'p_bar': p_bar,
                    'p_lbl': QLabel("0/0"),
                    'ammo_lbl': QLabel("0/0"),
                    'type_lbl': QLabel(entity.get_attribute('type', 'UNIT').upper())
                }
                
                # Style font
                for k in ['p_lbl', 'ammo_lbl', 'type_lbl']:
                    self.cards[aid][k].setStyleSheet(STYLE_MONO_LBL)
                
                vitals_layout.addRow(STR_LBL_TYPE, self.cards[aid]['type_lbl'])
                vitals_layout.addRow(STR_LBL_HULL, p_bar)
                vitals_layout.addRow(STR_LBL_STATUS, self.cards[aid]['p_lbl'])
                vitals_layout.addRow(STR_LBL_AMMO, self.cards[aid]['ammo_lbl'])
                
                card.addLayout(vitals_layout)
                self.grid.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

class ReferenceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(HTML_REFERENCE)
        layout.addWidget(text)
        self.setLayout(layout)

class BarChart(QWidget):
    """Simple Custom Painted Bar Chart"""
    def __init__(self, horizontal=False):
        super().__init__()
        self.data = {}
        self.horizontal = horizontal
        self.colors = [QColor(Theme.ACCENT_ALLY), QColor(Theme.ACCENT_ENEMY), QColor(Theme.OLIVE_DRAB), QColor(Theme.ACCENT_WARN), QColor(Theme.SAND_DESERT)]
        
    def set_data(self, data):
        self.data = data
        self.update() # Trigger repaint
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.data:
            painter.setPen(QColor("#777"))
            painter.drawText(self.rect(), Qt.AlignCenter, STR_LBL_NO_DATA)
            return
            
        rect = self.rect()
        margin = 30
        
        keys = list(self.data.keys())
        values = list(self.data.values())
        max_val = max(values) if values else 0
        if max_val == 0: max_val = 1
        
        # Draw Bars
        count = len(keys)
        if count == 0: return
        
        bar_width = (rect.width() - 2 * margin) / count
        if self.horizontal:
             bar_height = (rect.height() - 2 * margin) / count
        
        painter.setFont(QFont(Theme.FONT_MONO, 8, QFont.Bold))
        
        for i, key in enumerate(keys):
            val = self.data[key]
            pct = val / max_val
            color = self.colors[i % len(self.colors)]
            
            params = self.get_bar_geometry(i, count, pct, rect, margin)
            
            # Bar
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            rect_f = QRectF(*params['rect'])
            painter.drawRect(rect_f)
            
            # Label
            label_rect_f = QRectF(*params['label_rect'])
            painter.drawText(label_rect_f, Qt.AlignCenter, str(key))
            
            # Value
            val_rect_f = QRectF(*params['val_rect'])
            painter.drawText(val_rect_f, Qt.AlignCenter, str(val))
            
    def get_bar_geometry(self, i, count, pct, rect, margin):
        if not self.horizontal:
            # Vertical Bars
            w = (rect.width() - 2 * margin) / count
            spacing = w * 0.2
            bar_w = w - spacing
            
            bar_h = (rect.height() - 2 * margin) * pct
            x = margin + i * w + spacing/2
            y = rect.height() - margin - bar_h
            
            return {
                'rect': (x, y, bar_w, bar_h),
                'label_rect': (x, rect.height() - margin, bar_w, margin),
                'val_rect': (x, y - 20, bar_w, 20)
            }
        else:
            # Horizontal Bars (Stacked vertically)
            h = (rect.height() - 2 * margin) / count
            spacing = h * 0.2
            bar_h = h - spacing
            
            bar_w = (rect.width() - 2 * margin * 2) * pct # Reserve space for labels
            y = margin + i * h + spacing/2
            x = margin + 80 # Label space
            
            return {
                'rect': (x, y, bar_w, bar_h),
                'label_rect': (margin, y, 80, bar_h),
                'val_rect': (x + bar_w + 5, y, 40, bar_h)
            }

class AgentBrainTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # --- Asset Selection ---
        top_bar = QHBoxLayout()
        lbl_asset = QLabel(STR_LBL_ASSET_MONITOR)
        lbl_asset.setStyleSheet(STYLE_ASSET_LBL)
        top_bar.addWidget(lbl_asset)
        
        self.combo_agent = QComboBox()
        self.combo_agent.setStyleSheet(STYLE_COMBO)
        self.combo_agent.currentIndexChanged.connect(self.refresh_view)
        top_bar.addWidget(self.combo_agent, 1)
        self.layout.addLayout(top_bar)
        
        # --- Middle: Tactical Vitals & Cognitive State ---
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(15)
        
        # 1. Tactical Vitals
        self.card_vitals = TacticalCard(title=STR_CARD_TELEMETRY, accent_color=Theme.ACCENT_ALLY)
        self.lbl_pers = QLabel(STR_LBL_PERSONNEL.format(val="-"))
        self.lbl_ammo = QLabel(STR_LBL_HARDWARE.format(val="-"))
        self.lbl_pos = QLabel(STR_LBL_GRID_POS.format(val="-"))
        
        for lbl in [self.lbl_pers, self.lbl_ammo, self.lbl_pos]:
            lbl.setStyleSheet(STYLE_MONO_VITALS)
            self.card_vitals.addWidget(lbl)
        
        # 2. Decision Brain
        self.card_brain = TacticalCard(title=STR_CARD_COGNITIVE, accent_color=Theme.ACCENT_WARN)
        self.lbl_mode = QLabel(STR_LBL_OP_MODE.format(val="-"))
        self.lbl_state_desc = QLabel(STR_LBL_ENV_STATE.format(val="-"))
        self.lbl_last_reward = QLabel(STR_LBL_EFFICIENCY.format(val="-"))
        
        for lbl in [self.lbl_mode, self.lbl_state_desc, self.lbl_last_reward]:
            lbl.setStyleSheet(STYLE_MONO_VITALS)
            self.card_brain.addWidget(lbl)
            
        mid_layout.addWidget(self.card_vitals)
        mid_layout.addWidget(self.card_brain)
        self.layout.addLayout(mid_layout)

        # --- Action Value Matrix ---
        self.layout.addSpacing(10)
        self.card_table = TacticalCard(title=STR_CARD_VAL_MATRIX)
        
        self.table = TacticalTable(COLS_BRAIN)
        self.card_table.addWidget(self.table)
        self.layout.addWidget(self.card_table, 1)
        
        self.current_data = {}
        
    def update_info(self, debug_info):
        self.current_data = debug_info
        
        # Update Combo logic
        current_selection = self.combo_agent.currentText()
        self.combo_agent.blockSignals(True)
        self.combo_agent.clear()
        
        agents = sorted(debug_info.keys())
        self.combo_agent.addItems(agents)
        
        if current_selection in agents:
            self.combo_agent.setCurrentText(current_selection)
        elif agents:
            self.combo_agent.setCurrentIndex(0)
            
        self.combo_agent.blockSignals(False)
        self.refresh_view() # Update labels and tables for the newly selected agent.
        
    def refresh_view(self):
        agent = self.combo_agent.currentText()
        if not agent or agent not in self.current_data:
            self.table.setRowCount(0)
            return
            
        info = self.current_data[agent]
        
        # Vitals
        self.lbl_pers.setText(STR_LBL_PERSONNEL.format(val=info.get('personnel', '?')))
        self.lbl_pos.setText(STR_LBL_GRID_POS.format(val=info.get('last_pos', '?')))
        
        # New: Inventory
        inv = info.get('inventory', {})
        w_list = [getattr(w, 'name', w.get('name', 'Weapon')) if isinstance(w, object) else w.get('name', 'Weapon') for w in inv.get('weapons', [])]
        w_str = ", ".join(w_list) if w_list else "None"
        
        res_list = [f"{k}: {v}" for k, v in inv.get('resources', {}).items()]
        res_str = " | ".join(res_list) if res_list else "Empty"
        
        self.lbl_ammo.setText(STR_LBL_HARDWARE.format(val=f"{w_str}<br>Resources: {res_str}"))
        
        # Brain
        self.lbl_mode.setText(STR_LBL_OP_MODE.format(val=f"<b>{info.get('mode', '?')}</b>"))
        self.lbl_state_desc.setText(STR_LBL_ENV_STATE.format(val=info.get('state', '?')))
        self.lbl_last_reward.setText(STR_LBL_EFFICIENCY.format(val=f"{info.get('reward', 0):.2f}"))
        
        # Table
        q_vals = info.get('q_values', {})
        sorted_q = sorted(q_vals.items(), key=lambda x: x[1], reverse=True)
        
        self.table.setRowCount(len(sorted_q))
        chosen_action = info.get('action', '')
        
        from engine.data.definitions.constants import RL_ACTION_MAP
        
        for row, (action_id, val) in enumerate(sorted_q):
            action_name = str(action_id)
            try:
                action_id_int = int(action_id)
                if action_id_int in RL_ACTION_MAP:
                    act_tuple = RL_ACTION_MAP[action_id_int]
                    base_name = f"{act_tuple[0]}"
                    if act_tuple[1]: base_name += f"_{act_tuple[1]}"
                    action_name = f"[{action_id}] {base_name}"
                else: action_name = f"[{action_id}] UNKNOWN"
            except ValueError: pass
            
            item_name = QTableWidgetItem(action_name)
            
            is_chosen = False
            norm_name = action_name.replace("_", " ").upper()
            norm_chosen = str(chosen_action).upper()
            
            if str(action_id) == str(chosen_action): is_chosen = True 
            elif norm_name in norm_chosen: is_chosen = True 
            
            if is_chosen:
                item_name.setBackground(QBrush(QColor(Theme.BG_INPUT)))
                item_name.setForeground(QBrush(QColor(Theme.ACCENT_ALLY)))
                item_name.setText(f"{action_name} 🎯")
            
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(f"{val:.4f}"))
            atype = "FIRE" if "FIRE" in action_name else "MOVE" if "MOVE" in action_name else "ENGAGEMENT"
            self.table.setItem(row, 2, QTableWidgetItem(atype))

class LiveFeedTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(STYLE_FEED_SCROLL)
        
        self.container = QWidget()
        self.feed_layout = QVBoxLayout(self.container)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(0)
        self.feed_layout.addStretch()
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        
    def update_log(self, events):
        if len(events) == self.feed_layout.count() - 1: return
            
        while self.feed_layout.count() > 1:
            item = self.feed_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
                
        import time
        now_str = time.strftime("%H:%M:%S")
        
        for ev in events:
            color = None
            if "REWARD" in ev.upper() or "HIT" in ev.upper(): color = Theme.ACCENT_ALLY
            elif "CRITICAL" in ev.upper() or "ERROR" in ev.upper(): color = Theme.ACCENT_ENEMY
            elif "EPISODE" in ev.upper(): color = Theme.ACCENT_WARN
            
            log_item = TacticalLogItem(now_str, ev, color)
            self.feed_layout.insertWidget(self.feed_layout.count() - 1, log_item)
        
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
