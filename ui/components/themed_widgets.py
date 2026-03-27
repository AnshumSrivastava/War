from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QTableWidget, QHeaderView, QHBoxLayout
from PyQt5.QtCore import Qt
from ui.styles.theme import Theme

class TacticalHeader(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
        self.setStyleSheet(f"color: {Theme.ACCENT_ALLY}; margin-bottom: 10px;")

class TacticalCard(QGroupBox):
    def __init__(self, title="", accent_color=None, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {Theme.BORDER_STRONG};
                margin-top: 10px;
                font-weight: bold;
                color: {accent_color if accent_color else Theme.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
        """)
        self._layout = QVBoxLayout(self)
    
    def addWidget(self, widget, stretch=0):
        self._layout.addWidget(widget, stretch)
        
    def addLayout(self, layout):
        self._layout.addLayout(layout)

class TacticalTable(QTableWidget):
    def __init__(self, columns, parent=None):
        super().__init__(0, len(columns), parent)
        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_DEEP};
                gridline-color: {Theme.BORDER_STRONG};
                color: {Theme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.TEXT_DIM};
                padding: 5px;
                border: 1px solid {Theme.BORDER_STRONG};
            }}
        """)

class TacticalLogItem(QWidget):
    def __init__(self, timestamp, message, color=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        ts_lbl = QLabel(f"[{timestamp}]")
        ts_lbl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
        
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        color = color if color else Theme.TEXT_PRIMARY
        msg_lbl.setStyleSheet(f"color: {color}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
        
        layout.addWidget(ts_lbl)
        layout.addWidget(msg_lbl, 1)
