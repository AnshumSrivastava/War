import os
"""
FILE: ui/widgets/report_widget.py
ROLE: Mission After-Action Report (AAR).
DESCRIPTION: Generates a summary of the simulation results, including casualties, ammo spent, and objective status.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt
from ui.styles.theme import Theme
from ui.components.themed_widgets import TacticalCard, TacticalHeader

# --- UI CONFIGURATION ---
# Titles & Headings
STR_TITLE_AAR = "AFTER-ACTION REPORT (AAR)"
STR_LBL_CASUALTIES = "CASUALTIES"
STR_LBL_AMMO_SPENT = "AMMO SPENT"
STR_LBL_OBJECTIVE = "OBJECTIVE"

# Result & Status Texts
STR_STATUS_COMPLETED = "COMPLETED"
STR_STATUS_INVOLVED = "INVOLVED"
STR_STATUS_NA = "N/A"
STR_STATUS_ZERO = "0"
STR_STATUS_INITIALIZE = "INITIALIZE MISSION TO GENERATE TACTICAL REPORT"
STR_FOOTER_END = "/// END OF REPORT ///"

# Card Titles
STR_CARD_ATK_LOG = "ATTACKER PERFORMANCE LOG"
STR_CARD_DEF_LOG = "DEFENDER PERFORMANCE LOG"

# Formatting Templates
STR_LOG_ENTRY_FMT = "• UNIT {agent_id}: {type} AT {location}"

# Stylesheets
STYLE_RIBBON_FRAME = f"background-color: {Theme.BG_SURFACE}; border: 1px solid {Theme.BORDER_STRONG}; border-left: 4px solid {Theme.ACCENT_WARN};"
STYLE_RIBBON_LABEL = f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_HEADER}'; font-size: 10px; letter-spacing: 1px;"
STYLE_RIBBON_VALUE = f"color: {Theme.ACCENT_ALLY}; font-family: '{Theme.FONT_MONO}'; font-size: 18px; font-weight: bold;"
STYLE_PLACEHOLDER = f"color: {Theme.TEXT_DIM}; font-style: italic; font-size: 11px;"
STYLE_LOG_LABEL = f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;"
# -------------------------

class ReportWidget(QWidget):
    """
    Military-style After Action Report (AAR) Viewer.
    Uses native Tactical Cards instead of HTML for a light, consistent feel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        self.setStyleSheet(f"background-color: {Theme.BG_DEEP};")
        
        # 1. Header
        self.header = TacticalHeader(STR_TITLE_AAR)
        self.layout.addWidget(self.header)
        
        # 2. Summary Ribbon (High-Visibility Stats)
        self.ribbon_frame = QFrame()
        self.ribbon_frame.setStyleSheet(STYLE_RIBBON_FRAME)
        self.ribbon_layout = QHBoxLayout(self.ribbon_frame)
        self.ribbon_layout.setContentsMargins(20, 10, 20, 10)
        
        self.ribbon_stat_cas = self._create_ribbon_stat(STR_LBL_CASUALTIES, STR_STATUS_ZERO)
        self.ribbon_stat_ammo = self._create_ribbon_stat(STR_LBL_AMMO_SPENT, STR_STATUS_ZERO)
        self.ribbon_stat_obj = self._create_ribbon_stat(STR_LBL_OBJECTIVE, STR_STATUS_NA)
        
        self.ribbon_layout.addWidget(self.ribbon_stat_cas)
        self.ribbon_layout.addStretch()
        self.ribbon_layout.addWidget(self.ribbon_stat_ammo)
        self.ribbon_layout.addStretch()
        self.ribbon_layout.addWidget(self.ribbon_stat_obj)
        
        self.layout.addWidget(self.ribbon_frame)
        
        # 3. Scroll Area for Detailed Reports
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        self.container = QWidget()
        self.report_layout = QVBoxLayout(self.container)
        self.report_layout.setContentsMargins(0, 10, 0, 0)
        self.report_layout.setSpacing(15)
        self.report_layout.addStretch()
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        
        self.clear_report()

    def _create_ribbon_stat(self, label, value):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        lvl = QLabel(label)
        lvl.setStyleSheet(STYLE_RIBBON_LABEL)
        vvl = QLabel(value)
        vvl.setStyleSheet(STYLE_RIBBON_VALUE)
        layout.addWidget(lvl)
        layout.addWidget(vvl)
        
        if not hasattr(self, 'value_labels'): self.value_labels = {}
        self.value_labels[label] = vvl
        
        return container

    def clear_report(self):
        """Reset the AAR empty state."""
        while self.report_layout.count() > 1:
            item = self.report_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        placeholder = QLabel(STR_STATUS_INITIALIZE)
        placeholder.setStyleSheet(STYLE_PLACEHOLDER)
        placeholder.setAlignment(Qt.AlignCenter)
        self.report_layout.insertWidget(0, placeholder)

    def generate_report(self, events_history, total_episodes):
        """Ingest events and build a native card-based report."""
        self.clear_report()
        # Remove placeholder
        item = self.report_layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()
        
        # Calculate Stats
        casualties = 0
        ammo_spent = 0
        attacker_events = []
        defender_events = []
        
        for evt in events_history:
            if evt.get('type') == 'fire':
                ammo_spent += 1
                if evt.get('hit'):
                    casualties += 1 # Rough estimate for report
            
            aid = str(evt.get('agent_id', ''))
            if 'attacker' in aid.lower(): attacker_events.append(evt)
            else: defender_events.append(evt)

        # Update Ribbon
        self.value_labels[STR_LBL_CASUALTIES].setText(str(casualties))
        self.value_labels[STR_LBL_AMMO_SPENT].setText(str(ammo_spent * 25)) # Assuming 25 rounds/shot
        self.value_labels[STR_LBL_OBJECTIVE].setText(STR_STATUS_COMPLETED if casualties > 0 else STR_STATUS_INVOLVED)
        
        # Add Segmented Cards
        if attacker_events:
            a_card = TacticalCard(STR_CARD_ATK_LOG, accent_color=Theme.ACCENT_ALLY)
            for ev in attacker_events[:20]: # Cap at 20 for readability
                loc = ev.get('to') or ev.get('source_hex')
                lbl = QLabel(STR_LOG_ENTRY_FMT.format(
                    agent_id=ev.get('agent_id'), 
                    type=ev.get('type','ACTION').upper(), 
                    location=loc
                ))
                lbl.setStyleSheet(STYLE_LOG_LABEL)
                a_card.addWidget(lbl)
            self.report_layout.insertWidget(0, a_card)
            
        if defender_events:
            d_card = TacticalCard(STR_CARD_DEF_LOG, accent_color=Theme.ACCENT_ENEMY)
            for ev in defender_events[:20]:
                loc = ev.get('to') or ev.get('source_hex')
                lbl = QLabel(STR_LOG_ENTRY_FMT.format(
                    agent_id=ev.get('agent_id'), 
                    type=ev.get('type','ACTION').upper(), 
                    location=loc
                ))
                lbl.setStyleSheet(STYLE_LOG_LABEL)
                d_card.addWidget(lbl)
            self.report_layout.insertWidget(1, d_card)

        self.report_layout.insertWidget(self.report_layout.count() - 1, QLabel(STR_FOOTER_END))
