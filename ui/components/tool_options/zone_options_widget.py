from PyQt5.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QComboBox, QHBoxLayout, QToolButton
from PyQt5.QtCore import Qt
from ui.styles.theme import Theme

class ZoneOptionsWidget(QWidget):
    def __init__(self, main_window, state):
        super().__init__(main_window)
        self.mw = main_window
        self.state = state
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        app_mode = getattr(self.state, "app_mode", "terrain")
        
        # Header Label for Intuition
        header = QLabel("ZONE CONFIGURATION")
        header.setObjectName("InspectorLabel")
        layout.addRow(header)

        # Active Side Banner
        if "areas" in app_mode:
            side = getattr(self.state, "active_scenario_side", "Attacker")
            color = Theme.ACCENT_ENEMY if side == "Attacker" else Theme.ACCENT_ALLY
            banner = QLabel(f"Deploying for: {side.upper()}")
            banner.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; padding: 4px; border-radius: 4px;")
            banner.setAlignment(Qt.AlignCenter)
            layout.addRow(banner)

        label_instr = QLabel("Define clickable regions on the map. (Right-click to finish)")
        label_instr.setStyleSheet("color: #777777; font-size: 11px; margin-bottom: 10px;")
        layout.addRow(label_instr)
        
        # Name Input
        if not hasattr(self.state, 'zone_opt_name'): self.state.zone_opt_name = ""
        name_edit = QLineEdit(self.state.zone_opt_name)
        name_edit.setPlaceholderText("Optional: Custom Name")
        name_edit.textChanged.connect(lambda t: setattr(self.state, 'zone_opt_name', t))
        
        name_label = QLabel("Zone Name")
        name_label.setObjectName("InspectorLabel")
        layout.addRow(name_label, name_edit)

        # Type Dropdown
        type_combo = QComboBox()
        if app_mode == "terrain":
            type_combo.addItems(["Terrain"])
        elif "areas" in app_mode:
            active_side = getattr(self.state, "active_scenario_side", "Attacker")
            if active_side == "Attacker":
                type_combo.addItems(["Attacker Area", "Obstacle"])
            else:
                type_combo.addItems(["Defender Area", "Goal Area", "Obstacle"])
        else:
            type_combo.addItems(["Attacker Area", "Defender Area", "Goal Area", "Obstacle"])
            
        curr_type = getattr(self.state, 'zone_opt_type', "")
        if curr_type and type_combo.findText(curr_type) >= 0:
            type_combo.setCurrentText(curr_type)
        
        subtype_combo = QComboBox()
        
        def update_subtypes(idx):
            t = type_combo.currentText()
            self.state.zone_opt_type = t
            subtype_combo.clear()
            
            if app_mode == "terrain":
                keys = self.state.terrain_controller.get_available_terrains()
                display_keys = sorted([k.title() for k in keys])
                subtype_combo.addItems(display_keys)
            else:
                items = []
                if "Attacker" in t:
                    if hasattr(self.state, 'data_controller'):
                        items = sorted(list(self.state.data_controller.zone_types.get("Attacker", {}).keys()))
                elif "Defender" in t:
                    if hasattr(self.state, 'data_controller'):
                        items = sorted(list(self.state.data_controller.zone_types.get("Defender", {}).keys()))
                elif t == "Goal Area":
                    items = ["Goal Area"]
                elif t == "Obstacle":
                    if hasattr(self.state, 'data_controller'):
                        items = sorted(list(self.state.data_controller.obstacle_types.keys()))
                
                if items:
                    subtype_combo.addItems(items)
                else:
                    subtype_combo.addItem("None Found")

            self.state.zone_opt_subtype = subtype_combo.currentText()
        
        type_combo.currentIndexChanged.connect(update_subtypes)
        subtype_combo.currentTextChanged.connect(lambda t: setattr(self.state, 'zone_opt_subtype', t))
        
        update_subtypes(0)
        
        type_label = QLabel("Zone Type")
        type_label.setObjectName("InspectorLabel")
        layout.addRow(type_label, type_combo)
        
        subtype_label = QLabel("Sub-Type Selection")
        subtype_label.setObjectName("InspectorLabel")
        layout.addRow(subtype_label, subtype_combo)
        
        if app_mode == "terrain":
            h_layout = QHBoxLayout()
            h_layout.addWidget(subtype_combo)
            btn_new = QToolButton()
            btn_new.setText("+")
            btn_new.setToolTip("Create New Terrain Type")
            btn_new.clicked.connect(self.mw.prompt_new_terrain)
            h_layout.addWidget(btn_new)
            layout.addRow("Subtype/ID:", h_layout)
        else:
            layout.addRow("Subtype/ID:", subtype_combo)
            
        layout.addRow(QLabel("<i>Right Click to Commit</i>"))
