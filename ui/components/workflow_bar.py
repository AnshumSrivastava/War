from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from ui.styles.theme import Theme

# --- UI CONFIGURATION ---
# Object Names & Identifiers
OBJ_BAR = "WorkflowBar"
OBJ_STATUS = "StatusLabel"
OBJ_PHASE = "PhaseLabel"
OBJ_ACTION = "ActionBtn"
OBJ_BACK = "BackBtn"
OBJ_RULES = "RulesLabel"

# Stylesheets
STYLE_BAR = f"""
    QFrame#{OBJ_BAR} {{
        background-color: {Theme.BG_SURFACE};
        border-top: 1px solid {Theme.BORDER_STRONG};
    }}
    QLabel#{OBJ_STATUS} {{
        color: {Theme.TEXT_DIM};
        font-family: '{Theme.FONT_HEADER}';
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QLabel#{OBJ_PHASE} {{
        color: {Theme.TEXT_PRIMARY};
        font-family: '{Theme.FONT_HEADER}';
        font-size: 14px;
        font-weight: bold;
    }}
    QPushButton#{OBJ_ACTION} {{
        background-color: {Theme.ACCENT_ALLY};
        color: {Theme.BG_DEEP};
        font-weight: bold;
        border-radius: 4px;
        padding: 8px 20px;
        min-width: 150px;
    }}
    QPushButton#{OBJ_ACTION}:hover {{
        background-color: {Theme.ACCENT_WARN};
    }}
    QPushButton#{OBJ_BACK} {{
        background-color: {Theme.BG_INPUT};
        color: {Theme.TEXT_PRIMARY};
        border: 1px solid {Theme.BORDER_SUBTLE};
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
    }}
    QPushButton#{OBJ_BACK}:hover {{
        background-color: {Theme.BORDER_SUBTLE};
    }}
    QLabel#{OBJ_RULES} {{
        color: {Theme.ACCENT_WARN};
        font-family: '{Theme.FONT_MONO}';
        font-size: 11px;
        font-weight: bold;
        padding: 2px 8px;
        border: 1px solid {Theme.BORDER_SUBTLE};
        border-radius: 3px;
        background-color: {Theme.BG_INPUT};
    }}
"""
STYLE_TIP = f"color: {Theme.TEXT_DIM}; font-style: italic; font-size: 11px;"

# Tooltips
STR_TIP_BACK = "Return to Previous Phase"

# Default Labels
STR_LBL_OPS_ROOT = "CURRENT OPERATIONS"
STR_LBL_PHASE_ROOT = "PROJECT DASHBOARD"
STR_LBL_TIP_ROOT = "Select a mission or map to begin."
STR_LBL_BTN_FINALIZE = "FINALIZE STEP"

# Phase 0: Dashboard
STR_STATUS_DASHBOARD = "MISSION CONTROL"
STR_PHASE_PROJECT_FMT = "PROJECT: {name}"
STR_TIP_DASHBOARD = "Select a tactical map or scenario to start."

# Phase 1: Terrain
STR_STATUS_TERRAIN = "STEP 1: TERRAIN"
STR_PHASE_MAP_FMT = "MAP: {name}"
STR_TIP_TERRAIN = "Define topography and terrain types."
STR_BTN_TERRAIN = "FINALIZE TERRAIN"

# Phase 2: Rules
STR_STATUS_RULES = "STEP 2: COMBAT RULES"
STR_PHASE_RULES = "SCENARIO CONSTRAINTS"
STR_TIP_RULES = "Define unit ceilings and weapon regulations."
STR_BTN_RULES = "CONFIRM RULES"

# Phase 3: Defender Areas
STR_STATUS_DEF_AREAS = "STEP 3: DEFENDER ZONES"
STR_PHASE_DEF_GZ = "DEFENSIVE PERIMETERS"
STR_TIP_DEF_AREAS = "Draw fortified goals, deployment zones, and mines for the Defender."
STR_BTN_DEF_AREAS = "FINALIZE DEFENDER AREAS"

# Phase 4: Defender Agents
STR_STATUS_DEF_FORCES = "STEP 4: DEFENDER FORCES"
STR_PHASE_GARRISON = "DEPLOYING GARRISON"
STR_TIP_DEF_AGENTS = "Place defender units and issue weapons."
STR_BTN_DEPLOY_DEF = "DEPLOY DEFENDERS"

# Phase 5: Attacker Areas
STR_STATUS_ATK_AREAS = "STEP 5: ATTACKER ZONES"
STR_PHASE_ASSAULT_P = "ASSAULT PERIMETERS"
STR_TIP_ATK_AREAS = "Draw insertion zones and waypoints for the Attacker."
STR_BTN_ATK_AREAS = "FINALIZE ATTACKER AREAS"

# Phase 6: Attacker Agents
STR_STATUS_ATK_FORCES = "STEP 6: ATTACKER FORCES"
STR_PHASE_ASSAULT_D = "DEPLOYING ASSAULT"
STR_TIP_ATK_AGENTS = "Place attacker units and issue loadouts."
STR_BTN_DEPLOY_ATK = "DEPLOY ATTACKERS"

# Phase 7: Play
STR_STATUS_PLAY = "STEP 7: COMBAT SIMULATION"
STR_PHASE_EXECUTION = "TACTICAL EXECUTION"
STR_TIP_SIM = "AI is analyzing and learning from the battlefield."
STR_BTN_FINISH = "FINISH MISSION"

# Phase 8: Master Data
STR_STATUS_MASTER = "ENGINEERING LOCK"
STR_PHASE_MASTER = "MASTER DATA REGISTRY"
STR_TIP_MASTER = "Modify global unit and weapon statistics."

# Formatting
STR_RULES_FMT = "ATK: {atk_count}/{atk_limit}  |  DEF: {def_count}/{def_limit}"
# -------------------------

class WorkflowBar(QFrame):
    """
    Command Center Bar: A unified workflow controller at the bottom of the screen.
    Supports the 6-phase workflow: Dashboard → Terrain → Area → Agents → Play → Master Data.
    """
    action_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(OBJ_BAR)
        self.setFixedHeight(60)
        
        # Styles
        self.setStyleSheet(STYLE_BAR)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # --- LEFT: Navigation & Current Phase ---
        self.back_btn = QPushButton("←")
        self.back_btn.setObjectName(OBJ_BACK)
        self.back_btn.setToolTip(STR_TIP_BACK)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(self.back_btn)
        
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_lbl = QLabel(STR_LBL_OPS_ROOT)
        self.status_lbl.setObjectName(OBJ_STATUS)
        
        self.phase_lbl = QLabel(STR_LBL_PHASE_ROOT)
        self.phase_lbl.setObjectName(OBJ_PHASE)
        
        left_layout.addWidget(self.status_lbl)
        left_layout.addWidget(self.phase_lbl)
        layout.addWidget(left_container)
        
        layout.addStretch()
        
        # --- MIDDLE: Contextual Tip ---
        self.tip_lbl = QLabel(STR_LBL_TIP_ROOT)
        self.tip_lbl.setStyleSheet(STYLE_TIP)
        layout.addWidget(self.tip_lbl)
        
        layout.addStretch()
        
        # --- RULES INFO (visible only in Agents mode) ---
        self.rules_lbl = QLabel("")
        self.rules_lbl.setObjectName(OBJ_RULES)
        self.rules_lbl.hide()
        layout.addWidget(self.rules_lbl)
        
        # --- RIGHT: Action Button ---
        self.action_btn = QPushButton(STR_LBL_BTN_FINALIZE)
        self.action_btn.setObjectName(OBJ_ACTION)
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
            self.status_lbl.setText(STR_STATUS_DASHBOARD)
            self.phase_lbl.setText(STR_PHASE_PROJECT_FMT.format(name=project_name.upper() if project_name else 'NONE'))
            self.tip_lbl.setText(STR_TIP_DASHBOARD)
            
        elif mode_index == 1:  # Terrain
            self.status_lbl.setText(STR_STATUS_TERRAIN)
            self.phase_lbl.setText(STR_PHASE_MAP_FMT.format(name=map_name.upper() if map_name else 'NEW'))
            self.tip_lbl.setText(STR_TIP_TERRAIN)
            self.action_btn.setText(STR_BTN_TERRAIN)
            self.action_btn.show()

        elif mode_index == 2:  # Rules
            self.status_lbl.setText(STR_STATUS_RULES)
            self.phase_lbl.setText(STR_PHASE_RULES)
            self.tip_lbl.setText(STR_TIP_RULES)
            self.action_btn.setText(STR_BTN_RULES)
            self.action_btn.show()

        elif mode_index == 3:  # Defender Areas
            self.status_lbl.setText(STR_STATUS_DEF_AREAS)
            self.phase_lbl.setText(STR_PHASE_DEF_GZ)
            self.tip_lbl.setText(STR_TIP_DEF_AREAS)
            self.action_btn.setText(STR_BTN_DEF_AREAS)
            self.action_btn.show()

        elif mode_index == 4:  # Defender Agents
            self.status_lbl.setText(STR_STATUS_DEF_FORCES)
            self.phase_lbl.setText(STR_PHASE_GARRISON)
            self.tip_lbl.setText(STR_TIP_DEF_AGENTS)
            self.action_btn.setText(STR_BTN_DEPLOY_DEF)
            self.action_btn.show()
            self.rules_lbl.show()

        elif mode_index == 5:  # Attacker Areas
            self.status_lbl.setText(STR_STATUS_ATK_AREAS)
            self.phase_lbl.setText(STR_PHASE_ASSAULT_P)
            self.tip_lbl.setText(STR_TIP_ATK_AREAS)
            self.action_btn.setText(STR_BTN_ATK_AREAS)
            self.action_btn.show()

        elif mode_index == 6:  # Attacker Agents
            self.status_lbl.setText(STR_STATUS_ATK_FORCES)
            self.phase_lbl.setText(STR_PHASE_ASSAULT_D)
            self.tip_lbl.setText(STR_TIP_ATK_AGENTS)
            self.action_btn.setText(STR_BTN_DEPLOY_ATK)
            self.action_btn.show()
            self.rules_lbl.show()
            
        elif mode_index == 7:  # Simulation / Play
            self.status_lbl.setText(STR_STATUS_PLAY)
            self.phase_lbl.setText(STR_PHASE_EXECUTION)
            self.tip_lbl.setText(STR_TIP_SIM)
            self.action_btn.setText(STR_BTN_FINISH)
            self.action_btn.show()
            
        elif mode_index == 8:  # Master Data
            self.back_btn.hide()
            self.status_lbl.setText(STR_STATUS_MASTER)
            self.phase_lbl.setText(STR_PHASE_MASTER)
            self.tip_lbl.setText(STR_TIP_MASTER)
            self.action_btn.hide()

    def update_force_counts(self, atk_count=0, atk_limit=10, def_count=0, def_limit=10):
        """Updates the force limit display in the workflow bar."""
        self.rules_lbl.setText(STR_RULES_FMT.format(
            atk_count=atk_count, atk_limit=atk_limit, 
            def_count=def_count, def_limit=def_limit
        ))
