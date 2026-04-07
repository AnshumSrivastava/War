import datetime
"""
FILE: ui/widgets/event_log_widget.py
ROLE: The "Black Box" Recorder.
DESCRIPTION: A scrolling text area that keeps a complete history of every command, hit, and death in the simulation.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QCheckBox, QTextEdit, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QColor
from ui.styles.theme import Theme

# --- UI CONFIGURATION ---
# Titles & Labels
STR_LBL_EVENT_LOG = "<b>EVENT LOG</b>"
STR_BTN_FONT_UP = "A+"
STR_BTN_FONT_DOWN = "A-"
STR_BTN_POPOUT = "Pop Out"
STR_CHK_TABLE_MODE = "Table View"

# Formatting
STR_TS_FMT = "%H:%M:%S"
STR_LOG_MSG_FMT = "<span style='color: {color};'>[{timestamp}]</span> {message}"

# Stylesheets
STYLE_LOG_BOX = f"""
    QListWidget {{
        background-color: {Theme.BG_DEEP};
        color: {Theme.TEXT_PRIMARY};
        font-family: '{Theme.FONT_MONO}';
        font-size: 13px;
        border: 1px solid {Theme.BORDER_STRONG};
        border-radius: 6px;
        padding: 8px;
    }}
"""
# -------------------------

class EventLogWidget(QWidget):
    popout_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        
        self.splitter = QSplitter(Qt.Vertical)
        
        # --- TOP PANE (Live Data) ---
        self.data_container = QWidget()
        data_layout = QVBoxLayout(self.data_container)
        data_layout.setContentsMargins(0, 0, 0, 0)
        
        data_tools = QHBoxLayout()
        data_tools.addWidget(QLabel("<b>LIVE AGENT DATA</b>"))
        data_tools.addStretch()
        data_layout.addLayout(data_tools)
        
        self.table_live = QTableWidget(0, 6)
        self.table_live.setHorizontalHeaderLabels(["Agent", "Pos", "Personnel", "Ammo", "Suppression", "Action"])
        self.table_live.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_live.verticalHeader().setVisible(False)
        self.table_live.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_live.setSelectionMode(QTableWidget.NoSelection)
        self.table_live.setStyleSheet(f"background-color: {Theme.BG_DEEP}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_STRONG};")
        data_layout.addWidget(self.table_live)
        
        # --- BOTTOM PANE (Log) ---
        self.log_container = QWidget()
        log_layout = QVBoxLayout(self.log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- HEADER ROW (Episode & Tools) ---
        log_tools = QHBoxLayout()
        
        self.lbl_current_episode = QLabel("EPISODE: 0")
        self.lbl_current_episode.setStyleSheet(f"color: {Theme.ACCENT_ALLY}; font-weight: bold; font-family: '{Theme.FONT_HEADER}'; font-size: 14px;")
        
        self.chk_table_mode = QCheckBox(STR_CHK_TABLE_MODE)
        self.chk_table_mode.setChecked(True)
        
        self.btn_popout = QToolButton()
        self.btn_popout.setText(STR_BTN_POPOUT)
        self.btn_popout.clicked.connect(self.popout_requested.emit)
        
        log_tools.addWidget(self.lbl_current_episode)
        log_tools.addStretch()
        log_tools.addWidget(self.chk_table_mode)
        log_tools.addWidget(self.btn_popout)
        log_layout.addLayout(log_tools)
        
        # --- STRUCTURED LIST FEED ---
        self.info_log = QListWidget()
        self.info_log.setStyleSheet(STYLE_LOG_BOX)
        self.info_log.setSelectionMode(QListWidget.NoSelection)
        self.info_log.setWordWrap(True)
        log_layout.addWidget(self.info_log)
        
        # Add to splitter
        self.splitter.addWidget(self.data_container)
        self.splitter.addWidget(self.log_container)
        self.splitter.setSizes([300, 300]) # Example default sizes
        
        layout.addWidget(self.splitter)

    def update_live_data(self, agents, game_map=None):
        """Populates the live agent table."""
        self.table_live.setRowCount(0)
        
        for agent in agents:
            # We filter out non-agent entities. Usually, an agent has standard simulation attrs
            if not agent.get_attribute("is_agent", True): continue
                
            row = self.table_live.rowCount()
            self.table_live.insertRow(row)
            
            # Agent info
            side = str(agent.get_attribute("side", "Unknown"))
            name = getattr(agent, "name", str(agent.id))
            name_item = QTableWidgetItem(f"{name} ({side[0]})")
            
            # Map coordinates
            pos = game_map.get_entity_position(agent.id) if game_map else None
            if pos:
                try:
                    from engine.core.hex_math import HexMath
                    col, r = HexMath.cube_to_offset(pos)
                    pos_str = f"({col},{r})"
                except ImportError:
                    pos_str = ""
            else:
                pos_str = ""
            pos_item = QTableWidgetItem(pos_str)
            
            # Personnel
            hp = str(agent.get_attribute("personnel", 0))
            hp_item = QTableWidgetItem(hp)
            
            # Ammo
            ammo = str(agent.get_attribute("ammo", 0))
            ammo_item = QTableWidgetItem(ammo)
            
            # Suppression
            sup = f"{agent.get_attribute('suppression_level', 0.0):.1f}"
            sup_item = QTableWidgetItem(sup)
            
            # Action Tracking
            action_desc = str(agent.get_attribute("last_action", "IDLE"))
            action_item = QTableWidgetItem(action_desc)
            
            # Set alignment
            for item in [name_item, pos_item, hp_item, ammo_item, sup_item, action_item]:
                item.setTextAlignment(Qt.AlignCenter)
                
            self.table_live.setItem(row, 0, name_item)
            self.table_live.setItem(row, 1, pos_item)
            self.table_live.setItem(row, 2, hp_item)
            self.table_live.setItem(row, 3, ammo_item)
            self.table_live.setItem(row, 4, sup_item)
            self.table_live.setItem(row, 5, action_item)

    def set_current_episode(self, episode):
        self.lbl_current_episode.setText(f"EPISODE: {episode}")
        
    def set_popout_text(self, text):
        self.btn_popout.setText(text)
        
    def is_table_mode(self):
        return self.chk_table_mode.isChecked()

    def log_info(self, message):
        """Adds a structured item to the list feed."""
        timestamp = datetime.datetime.now().strftime(STR_TS_FMT)
        
        # Colorize items contextually based on message content
        fg_color = Theme.TEXT_PRIMARY
        msg_lower = message.lower()
        if any(k in msg_lower for k in ("completed", "finished", "captured", "victory")):
            fg_color = Theme.ACCENT_GOOD
        elif any(k in msg_lower for k in ("error", "failed", "critical")):
            fg_color = Theme.ACCENT_WARN
        elif any(k in msg_lower for k in ("attack", "damage", "fire", "kill", "casualt", "destroyed")):
            fg_color = Theme.ACCENT_ENEMY
        elif any(k in msg_lower for k in ("deploy", "placed", "move", "reposit")):
            fg_color = Theme.ACCENT_ALLY
            
        item = QListWidgetItem(f"[{timestamp}] {message}")
        item.setForeground(QBrush(QColor(fg_color)))
        
        self.info_log.addItem(item)
        self.info_log.scrollToBottom()
        
    def clear(self):
        self.info_log.clear()
