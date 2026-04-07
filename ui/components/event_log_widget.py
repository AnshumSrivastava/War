import datetime
"""
FILE: ui/widgets/event_log_widget.py
ROLE: The "Black Box" Recorder.
DESCRIPTION: A scrolling text area that keeps a complete history of every command, hit, and death in the simulation.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QCheckBox, QTextEdit
from PyQt5.QtCore import pyqtSignal
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
    QTextEdit {{
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
        
        # Log Toolbar
        log_tools = QHBoxLayout()
        log_tools.addWidget(QLabel(STR_LBL_EVENT_LOG))
        
        self.btn_font_up = QToolButton()
        self.btn_font_up.setText(STR_BTN_FONT_UP)
        self.btn_font_up.clicked.connect(self.increase_log_font)
        
        self.btn_font_down = QToolButton()
        self.btn_font_down.setText(STR_BTN_FONT_DOWN)
        self.btn_font_down.clicked.connect(self.decrease_log_font)
        
        self.btn_popout = QToolButton()
        self.btn_popout.setText(STR_BTN_POPOUT)
        self.btn_popout.clicked.connect(self.popout_requested.emit)
        
        self.chk_table_mode = QCheckBox(STR_CHK_TABLE_MODE)
        self.chk_table_mode.setChecked(True) # Default to Table
        
        log_tools.addStretch()
        log_tools.addWidget(self.chk_table_mode)
        log_tools.addWidget(self.btn_popout)
        log_tools.addWidget(self.btn_font_down)
        log_tools.addWidget(self.btn_font_up)
        
        layout.addLayout(log_tools)
        
        self.info_log = QTextEdit()
        self.info_log.setReadOnly(True)
        # Apply a sleek, authentic dark terminal aesthetic
        self.info_log.setStyleSheet(STYLE_LOG_BOX)
        layout.addWidget(self.info_log)

    def increase_log_font(self):
        self.info_log.zoomIn(1)

    def decrease_log_font(self):
        self.info_log.zoomOut(1)
        
    def set_popout_text(self, text):
        self.btn_popout.setText(text)
        
    def is_table_mode(self):
        return self.chk_table_mode.isChecked()

    def log_info(self, message):
        timestamp = datetime.datetime.now().strftime(STR_TS_FMT)
        self.info_log.append(STR_LOG_MSG_FMT.format(color=Theme.TEXT_DIM, timestamp=timestamp, message=message))
        self.info_log.verticalScrollBar().setValue(self.info_log.verticalScrollBar().maximum())
        
    def clear(self):
        self.info_log.clear()
