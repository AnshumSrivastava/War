"""
FILE: ui/views/main_window.py
ROLE: The "Director" (Main Application Controller).

DESCRIPTION:
This is the heart of the user interface. It acts like a director on a movie set:
1. It creates and organizes all the "actors" (the map, the panels, the buttons).
2. It listens for your commands (shortcuts like Ctrl+S, or clicking on a tab).
3. It handles switching between different "Scenes" (Terrain mode vs. Scenario mode).
4. It manages "Saving" and "Loading" your projects.

If HexWidget is the 'Canvas', MainWindow is the 'Studio' that holds the canvas.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QDockWidget, QPushButton, QLabel, QFrame, QTextEdit, QButtonGroup, 
                             QToolBar, QAction, QActionGroup, QDialog, QFormLayout, QSpinBox, 
                             QDialogButtonBox, QScrollArea, QSlider, QLineEdit, QComboBox, QFileDialog, QMessageBox,
                             QTabWidget, QListWidget, QInputDialog, QToolButton, QSizePolicy, QStyle, QShortcut, QStackedWidget, QGridLayout, QCheckBox, QStatusBar, QSplitter, QMenu, QApplication, QRadioButton, QGroupBox)
from PyQt5.QtCore import Qt, QSize, QTimer, QTime
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QColor, QCursor

import os
import sys
import json
import datetime
import logging

log = logging.getLogger(__name__)

from engine.state.global_state import GlobalState
from ui.views.hex_widget import HexWidget
from ui.views.timeline_panel import TimelinePanel
from ui.core.visualizer import Visualizer
from ui.components.data_widget import DataWidget
from ui.components.rules_widget import RulesWidget
from ui.dialogs.themed_dialogs import ThemedMessageBox

from ui.views.maps_widget import MapsWidget
from ui.core.icon_painter import VectorIconPainter
from ui.styles.theme import Theme

# Import Service Layer
import services.map_service as map_svc
import services.entity_service as entity_svc
import services.simulation_service as sim_svc
import services.scenario_service as scenario_svc
import services.rules_service as rules_svc
import services.data_service as data_svc
import services.zone_service as zone_svc
import services.path_service as path_svc

# New Specialized Controllers
from ui.core.toolbar_controller import ToolbarController
from ui.core.mode_state_machine import ModeStateMachine
from ui.core.scenario_side_manager import ScenarioSideManager
from ui.core.simulation_manager import SimulationManager
from ui.core.shortcut_registry import ShortcutRegistry
from ui.core.ui_settings_persistence import UISettingsPersistence

class MainWindow(QMainWindow):
    """
    The main window that pulls everything together.
    It manages the layout, toolbars, and high-level application logic.
    """

    def __init__(self):
        """
        THE HEART OF THE ENGINE: Initializes the application window.
        Bridges the Gap between the mathematical Engine and the visual UI.
        
        This constructor:
        1. Loads the Global State (source of truth).
        2. Injects state into the Service Layer (Logic handlers).
        3. Prepares the Hex map canvas and Simulation managers.
        4. Triggers the UI assembly process.
        """
        super().__init__()
        # GlobalState is the 'Source of Truth' - all data resides here.
        self.state = GlobalState()
        
        # --- SERVICE LAYER INITIALIZATION ---
        # We pass the state to our logic services so they can modify the world.
        map_svc.init(self.state)
        entity_svc.init(self.state)
        sim_svc.init(self.state)
        scenario_svc.init(self.state)
        rules_svc.init(self.state)
        data_svc.init(self.state)
        zone_svc.init(self.state)
        path_svc.init(self.state)
        
        # --- DATA & MODELS ---
        from engine.data.loaders.data_manager import DataManager
        self.data_loader = DataManager()
        
        # ActionModel provides the tactical logic for AI agents.
        from engine.simulation.act_model import ActionModel
        self._internal_action_model = ActionModel(self.state)
        self.action_model = self._internal_action_model
        
        # --- WINDOW GEOMETRY ---
        self.setMinimumSize(1280, 800)
        self.theme = Theme
        
        # The Map Canvas: Where the actual hexagons are rendered.
        self.hex_widget = HexWidget(self, state=self.state)
        self.hex_widget.action_model = self.action_model
        # Visualizer: Draws transient effects like fire or explosions.
        self.visualizer = Visualizer(self.hex_widget)
        
        # --- SIMULATION & MODE CONTROL ---
        from ui.core.simulation_controller import SimulationController
        self.sim_controller = SimulationController(self.state, self.action_model)
        self.sim_manager = SimulationManager(self)
        
        # Controllers for specific UI sections (Toolbars, Transitions, Teams)
        self.toolbar_controller = ToolbarController(self)
        self.mode_machine = ModeStateMachine(self)
        self.scenario_side_manager = ScenarioSideManager(self)
        
        # --- NEW MODULAR CORE ---
        from src.presentation.controllers.tool_controller import ToolController
        from src.presentation.viewmodels.tool_handlers import EraserHandler
        self.core_tool_controller = ToolController()
        self.core_tool_controller.register_handler("eraser", EraserHandler())
        
        # --- PROJECT STATE ---
        self.current_project_path = None
        
        # --- AUTO-SAVE ENGINE ---
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(60000) # Safeguard: Saves progress every minute.
        self.autosave_timer.timeout.connect(lambda: self.action_save_project(silent=True))
        self.autosave_timer.start()
        
        # --- ASSEMBLY: Build the physical widgets and buttons ---
        self._init_ui()
        
        # --- SESSION RECOVERY (Load Last Project) ---
        self._load_last_project()
        
        # --- FALLBACK: If no project loaded, open Default ---
        if not self.current_project_path:
            self._load_default_project()
        
        # --- STATUS & TIME ---
        self.statusBar().showMessage("System Ready")
        
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-family: 'Consolas', monospace; font-size: 13px; padding-right: 10px;")
        self.statusBar().addPermanentWidget(self.clock_label)
        
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()
        
    def _init_ui(self):
        """
        THE ARCHITECT: Defines the layout and appearance of the application.
        Uses a Stacked approach to switch between the Map and the Gallery.
        """
        # Apply the CSS skin (zinc-dark or slate-light)
        self.setStyleSheet(Theme.get_main_qss())
        
        # Main vertical container for the whole window
        self.central_container = QWidget()
        self.central_layout = QVBoxLayout(self.central_container)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.setCentralWidget(self.central_container)
        
        # --- NAVIGATION STACK ---
        # This allows us to flip between different main screens (Map vs Catalog).
        self.content_stack = QStackedWidget()
        self.central_layout.addWidget(self.content_stack, 1) 
        
        # PAGE 1: THE GALLERY (Map Picker)
        self.maps_widget = MapsWidget(self, state=self.state)
        self.maps_widget.deep_link_requested.connect(self.handle_deep_link)
        self.content_stack.addWidget(self.maps_widget)
        
        from ui.components.workflow_bar import WorkflowBar
        self.workflow_bar = WorkflowBar(self)
        self.workflow_bar.action_clicked.connect(self._on_done_clicked)
        self.workflow_bar.back_clicked.connect(self._on_back_clicked)
        self.central_layout.addWidget(self.workflow_bar)
        
        # --- TOOL PALETTE controller ---
        from ui.core.toolbar_controller import ToolbarController
        self.toolbar_controller = ToolbarController(self)
        self.toolbar_controller.setup_left_toolbar()
        
        # PAGE 2: THE THEATER (The Interactive Map)
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        self.theater_container = QWidget()
        theater_layout = QVBoxLayout(self.theater_container)
        theater_layout.setContentsMargins(0, 0, 0, 0)
        theater_layout.setSpacing(0)
        
        # Layout no longer includes map_header_tabs (Tabs were visually stripped for linear phase view)
        theater_layout.addWidget(self.hex_widget, 1)
        
        self.main_splitter.addWidget(self.theater_container)
        self.content_stack.addWidget(self.main_splitter)
        
        # PAGE 3: THE RULES (Strategic Constraints)
        from ui.components.rules_widget import RulesWidget
        self.rules_widget = RulesWidget(self, state=self.state)
        self.content_stack.addWidget(self.rules_widget)
        
        # PAGE 4: THE DATA HUB (Configuration)
        from ui.components.master_data_widget import MasterDataWidget
        self.master_data_widget = MasterDataWidget(self, state=self.state)
        self.content_stack.addWidget(self.master_data_widget)
        
        # --- TACTICAL OPERATIONS CENTER (TOC) ---
        # Initialize legacy stubs for background property compatibility (tool_opts_layout, etc)
        self.setup_object_inspector()
        self.setup_right_panel()
        
        from ui.components.tactical_side_panel import TacticalSidePanel
        self.toc_dock = QDockWidget("MISSION CONTROL", self)
        self.tac_panel = TacticalSidePanel(self, self.state)
        self.toc_dock.setWidget(self.tac_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toc_dock)
        
        # Timeline & Terminal panels (initialized but hidden by default)
        self.setup_timeline_panel()
        
        # Input/Shortcut registry
        self.shortcuts = ShortcutRegistry(self)
        self.shortcuts.setup_default_shortcuts()
        
        # Connect map clicks to inspector logic
        self.hex_widget.hex_clicked.connect(self.on_hex_clicked)
        self.final_episode_events = []

        # --- PERSISTENCE RESTORATION ---
        # Restore sidebars and window size to exactly where they were last time.
        UISettingsPersistence.restore(self)
        self.apply_theme(self.state.theme_mode)

        self.statusBar().showMessage("Ready")
        self.setup_menu_bar()
        

    # Shortcuts are now managed by ShortcutRegistry

    def setup_menu_bar(self):
        """
        Builds the standard top-level menu (File, Edit, View, Simulation).
        Each action is linked to a specific logic callback.
        """
        menubar = self.menuBar()
        menubar.clear()
        
        # --- File Menu ---
        file_menu = menubar.addMenu("File")
        
        # Projects
        a_new_proj = file_menu.addAction(VectorIconPainter.create_icon("new_file"), "New Project")
        a_new_proj.setShortcut("Ctrl+Shift+N")
        a_new_proj.triggered.connect(self.action_new_project)
        
        a_load_proj = file_menu.addAction(VectorIconPainter.create_icon("load"), "Open Project")
        a_load_proj.setShortcut("Ctrl+Shift+O")
        a_load_proj.triggered.connect(self.action_load_project)
        
        file_menu.addSeparator()
        
        # Maps
        a_new_map = file_menu.addAction(VectorIconPainter.create_icon("edit"), "New Map")
        a_new_map.setShortcut("Ctrl+N")
        a_new_map.triggered.connect(self.action_create_new_map)
        
        a_save = file_menu.addAction(VectorIconPainter.create_icon("save"), "Save Map")
        a_save.setShortcut("Ctrl+S")
        a_save.triggered.connect(self.action_save_project)
        
        file_menu.addSeparator()
        
        # Scenarios
        a_load_scen = file_menu.addAction("Load Scenario")
        a_load_scen.triggered.connect(self.action_load_scenario)
        
        a_save_scen = file_menu.addAction("Save Scenario")
        a_save_scen.triggered.connect(self.action_save_scenario)
        
        file_menu.addSeparator()
        
        a_exit = file_menu.addAction("Exit")
        a_exit.setShortcut("Ctrl+Q")
        a_exit.triggered.connect(self.close)
        
        a_restart = file_menu.addAction("Restart Application")
        a_restart.setShortcut("Ctrl+R")
        a_restart.triggered.connect(self.restart_app)
        
        a_reload_data = file_menu.addAction("Reload Master Data")
        a_reload_data.setToolTip("Reload JSON configuration files without restarting.")
        a_reload_data.triggered.connect(self.action_reload_master_data)
        
        # --- Edit Menu ---
        edit_menu = menubar.addMenu("Edit")
        
        a_undo = edit_menu.addAction(VectorIconPainter.create_icon("undo"), "Undo")
        a_undo.setShortcut("Ctrl+Z")
        a_undo.triggered.connect(self.undo_action)
        
        a_redo = edit_menu.addAction(VectorIconPainter.create_icon("redo"), "Redo")
        a_redo.setShortcut("Ctrl+Y")
        a_redo.triggered.connect(self.redo_action)
        
        edit_menu.addSeparator()
        
        a_resize = edit_menu.addAction(VectorIconPainter.create_icon("settings"), "Resize Map")
        a_resize.triggered.connect(self.action_resize_map)
        
        a_alloc = edit_menu.addAction(VectorIconPainter.create_icon("place_agent"), "Agent Allocation")
        a_alloc.triggered.connect(self.prompt_agent_allocation)
        
        edit_menu.addSeparator()
        
        a_border = edit_menu.addAction(VectorIconPainter.create_icon("draw_zone"), "Border Setup")
        a_border.triggered.connect(self.action_add_border)
        
        edit_menu.addSeparator()
        
        a_clear = edit_menu.addAction(VectorIconPainter.create_icon("trash"), "Clear Map")
        a_clear.triggered.connect(self.action_clear_map)
        
        # --- View Menu ---
        view_menu = menubar.addMenu("View")
        
        a_zoom_in = view_menu.addAction("Zoom In")
        a_zoom_in.setShortcut("Ctrl++")
        a_zoom_in.triggered.connect(self.action_zoom_in)
        
        a_zoom_out = view_menu.addAction("Zoom Out")
        a_zoom_out.setShortcut("Ctrl+-")
        a_zoom_out.triggered.connect(self.action_zoom_out)
        
        a_reset_cam = view_menu.addAction("Reset Camera")
        a_reset_cam.setShortcut("Ctrl+0")
        a_reset_cam.triggered.connect(self.action_reset_camera)
        
        view_menu.addSeparator()
        
        # Toggles
        self.a_inf = view_menu.addAction("Infinite Grid")
        self.a_inf.setCheckable(True)
        self.a_inf.setChecked(self.state.grid_mode == "infinite")
        self.a_inf.triggered.connect(lambda: self.toggle_infinite_menu(self.a_inf.isChecked()))
        
        self.a_coords = view_menu.addAction("Show Coordinates")
        self.a_coords.setCheckable(True)
        self.a_coords.setChecked(False)
        self.a_coords.triggered.connect(lambda: self.toggle_coords_menu(self.a_coords.isChecked()))
        
        view_menu.addSeparator()
        
        self.a_threat_map = view_menu.addAction("Show Threat Map")
        self.a_threat_map.setToolTip("Displays AI-calculated danger zones on the map.")
        self.a_threat_map.setCheckable(True)
        self.a_threat_map.setChecked(getattr(self.state, "show_threat_map", False))
        self.a_threat_map.triggered.connect(lambda: self.toggle_threat_map(self.a_threat_map.isChecked()))
        
        self.a_show_rewards = view_menu.addAction("Show Rewards Over Head")
        self.a_show_rewards.setCheckable(True)
        self.a_show_rewards.setChecked(False)
        self.a_show_rewards.triggered.connect(lambda: self.toggle_rewards(self.a_show_rewards.isChecked()))
        
        view_menu.addSeparator()
        
        a_theme = view_menu.addAction("Switch Theme")
        a_theme.triggered.connect(self.toggle_theme_ribbon) # Reusing existing logic
        
        # --- Simulation Menu ---
        sim_menu = menubar.addMenu("Simulation")
        
        a_step = sim_menu.addAction(VectorIconPainter.create_icon("redo"), "Step")
        a_step.setShortcut("F10")
        a_step.triggered.connect(self.advance_simulation)
        
        a_play = sim_menu.addAction(VectorIconPainter.create_icon("play"), "Play")
        a_play.setShortcut("F5")
        a_play.triggered.connect(self.start_simulation_loop)
        
        a_pause = sim_menu.addAction(VectorIconPainter.create_icon("pause"), "Pause")
        a_pause.setShortcut("F6")
        a_pause.triggered.connect(self.pause_simulation)
        
        a_reset = sim_menu.addAction(VectorIconPainter.create_icon("refresh"), "Reset Environment")
        a_reset.triggered.connect(self.action_reset_env)
        
        sim_menu.addSeparator()
        
        a_gen_goal = sim_menu.addAction("Generate Goal Area")
        a_gen_goal.triggered.connect(lambda: self.action_generate_goal_area(self.hex_widget.hovered_hex))
        
        a_gen_attack = sim_menu.addAction("Generate Initial Attack Area")
        a_gen_attack.triggered.connect(lambda: self.action_generate_attack_area(self.hex_widget.hovered_hex))
        
        a_scatter_mines = sim_menu.addAction("Scatter Mines")
        a_scatter_mines.triggered.connect(self.action_scatter_mines)
        
        # --- Help Menu ---
        help_menu = menubar.addMenu("Help")
        
        a_manual = help_menu.addAction(VectorIconPainter.create_icon("help"), "Manual")
        a_manual.triggered.connect(self.show_user_manual)
        
        a_about = help_menu.addAction(VectorIconPainter.create_icon("info"), "About")
        a_about.triggered.connect(lambda: ThemedMessageBox.information(self, "About", "Wargame Engine v1.0"))
        



    def perform_autosave(self):
        """Save current map state to Live Directory."""
        if not self.state.project_path: return
        
        # Don't overwrite scenario file while simulation is modifying state!
        if self.sim_controller.is_running:
            return
        
        try:
            import json
            map_path = os.path.join(self.state.project_path, "map.json")
            
            # Serialize Map + Scenarios + Entities
            data = self.state.map.to_dict(include_scenarios=True, entity_manager=self.state.entity_manager)
            
            with open(map_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            # log.debug(f"Autosaved to {map_path}") # Spammy?
        except Exception as e:
            log.error(f"Autosave failed: {e}")

    def show_user_manual(self):
        """Display the User Manual in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("User Manual")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Determine path to USER_MANUAL.md
        manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "USER_MANUAL.md")
        if os.path.exists(manual_path):
            with open(manual_path, "r") as f:
                md_content = f.read()
                text_edit.setMarkdown(md_content)
        else:
            text_edit.setText(f"Error: Manual not found at {manual_path}")
            
        layout.addWidget(text_edit)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec_()

    def toggle_theme_ribbon(self):
        new = "light" if self.state.theme_mode == "dark" else "dark"
        self.set_theme(new)

    def set_theme(self, mode):
        """Sets the active theme and applies it across the UI."""
        self.state.theme_mode = mode
        self.apply_theme(mode)
        self.log_info(f"Theme switched to: <b>{mode.upper()}</b>")
    
    def apply_theme(self, mode):
        """Applies QSS and notifies widgets to update their internal colors."""
        # mode can be 'dark' or 'light'
        self.setStyleSheet(Theme.get_qss(mode))
        if hasattr(self.hex_widget, 'update_theme'):
             self.hex_widget.update_theme()
        self.hex_widget.update()


    def restart_app(self):
        """
        SYSTEM-SAFE RESTART: Spawns a new instance and exits the current one.
        Avoids 'os.execl' which can trigger session-level side effects (like Hyprland restarts) on Linux.
        """
        log.info("Initiating Application Restart...")
        
        from PyQt5.QtCore import QProcess
        import sys
        
        # 1. Spawn the new process before we die.
        #    startDetached ensures the new process lives independently.
        QProcess.startDetached(sys.executable, sys.argv)
        
        # 2. Trigger a clean shutdown.
        #    Calling self.close() ensures closeEvent runs, saving current projects.
        self.close()

    def open_map(self, map_name):
        """Load a selected map project directly via the service layer."""
        project = self.state.current_project
        if not project: return
        
        # Construct the project-standard path (UI still knows project folder for now)
        base_dir = self.state.data_controller.content_root
        map_dir = os.path.join(base_dir, "Projects", project, "Maps", map_name)
        
        result = map_svc.load_project_folder(map_dir)
        
        if result.ok:
            self.current_project_path = map_dir
            self.state.current_map = map_name
            
            # Refresh Scenario UI
            if hasattr(self, 'scenario_manager_group'):
                self.scenario_manager_group.refresh_list()
            
            self.switch_mode(1) # Terrain Mode
            
            # Critical: UI Reset and Visual Update
            self.hex_widget.recenter_view()
            self.action_model.reinit_models()
            self.hex_widget.refresh_map()
            
            self.log_info(f"Loaded Map: <b>{map_name}</b> ({result.data['scenarios_loaded']} scenarios)")
        else:
            ThemedMessageBox.critical(self, "Load Error", result.error)

    def switch_mode(self, index):
        """Unified mode switcher that synchronizes State Machine, Stacked Widgets, and Command Bar."""
        self.mode_machine.switch_mode(index)
        
        # Visually swap the main content
        if index == 0:
            self.content_stack.setCurrentWidget(self.maps_widget)
        elif index == 2:
            self.content_stack.setCurrentWidget(self.rules_widget)
        elif index == 8:
            self.content_stack.setCurrentWidget(self.master_data_widget)
        else:
            # All other tactical phases (1, 3-7) use the Theater view (Map + Side Panel)
            self.content_stack.setCurrentWidget(self.main_splitter)
            
        # Update Command Center Bar
        if hasattr(self, 'workflow_bar'):
            self.workflow_bar.set_state(
                index, 
                project_name=self.state.current_project,
                map_name=self.state.current_map
            )

    def update_tools_visibility(self):
        self.toolbar_controller.update_tools_visibility()

    def on_scenario_side_tab_changed(self, index):
        self.scenario_side_manager.on_scenario_side_tab_changed(index)

    def start_side_assignment(self):
        self.scenario_side_manager.start_side_assignment()

    def handle_section_click(self, hex_obj):
        self.scenario_side_manager.handle_section_click(hex_obj)

    def action_zoom_in(self):
        """Zooms the map view in."""
        self.hex_widget.zoom_by(1.2)
        
    def action_zoom_out(self):
        """Zooms the map view out."""
        self.hex_widget.zoom_by(1.0/1.2)

    def start_simulation_loop(self):
        self.sim_manager.start_simulation_loop()

    def pause_simulation(self):
        self.sim_manager.pause_simulation()

    def advance_simulation(self):
        self.sim_manager.advance_simulation()

    def action_reset_env(self, silent=False):
        self.sim_manager.action_reset_env(silent)
        self.hex_widget.refresh_map()

    def start_learning_phase(self):
        self.sim_manager.start_learning_phase()
    def closeEvent(self, event):
        """Called when the application is closing."""
        # 1. Save Window Layout (Geometry, Docks, Toolbars)
        UISettingsPersistence.save(self)
        
        # 2. Save current project if one is open
        self.action_save_project(silent=True)
        
        super().closeEvent(event)

    def auto_split_map(self, direction="Vertical", ratio=0.5):
        """
        THE CARTOGRAPHER (Auto-Border Tool):
        This function automatically draws a line across the map to separate 
        the starting territories of the Attacker and Defender.
        
        Parameters:
        - direction: "Vertical", "Horizontal", or "Diagonal".
        - ratio: A number from 0 to 1 (e.g., 0.5 splits it exactly in half).
        """
        width = self.state.map.width
        height = self.state.map.height
        from engine.core.hex_math import HexMath
        path = []
        
        # 1. CALCULATE THE LINE: Find the sequence of hexagons that form the cut.
        if direction == "Vertical":
            # Draw a straight line from top to bottom at a specific column.
            target_col = int(width * ratio)
            target_col = max(0, min(width-1, target_col)) # Keep it inside the map.
            for row in range(height):
                h = HexMath.offset_to_cube(target_col, row)
                path.append(h)
                
        elif direction == "Horizontal":
            # Draw a straight line from left to right at a specific row.
            target_row = int(height * ratio)
            target_row = max(0, min(height-1, target_row)) 
            for col in range(width):
                h = HexMath.offset_to_cube(col, target_row)
                path.append(h)
                
        else: # Diagonal
            # Draw a slanted line between two opposite corners.
            start_hex = None
            end_hex = None
            
            if "TL-BR" in direction:
                # From Top-Left corner to Bottom-Right.
                start_hex = HexMath.offset_to_cube(0, 0)
                end_hex = HexMath.offset_to_cube(width-1, height-1)
            else: # BL-TR: From Bottom-Left to Top-Right.
                start_hex = HexMath.offset_to_cube(0, height-1)
                end_hex = HexMath.offset_to_cube(width-1, 0)
            
            # Use the HexMath 'line' algorithm to find every hexagon between the corners.
            line_hexes = HexMath.line(start_hex, end_hex)
            path = line_hexes

        # 2. COMMIT: Save this line as the "Official Border" in the Map's memory.
        self.state.map.border_path = path
        
        # 3. VISUALS: Create a physical 'Path' entity on the map so you can see the Red line.
        import uuid
        path_id = str(uuid.uuid4())[:8]
        path_data = {
            "name": f"Auto {direction} ({ratio*100:.0f}%)",
            "hexes": path,
            "color": "#FF0000", # The classic Red border.
            "mode": "Center-to-Center",
            "type": "Border",
            "app_mode": "area"
        }
        self.state.map.add_path(path_id, path_data)
        
        self.log_info(f"Auto-Split Map: {direction} Border created.")
        self.hex_widget.update()
        
        # 4. ENFORCE OWNERSHIP: Automatically assign all hexagons to either 
        # the Attacker or Defender based on which side of the line they are on.
        self.start_side_assignment()

    def update_tools_visibility(self):
        mode = getattr(self.state, "app_mode", "terrain")
        
        # Define allowed tools per mode
        allowed = []
        if mode == "terrain":
            allowed = ["cursor", "edit", "eraser", "paint_tool"]
        elif mode == "area":
            allowed = ["cursor", "edit", "eraser", "draw_zone", "draw_path"]
        elif mode == "agents":
            side = getattr(self.state, "active_scenario_side", "Attacker")
            side = side.lower() if side else "attacker"
            if side == "defender":
                allowed = ["cursor", "eraser", "place_agent"]
            else:
                allowed = ["cursor", "eraser", "place_agent", "assign_goal"]
        elif mode == "play":
            side = getattr(self.state, "active_scenario_side", "Defender")
            if side.lower() == "defender":  # Blue
                allowed = ["cursor"]
            else:
                allowed = ["cursor", "assign_goal"]
            
        for action in self.tool_actions.values():
            tid = action.data()
            visible = tid in allowed
            action.setVisible(visible)
            action.setEnabled(visible)
                
        # Reset to cursor if current tool is hidden
        if self.state.selected_tool not in allowed:
            self.set_tool("cursor")

    def action_save_project(self, silent=False):
        """Standard project save: Map + all Scenarios."""
        if not silent:
            self.statusBar().showMessage("Saving Project...")
        else:
            self.statusBar().showMessage("Autosaving...", 3000)

        if not self.current_project_path:
            if silent: return
            if not self.action_new_project(reset_map=False):
                return

        # 1. Save Map (Terrain)
        terrain_path = os.path.join(self.current_project_path, "Terrain.json")
        res_map = map_svc.save_map(terrain_path)
        
        # 2. Save Scenarios
        res_scen = scenario_svc.save_all_scenarios(self.current_project_path)
        
        if res_map.ok and res_scen.ok:
            # 3. Handle UI-specific post-save (thumbnails, etc)
            self.generate_map_thumbnail(terrain_path)
            
            if not silent:
                self.statusBar().showMessage(f"Project Saved ({res_scen.data['saved_count']} scenarios)", 5000)
                ThemedMessageBox.information(self, "Success", "Project saved successfully.")
        else:
            if not silent:
                error = res_map.error or res_scen.error
                ThemedMessageBox.critical(self, "Save Error", f"Failed to save project: {error}")

    def generate_map_thumbnail(self, terrain_path):
        """UI-Specific logic to generate a gallery thumbnail."""
        try:
            from ui.views.hex_renderer import HexRenderer
            pixmap = HexRenderer.render_map_to_image(self.state.map, 500, 400)
            thumb_path = os.path.join(os.path.dirname(terrain_path), "thumbnail.png")
            pixmap.save(thumb_path, "PNG")
            if hasattr(self, 'maps_widget'):
                 self.maps_widget.refresh_list()
        except Exception as e:
            log.error(f"Failed to save thumbnail: {e}")

    # do_save_map removed — functionality moved to action_save_project + map_svc.save_map

    def action_save_scenario(self):
        """Save the active scenario as a new file in the project."""
        if not self.current_project_path:
            ThemedMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        name, ok = QInputDialog.getText(self, "Save Scenario", "Scenario Name:")
        if ok and name:
            # We use scenario_svc for saving
            result = scenario_svc.save_scenario() # This saves current active
            if result.ok:
                # For now, let's keep it simple and use the service-wrapped save_all for the project
                self.action_save_project(silent=True)
                ThemedMessageBox.information(self, "Success", f"Scenario '{name}' added to Project.")
            else:
                 ThemedMessageBox.critical(self, "Error", result.error)

    def action_load_scenario(self):
        """Load a single scenario JSON into the active map world."""
        base = os.path.join(self.current_project_path, "Scenarios") if self.current_project_path else self.data_loader.content_root
        os.makedirs(base, exist_ok=True)
        
        filename, _ = QFileDialog.getOpenFileName(self, "Load Scenario", base, "Scenario (*.json)")
        if filename:
            result = scenario_svc.load_scenario(filename)
            if result.ok:
                self.hex_widget.refresh_map()
                self.log_info(f"Loaded scenario: {result.data['name']}")
            else:
                ThemedMessageBox.critical(self, "Error", result.error)

    def action_load_project(self):
        """Standard project folder load via map_svc."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Project / Map Folder", self.data_loader.content_root)
        if not dir_path: return

        # Try to find Terrain.json if user picked the root project folder
        if not os.path.exists(os.path.join(dir_path, "Terrain.json")):
             maps_dir = os.path.join(dir_path, "Maps")
             if os.path.exists(maps_dir):
                 subs = [d for d in os.listdir(maps_dir) if os.path.isdir(os.path.join(maps_dir, d))]
                 if subs:
                     dir_path = os.path.join(maps_dir, subs[0])

        result = map_svc.load_project_folder(dir_path)
        if result.ok:
            self.current_project_path = dir_path
            self.state.current_map = result.data['map_name']
            self._save_last_project(dir_path)
            
            self.action_model.reinit_models()
            self.hex_widget.refresh_map()
            
            ThemedMessageBox.information(self, "Success", f"Loaded Project: {result.data['map_name']}")
            self.setWindowTitle(f"Wargame Engine - {result.data['map_name']}")
            
            if hasattr(self, 'maps_widget'): self.maps_widget.refresh_list()
        else:
            ThemedMessageBox.critical(self, "Load Error", result.error)

    def action_reload_master_data(self):
         """Hot-reloads Master Data JSON files without a full app restart.""" # Docstring for the function.
         try:
             # Repopulate Layer 2 caches
             self.state.data_controller.reload_catalogs() # Instruct the data controller to reload all catalogs.
             # Refresh Data Tree if visible
             if hasattr(self, 'master_data_widget'): # Check if the master data widget exists.
                 self.master_data_widget.refresh_tree() # Refresh its tree view.
                 
             ThemedMessageBox.information(self, "Success", "Master Data Reloaded Successfully.") # Show a success message.
         except Exception as e: # Catch any exceptions during data reloading.
             ThemedMessageBox.critical(self, "Error", f"Failed to reload JSON configs: {e}") # Show a critical error message.

    def action_new_project(self, reset_map=True):
        parent_dir = QFileDialog.getExistingDirectory(self, "Select Parent Folder for New Project", self.data_loader.content_root)
        if not parent_dir: return False

        name, ok = QInputDialog.getText(self, "New Project", "Project Name:")
        if ok and name:
            project_dir = os.path.join(parent_dir, name)
            if os.path.exists(project_dir):
                 ThemedMessageBox.warning(self, "Error", f"Folder '{name}' already exists.")
                 return False
            
            try:
                # V3 Folder Structure: [Project]/Maps/[MapName]/Terrain.json
                map_dir = os.path.join(project_dir, "Maps", name)
                os.makedirs(map_dir, exist_ok=True)
                os.makedirs(os.path.join(map_dir, "Scenarios"), exist_ok=True)
                
                # Create default terrain
                terrain_path = os.path.join(map_dir, "Terrain.json")
                terrain_data = {
                    "dimensions": {"width": self.state.map.width, "height": self.state.map.height},
                    "grid": {"default": "plain"},
                    "layers": {}
                }
                with open(terrain_path, 'w') as f:
                    json.dump(terrain_data, f, indent=4)
                
                self.state.current_project = name
                self.state.current_map = name
                self.current_project_path = map_dir
                self._save_last_project(map_dir)
                
                if reset_map:
                    self.state.map = self.state.map.__class__()
                    self.state.entity_manager._entities = {}
                    self.hex_widget.recenter_view()
                    self.action_model.reinit_models()
                    self.hex_widget.refresh_map()
                
                ThemedMessageBox.information(self, "New Project", f"Project '{name}' created at {project_dir}")
                self.setWindowTitle(f"Wargame Engine - {name} / {name}")
                
                if hasattr(self, 'maps_widget'):
                    self.maps_widget.refresh_list()
                    
                return True
            except Exception as e:
                ThemedMessageBox.critical(self, "Error", f"Failed to create project: {e}")
                return False
        return False

    def action_create_new_map(self):
        """Creates a new map within the CURRENT project."""
        if not self.state.current_project or not self.current_project_path:
            ThemedMessageBox.warning(self, "No Project", "No project is currently active. Please create or load a project first.")
            return

        name, ok = QInputDialog.getText(self, "New Map", "Map Name:")
        if ok and name:
            # Structure: [ProjectRoot]/Maps/[name]/Terrain.json
            project_root = os.path.dirname(os.path.dirname(self.current_project_path))
            map_dir = os.path.join(project_root, "Maps", name)
            
            if os.path.exists(map_dir):
                ThemedMessageBox.warning(self, "Error", f"Map '{name}' already exists in this project.")
                return

            try:
                os.makedirs(map_dir, exist_ok=True)
                os.makedirs(os.path.join(map_dir, "Scenarios"), exist_ok=True)
                
                terrain_path = os.path.join(map_dir, "Terrain.json")
                terrain_data = {
                    "dimensions": {"width": self.state.map.width, "height": self.state.map.height},
                    "grid": {"default": "plain"},
                    "layers": {}
                }
                with open(terrain_path, 'w') as f:
                    json.dump(terrain_data, f, indent=4)
                
                self.state.current_map = name
                self.current_project_path = map_dir
                self.state.map = self.state.map.__class__()
                self.state.entity_manager._entities = {}
                self.hex_widget.recenter_view()
                self.action_model.reinit_models()
                self.hex_widget.refresh_map()
                
                ThemedMessageBox.information(self, "Success", f"Created map '{name}' in project '{self.state.current_project}'")
                self.setWindowTitle(f"Wargame Engine - {self.state.current_project} / {name}")
                
                if hasattr(self, 'maps_widget'):
                    self.maps_widget.refresh_list()
            except Exception as e:
                ThemedMessageBox.critical(self, "Error", f"Failed to create map: {e}")

    def action_resize_map(self):
        """THE CIVIL ENGINEER: Change the dimensions of the world.""" # Docstring for the function.
        # Pop up a small form to ask for Width and Height.
        d = QDialog(self) # Create a new QDialog.
        d.setWindowTitle("Resize Map") # Set the dialog window title.
        l = QFormLayout(d) # Create a QFormLayout for the dialog.
        
        w_spin = QSpinBox() # Create a QSpinBox for width input.
        w_spin.setRange(10, 10000) # Set the valid range for width.
        w_spin.setValue(self.state.map.width) # Set the initial value to the current map width.
        
        h_spin = QSpinBox() # Create a QSpinBox for height input.
        h_spin.setRange(10, 10000) # Set the valid range for height.
        h_spin.setValue(self.state.map.height) # Set the initial value to the current map height.
        
        l.addRow("Width:", w_spin) # Add the width spin box to the form layout.
        l.addRow("Height:", h_spin) # Add the height spin box to the form layout.
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel) # Create OK and Cancel buttons.
        bb.accepted.connect(d.accept) # Connect the accepted signal to the dialog's accept slot.
        bb.rejected.connect(d.reject) # Connect the rejected signal to the dialog's reject slot.
        l.addRow(bb) # Add the button box to the form layout.
        
        if d.exec_() == QDialog.Accepted: # If the dialog was accepted (OK button clicked).
            # Update the map size and redraw everything.
            self.state.map.width = w_spin.value() # Update the map's width with the new value.
            self.state.map.height = h_spin.value() # Update the map's height with the new value.
            self.hex_widget.update() # Request a redraw of the hex widget to reflect the new size.

    def action_clear_map(self):
        """THE BULLDOZER: Wipe everything clean.""" # Docstring for the function.
        res = ThemedMessageBox.warning(self, "Clear Map", "This will wipe all terrain and zones. Continue?", QMessageBox.Yes | QMessageBox.No) # Show a warning message box.
        if res == QMessageBox.Yes: # If the user confirms to clear the map.
            self.state.map._terrain = {} # Clear all terrain data.
            self.state.map.active_scenario._zones = {} # Clear all mission zones from the active scenario.
            self.hex_widget.update() # Request a redraw of the hex widget.

    # set_theme defined above at line 475 — removed duplicate here
        
    def toggle_infinite_menu(self, checked):
        self.state.grid_mode = "infinite" if checked else "bounded" # Set grid mode based on checkbox state.
        self.hex_widget.update() # Request a redraw of the hex widget.
        
    def toggle_coords_menu(self, checked):
        self.hex_widget.show_coords = checked # Set coordinate visibility based on checkbox state.
        self.hex_widget.update() # Request a redraw of the hex widget.
        
    def toggle_rewards(self, checked):
        self.hex_widget.show_rewards = checked
        self.hex_widget.update()
        self.statusBar().showMessage(f"Reward Visualization: {'ON' if checked else 'OFF'}")

    def toggle_threat_map(self, checked):
        self.state.show_threat_map = checked
        if hasattr(self, 'hex_widget'):
            self.hex_widget.show_threat_map = checked
            self.hex_widget.update()

    def toggle_reward_viz(self, checked):
        self.state.show_reward_viz = checked
        if hasattr(self, 'hex_widget'):
            self.hex_widget.show_rewards = checked
            self.hex_widget.update()
        

    def action_reset_camera(self):
        """Resets the map view to default zoom and position."""
        self.hex_widget.scale = 1.0
        self.hex_widget.offset_x = 0
        self.hex_widget.offset_y = 0
        self.hex_widget.update()
        self.log_info("Camera Reset")

    def action_add_border(self):
        self.auto_split_map()

    def toggle_tactical_panel(self, checked):
        self.toc_dock.setVisible(checked)

    def toggle_timeline_panel(self, checked):
        if hasattr(self, 'timeline_dock'):
            self.timeline_dock.setVisible(checked)
        if hasattr(self, 'terminal_dock'):
            self.terminal_dock.setVisible(checked)

    def set_tool(self, tool_id):
        """
        Switch the active tool and update the UI accordingly.
        """ # Docstring for the function.
        # Prevent recursion and unnecessary updates
        if getattr(self.state, 'selected_tool', None) == tool_id:
            return 

        active_side = getattr(self.state, "active_scenario_side", "Attacker") # Get the active scenario side.

        # 🚫 Disable Assign Goal for BLUE (Defender)
        if tool_id == "assign_goal" and active_side.lower() == "defender": # If trying to assign goal as defender.
            self.log_info("<span style='color:red;'>Assign Goal is disabled for BLUE side.</span>") # Log a warning.
            return # Exit the function.

        # Update state
        self.state.selected_tool = tool_id 
        
        # Visually sync the UI toolbar button if switched via shortcut
        if hasattr(self, 'toolbar_controller') and tool_id in self.toolbar_controller.tool_actions:
            action = self.toolbar_controller.tool_actions[tool_id]
            if not action.isChecked():
                action.blockSignals(True)
                action.setChecked(True)
                action.blockSignals(False)

        # Update HexWidget
        if hasattr(self, 'hex_widget'):
            self.hex_widget.set_tool(tool_id)

        self.log_info(f"Tool selected: <b>{tool_id}</b>") # Log the selected tool.
        self.update_tool_options() # Update the tool options panel to reflect the new tool.

    def update_tool_options(self):
        """THE DYNAMIC OPTIONS: Delegates settings display to the Tactical Sidebar."""
        if hasattr(self, 'tac_panel'):
            self.tac_panel.sync_to_tool(self.state.selected_tool)
            
        if hasattr(self, 'object_properties_widget'):
            self.object_properties_widget.show_properties(None, None)

        return # Unified UI Fix
        app_mode = getattr(self.state, "app_mode", "terrain") # Get the current application mode.
        if tool == "draw_zone":
            self.tool_opts_group.show()
            
            # Form Layout Spacing
            self.tool_opts_layout.setSpacing(10)
            self.tool_opts_layout.setContentsMargins(5, 5, 5, 5)
            
            # Header Label for Intuition (ID for Special Styling)
            header = QLabel("ZONE CONFIGURATION")
            header.setObjectName("InspectorLabel")
            self.tool_opts_layout.addRow(header)

            label_instr = QLabel("Define clickable regions on the map.")
            label_instr.setStyleSheet("color: #777777; font-size: 11px; margin-bottom: 10px;")
            self.tool_opts_layout.addRow(label_instr)
            
            # Name Input
            if not hasattr(self.state, 'zone_opt_name'): self.state.zone_opt_name = ""
            name_edit = QLineEdit(self.state.zone_opt_name)
            name_edit.setPlaceholderText("Optional: Custom Name")
            name_edit.textChanged.connect(lambda t: setattr(self.state, 'zone_opt_name', t))
            
            # Add label for Name
            name_label = QLabel("Zone Name")
            name_label.setObjectName("InspectorLabel")
            self.tool_opts_layout.addRow(name_label, name_edit)

            # Type Dropdown
            type_combo = QComboBox()
            if app_mode == "terrain":
                type_combo.addItems(["Terrain"])
            elif app_mode in ("area", "agents"):
                active_side = getattr(self.state, "active_scenario_side", "Attacker")
                if active_side == "Attacker":
                    type_combo.addItems(["Attacker Area", "Obstacle"])
                else:
                    type_combo.addItems(["Defender Area", "Goal Area", "Obstacle"])
            else:
                type_combo.addItems(["Attacker Area", "Defender Area", "Goal Area", "Obstacle"])
                
            # Restore selection if valid
            curr_type = getattr(self.state, 'zone_opt_type', "") # Get the current zone option type from state.
            if curr_type and type_combo.findText(curr_type) >= 0: # If a valid current type exists in the combo box.
                 type_combo.setCurrentText(curr_type) # Set the combo box to that type.
            
            # Subtype Dropdown (Dependent)
            subtype_combo = QComboBox() # Create a QComboBox for zone subtype.
            
            def update_subtypes(idx): # Define a helper function to update subtypes based on selected type.
                t = type_combo.currentText() # Get the currently selected type text.
                self.state.zone_opt_type = t # Update the zone_opt_type in state.
                subtype_combo.clear() # Clear existing items in the subtype combo box.
                
                if app_mode == "terrain": # If in terrain mode.
                    # Dynamic Terrain List
                    keys = self.state.terrain_controller.get_available_terrains() # Get available terrain keys.
                    display_keys = sorted([k.title() for k in keys]) # Capitalize and sort them for display.
                    subtype_combo.addItems(display_keys) # Add them to the subtype combo box.
                else: # If in scenario or other modes.
                    # Master DB Lookup
                    items = [] # Initialize an empty list for items.
                    if "Attacker" in t: # If the type is related to Attacker.
                         if hasattr(self.state, 'data_controller'): # Check if data controller exists.
                             items = sorted(list(self.state.data_controller.zone_types.get("Attacker", {}).keys())) # Get Attacker zone types.
                    elif "Defender" in t: # If the type is related to Defender.
                         if hasattr(self.state, 'data_controller'): # Check if data controller exists.
                             items = sorted(list(self.state.data_controller.zone_types.get("Defender", {}).keys())) # Get Defender zone types.
                    elif t == "Obstacle": # If the type is "Obstacle".
                         if hasattr(self.state, 'data_controller'): # Check if data controller exists.
                             items = sorted(list(self.state.data_controller.obstacle_types.keys())) # Get Obstacle types.
                    
                    if items: # If there are items to add.
                         subtype_combo.addItems(items) # Add them to the subtype combo box.
                    else:
                         subtype_combo.addItem("None Found") # Add "None Found" if no items.

                self.state.zone_opt_subtype = subtype_combo.currentText() # Update the zone_opt_subtype in state.
            
            type_combo.currentIndexChanged.connect(update_subtypes) # Connect type combo box change to update_subtypes.
            subtype_combo.currentTextChanged.connect(lambda t: setattr(self.state, 'zone_opt_subtype', t)) # Connect subtype combo box change to update state.
            
            # Init
            update_subtypes(0) # Call update_subtypes once to initialize.
            
            # Add labels for remaining fields
            type_label = QLabel("Zone Type")
            type_label.setObjectName("InspectorLabel")
            self.tool_opts_layout.addRow(type_label, type_combo)
            
            # Subtype Label
            subtype_label = QLabel("Sub-Type Selection")
            subtype_label.setObjectName("InspectorLabel")
            self.tool_opts_layout.addRow(subtype_label, subtype_combo)
            
            if app_mode == "terrain": # If in terrain mode.
                h_layout = QHBoxLayout() # Create a horizontal layout.
                h_layout.addWidget(subtype_combo) # Add subtype combo box.
                btn_new = QToolButton() # Create a new QToolButton.
                btn_new.setText("+") # Set button text to "+".
                btn_new.setToolTip("Create New Terrain Type") # Set tooltip.
                btn_new.clicked.connect(self.prompt_new_terrain) # Connect click to prompt_new_terrain.
                h_layout.addWidget(btn_new) # Add button to horizontal layout.
                self.tool_opts_layout.addRow("Subtype/ID:", h_layout) # Add horizontal layout to form layout.
            else: # For other modes.
                self.tool_opts_layout.addRow("Subtype/ID:", subtype_combo) # Add subtype combo box directly.
                
            self.tool_opts_layout.addRow(QLabel("<i>Right Click to Commit</i>")) # Add an instructional label.
            
        elif tool == "draw_path":
            self.tool_opts_group.show()

            # Form Layout Spacing
            self.tool_opts_layout.setSpacing(10)
            self.tool_opts_layout.setContentsMargins(5, 5, 5, 5)

            # Header Label
            header = QLabel("<b>PATH CONFIGURATION</b>")
            header.setStyleSheet("color: #3daee9; font-size: 14px; margin-bottom: 2px;")
            self.tool_opts_layout.addRow(header)

            label_instr = QLabel("Draw tactical lines, roads, or borders.")
            label_instr.setStyleSheet("color: #777777; font-size: 11px; margin-bottom: 10px;")
            self.tool_opts_layout.addRow(label_instr)
            
            # Name Input
            if not hasattr(self.state, 'path_opt_name'): self.state.path_opt_name = "" # Initialize path_opt_name.
            path_name_edit = QLineEdit(self.state.path_opt_name) # Create QLineEdit for path name.
            path_name_edit.setPlaceholderText("Optional: Custom Name") # Set placeholder text.
            path_name_edit.textChanged.connect(lambda t: setattr(self.state, 'path_opt_name', t)) # Connect text change to update state.
            
            # Path Type Dropdown
            path_type_combo = QComboBox() # Create QComboBox for path type.
            default_items = ["Canal", "Road"] if app_mode == "terrain" else ["Border", "Supply Line"] # Define default items based on app mode.
            
            # Add Customs
            customs = getattr(self.state, 'custom_path_types', []) # Get custom path types from state.
            all_items = default_items + customs # Combine default and custom items.
            path_type_combo.addItems(all_items) # Add all items to the combo box.
            
            def on_path_type_change(t): # Define helper function for path type change.
                 self.state.path_opt_type = t # Update path_opt_type in state.
                 # Set default color if standard type
                 defaults = {"Canal": "#00FFFF", "Road": "#8B4513", "Border": "#FF0000", "Supply Line": "#00FF00"} # Define default colors.
                 defaults.update(getattr(self.state, 'custom_path_colors', {})) # Update with custom path colors.
                 
                 if t in defaults: # If the selected type has a default color.
                      self.state.path_opt_color = defaults[t] # Set the path_opt_color in state.
            
            path_type_combo.currentTextChanged.connect(on_path_type_change) # Connect text change to on_path_type_change.
            
            # Init state defaults
            current_t = self.state.path_opt_type if hasattr(self.state, 'path_opt_type') else path_type_combo.itemText(0) # Get current type or first item.
            path_type_combo.setCurrentText(current_t) # Set the combo box text.
            
            # Ensure color is set for initial/current
            on_path_type_change(current_t) # Call to set initial color.
            
            # Path Mode Dropdown
            path_mode_combo = QComboBox() # Create QComboBox for path mode.
            path_mode_combo.addItems(["Center-to-Center", "Edge-Aligned"]) # Add path mode options.
            path_mode_combo.setCurrentText(self.state.path_mode) # Set current text from state.
            path_mode_combo.currentTextChanged.connect(lambda t: setattr(self.state, 'path_mode', t)) # Connect text change to update state.
            
            self.tool_opts_layout.addRow("Name:", path_name_edit) # Add name input to layout.
            
            h_path = QHBoxLayout() # Create horizontal layout for path type and new button.
            h_path.addWidget(path_type_combo) # Add path type combo box.
            btn_new_p = QToolButton() # Create new QToolButton.
            btn_new_p.setText("+") # Set button text.
            btn_new_p.setToolTip("Create New Path Type") # Set tooltip.
            btn_new_p.clicked.connect(self.prompt_new_path_type) # Connect click to prompt_new_path_type.
            h_path.addWidget(btn_new_p) # Add button to horizontal layout.
            
            self.tool_opts_layout.addRow("Path Type:", h_path) # Add horizontal layout to form layout.
            self.tool_opts_layout.addRow("Draw Mode:", path_mode_combo) # Add path mode combo box to layout.
            self.tool_opts_layout.addRow(QLabel("<i>Right Click to Commit</i>")) # Add instructional label.
            
        elif tool == "place_agent":
            self.tool_opts_group.show()

            # Header Label
            header = QLabel("<b>AGENT DEPLOYMENT</b>")
            header.setStyleSheet("color: #3daee9; font-size: 14px; margin-bottom: 2px;")
            self.tool_opts_layout.addRow(header)

            label_instr = QLabel("Place individual units on the battlefield.")
            label_instr.setStyleSheet("color: #777777; font-size: 11px; margin-bottom: 10px;")
            self.tool_opts_layout.addRow(label_instr)
            
            # Side Selection First (to filter names)
            if not hasattr(self.state, 'place_opt_side'): self.state.place_opt_side = "Attacker" # Initialize place_opt_side.
            
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
            
            if app_mode in ("area", "agents"): # If in area or agents mode.
                active_side = getattr(self.state, "active_scenario_side", "Attacker") # Get active scenario side.
                if active_side == "Combined": # If active side is "Combined".
                    side_widget.setEnabled(True)
                    if self.state.place_opt_side == "Defender":
                        radio_defender.setChecked(True)
                    else:
                        radio_attacker.setChecked(True)
                else: # If active side is Attacker or Defender.
                    side_widget.setEnabled(False) # Lock to current tab's side.
                    self.state.place_opt_side = active_side # Set state's place_opt_side to active side.
                    if active_side == "Defender":
                        radio_defender.setChecked(True)
                    else:
                        radio_attacker.setChecked(True)
            else: # For other modes.
                side_widget.setEnabled(True)
                if self.state.place_opt_side == "Defender":
                    radio_defender.setChecked(True)
                else:
                    radio_attacker.setChecked(True)
            
            # Name Dropdown (Dynamic from Master Database)
            if not hasattr(self.state, 'place_opt_name'): self.state.place_opt_name = "" # Initialize place_opt_name.
            name_combo = QComboBox() # Create QComboBox for agent name.
            
            def update_names(): # Define helper function to update agent names based on selected side.
                side = "Attacker" if radio_attacker.isChecked() else "Defender" # Get selected side.
                self.state.place_opt_side = side # Update place_opt_side in state.
                
                name_combo.clear() # Clear existing items.
                
                keys = [] # Initialize empty list for keys.
                if hasattr(self.state, 'data_controller') and side in self.state.data_controller.agent_types: # Check for data controller and agent types for the side.
                     keys = sorted(list(self.state.data_controller.agent_types[side].keys())) # Get and sort agent type keys.
                
                if keys: # If there are keys.
                    name_combo.addItems(keys) # Add them to the name combo box.
                else:
                    name_combo.addItem("No Agents Found") # Add "No Agents Found" if none.
                
                # Restore selection if possible
                if self.state.place_opt_name in keys: # If the previously selected name is in the new keys.
                     name_combo.setCurrentText(self.state.place_opt_name) # Set the combo box to that name.
                elif keys: # If there are new keys but previous name not found.
                     self.state.place_opt_name = keys[0] # Set to the first available agent.

            radio_attacker.toggled.connect(update_names)
            radio_defender.toggled.connect(update_names)
            name_combo.currentTextChanged.connect(lambda t: setattr(self.state, 'place_opt_name', t)) # Connect name combo box change to update state.

            # Init
            update_names() # Call update_names once to initialize.

            # Agent Personnel
            if not hasattr(self.state, 'place_opt_personnel'): self.state.place_opt_personnel = 100 
            pers_spin = QSpinBox() # Create QSpinBox for personnel.
            pers_spin.setRange(0, 1000) # Set personnel range.
            pers_spin.setValue(self.state.place_opt_personnel) 
            pers_spin.valueChanged.connect(lambda v: setattr(self.state, 'place_opt_personnel', v)) 
            
            self.tool_opts_layout.addRow("Side:", side_widget) # Add side widget to layout.
            self.tool_opts_layout.addRow("Agent Type:", name_combo) # Add agent type combo box to layout.
            self.tool_opts_layout.addRow("Personnel:", pers_spin) # Add personnel spin box to layout.
            
        else: # If no specific tool options are defined for the current tool.
            self.tool_opts_group.hide() # Hide the tool options group.

    def setup_right_panel(self):
        """LEGACY: Replaced by TacticalSidePanel (TOC)."""
        pass
    def setup_object_inspector(self):
        """LEGACY: Replaced by TacticalSidePanel (TOC)."""
        # We still need tool_opts_layout references for some tool logic compatibility
        from PyQt5.QtWidgets import QGroupBox, QFormLayout
        self.tool_opts_group = QGroupBox("Tool Options")
        self.tool_opts_layout = QFormLayout()
        self.tool_opts_group.setLayout(self.tool_opts_layout)

    def on_scenario_side_tab_changed(self, index):
        """LEGACY: Side switching is now handles by linear phases in TOC."""
        pass
                  
    def _final_state_sync(self):
        """Internal cleanup for side assignment and tool refreshing."""
        self.update_tool_options()
        self.update_tools_visibility()
        if hasattr(self, 'hex_widget'):
            self.hex_widget.update()

    def on_hex_clicked(self, hex_obj):
        # Triggered when a hex is clicked
        
        # 1. Side Picking Mode (Special Flow)
        if getattr(self.state, 'assign_sides_mode', False):
            self.handle_section_click(hex_obj)
            return

        # 2. General Tool Logic
        tool = self.state.selected_tool
        if tool == "cursor":
            if hasattr(self, 'scene_hierarchy_widget'):
                self.scene_hierarchy_widget.select_by_hex(hex_obj)
        elif tool == "eraser":
            self.state.map.clear_hex(hex_obj)
            self.hex_widget.update()
            if hasattr(self, 'scene_hierarchy_widget'): self.scene_hierarchy_widget.refresh_tree()
        elif tool == "place_agent":
            # Delegate to Tool class (handled via mousePress event)
            pass

            if hasattr(self, 'scene_hierarchy_widget'): self.scene_hierarchy_widget.refresh_tree()

    def prompt_new_path_type(self):
        """Dialog to create a new custom path type (like 'Secret Tunnel' or 'Minefield')."""
        from PyQt5.QtGui import QPixmap, QColor, QIcon
        
        dialog = QDialog(self)
        dialog.setWindowTitle("New Path Type")
        
        dialog.setStyleSheet(Theme.get_dialog_style())
        
        layout = QFormLayout(dialog)
        name_input = QLineEdit()
        
        # Color Selection
        color_layout = QHBoxLayout()
        color_edit = QLineEdit("#FF00FF")
        preview_label = QLabel()
        preview_label.setFixedSize(24, 24)
        preview_label.setStyleSheet("background-color: #FF00FF; border: 1px solid #555; border-radius: 12px;")
        
        def update_preview(text):
            if QColor.isValidColor(text):
                 preview_label.setStyleSheet(f"background-color: {text}; border: 1px solid #555; border-radius: 12px;")
        color_edit.textChanged.connect(update_preview)
        
        color_layout.addWidget(preview_label)
        color_layout.addWidget(color_edit)
        
        layout.addRow("Path Name:", name_input)
        layout.addRow("Color Hex:", color_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_():
            name = name_input.text().strip()
            if not name: return
            
            color_hex = color_edit.text().strip()
            if not color_hex.startswith("#"): color_hex = "#" + color_hex
            
            # Update State
            if not hasattr(self.state, 'custom_path_types'): self.state.custom_path_types = []
            if not hasattr(self.state, 'custom_path_colors'): self.state.custom_path_colors = {}
            
            self.state.custom_path_types.append(name)
            self.state.custom_path_colors[name] = color_hex
            
            self.log_info(f"Created new path type: <b>{name}</b>")
            self.update_tool_options()

    def prompt_new_terrain(self):
        """THE LANDSCAPER: Creates a custom terrain type (like 'Swamp' or 'Lava')."""
        from PyQt5.QtGui import QPixmap, QColor, QIcon
        
        dialog = QDialog(self)
        dialog.setWindowTitle("New Terrain Type")
        
        dialog.setStyleSheet(Theme.get_dialog_style())
        
        layout = QFormLayout(dialog)
        
        # 1. Name Input
        name_input = QLineEdit()
        
        # 2. Color Selection: Hex Code + Presets
        color_layout = QHBoxLayout()
        color_edit = QLineEdit("#808080")
        
        # Color Preview Circle
        preview_label = QLabel()
        preview_label.setFixedSize(24, 24)
        preview_label.setStyleSheet("background-color: #808080; border: 1px solid #555; border-radius: 12px;")
        
        def update_preview(text):
            if QColor.isValidColor(text):
                 preview_label.setStyleSheet(f"background-color: {text}; border: 1px solid #555; border-radius: 12px;")
        color_edit.textChanged.connect(update_preview)
        
        preset_combo = QComboBox()
        # Common colors for quick picking.
        preset_map = {
            "Gray": "#808080", "Brown": "#8B4513", "Forest Green": "#228B22", 
            "Steel Blue": "#4682B4", "Red": "#FF0000", "Yellow": "#FFFF00"
        }
        
        preset_combo.addItem("Presets...")
        for n, code in preset_map.items():
            preset_combo.addItem(n, code)
            
        def apply_preset(idx):
            code = preset_combo.itemData(idx)
            if code: color_edit.setText(code)
        preset_combo.currentIndexChanged.connect(apply_preset)
        
        color_layout.addWidget(preview_label)
        color_layout.addWidget(color_edit)
        color_layout.addWidget(preset_combo)
        
        # 3. Movement Cost: How hard is it to cross this land? (1=Easy, 10=Hard)
        cost_input = QSpinBox()
        cost_input.setRange(1, 100)
        cost_input.setValue(1)
        
        # 4. Elevation: Height/Depth.
        elev_input = QSpinBox()
        elev_input.setRange(-20, 20) 
        elev_input.setValue(0) 
        
        layout.addRow("Name:", name_input)
        layout.addRow("Color:", color_layout)
        layout.addRow("Movement Cost:", cost_input)
        layout.addRow("Elevation:", elev_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_():
            name = name_input.text().strip()
            if not name: return
            
            color_hex = color_edit.text().strip()
            if not color_hex.startswith("#"): color_hex = "#" + color_hex
            
            data = {
                "color": color_hex,
                "cost": cost_input.value(),
                "elevation": elev_input.value(),
                "stack_value": 0,
                "visibility": 1.0
            }
            
            # Save it to the specialized manager.
            success = self.state.terrain_controller.create_terrain_type(name, data)
            if success:
                self.log_info(f"Created new terrain: <b>{name}</b>")
                self.update_tools_visibility()
                self.update_tool_options()
            else:
                ThemedMessageBox.warning(self, "Error", f"Failed to create terrain '{name}'.")

    # Scenario Side Management delegated to ScenarioSideManager

    def setup_timeline_panel(self):
        """THE CONTROL CENTER: Setup the Simulation Timeline panel and Terminal."""
        from ui.views.timeline_panel import TimelinePanel
        from ui.components.event_log_widget import EventLogWidget
        
        # 1. Mission Control Dock (Right)
        self.timeline_dock = QDockWidget("Mission Control", self)
        self.timeline_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.timeline_panel = TimelinePanel(self, self.state)
        self.timeline_dock.setWidget(self.timeline_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.timeline_dock)
        self.timeline_dock.hide() # Hidden by default
        
        # 2. Tactical Log Console (Bottom)
        self.terminal_dock = QDockWidget("MISSION LOG", self)
        self.terminal_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.event_log_widget = EventLogWidget()
        self.event_log_widget.popout_requested.connect(self.popout_log)
        self.terminal_dock.setWidget(self.event_log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.terminal_dock)
        self.terminal_dock.hide() # Hidden by default
        
        # Tabify Mission Control with TOC for a clean layout
        if hasattr(self, 'toc_dock'):
             self.tabifyDockWidget(self.toc_dock, self.timeline_dock)
             self.toc_dock.raise_()

    def popout_log(self):
        """Detaches or Re-attaches the Tactical Terminal dock."""
        self.terminal_dock.setFloating(not self.terminal_dock.isFloating())
        if hasattr(self, 'event_log_widget'):
            if self.terminal_dock.isFloating():
                self.event_log_widget.set_popout_text("Pop In")
            else:
                self.event_log_widget.set_popout_text("Pop Out")
            
    def log_info(self, message):
        """Append a message to the Info Log panel and sync with Tactical Sidebar."""
        # 1. Update the Unified Side Panel (TOC) with the latest operational news
        if hasattr(self, 'tac_panel'):
            self.tac_panel.update_stats(message)

        # 2. Add to the Permanent Event Console (Terminal)
        if hasattr(self, 'event_log_widget'):
            self.event_log_widget.log_info(message)
        elif hasattr(self, 'info_log'):
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.info_log.append(f"<span style='color: #888888;'>[{timestamp}]</span> {message}")
            self.info_log.verticalScrollBar().setValue(self.info_log.verticalScrollBar().maximum())

    def sanitize_agents(self):
        """Remove agents that are not placed on the map to prevent crashes."""
        if hasattr(self.state.map, 'active_scenario') and self.state.map.active_scenario:
             all_entities = list(self.state.entity_manager._entities.keys())
             for aid in all_entities:
                  pos = self.state.map.get_entity_position(aid)
                  if pos is None:
                       self.log_info(f"Removing unplaced agent {aid} from simulation.")
                       self.state.entity_manager.remove_entity(aid)

    # Simulation Callback logic delegated to SimulationManager

    def update_clock(self):
        """Update the digital clock in the status bar."""
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.clock_label.setText(current_time)

        
    # Simulation Control delegated to SimulationManager

        
    # Simulation Pause delegated to SimulationManager
    # Simulation Reset delegated to SimulationManager
    
    def action_generate_goal_area(self, goal_hex):
        """Creates a Strategic Objective zone at the specified hex (spawning defenders)."""
        from ui.dialogs.themed_dialogs import ThemedMessageBox
        res_z = zone_svc.add_objective(goal_hex)
        if res_z.ok:
            self.log_info(f"Generated Objective at {goal_hex}.")
            self.hex_widget.refresh_map()
        else:
            ThemedMessageBox.critical(self, "Error", res_z.error)

    def action_generate_attack_area(self, attack_hex):
        """Creates an Initial Attack Area zone and spawns specialized attackers."""
        from ui.dialogs.themed_dialogs import ThemedMessageBox
        res_z = zone_svc.add_attack_area(attack_hex)
        if res_z.ok:
            self.log_info(f"Generated Initial Attack Area at {attack_hex}.")
            self.hex_widget.refresh_map()
        else:
            ThemedMessageBox.critical(self, "Error", res_z.error)

    def action_scatter_mines(self):
        """Scatters mine obstacles across the map using zone_svc."""
        from ui.dialogs.themed_dialogs import ThemedMessageBox
        res = zone_svc.scatter_mines()
        if res.ok:
            self.log_info(f"Scattered {res.data['count']} mines across the theater.")
            self.hex_widget.refresh_map()
        else:
            ThemedMessageBox.critical(self, "Error", res.error)

    def action_save_knowledge(self):
        """Save persistent RL knowledge to disk via sim_svc."""
        from ui.dialogs.themed_dialogs import ThemedMessageBox
        res = sim_svc.save_knowledge()
        if res.ok:
            self.log_info("<b>RL Knowledge Saved</b> to models/q_table.npy")
            ThemedMessageBox.information(self, "Saved", "Learned Q-Table saved successfully.")
        else:
            ThemedMessageBox.critical(self, "Error", res.error)


    def reset_to_scenario_start(self):
        """Instant in-memory restoration of the 'Design' state."""
        if self.state.map.active_scenario:
            self.state.map.active_scenario.restore_state(self.state.entity_manager)
            self.hex_widget.clear_animations()
            self.hex_widget.refresh_map()
            if hasattr(self, 'scene_hierarchy_widget'):
                self.scene_hierarchy_widget.refresh_tree()
            self.log_info("Simulation <b>Reset</b> to original design.")

    # Methods moved to ScenarioManagerWidget

            
    # Scenario Manager methods removed (moved to ui.scenario_manager_widget)

    
    def prompt_agent_allocation(self):
        """Dialog to configure Side Roles (Attacker/Defender)."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Agent Allocation")
        
        # Apply Dark Theme
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e23;
                color: #ffffff;
            }
            QLabel {
                color: #dcdcdc;
                font-size: 13px;
            }
            QComboBox {
                background-color: #2b2b30;
                color: #ffffff;
                border: 1px solid #3f3f46;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3f3f46;
                color: #ffffff;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #52525b;
            }
        """)
        
        layout = QFormLayout(dialog)
        
        red_combo = QComboBox()
        red_combo.addItems(["Attacker", "Defender"])
        
        blue_combo = QComboBox()
        blue_combo.addItems(["Attacker", "Defender"])
        
        # Set Initial
        alloc = getattr(self.state, 'role_allocation', {"Red": "Defender", "Blue": "Attacker"})
        red_combo.setCurrentText(alloc.get("Red", "Defender"))
        blue_combo.setCurrentText(alloc.get("Blue", "Attacker"))
        
        # Interlock
        def on_red_changed(txt):
            if txt == "Attacker": 
                blue_combo.blockSignals(True)
                blue_combo.setCurrentText("Defender")
                blue_combo.blockSignals(False)
            else: 
                blue_combo.blockSignals(True)
                blue_combo.setCurrentText("Attacker")
                blue_combo.blockSignals(False)
            
        def on_blue_changed(txt):
            if txt == "Attacker": 
                red_combo.blockSignals(True)
                red_combo.setCurrentText("Defender")
                red_combo.blockSignals(False)
            else: 
                red_combo.blockSignals(True)
                red_combo.setCurrentText("Attacker")
                red_combo.blockSignals(False)
            
        red_combo.currentTextChanged.connect(on_red_changed)
        blue_combo.currentTextChanged.connect(on_blue_changed)
        
        layout.addRow("Red Side Role:", red_combo)
        layout.addRow("Blue Side Role:", blue_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_():
            if not hasattr(self.state, 'role_allocation'): self.state.role_allocation = {}
            self.state.role_allocation["Red"] = red_combo.currentText()
            self.state.role_allocation["Blue"] = blue_combo.currentText()
            self.log_info(f"Roles Updated: Red={red_combo.currentText()}, Blue={blue_combo.currentText()}")
    def _load_last_project(self):
        """Loads the last opened project from user_settings.json."""
        settings_path = os.path.join(os.getcwd(), "user_settings.json")
        self.current_project_path = None
        
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    path = settings.get("last_project_path")
                    if path and os.path.exists(path):
                        # Load found project
                        result = map_svc.load_project_folder(path)
                        if result.ok:
                            self.current_project_path = path
                            self.state.current_map = result.data['map_name']
                            self.setWindowTitle(f"Wargame Engine - {result.data['map_name']}")
                            self.action_model.reinit_models()
                            
                            # Standard Auto-Entry: Switch directly to Landing Page (Gallery)
                            self.switch_mode(0)
                            return
            except Exception as e:
                print(f"Error loading user settings: {e}")

        # Fallback to Default if nothing loaded
        self._load_default_project()

    def _save_last_project(self, path):
        """Saves the current project path to user_settings.json."""
        settings_path = os.path.join(os.getcwd(), "user_settings.json")
        settings = {"last_project_path": path}
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving user settings: {e}")

    def handle_deep_link(self, data):
        """Processes interaction events from the Tactical Project Explorer."""
        if not isinstance(data, dict):
            print(f"Error: handle_deep_link received non-dict data: {data}")
            return
            
        kind = data.get('type', 'map')
        proj = data.get('project', 'Default')
        map_name = data.get('map_name', 'Default')
        scen_name = data.get('scenario_name', "")
        model_name = data.get('model_name', "")
        root = data.get('root', self.data_loader.content_root)
        
        self.log_info(f"Navigating to {kind}: <b>{proj}/{map_name}</b>")
        
        # 1. TACTICAL REGISTRIES: Bypass map loading for data-only links
        if kind == "data":
            sub_type = data.get("scenario_name") or data.get("model_name") or data.get("extra")
            self.switch_mode(8) # Phase 8: Master Data (Registry)
            if hasattr(self, 'master_data_widget'):
                self.master_data_widget.select_tab_by_key(sub_type)
            self.log_info(f"Opening Tactical Registry: <b>{sub_type.upper()}</b>")
            return
        
        # 1. Resolve Map Path
        map_path = os.path.join(root, "Projects", proj, "Maps", map_name)
        if not os.path.exists(map_path):
            self.log_info(f"<font color='red'>Error: Map Path not found {map_path}</font>")
            return
            
        # Standard load (Terrain + Scenarios discovery)
        import services.map_service as map_svc
        result = map_svc.load_project_folder(map_path)
        if not result.ok:
            self.log_info(f"<font color='red'>Load Failed: {result.error}</font>")
            return
            
        self.current_project_path = map_path
        self.state.current_project = proj
        self.state.current_map = map_name
        self.setWindowTitle(f"Wargame Engine - {proj} / {map_name}")
        self._save_last_project(map_path)
        self.action_model.reinit_models()
        self.switch_mode(1) # Start in Tactical Theater

    def action_delete_project(self, project_name):
        """DELETION COMMAND: Removes a project folder from the disk."""
        import shutil
        from ui.dialogs.themed_dialogs import ThemedMessageBox
        res = ThemedMessageBox.warning(self, "Delete Project", f"Are you sure you want to delete '{project_name}'?\nThis action is irreversible.", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            proj_path = os.path.join(self.data_loader.content_root, "Projects", project_name)
            if os.path.exists(proj_path):
                try:
                    shutil.rmtree(proj_path)
                    self.log_info(f"Project '{project_name}' deleted.")
                    # Refresh the dashboard
                    if hasattr(self, 'maps_widget'):
                        self.maps_widget.refresh_list()
                    # If it was the current project, reset to maps dashboard
                    if self.state.current_project == project_name:
                        self.switch_mode(0)
                        self.current_project_path = None
                        self.state.current_project = None
                except Exception as e:
                    self.log_info(f"<font color='red'>Delete Failed: {e}</font>")
        self.hex_widget.update()

        # 2. Refine based on Kind
        if kind == "map":
            self.switch_mode(1) # Terrain Doctrine
        elif kind == "scenario" and scen_name:
            import services.scenario_service as scenario_svc
            scen_path = os.path.join(map_path, "Scenarios", f"{scen_name}.json")
            load_res = scenario_svc.load_scenario(scen_path)
            if load_res.ok:
                self.state.current_scenario_name = scen_name
                # Snapshot the design state immediately upon entry
                if self.state.map.active_scenario:
                    self.state.map.active_scenario.capture_state(self.state.entity_manager)
                self.switch_mode(3) # Phase 3: Defensive Perimeters (def_areas)
            else:
                self.log_info(f"<font color='red'>Scenario Load Failed: {load_res.error}</font>")
        elif kind == "simulation" and model_name:
            # Simulation implies Map + Specific Model
            model_path = os.path.join(map_path, "Simulations", f"{model_name}.json")
            from engine.ai import commander
            commander.set_commander_model(model_path)
            
            # Snapshot the design state before jumping into simulation
            if self.state.map.active_scenario:
                self.state.map.active_scenario.capture_state(self.state.entity_manager)
                
            self.switch_mode(7) # Phase 7: Tactical Execution (play)
            self.log_info(f"Model <b>{model_name}</b> injected for simulation.")

    def get_simulation_model_path(self, model_name="default_model"):
        """Returns the absolute path for a simulation model within the current project/map."""
        if not self.current_project_path:
            return "data/models/commander_q_table.json" # Fallback
            
        sim_dir = os.path.join(self.current_project_path, "Simulations")
        os.makedirs(sim_dir, exist_ok=True)
        return os.path.join(sim_dir, f"{model_name}.json")

    def _load_default_project(self):
        """Ensures a project exists only if none is currently loaded."""
        if self.state.current_project:
             return # Already in a real project
             
        # Standard: content/Projects/[Proj]/Maps/[Map]
        proj_name = "Default"
        proj_path = os.path.join(self.data_loader.content_root, "Projects", proj_name)
        map_path = os.path.join(proj_path, "Maps", proj_name)
        
        if not os.path.exists(map_path):
            # Create standard folder structure
            try:
                os.makedirs(os.path.join(map_path, "Scenarios"), exist_ok=True)
                terrain_data = {
                    "dimensions": {"width": 30, "height": 20},
                    "grid": {"default": "plain"},
                    "layers": {}
                }
                with open(os.path.join(map_path, "Terrain.json"), 'w') as f:
                    json.dump(terrain_data, f, indent=4)
                
                # Seed a Default Scenario with a Roster
                scen_data = {
                    "name": "Default",
                    "rules": {
                        "roster": {
                            "Attacker": [
                                {"name": "Alpha HQ", "weapon_id": "None", "type_display": "Headquarters", "personnel": 10, "side": "Attacker", "placed": False},
                                {"name": "Vanguard 1", "weapon_id": "LMG", "type_display": "Company", "personnel": 110, "side": "Attacker", "placed": False},
                                {"name": "Ironclad 1", "weapon_id": "Main Battle Tank", "type_display": "Platoon", "personnel": 30, "side": "Attacker", "placed": False}
                            ],
                            "Defender": [
                                {"name": "Static HQ", "weapon_id": "None", "type_display": "Headquarters", "personnel": 10, "side": "Defender", "placed": False},
                                {"name": "Garrison A", "weapon_id": "Rifle", "type_display": "Section", "personnel": 10, "side": "Defender", "placed": False},
                                {"name": "Garrison B", "weapon_id": "Rifle", "type_display": "Section", "personnel": 10, "side": "Defender", "placed": False}
                            ]
                        }
                    }
                }
                with open(os.path.join(map_path, "Scenarios", "Default.json"), 'w') as f:
                    json.dump(scen_data, f, indent=4)

            except Exception as e:
                print(f"Error creating default project: {e}")
                return

        result = map_svc.load_project_folder(map_path)
        if result.ok:
            self.current_project_path = map_path
            self.state.current_project = proj_name
            self.switch_mode(1) # Go directly to Tactical Theater
            self.state.current_map = proj_name
            self.setWindowTitle(f"Wargame Engine - {proj_name} / {proj_name}")
            self.action_model.reinit_models()
            self.state.current_map = proj_name
            self.setWindowTitle(f"Wargame Engine - {proj_name} / {proj_name}")
            self.action_model.reinit_models()
            self._save_last_project(map_path)

    def update_workflow_state(self):
        """Refreshes the Command Center Bar."""
        if hasattr(self, 'workflow_bar'):
            self.workflow_bar.set_state(
                self.state.app_mode_index, 
                project_name=self.state.current_project,
                map_name=self.state.current_map
            )

    def _on_done_clicked(self):
        """Handles the 'Done' click, moving to the next logical phase."""
        mode = self.state.app_mode
        
        if mode == "terrain":
            # Terrain → Rules
            from PyQt5.QtWidgets import QInputDialog
            if self.state.current_map == "Default":
                name, ok = QInputDialog.getText(self, "Finalize Map", "Enter Map Name:")
                if ok and name:
                    self.action_save_project()
                    self.switch_mode(2)  # → Rules
            else:
                self.action_save_project(silent=True)
                self.switch_mode(2)  # → Rules
                
        elif mode == "rules":
            # Rules → Defender Areas
            self.switch_mode(3)
            self.log_info("Scenario constraints finalized.")
            
        elif mode == "def_areas":
            # Def Areas → Def Agents
            self.switch_mode(4)
            self.log_info("Defender perimeters established.")
            
        elif mode == "def_agents":
            # Def Agents → Atk Areas
            self.switch_mode(5)
            self.log_info("Defender garrison deployed.")
            
        elif mode == "atk_areas":
            # Atk Areas → Atk Agents
            self.switch_mode(6)
            self.log_info("Attacker perimeters established.")
                
        elif mode == "atk_agents":
            # Atk Agents → Play: Finalize scenario, capture golden state, start simulation
            from PyQt5.QtWidgets import QInputDialog
            import services.scenario_service as scenario_svc
            from ui.dialogs.themed_dialogs import ThemedMessageBox
            
            cur_scenario = getattr(self.state, 'current_scenario_name', "New Scenario")
            name, ok = QInputDialog.getText(self, "Finalize Scenario", "Enter Scenario Name:", text=cur_scenario)
            
            if ok and name:
                # Update the active scenario name in the map object
                if self.state.map.active_scenario:
                    old_name = self.state.map.active_scenario.name
                    self.state.map.active_scenario.name = name
                    
                    # Ensure the scenario is registered in the map's dictionary
                    if old_name in self.state.map.scenarios:
                        target_scen = self.state.map.scenarios.pop(old_name)
                        self.state.map.scenarios[name] = target_scen
                    else:
                        self.state.map.scenarios[name] = self.state.map.active_scenario
                
                self.state.current_scenario_name = name
                
                # Save all scenarios in this map's folder
                result = scenario_svc.save_all_scenarios(self.current_project_path)
                
                if result.ok:
                    # Capture the 'Golden State' before simulation begins
                    self.state.map.active_scenario.capture_state(self.state.entity_manager)
                    
                    self.switch_mode(7)  # → Play/Simulation
                    self.log_info(f"Scenario <b>'{name}'</b> Finalized and Saved.")
                else:
                    from ui.dialogs.themed_dialogs import ThemedMessageBox
                    ThemedMessageBox.critical(self, "Save Error", f"Failed to save scenario: {result.error}")

    def _on_back_clicked(self):
        """Navigate backward through the 8-phase tactical workflow."""
        current_mode = self.mode_machine.current_mode_index
        
        if current_mode == 7:  # Play → Atk Agents
            self.pause_simulation()
            if self.state.map.active_scenario:
                self.state.map.active_scenario.restore_state(self.state.entity_manager)
            self.hex_widget.clear_animations()
            self.switch_mode(6)
        elif current_mode > 1 and current_mode <= 6:
            self.switch_mode(current_mode - 1)
        elif current_mode == 1:  # Terrain → Dashboard
            self.switch_mode(0)
        elif current_mode == 8:  # Master Data → Dashboard
            self.switch_mode(0)

    def undo_action(self):
        if hasattr(self.state, "undo_stack"):
            self.state.undo_stack.undo()
            self.hex_widget.refresh_map()
            if hasattr(self, 'scene_hierarchy_widget'): self.scene_hierarchy_widget.refresh_tree()
            self.log_info("<i>Undo Performed</i>")

    def redo_action(self):
        if hasattr(self.state, "undo_stack"):
            self.state.undo_stack.redo()
            self.hex_widget.refresh_map()
            if hasattr(self, 'scene_hierarchy_widget'): self.scene_hierarchy_widget.refresh_tree()
            self.log_info("<i>Redo Performed</i>")

    def resizeEvent(self, event):
        """Standard resize handling."""
        super().resizeEvent(event)

    # Remove keyPressEvent completely, we will move shortcuts to __init__
