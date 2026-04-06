from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QSlider, QDialogButtonBox, QHBoxLayout
from PyQt5.QtCore import Qt
from ui.styles.theme import Theme

class AutoSplitDialog(QDialog):
    """
    Dialog for configuring Auto-Split parameters:
    - Direction: Vertical, Horizontal, Diagonal
    - Ratio: 10% - 90%
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto-Split Configuration")
        self.resize(300, 200)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Theme.BG_SURFACE}; color: {Theme.TEXT_PRIMARY}; }}
            QLabel {{ color: {Theme.TEXT_PRIMARY}; }}
            QComboBox {{ background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_PRIMARY}; padding: 5px; }}
            QSlider::groove:horizontal {{ height: 6px; background: {Theme.BG_INPUT}; }}
            QSlider::handle:horizontal {{ background: {Theme.ACCENT_ALLY}; width: 14px; margin: -4px 0; border-radius: 7px; }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Direction
        layout.addWidget(QLabel("Split Direction:"))
        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["Vertical", "Horizontal", "Diagonal (TL-BR)", "Diagonal (BL-TR)"])
        layout.addWidget(self.dir_combo)
        
        # Ratio
        layout.addWidget(QLabel("Split Ratio (%):"))
        self.ratio_slider = QSlider(Qt.Horizontal)
        self.ratio_slider.setRange(10, 90)
        self.ratio_slider.setValue(50)
        self.ratio_slider.setTickInterval(10)
        self.ratio_slider.setTickPosition(QSlider.TicksBelow)
        
        self.ratio_label = QLabel("50%")
        self.ratio_label.setAlignment(Qt.AlignCenter)
        self.ratio_slider.valueChanged.connect(lambda v: self.ratio_label.setText(f"{v}%"))
        
        layout.addWidget(self.ratio_slider)
        layout.addWidget(self.ratio_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_values(self):
        return {
            "direction": self.dir_combo.currentText(),
            "ratio": self.ratio_slider.value() / 100.0
        }
