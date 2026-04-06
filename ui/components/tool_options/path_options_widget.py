from PyQt5.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QComboBox, QHBoxLayout, QToolButton
from ui.styles.theme import Theme

class PathOptionsWidget(QWidget):
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
        header = QLabel("<b>PATH CONFIGURATION</b>")
        header.setStyleSheet(f"color: {Theme.ACCENT_ALLY}; font-size: 14px; margin-bottom: 2px;")
        layout.addRow(header)

        label_instr = QLabel("Draw tactical lines, roads, or borders.")
        label_instr.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin-bottom: 10px;")
        layout.addRow(label_instr)
        
        # Name Input
        if not hasattr(self.state, 'path_opt_name'): self.state.path_opt_name = ""
        path_name_edit = QLineEdit(self.state.path_opt_name)
        path_name_edit.setPlaceholderText("Optional: Custom Name")
        path_name_edit.textChanged.connect(lambda t: setattr(self.state, 'path_opt_name', t))
        
        # Path Type Dropdown
        path_type_combo = QComboBox()
        default_items = ["Canal", "Road"] if app_mode == "terrain" else ["Border", "Supply Line"]
        customs = getattr(self.state, 'custom_path_types', [])
        all_items = default_items + customs
        path_type_combo.addItems(all_items)
        
        def on_path_type_change(t):
            self.state.path_opt_type = t
            defaults = {"Canal": "#00FFFF", "Road": "#8B4513", "Border": "#FF0000", "Supply Line": "#00FF00"}
            defaults.update(getattr(self.state, 'custom_path_colors', {}))
            if t in defaults:
                self.state.path_opt_color = defaults[t]
        
        path_type_combo.currentTextChanged.connect(on_path_type_change)
        
        current_t = self.state.path_opt_type if hasattr(self.state, 'path_opt_type') else path_type_combo.itemText(0)
        path_type_combo.setCurrentText(current_t)
        on_path_type_change(current_t)
        
        # Path Mode Dropdown
        if not hasattr(self.state, 'path_mode'): self.state.path_mode = "Center-to-Center"
        path_mode_combo = QComboBox()
        path_mode_combo.addItems(["Center-to-Center", "Edge-Aligned"])
        path_mode_combo.setCurrentText(self.state.path_mode)
        path_mode_combo.currentTextChanged.connect(lambda t: setattr(self.state, 'path_mode', t))
        
        layout.addRow("Name:", path_name_edit)
        
        h_path = QHBoxLayout()
        h_path.addWidget(path_type_combo)
        btn_new_p = QToolButton()
        btn_new_p.setText("+")
        btn_new_p.setToolTip("Create New Path Type")
        btn_new_p.clicked.connect(self.mw.prompt_new_path_type)
        h_path.addWidget(btn_new_p)
        
        layout.addRow("Path Type:", h_path)
        layout.addRow("Draw Mode:", path_mode_combo)
        layout.addRow(QLabel("<i>Right Click to Commit</i>"))
