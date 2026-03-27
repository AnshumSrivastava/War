from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QSlider, QDialogButtonBox, QHBoxLayout
from PyQt5.QtCore import Qt

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
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QComboBox { background-color: #404040; color: #ffffff; padding: 5px; }
            QSlider::groove:horizontal { height: 6px; background: #404040; }
            QSlider::handle:horizontal { background: #3daee9; width: 14px; margin: -4px 0; border-radius: 7px; }
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
