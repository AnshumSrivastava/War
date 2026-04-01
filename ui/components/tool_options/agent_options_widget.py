from PyQt5.QtWidgets import QWidget, QFormLayout, QLabel, QRadioButton, QButtonGroup, QComboBox, QHBoxLayout, QSpinBox
from ui.styles.theme import Theme

class AgentOptionsWidget(QWidget):
    def __init__(self, main_window, state):
        super().__init__()
        self.mw = main_window
        self.state = state
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)

        app_mode = getattr(self.state, "app_mode", "terrain")

        # Header Label
        header = QLabel("<b>AGENT DEPLOYMENT</b>")
        header.setStyleSheet("color: #3daee9; font-size: 14px; margin-bottom: 2px;")
        layout.addRow(header)

        label_instr = QLabel("Place individual units on the battlefield.")
        label_instr.setStyleSheet("color: #777777; font-size: 11px; margin-bottom: 10px;")
        layout.addRow(label_instr)
        
        # Side Selection
        if not hasattr(self.state, 'place_opt_side'): self.state.place_opt_side = "Attacker"
        
        side_widget = QWidget()
        side_layout = QHBoxLayout(side_widget)
        side_layout.setContentsMargins(0, 0, 0, 0)
        
        radio_attacker = QRadioButton("Attacker")
        radio_defender = QRadioButton("Defender")
        side_group = QButtonGroup(side_widget)
        side_group.addButton(radio_attacker)
        side_group.addButton(radio_defender)
        
        side_layout.addWidget(radio_attacker)
        side_layout.addWidget(radio_defender)
        
        if app_mode == "agents":
            active_side = getattr(self.state, "active_scenario_side", "Attacker")
            if active_side == "Combined":
                side_widget.setEnabled(True)
                if self.state.place_opt_side == "Defender":
                    radio_defender.setChecked(True)
                else:
                    radio_attacker.setChecked(True)
            else:
                side_widget.setEnabled(False) # Lock to current tab's side
                self.state.place_opt_side = active_side
                if active_side == "Defender":
                    radio_defender.setChecked(True)
                else:
                    radio_attacker.setChecked(True)
        else:
            side_widget.setEnabled(True)
            if self.state.place_opt_side == "Defender":
                radio_defender.setChecked(True)
            else:
                radio_attacker.setChecked(True)
        
        # Name Dropdown
        if not hasattr(self.state, 'place_opt_name'): self.state.place_opt_name = ""
        name_combo = QComboBox()
        
        def update_names():
            side = "Attacker" if radio_attacker.isChecked() else "Defender"
            self.state.place_opt_side = side
            
            name_combo.clear()
            
            keys = []
            if hasattr(self.state, 'data_controller') and side in self.state.data_controller.agent_types:
                keys = sorted(list(self.state.data_controller.agent_types[side].keys()))
            
            if keys:
                name_combo.addItems(keys)
            else:
                name_combo.addItem("No Agents Found")
            
            if self.state.place_opt_name in keys:
                 name_combo.setCurrentText(self.state.place_opt_name)
            elif keys:
                 self.state.place_opt_name = keys[0]

        radio_attacker.toggled.connect(update_names)
        radio_defender.toggled.connect(update_names)
        name_combo.currentTextChanged.connect(lambda t: setattr(self.state, 'place_opt_name', t))

        update_names()

        # Agent Personnel
        if not hasattr(self.state, 'place_opt_personnel'): self.state.place_opt_personnel = 100 
        pers_spin = QSpinBox()
        pers_spin.setRange(0, 1000)
        pers_spin.setValue(self.state.place_opt_personnel) 
        pers_spin.valueChanged.connect(lambda v: setattr(self.state, 'place_opt_personnel', v)) 
        
        layout.addRow("Side:", side_widget)
        layout.addRow("Agent Type:", name_combo)
        layout.addRow("Personnel:", pers_spin)
