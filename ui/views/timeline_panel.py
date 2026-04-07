"""
FILE: ui/views/timeline_panel.py
ROLE: The "Remote Control" (Timeline Panel).

DESCRIPTION:
This panel is used to control the flow of time in the simulation. 
It contains the Play, Pause, and Step buttons.

It also allows you to:
1. Set how many rounds (Episodes) the AI should play.
2. Set how many seconds (Steps) each round should last.
3. Switch between 'Visual' mode (watching the game) and 'Batch' mode (training fast).
4. See a 'Log' of every event that happens in the battle.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, QSpinBox, 
                             QComboBox, QGridLayout, QPushButton, QHBoxLayout, QCheckBox, QFrame,
                             QGroupBox, QProgressBar, QToolButton, QSizePolicy)
from PyQt5.QtCore import Qt, QSize

# --- UI CONFIGURATION ---
# Group Titles
LABEL_GRP_MISSION = "Mission Configuration"
LABEL_GRP_CONTROLS = "Simulation Controls"
LABEL_GRP_MONITOR = "Monitoring"

# Labels & Headers
LABEL_MODE = "Mode:"
LABEL_EPISODES = "Episodes:"
LABEL_TIME_LIMIT = "Time Limit:"
LABEL_CB_TRAILS = "Trails"
LABEL_CB_FX = "FX"

# Button Titles
LABEL_BTN_LEARN = "Start Learning"
LABEL_BTN_RUN = "Run Simulation"
LABEL_BTN_PAUSE = "Pause"
LABEL_BTN_RESET_INTEL = "Reset Intel"
LABEL_BTN_STEP = "Step"
LABEL_BTN_PLAY = "Play"
LABEL_BTN_RESET = "Reset"

# Status & Formatting Templates
STATUS_STANDBY = "STANDBY"
MSG_STEP_CALC_FMT = "(= {steps} Steps)"
MSG_TIME_FMT = "Time: {time}"
MSG_EPISODE_FMT = "EP {current}/{total}"

# Dialog Messages
TITLE_RESET_INTEL = "CONFIRM RESET"
MSG_RESET_INTEL = "Wipe all learned data?"
# ------------------------

class TimelinePanel(QWidget):
    """
    The control panel for simulation execution and monitoring.
    """
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.main_window = parent
        self.state = state
        self._setup_ui()

    def _setup_ui(self):
        from ui.styles.theme import Theme
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # --- PARAMS ---
        self.spin_episodes = QSpinBox()
        self.spin_episodes.setRange(1, 10000)
        self.spin_episodes.setValue(getattr(self.main_window.sim_controller, 'max_episodes', 100))
        self.spin_episodes.valueChanged.connect(self._on_episodes_changed)
        
        self.spin_time_limit = QSpinBox()
        self.spin_time_limit.setRange(10, 1440)
        self.spin_time_limit.setValue(500)
        self.spin_time_limit.valueChanged.connect(self._on_time_limit_changed)
        
        layout.addWidget(QLabel("Ep:"))
        layout.addWidget(self.spin_episodes)
        layout.addWidget(QLabel("Steps:"))
        layout.addWidget(self.spin_time_limit)
        
        # Separator
        line1 = QFrame()
        line1.setFrameShape(QFrame.VLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)
        
        # --- BATCH ACTIONS ---
        self.btn_learn = QPushButton(LABEL_BTN_LEARN)
        self.btn_learn.clicked.connect(self.main_window.start_learning_phase)
        layout.addWidget(self.btn_learn)
        
        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.VLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # --- STATUS & PROGRESS ---
        self.lbl_status = QLabel(f"[{STATUS_STANDBY}]")
        self.lbl_status.setStyleSheet(f"color: {Theme.ACCENT_NEUTRAL}; font-weight: bold;")
        self.lbl_sim_time = QLabel(MSG_TIME_FMT.format(time="00m"))
        self.lbl_sim_time.setStyleSheet(f"color: {Theme.ACCENT_WARN}; font-family: '{Theme.FONT_MONO}'; font-weight: bold;")
        self.lbl_episode_count = QLabel(MSG_EPISODE_FMT.format(current=0, total=0))
        
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_sim_time)
        layout.addWidget(self.lbl_episode_count)
        
        self.progress_episodes = QProgressBar()
        self.progress_episodes.setTextVisible(False)
        self.progress_episodes.setFixedWidth(80)
        layout.addWidget(self.progress_episodes)
        
        layout.addStretch() # Push everything else to the left and live actions to the right
        
        # --- LIVE ACTIONS ---
        self.btn_start = QPushButton(LABEL_BTN_PLAY)
        self.btn_start.clicked.connect(self.main_window.start_simulation_loop)
        self.btn_step = QPushButton(LABEL_BTN_STEP)
        self.btn_step.clicked.connect(self.main_window.advance_simulation)
        self.btn_pause = QPushButton(LABEL_BTN_PAUSE)
        self.btn_pause.clicked.connect(self.main_window.pause_simulation)
        self.btn_reset = QPushButton(LABEL_BTN_RESET)
        self.btn_reset.clicked.connect(self.main_window.action_reset_env)
        
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_step)
        layout.addWidget(self.btn_pause)
        layout.addWidget(self.btn_reset)

        # --- MONITORING ---
        self.cb_moves = QCheckBox(LABEL_CB_TRAILS)
        self.cb_moves.setChecked(True)
        self.cb_moves.toggled.connect(lambda c: setattr(self.main_window.visualizer, 'show_trails', c) or self.main_window.hex_widget.update())
        self.cb_fire = QCheckBox(LABEL_CB_FX)
        self.cb_fire.setChecked(True)
        self.cb_fire.toggled.connect(lambda c: setattr(self.main_window.visualizer, 'show_fire', c) or self.main_window.hex_widget.update())
        
        layout.addWidget(self.cb_moves)
        layout.addWidget(self.cb_fire)


    def _on_time_limit_changed(self, mins):
        steps = max(1, mins // 10)
        self.lbl_step_calc.setText(MSG_STEP_CALC_FMT.format(steps=steps))
        setattr(self.main_window, 'max_steps', steps)
        self.main_window.sim_controller.max_steps = steps

    def _on_episodes_changed(self, v):
        setattr(self.main_window, 'max_episodes', v)
        self.main_window.sim_controller.max_episodes = v
        self.update_progress(self.main_window.sim_controller.current_episode)

    def _on_steps_changed(self, v):
        pass

    def update_progress(self, episode):
        max_ep = self.main_window.sim_controller.max_episodes
        self.progress_episodes.setMaximum(max_ep)
        self.progress_episodes.setValue(episode)
        self.lbl_episode_count.setText(MSG_EPISODE_FMT.format(current=episode, total=max_ep))

    def _on_reset_intel(self):
        from PyQt5.QtWidgets import QMessageBox
        res = QMessageBox.question(self, TITLE_RESET_INTEL, MSG_RESET_INTEL, QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            count = self.main_window.sim_controller.reset_intelligence()
            self.update_progress(1)

    def set_status(self, status_text, color=None):
        from ui.styles.theme import Theme
        self.lbl_status.setText(f"[{status_text.upper()}]")
        if color:
            self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-family: '{Theme.FONT_MONO}';")
        else:
            self.lbl_status.setStyleSheet(f"color: {Theme.ACCENT_NEUTRAL}; font-weight: bold; font-family: '{Theme.FONT_MONO}';")

    def set_simulation_time(self, time_str):
        self.lbl_sim_time.setText(MSG_TIME_FMT.format(time=time_str))
