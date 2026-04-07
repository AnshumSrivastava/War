"""
FILE: ui/core/simulation_controller.py
ROLE: The "Conductor" (Qt UI Wrapper).

DESCRIPTION:
    This class manages the simulation heartbeat and learning batch execution
    within the PyQt environment.
    
    CRITICAL: It NO LONGER contains simulation logic. 
    It delegates all operations to services.simulation_service.
"""
from PyQt5.QtCore import QObject, QTimer, QTime, pyqtSignal
from PyQt5.QtWidgets import QApplication, QProgressDialog
from PyQt5.QtCore import Qt

import services.simulation_service as sim_svc

class SimulationController(QObject):
    """
    Lean Qt-based wrapper for the Simulation Service.
    Emits signals that the UI (MainWindow, TimelinePanel) can subscribe to.
    """
    step_completed = pyqtSignal(int, list, list)  # step_number, events, logs
    episode_completed = pyqtSignal(int)      # episode_number
    simulation_state_changed = pyqtSignal(bool) # is_running
    learning_started = pyqtSignal()
    learning_finished = pyqtSignal()
    game_over = pyqtSignal(str) # result message

    def __init__(self, state, action_model=None):
        super().__init__()
        self.state = state
        
        # UI & FLOW STATE
        self.is_running = False
        self.is_learning = False
        
        self.current_episode = 1
        self.current_step = 1
        self.max_steps = 50
        self.max_episodes = 100
        
        # TIMING
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.tick)
        self.sim_start_time = QTime(8, 0, 0)
        self.sim_current_time = self.sim_start_time

    def start(self, interval=800):
        """Starts the simulation loop."""
        if not self.is_running:
            self.is_running = True
            self.sim_timer.start(interval)
            self.simulation_state_changed.emit(True)

    def pause(self):
        """Pauses the simulation loop."""
        if self.is_running:
            self.is_running = False
            self.sim_timer.stop()
            self.simulation_state_changed.emit(False)
        if getattr(self, "is_learning", False):
            self.is_learning = False

    def reset_episode(self, silent=False):
        """Resets the world via sim_svc."""
        sim_svc.reset()
        self.current_step = 1
        self.sim_current_time = self.sim_start_time
        if not silent:
            self.episode_completed.emit(self.current_episode)

    def step(self):
        """Manual single-step trigger. Works even when simulation is paused."""
        # Temporarily allow a single tick regardless of running state
        was_running = self.is_running
        self.is_running = True
        self.tick()
        if not was_running:
            self.is_running = False

    def tick(self):
        """A single 'heartbeat' triggered by the QTimer."""
        if not self.is_running:
            return
            
        # 1. Delegate Step to Service
        res = sim_svc.step(
            step_number=self.current_step,
            episode_number=self.current_episode,
            max_steps=self.max_steps
        )
        
        if not res.ok:
            print(f"Tick Failed: {res.error}")
            self.pause()
            return

        events = res.data["events"]
        logs = res.data["logs"]
        
        # 2. Update Clock (UI side only)
        self.sim_current_time = self.sim_current_time.addSecs(600)
        
        # 3. Check Terminal Conditions via Service
        term_res = sim_svc.check_terminal_conditions(self.current_step, self.max_steps)
        
        # 4. Notify UI
        self.step_completed.emit(self.current_step, events, logs)
        
        if term_res.ok and term_res.data["done"]:
            msg = term_res.data["reason"]
            print(f"Simulation Terminated: {msg}")
            self.pause()
            self.game_over.emit(msg)
            self.current_episode += 1
            return
            
        self.current_step += 1

    def run_learning(self, episodes):
        """High-speed training batch via service."""
        if self.is_running: return
        
        self.is_learning = True
        self.learning_started.emit()
        
        progress = QProgressDialog("Conducting Targeted Learning...", "Cancel", 0, episodes)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        def progress_cb(ep, total, eps):
            progress.setValue(ep)
            progress.setLabelText(f"Targeted Learning... Episode {ep}/{total} (eps: {eps:.2f})")
            QApplication.processEvents()
            self.current_episode = ep
            if ep % 10 == 0:
                self.episode_completed.emit(ep)

        # Delegate to Service
        res = sim_svc.run_episodes(episodes, max_steps=self.max_steps, progress_callback=progress_cb)
        
        progress.setValue(episodes)
        self.is_learning = False
        self.learning_finished.emit()
        
        if not res.ok:
            print(f"Learning Phase Error: {res.error}")

    def reset_intelligence(self):
        """Wipe AI knowledge via service."""
        res = sim_svc.reset_intelligence()
        if res.ok:
            return res.data.get("count", 0)
        return 0
