import sys
import os
from PyQt5.QtWidgets import QApplication

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.views.main_window import MainWindow
from engine.state.global_state import GlobalState

def run_test():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Needs to transition to Hex Editor to actually set tools sometimes, or at least have hex_widget
    tools = ["select", "draw_hex", "draw_zone", "draw_path", "place_agent", "remove_entity", "assign_goal"]
    
    success = True
    for t in tools:
        print(f"Testing set_tool: {t}")
        try:
            window.set_tool(t)
            print(f" -> Tool {t} SUCCESS")
        except Exception as e:
            print(f" -> Tool {t} FAILED with {type(e).__name__}: {e}")
            success = False
            import traceback
            traceback.print_exc()

    if success:
        print("All tools tested successfully without UnboundLocalError!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_test()
