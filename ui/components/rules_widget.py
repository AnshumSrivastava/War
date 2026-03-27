"""
FILE: ui/widgets/rules_widget.py
ROLE: The "Rulebook" Editor.
DESCRIPTION: A panel for modifying simulation-wide constants like learning rate, weapon lethality, and movement speeds.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, 
                             QLabel, QPushButton, QMessageBox)
from engine.state.global_state import GlobalState

class RulesWidget(QWidget):
    """
    Widget to configure Scenario Rules.
    """
    def __init__(self, parent=None, state: GlobalState = None):
        super().__init__(parent)
        self.state = state if state else GlobalState()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.form = QFormLayout()
        
        self.sb_max_agents = QSpinBox()
        self.sb_max_agents.setRange(1, 10)
        self.sb_max_agents.setValue(3)
        self.form.addRow("Max Agents per Hex:", self.sb_max_agents)
        
        self.sb_max_turns = QSpinBox()
        self.sb_max_turns.setRange(1, 1000)
        self.sb_max_turns.setValue(30)
        self.form.addRow("Max Turns:", self.sb_max_turns)
        
        self.sb_atk_force = QSpinBox()
        self.sb_atk_force.setRange(1, 100)
        self.sb_atk_force.setValue(10)
        self.form.addRow("Attacker Max Force:", self.sb_atk_force)

        self.sb_def_force = QSpinBox()
        self.sb_def_force.setRange(1, 100)
        self.sb_def_force.setValue(10)
        self.form.addRow("Defender Max Force:", self.sb_def_force)
        
        layout.addLayout(self.form)
        
        btn_save = QPushButton("Apply Rules")
        btn_save.clicked.connect(self.save_rules)
        layout.addWidget(btn_save)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def refresh(self):
        """Load rules from active scenario."""
        if not self.state.map or not self.state.map.active_scenario:
            self.setEnabled(False)
            return
            
        self.setEnabled(True)
        rules = self.state.map.active_scenario.rules
        
        self.sb_max_agents.setValue(rules.get("max_agents_per_hex", 3))
        self.sb_max_turns.setValue(rules.get("max_turns", 30))
        self.sb_atk_force.setValue(rules.get("attacker_max_force", 10))
        self.sb_def_force.setValue(rules.get("defender_max_force", 10))
        
    def save_rules(self):
        if not self.state.map or not self.state.map.active_scenario:
            return
            
        rules = self.state.map.active_scenario.rules
        rules["max_agents_per_hex"] = self.sb_max_agents.value()
        rules["max_turns"] = self.sb_max_turns.value()
        rules["attacker_max_force"] = self.sb_atk_force.value()
        rules["defender_max_force"] = self.sb_def_force.value()
        
        QMessageBox.information(self, "Success", "Scenario rules updated.")
