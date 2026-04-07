from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QTableWidget, QHeaderView, QHBoxLayout
from PyQt5.QtCore import Qt
from ui.styles.theme import Theme

# --- UI CONFIGURATION ---
# Default Header Styling
STYLE_TACTICAL_HEADER = f"color: {Theme.ACCENT_ALLY}; margin-bottom: 10px;"

# Card Styling Template
STYLE_TACTICAL_CARD = """
    QGroupBox {{
        border: 1px solid {border};
        margin-top: 10px;
        font-weight: bold;
        color: {accent};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }}
"""

# Table Styling
STYLE_TACTICAL_TABLE = f"""
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
"""

# Log Item Styling & Formats
STR_TS_FMT = "[{timestamp}]"
STYLE_LOG_TS = f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;"
STYLE_LOG_MSG_FMT = "color: {color}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;"
# -------------------------

class TacticalHeader(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
        self.setStyleSheet(STYLE_TACTICAL_HEADER)

class TacticalCard(QGroupBox):
    def __init__(self, title="", accent_color=None, parent=None):
        super().__init__(title, parent)
        accent = accent_color if accent_color else Theme.TEXT_PRIMARY
        self.setStyleSheet(STYLE_TACTICAL_CARD.format(border=Theme.BORDER_STRONG, accent=accent))
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
        self.setStyleSheet(STYLE_TACTICAL_TABLE)

class TacticalLogItem(QWidget):
    def __init__(self, timestamp, message, color=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        ts_lbl = QLabel(STR_TS_FMT.format(timestamp=timestamp))
        ts_lbl.setStyleSheet(STYLE_LOG_TS)
        
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        color = color if color else Theme.TEXT_PRIMARY
        msg_lbl.setStyleSheet(STYLE_LOG_MSG_FMT.format(color=color))
        
        layout.addWidget(ts_lbl)
        layout.addWidget(msg_lbl, 1)
