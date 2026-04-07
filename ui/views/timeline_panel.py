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
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # --- MISSION CONFIGURATION ---
        group_params = QGroupBox(LABEL_GRP_MISSION)
        param_layout = QFormLayout()
        
        self.spin_episodes = QSpinBox()
        self.spin_episodes.setRange(1, 10000)
        self.spin_episodes.setValue(getattr(self.main_window.sim_controller, 'max_episodes', 100))
        self.spin_episodes.valueChanged.connect(self._on_episodes_changed)
        
        self.spin_time_limit = QSpinBox()
        self.spin_time_limit.setRange(10, 1440)
        self.spin_time_limit.setValue(500)
        self.spin_time_limit.valueChanged.connect(self._on_time_limit_changed)
        
        self.lbl_step_calc = QLabel(MSG_STEP_CALC_FMT.format(steps=50))
        self.lbl_step_calc.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        
        self.combo_sim_mode = QComboBox()
        self.combo_sim_mode.addItems(["Visual", "Batch"])
        self.combo_sim_mode.currentIndexChanged.connect(lambda idx: setattr(self.main_window, 'is_batch_mode', idx == 1))
        
        param_layout.addRow(LABEL_MODE, self.combo_sim_mode)
        param_layout.addRow(LABEL_EPISODES, self.spin_episodes)
        param_layout.addRow(LABEL_TIME_LIMIT, self.spin_time_limit)
        param_layout.addRow("", self.lbl_step_calc)
        
        group_params.setLayout(param_layout)
        layout.addWidget(group_params)

        # --- SIMULATION CONTROLS ---
        group_commands = QGroupBox(LABEL_GRP_CONTROLS)
        deck_layout = QVBoxLayout()
        
        row_actions = QHBoxLayout()
        self.btn_learn = QPushButton(LABEL_BTN_LEARN)
        self.btn_learn.clicked.connect(self.main_window.start_learning_phase)
        self.btn_start = QPushButton(LABEL_BTN_RUN)
        self.btn_start.clicked.connect(self.main_window.start_simulation_loop)
        row_actions.addWidget(self.btn_learn)
        row_actions.addWidget(self.btn_start)
        deck_layout.addLayout(row_actions)

        row_sec = QHBoxLayout()
        self.btn_pause = QPushButton(LABEL_BTN_PAUSE)
        self.btn_pause.clicked.connect(self.main_window.pause_simulation)
        self.btn_reset_intel = QPushButton(LABEL_BTN_RESET_INTEL)
        self.btn_reset_intel.clicked.connect(self._on_reset_intel)
        row_sec.addWidget(self.btn_pause)
        row_sec.addWidget(self.btn_reset_intel)
        deck_layout.addLayout(row_sec)
        
        # Status & Progress
        status_row = QHBoxLayout()
        self.lbl_status = QLabel(f"[{STATUS_STANDBY}]")
        self.lbl_status.setStyleSheet(f"color: {Theme.ACCENT_NEUTRAL}; font-weight: bold;")
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        
        self.lbl_sim_time = QLabel(MSG_TIME_FMT.format(time="00m"))
        self.lbl_sim_time.setStyleSheet(f"color: {Theme.ACCENT_WARN}; font-family: '{Theme.FONT_MONO}'; font-weight: bold;")
        status_row.addWidget(self.lbl_sim_time)
        
        self.lbl_episode_count = QLabel(MSG_EPISODE_FMT.format(current=0, total=0))
        self.lbl_episode_count.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px;")
        status_row.addWidget(self.lbl_episode_count)
        deck_layout.addLayout(status_row)
        
        self.progress_episodes = QProgressBar()
        self.progress_episodes.setTextVisible(False)
        self.progress_episodes.setFixedHeight(4)
        deck_layout.addWidget(self.progress_episodes)
        
        # Operation Buttons (Compact)
        btn_row = QHBoxLayout()
        self.btn_step = QPushButton(LABEL_BTN_STEP)
        self.btn_step.clicked.connect(self.main_window.advance_simulation)
        self.btn_play = QPushButton(LABEL_BTN_PLAY)
        self.btn_play.clicked.connect(self.main_window.start_simulation_loop)
        self.btn_pause_sim = QPushButton(LABEL_BTN_PAUSE)
        self.btn_pause_sim.clicked.connect(self.main_window.pause_simulation)
        self.btn_reset = QPushButton(LABEL_BTN_RESET)
        self.btn_reset.clicked.connect(self.main_window.action_reset_env)
        
        btn_row.addWidget(self.btn_step)
        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_pause_sim)
        btn_row.addWidget(self.btn_reset)
        deck_layout.addLayout(btn_row)

        group_commands.setLayout(deck_layout)
        layout.addWidget(group_commands)

        # --- MONITORING ---
        group_layers = QGroupBox(LABEL_GRP_MONITOR)
        layer_layout = QHBoxLayout()
        self.cb_moves = QCheckBox(LABEL_CB_TRAILS)
        self.cb_moves.setChecked(True)
        self.cb_moves.toggled.connect(lambda c: setattr(self.main_window.visualizer, 'show_trails', c) or self.main_window.hex_widget.update())
        self.cb_fire = QCheckBox(LABEL_CB_FX)
        self.cb_fire.setChecked(True)
        self.cb_fire.toggled.connect(lambda c: setattr(self.main_window.visualizer, 'show_fire', c) or self.main_window.hex_widget.update())
        layer_layout.addWidget(self.cb_moves)
        layer_layout.addWidget(self.cb_fire)
        group_layers.setLayout(layer_layout)
        layout.addWidget(group_layers)
        
        # Give layout stretch so elements compactly align to the top
        layout.addStretch()

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
