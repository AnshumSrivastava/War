import datetime
"""
FILE: ui/widgets/event_log_widget.py
ROLE: The "Black Box" Recorder.
DESCRIPTION: A scrolling text area that keeps a complete history of every command, hit, and death in the simulation.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QCheckBox, QTextEdit
from PyQt5.QtCore import pyqtSignal

class EventLogWidget(QWidget):
    popout_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Log Toolbar
        log_tools = QHBoxLayout()
        log_tools.addWidget(QLabel("<b>EVENT LOG</b>"))
        
        self.btn_font_up = QToolButton()
        self.btn_font_up.setText("A+")
        self.btn_font_up.clicked.connect(self.increase_log_font)
        
        self.btn_font_down = QToolButton()
        self.btn_font_down.setText("A-")
        self.btn_font_down.clicked.connect(self.decrease_log_font)
        
        self.btn_popout = QToolButton()
        self.btn_popout.setText("Pop Out")
        self.btn_popout.clicked.connect(self.popout_requested.emit)
        
        self.chk_table_mode = QCheckBox("Table View")
        self.chk_table_mode.setChecked(True) # Default to Table
        
        log_tools.addStretch()
        log_tools.addWidget(self.chk_table_mode)
        log_tools.addWidget(self.btn_popout)
        log_tools.addWidget(self.btn_font_down)
        log_tools.addWidget(self.btn_font_up)
        
        layout.addLayout(log_tools)
        
        self.info_log = QTextEdit()
        self.info_log.setReadOnly(True)
        self.info_log.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #dcdcdc;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
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
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.info_log.append(f"<span style='color: #888888;'>[{timestamp}]</span> {message}")
        self.info_log.verticalScrollBar().setValue(self.info_log.verticalScrollBar().maximum())
        
    def clear(self):
        self.info_log.clear()
