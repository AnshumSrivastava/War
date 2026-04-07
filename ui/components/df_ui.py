import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QFormLayout, QComboBox,
    QSpinBox
)
from PyQt5.QtCore import Qt
from ui.styles.theme import Theme

# --- UI CONFIGURATION ---
# Titles & Headings
STR_WIN_TITLE = "Direct Fire Order"
STR_BTN_EXECUTE = "EXECUTE FIRE ORDER"

# Form Labels
STR_LBL_SIDE = "Agent Side:"
STR_LBL_FIRING_UNIT = "Firing Unit:"
STR_LBL_FIRE_LOC = "Fire Location:"
STR_LBL_TARGET = "Target Agent:"
STR_LBL_DURATION = "Duration:"
STR_LBL_ROF = "Rate of Fire:"
STR_LBL_WEAPON = "Weapon Type:"

# Suffixes
STR_SUFFIX_MIN = " min"
STR_SUFFIX_RDS = " rds"

# Default List Items
LIST_SIDES = ["Blue", "Red"]
LIST_UNITS = ["Unit 1", "Unit 2", "Unit 3"]
LIST_LOCATIONS = ["Firebase 1", "Firebase 2", "Firebase 3"]
LIST_TARGETS = ["Target A", "Target B", "Target C"]
LIST_WEAPONS = ["Rifle", "Machine Gun", "Tank Gun", "ATGM"]

# Stylesheets
STYLE_EXECUTE_BTN = f"""
    QPushButton {{
        background-color: {Theme.ACCENT_GOOD};
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 6px;
    }}
    QPushButton:hover {{
        background-color: {Theme.ACCENT_GOOD};
        filter: brightness(0.85);
    }}
"""
# -------------------------

class DirectFireSimpleUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(STR_WIN_TITLE)
        self.setGeometry(400, 200, 420, 420)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # 1. Agent Side
        self.agent_side = QComboBox()
        self.agent_side.addItems(LIST_SIDES)

        # 2. Firing Unit
        self.firing_unit = QComboBox()
        self.firing_unit.addItems(LIST_UNITS)

        # 3. Fire Location
        self.fire_location = QComboBox()
        self.fire_location.addItems(LIST_LOCATIONS)

        # 4. Target Agent
        self.target_agent = QComboBox()
        self.target_agent.addItems(LIST_TARGETS)

        # 5. Duration (minutes)
        self.duration = QSpinBox()
        self.duration.setRange(1, 120)
        self.duration.setSuffix(STR_SUFFIX_MIN)

        # 6. Rate of Fire
        self.rate_of_fire = QSpinBox()
        self.rate_of_fire.setRange(1, 10)
        self.rate_of_fire.setSuffix(STR_SUFFIX_RDS)

        # 7. Weapon Type
        self.weapon_type = QComboBox()
        self.weapon_type.addItems(LIST_WEAPONS)

        # Add to form
        form_layout.addRow(STR_LBL_SIDE, self.agent_side)
        form_layout.addRow(STR_LBL_FIRING_UNIT, self.firing_unit)
        form_layout.addRow(STR_LBL_FIRE_LOC, self.fire_location)
        form_layout.addRow(STR_LBL_TARGET, self.target_agent)
        form_layout.addRow(STR_LBL_DURATION, self.duration)
        form_layout.addRow(STR_LBL_ROF, self.rate_of_fire)
        form_layout.addRow(STR_LBL_WEAPON, self.weapon_type)

        # Execute Button
        self.execute_btn = QPushButton(STR_BTN_EXECUTE)
        self.execute_btn.setEnabled(True)
        self.execute_btn.setFixedHeight(45)
        self.execute_btn.setStyleSheet(STYLE_EXECUTE_BTN)
        self.execute_btn.clicked.connect(self.execute_order)

        main_layout.addLayout(form_layout)
        main_layout.addSpacing(25)
        main_layout.addWidget(self.execute_btn, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

    # Placeholder execution hook
    def execute_order(self):
        order = {
            "side": self.agent_side.currentText(),
            "firing_unit": self.firing_unit.currentText(),
            "fire_location": self.fire_location.currentText(),
            "target": self.target_agent.currentText(),
            "duration_min": self.duration.value(),
            "rate_of_fire": self.rate_of_fire.value(),
            "weapon": self.weapon_type.currentText()
        }

        print("🔥 Direct Fire Order Issued:")
        for k, v in order.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DirectFireSimpleUI()
    window.show()
    sys.exit(app.exec_())
