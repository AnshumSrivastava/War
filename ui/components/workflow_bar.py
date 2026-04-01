from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from ui.styles.theme import Theme

class WorkflowBar(QFrame):
    """
    Command Center Bar: A unified workflow controller at the bottom of the screen.
    Supports the 6-phase workflow: Dashboard → Terrain → Area → Agents → Play → Master Data.
    """
    action_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkflowBar")
        self.setFixedHeight(60)
        
        # Styles
        self.setStyleSheet(f"""
            QFrame#WorkflowBar {{
                background-color: {Theme.BG_SURFACE};
                border-top: 1px solid {Theme.BORDER_STRONG};
            }}
            QLabel#StatusLabel {{
                color: {Theme.TEXT_DIM};
                font-family: '{Theme.FONT_HEADER}';
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QLabel#PhaseLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-family: '{Theme.FONT_HEADER}';
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#ActionBtn {{
                background-color: {Theme.ACCENT_ALLY};
                color: {Theme.BG_DEEP};
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
                min-width: 150px;
            }}
            QPushButton#ActionBtn:hover {{
                background-color: {Theme.ACCENT_WARN};
            }}
            QPushButton#BackBtn {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton#BackBtn:hover {{
                background-color: {Theme.BORDER_SUBTLE};
            }}
            QLabel#RulesLabel {{
                color: {Theme.ACCENT_WARN};
                font-family: '{Theme.FONT_MONO}';
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 3px;
                background-color: {Theme.BG_INPUT};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # --- LEFT: Navigation & Current Phase ---
        self.back_btn = QPushButton("←")
        self.back_btn.setObjectName("BackBtn")
        self.back_btn.setToolTip("Return to Previous Phase")
        self.back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(self.back_btn)
        
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_lbl = QLabel("CURRENT OPERATIONS")
        self.status_lbl.setObjectName("StatusLabel")
        
        self.phase_lbl = QLabel("PROJECT DASHBOARD")
        self.phase_lbl.setObjectName("PhaseLabel")
        
        left_layout.addWidget(self.status_lbl)
        left_layout.addWidget(self.phase_lbl)
        layout.addWidget(left_container)
        
        layout.addStretch()
        
        # --- MIDDLE: Contextual Tip ---
        self.tip_lbl = QLabel("Select a mission or map to begin.")
        self.tip_lbl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-style: italic; font-size: 11px;")
        layout.addWidget(self.tip_lbl)
        
        layout.addStretch()
        
        # --- RULES INFO (visible only in Agents mode) ---
        self.rules_lbl = QLabel("")
        self.rules_lbl.setObjectName("RulesLabel")
        self.rules_lbl.hide()
        layout.addWidget(self.rules_lbl)
        
        # --- RIGHT: Action Button ---
        self.action_btn = QPushButton("FINALIZE STEP")
        self.action_btn.setObjectName("ActionBtn")
        self.action_btn.hide()  # Hidden by default on Dashboard
        self.action_btn.clicked.connect(self.action_clicked.emit)
        layout.addWidget(self.action_btn)

    def set_state(self, mode_index, project_name=None, map_name=None):
        """Updates the bar based on the current application mode (6-phase workflow)."""
        self.action_btn.hide()
        self.back_btn.show()
        self.rules_lbl.hide()
        
        if mode_index == 0:  # Dashboard
            self.back_btn.hide()
            self.status_lbl.setText("MISSION CONTROL")
            self.phase_lbl.setText(f"PROJECT: {project_name.upper() if project_name else 'NONE'}")
            self.tip_lbl.setText("Select a tactical map or scenario to start.")
            
        elif mode_index == 1:  # Terrain
            self.status_lbl.setText("STEP 1: TERRAIN")
            self.phase_lbl.setText(f"MAP: {map_name.upper() if map_name else 'NEW'}")
            self.tip_lbl.setText("Define topography and terrain types.")
            self.action_btn.setText("FINALIZE TERRAIN")
            self.action_btn.show()

        elif mode_index == 2:  # Rules
            self.status_lbl.setText("STEP 2: COMBAT RULES")
            self.phase_lbl.setText("SCENARIO CONSTRAINTS")
            self.tip_lbl.setText("Define unit ceilings and weapon regulations.")
            self.action_btn.setText("CONFIRM RULES")
            self.action_btn.show()

        elif mode_index == 3:  # Defender Areas
            self.status_lbl.setText("STEP 3: DEFENDER ZONES")
            self.phase_lbl.setText("DEFENSIVE PERIMETERS")
            self.tip_lbl.setText("Draw fortified goals, deployment zones, and mines for the Defender.")
            self.action_btn.setText("FINALIZE DEFENDER AREAS")
            self.action_btn.show()

        elif mode_index == 4:  # Defender Agents
            self.status_lbl.setText("STEP 4: DEFENDER FORCES")
            self.phase_lbl.setText("DEPLOYING GARRISON")
            self.tip_lbl.setText("Place defender units and issue weapons.")
            self.action_btn.setText("DEPLOY DEFENDERS")
            self.action_btn.show()
            self.rules_lbl.show()

        elif mode_index == 5:  # Attacker Areas
            self.status_lbl.setText("STEP 5: ATTACKER ZONES")
            self.phase_lbl.setText("ASSAULT PERIMETERS")
            self.tip_lbl.setText("Draw insertion zones and waypoints for the Attacker.")
            self.action_btn.setText("FINALIZE ATTACKER AREAS")
            self.action_btn.show()

        elif mode_index == 6:  # Attacker Agents
            self.status_lbl.setText("STEP 6: ATTACKER FORCES")
            self.phase_lbl.setText("DEPLOYING ASSAULT")
            self.tip_lbl.setText("Place attacker units and issue loadouts.")
            self.action_btn.setText("DEPLOY ATTACKERS")
            self.action_btn.show()
            self.rules_lbl.show()
            
        elif mode_index == 7:  # Simulation / Play
            self.status_lbl.setText("STEP 7: COMBAT SIMULATION")
            self.phase_lbl.setText("TACTICAL EXECUTION")
            self.tip_lbl.setText("AI is analyzing and learning from the battlefield.")
            self.action_btn.setText("FINISH MISSION")
            self.action_btn.show()
            
        elif mode_index == 8:  # Master Data
            self.back_btn.hide()
            self.status_lbl.setText("ENGINEERING LOCK")
            self.phase_lbl.setText("MASTER DATA REGISTRY")
            self.tip_lbl.setText("Modify global unit and weapon statistics.")
            self.action_btn.hide()

    def update_force_counts(self, atk_count=0, atk_limit=10, def_count=0, def_limit=10):
        """Updates the force limit display in the workflow bar."""
        self.rules_lbl.setText(f"ATK: {atk_count}/{atk_limit}  |  DEF: {def_count}/{def_limit}")
