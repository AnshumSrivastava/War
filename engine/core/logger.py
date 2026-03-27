# logger.py
import os
import json
import datetime

class CombatLogger:
    """
    A professional-grade tactical logger for recording simulation events.
    Writes structured data to disk for later analysis and AAR generation.
    """
    def __init__(self, log_path="data/logs/simulation_actions.json"):
        self.log_path = log_path
        dir_name = os.path.dirname(self.log_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # Start a new session in the log
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_action("SESSION_START", {"timestamp": str(datetime.datetime.now())})

    def log_action(self, action_type, data):
        """Records a structured action event."""
        log_entry = {
            "session": self.session_id,
            "timestamp": str(datetime.datetime.now()),
            "type": action_type,
            "data": data
        }
        
        try:
            # We append in a line-delimited JSON format for easy stream processing
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"CombatLogger Error: {e}")

    def log_step(self, episode, step, events):
        """Records a full tactical step summary."""
        self.log_action("STEP_SUMMARY", {
            "episode": episode,
            "step": step,
            "event_count": len(events)
        })
        for evt in events:
            # Filter visual event data to only log tactical essentials
            t_evt = evt.copy()
            if "hex" in t_evt and hasattr(t_evt["hex"], "to_tuple"):
                t_evt["hex"] = t_evt["hex"].to_tuple()
            self.log_action("TACTICAL_EVENT", t_evt)
