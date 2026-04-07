"""
FILE: ui/core/simulation_manager.py
ROLE: The "Conductor".

DESCRIPTION:
This controller manages the simulation lifecycle, including starting/pausing,
handling step/episode completion signals, and updating the UI (TimelinePanel, Visualizer).
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QTimer, QTime
from ui.styles.theme import Theme
import datetime
import os

class SimulationManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.state = main_window.state
        self.sim_controller = main_window.sim_controller
        self.data_loader = main_window.data_loader
        self.action_model = main_window.action_model
        
        self.final_episode_events = []
        
        # Connect signals
        self.sim_controller.step_completed.connect(self.on_sim_step_completed)
        self.sim_controller.episode_completed.connect(self.on_sim_episode_completed)
        self.sim_controller.learning_started.connect(self.on_learning_started)
        self.sim_controller.learning_finished.connect(self.on_learning_finished)

    def start_simulation_loop(self):
        """Starts the main tactical simulation."""
        self.mw.switch_mode(7) # Tactical Execution Phase (Play)

        if not self.sim_controller.is_running:
            # Inject map-specific brain
            from engine.ai import commander
            model_path = self.mw.get_simulation_model_path()
            commander.set_commander_model(model_path)
            
            self.mw.sanitize_agents()
            if hasattr(self.mw, 'event_log_widget'):
                self.mw.event_log_widget.clear()
                
            # --- CRITICAL: RE-INITIALIZE SIMULATION SERVICE ---
            # Ensure the service is looking at the LATEST WorldState
            import services.simulation_service as sim_svc
            sim_svc.init(self.state)
            
            self.mw.log_info(f"<b>Priming Systems...</b>")
            
            # Save the current tactical layout as the 'Start State'
            # ONLY capture if not already in Play mode or if state was never captured
            if self.state.map.active_scenario:
                # Basic check: if scenario has no saved state at all, capture now.
                # This prevents overwriting the design state if we resume from a pause.
                if not getattr(self.state.map.active_scenario, '_captured_state', None):
                    self.state.map.active_scenario.capture_state(self.state.entity_manager)
                    self.mw.log_info("Tactical Design <b>Captured</b> as Reset-Point.")
            
            import services.scenario_service as scenario_svc
            scenario_svc.save_scenario("active_scenario.json")
            
            # Re-init models to match map size/content
            sim_svc.reinit_models()
            
            # Start the simulation wrapper
            self.sim_controller.start()
            self.mw.log_info(f"--- Simulation <b>LIVE</b> ---")

    def pause_simulation(self):
        """Pauses the simulation."""
        if self.sim_controller.is_running:
            self.mw.log_info("Simulation <b>Paused</b>.")
        self.sim_controller.pause()
        
        # Generate AAR if events exist
        if hasattr(self.mw, 'report_widget') and self.final_episode_events:
            self.mw.report_widget.generate_report(self.final_episode_events, getattr(self.mw, 'current_episode', 1))

    def advance_simulation(self):
        """Advances the simulation by a single step."""
        if not self.sim_controller.is_running:
            self.sim_controller.step()
            self.mw.log_info("Simulation: <b>Step Forward</b>")

    def action_reset_env(self, silent=False):
        """Resets the environment to the starting state."""
        self.sim_controller.pause()
        self.mw.is_running = False
        self.sim_controller.reset_episode(silent=silent)
        self.mw.reset_to_scenario_start()
        # Clear stale events from the previous episode
        if hasattr(self.mw, 'event_log_widget') and hasattr(self.mw.event_log_widget, 'clear'):
            self.mw.event_log_widget.clear()
        if not silent:
            self.mw.log_info("Simulation <b>Reset</b>.")

    def start_learning_phase(self):
        """Initiates a batch learning session (AI training)."""
        if self.sim_controller.is_running:
            return
            
        self.mw.sanitize_agents()
        
        # Inject map-specific brain
        from engine.ai import commander
        model_path = self.mw.get_simulation_model_path()
        commander.set_commander_model(model_path)
        
        import services.scenario_service as scenario_svc
        scenario_svc.save_scenario("active_scenario.json")
        
        episodes = getattr(self.sim_controller, 'max_episodes', 100)
        
        if hasattr(self.mw, 'timeline_panel'):
            self.mw.timeline_panel.btn_learn.setEnabled(False)
            
        self.sim_controller.run_learning(episodes)
        
        if hasattr(self.mw, 'timeline_panel'):
            self.mw.timeline_panel.btn_learn.setEnabled(True)

    def on_learning_started(self):
        if hasattr(self.mw, 'timeline_panel'):
            self.mw.timeline_panel.set_status("LEARNING", Theme.ACCENT_WARN)
        self.mw.log_info("<b style='color: #ffa500;'>[LEARNING PHASE]</b> Running silent episodes for AI training...")
        QApplication.processEvents()

    def on_learning_finished(self):
        if hasattr(self.mw, 'timeline_panel'):
            self.mw.timeline_panel.set_status("SIMULATING", Theme.ACCENT_ALLY)
        self.mw.log_info("<b style='color: #4caf50;'>[TRAINING COMPLETE]</b> Saving tactical model.")
        
        # Save the model
        from engine.ai import commander
        commander.get_commander_brain().save_model()

    def on_sim_step_completed(self, step, events, logs):
        """Handles visual and logical updates after each step."""
        self.final_episode_events.extend(events)

        # Visual Feedback via Visualizer
        if events:
            self.mw.visualizer.enqueue_batch(events)
            for evt in events:
                if evt['type'] == 'move':
                    self.mw.hex_widget.enqueue_agent_move(evt['agent_id'], evt['to'])
        
        if hasattr(self.mw, 'timer_label'):
            t_str = self.sim_controller.sim_current_time.toString("HH:mm:ss")
            self.mw.timer_label.setText(t_str)
            if hasattr(self.mw, 'timeline_panel'):
                self.mw.timeline_panel.set_simulation_time(t_str)
            
        if logs:
            for log_msg in logs:
                self.mw.log_info(log_msg)
            
        if hasattr(self.mw, 'event_log_widget'):
            if hasattr(self.mw.event_log_widget, 'update_live_data'):
                agents = self.mw.state.entity_manager.get_all_entities()
                self.mw.event_log_widget.update_live_data(agents, self.mw.state.map)
            
            # Update Episode Indicator
            if hasattr(self.mw.event_log_widget, 'set_current_episode'):
                self.mw.event_log_widget.set_current_episode(self.current_episode)

        self.mw.hex_widget.update()

    def on_sim_episode_completed(self, episode_number):
        self.mw.log_info(f"--- Episode {episode_number-1} Completed ---")
        if hasattr(self.mw, 'timeline_panel'):
            self.mw.timeline_panel.update_progress(episode_number)
        self.action_reset_env(silent=True)
