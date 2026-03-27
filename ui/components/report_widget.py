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
        self.header = TacticalHeader("AFTER-ACTION REPORT (AAR)")
        self.layout.addWidget(self.header)
        
        # 2. Summary Ribbon (High-Visibility Stats)
        self.ribbon_frame = QFrame()
        self.ribbon_frame.setStyleSheet(f"background-color: {Theme.BG_SURFACE}; border: 1px solid {Theme.BORDER_STRONG}; border-left: 4px solid {Theme.ACCENT_WARN};")
        self.ribbon_layout = QHBoxLayout(self.ribbon_frame)
        self.ribbon_layout.setContentsMargins(20, 10, 20, 10)
        
        self.ribbon_stat_cas = self._create_ribbon_stat("CASUALTIES", "0")
        self.ribbon_stat_ammo = self._create_ribbon_stat("AMMO SPENT", "0")
        self.ribbon_stat_obj = self._create_ribbon_stat("OBJECTIVE", "N/A")
        
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
        lvl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-family: '{Theme.FONT_HEADER}'; font-size: 10px; letter-spacing: 1px;")
        vvl = QLabel(value)
        vvl.setStyleSheet(f"color: {Theme.ACCENT_ALLY}; font-family: '{Theme.FONT_MONO}'; font-size: 18px; font-weight: bold;")
        layout.addWidget(lvl)
        layout.addWidget(vvl)
        
        # Save reference for updates
        if not hasattr(self, 'value_labels'): self.value_labels = {}
        self.value_labels[label] = vvl
        
        return container

    def clear_report(self):
        """Reset the AAR empty state."""
        while self.report_layout.count() > 1:
            item = self.report_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        placeholder = QLabel("INITIALIZE MISSION TO GENERATE TACTICAL REPORT")
        placeholder.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-style: italic; font-size: 11px;")
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
            
            # Simple sorting by agent_id for now (usually defined in state)
            aid = str(evt.get('agent_id', ''))
            if 'attacker' in aid.lower(): attacker_events.append(evt)
            else: defender_events.append(evt)

        # Update Ribbon
        self.value_labels["CASUALTIES"].setText(str(casualties))
        self.value_labels["AMMO SPENT"].setText(str(ammo_spent * 25)) # Assuming 25 rounds/shot
        self.value_labels["OBJECTIVE"].setText("COMPLETED" if casualties > 0 else "INVOLVED")
        
        # Add Segmented Cards
        if attacker_events:
            a_card = TacticalCard("ATTACKER PERFORMANCE LOG", accent_color=Theme.ACCENT_ALLY)
            for ev in attacker_events[:20]: # Cap at 20 for readability
                lbl = QLabel(f"• UNIT {ev.get('agent_id')}: {ev.get('type','ACTION').upper()} AT {ev.get('to') or ev.get('source_hex')}")
                lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
                a_card.addWidget(lbl)
            self.report_layout.insertWidget(0, a_card)
            
        if defender_events:
            d_card = TacticalCard("DEFENDER PERFORMANCE LOG", accent_color=Theme.ACCENT_ENEMY)
            for ev in defender_events[:20]:
                lbl = QLabel(f"• UNIT {ev.get('agent_id')}: {ev.get('type','ACTION').upper()} AT {ev.get('to') or ev.get('source_hex')}")
                lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-family: '{Theme.FONT_MONO}'; font-size: 10px;")
                d_card.addWidget(lbl)
            self.report_layout.insertWidget(1, d_card)

        self.report_layout.insertWidget(self.report_layout.count() - 1, QLabel("/// END OF REPORT ///"))
