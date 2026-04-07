import datetime
"""
FILE: ui/components/event_log_widget.py
ROLE: The "Black Box" Recorder.

DESCRIPTION:
A split panel showing:
  - Top: Live agent table (name, position, personnel, ammo, suppression, action)
  - Bottom: Scrolling HTML-rendered event log with episode tracker

Messages from log_info() are rendered as HTML so callers can use <b>, <i>, etc.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QToolButton, QCheckBox, QTextEdit, QSplitter,
                              QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from ui.styles.theme import Theme

# --- UI CONFIGURATION -------------------------------------------------------
STR_LBL_LIVE      = "<b>LIVE AGENT DATA</b>"
STR_BTN_POPOUT    = "Pop Out"
STR_CHK_TABLE_MODE = "Table View"
STR_TS_FMT        = "%H:%M:%S"
MAX_LOG_ENTRIES   = 500          # Cap to prevent memory bloat in long sessions

STYLE_LOG_BOX = f"""
    QTextEdit {{
        background-color: {Theme.BG_DEEP};
        color: {Theme.TEXT_PRIMARY};
        font-family: '{Theme.FONT_MONO}';
        font-size: 12px;
        border: 1px solid {Theme.BORDER_STRONG};
        border-radius: 6px;
        padding: 6px;
    }}
"""
STYLE_TABLE = f"""
    QTableWidget {{
        background-color: {Theme.BG_DEEP};
        color: {Theme.TEXT_PRIMARY};
        border: 1px solid {Theme.BORDER_STRONG};
        gridline-color: {Theme.BORDER_SOFT};
    }}
    QHeaderView::section {{
        background-color: {Theme.BG_PANEL};
        color: {Theme.TEXT_DIM};
        font-size: 10px;
        font-weight: bold;
        padding: 4px;
        border: none;
        border-bottom: 1px solid {Theme.BORDER_STRONG};
    }}
"""
# ---------------------------------------------------------------------------

# Map message keywords → HTML color (uses actual Theme hex values)
_COLOR_MAP = [
    (("completed", "finished", "captured", "victory"),   Theme.ACCENT_GOOD),
    (("error", "failed", "critical"),                     Theme.ACCENT_WARN),
    (("attack", "damage", "fire", "kill", "casualt", "destroyed"), Theme.ACCENT_ENEMY),
    (("deploy", "placed", "move", "reposit"),             Theme.ACCENT_ALLY),
]


def _resolve_color(message_lower: str) -> str:
    for keywords, color in _COLOR_MAP:
        if any(k in message_lower for k in keywords):
            return color
    return Theme.TEXT_PRIMARY


class EventLogWidget(QWidget):
    popout_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entry_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Vertical)

        # ── TOP PANE: Live Data Table ────────────────────────────────────────
        data_container = QWidget()
        data_layout = QVBoxLayout(data_container)
        data_layout.setContentsMargins(0, 0, 0, 0)

        hdr = QHBoxLayout()
        self.lbl_live = QLabel(STR_LBL_LIVE)
        self.lbl_live.setTextFormat(Qt.RichText)
        hdr.addWidget(self.lbl_live)
        hdr.addStretch()
        data_layout.addLayout(hdr)

        self.table_live = QTableWidget(0, 6)
        self.table_live.setHorizontalHeaderLabels(
            ["Agent", "Pos", "Personnel", "Ammo", "Suppression", "Action"]
        )
        self.table_live.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_live.verticalHeader().setVisible(False)
        self.table_live.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_live.setSelectionMode(QTableWidget.NoSelection)
        self.table_live.setStyleSheet(STYLE_TABLE)
        data_layout.addWidget(self.table_live)

        # ── BOTTOM PANE: Event Log ───────────────────────────────────────────
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(4)

        # Header row: Episode label + controls
        log_tools = QHBoxLayout()

        self.lbl_current_episode = QLabel("EPISODE: 0")
        self.lbl_current_episode.setStyleSheet(
            f"color: {Theme.ACCENT_ALLY}; font-weight: bold; "
            f"font-family: '{Theme.FONT_HEADER}'; font-size: 13px;"
        )

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

        # HTML-rendering log area
        self.info_log = QTextEdit()
        self.info_log.setReadOnly(True)
        self.info_log.setStyleSheet(STYLE_LOG_BOX)
        self.info_log.setFont(QFont(Theme.FONT_MONO, 11))
        # Enable rich text (default) so HTML in messages renders correctly
        log_layout.addWidget(self.info_log)

        # Assemble splitter
        self.splitter.addWidget(data_container)
        self.splitter.addWidget(log_container)
        self.splitter.setSizes([250, 300])
        layout.addWidget(self.splitter)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_live_data(self, agents, game_map=None):
        """Refresh the live agent status table."""
        self.table_live.blockSignals(True)
        self.table_live.setRowCount(0)

        for agent in agents:
            if not agent.get_attribute("is_agent", True):
                continue

            row = self.table_live.rowCount()
            self.table_live.insertRow(row)

            side = str(agent.get_attribute("side", "?"))
            name = getattr(agent, "name", str(agent.id))
            name_item = QTableWidgetItem(f"{name} ({side[0]})")

            pos = game_map.get_entity_position(agent.id) if game_map else None
            if pos:
                try:
                    from engine.core.hex_math import HexMath
                    col, r = HexMath.cube_to_offset(pos)
                    pos_str = f"({col},{r})"
                except Exception:
                    pos_str = ""
            else:
                pos_str = ""

            hp     = str(agent.get_attribute("personnel", 0))
            ammo   = str(agent.get_attribute("ammo", 0))
            sup    = f"{agent.get_attribute('suppression_level', 0.0):.1f}"
            action = str(agent.get_attribute("last_action", "IDLE"))

            items = [
                QTableWidgetItem(name_item.text()),
                QTableWidgetItem(pos_str),
                QTableWidgetItem(hp),
                QTableWidgetItem(ammo),
                QTableWidgetItem(sup),
                QTableWidgetItem(action),
            ]
            for col_idx, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table_live.setItem(row, col_idx, item)

        self.table_live.blockSignals(False)

    def set_current_episode(self, episode: int):
        """Update the episode counter label."""
        self.lbl_current_episode.setText(f"EPISODE: {episode}")

    def set_popout_text(self, text: str):
        self.btn_popout.setText(text)

    def is_table_mode(self) -> bool:
        return self.chk_table_mode.isChecked()

    def log_info(self, message: str):
        """
        Append a timestamped HTML entry to the event log.
        Message may contain HTML tags — they are rendered correctly.
        Color is chosen automatically based on message keywords.
        """
        timestamp = datetime.datetime.now().strftime(STR_TS_FMT)
        color = _resolve_color(message.lower())

        html = (
            f"<span style='color:{Theme.TEXT_DIM};'>[{timestamp}]</span> "
            f"<span style='color:{color};'>{message}</span>"
        )
        self.info_log.append(html)

        # Cap log entries to prevent unbounded memory growth
        self._entry_count += 1
        if self._entry_count > MAX_LOG_ENTRIES:
            cursor = self.info_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()  # remove the trailing newline

        # Auto-scroll to bottom
        sb = self.info_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self):
        """Clear all log entries and reset the entry counter."""
        self.info_log.clear()
        self._entry_count = 0
