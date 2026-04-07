"""
FILE: main.py
ROLE: Main Entry Point for the War Game Application.

DESCRIPTION:
This file is the starting point of the entire application. It performs the following:
1. Sets up the environment (like disabling sandboxing for the web engine to prevent crashes on Linux).
2. Initializes the graphics system (PyQt5).
3. Creates and displays the Main Window, which contains the entire game interface.
4. Starts the "Event Loop," which keeps the application running and responding to user clicks.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# --- UI MODULES ---
from ui.views.main_window import MainWindow 
from ui.styles.theme import Theme

import logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    The main engine that drives the start of the program.
    """
    log.info("Starting Main App...")

    # High-DPI support — must be set before QApplication creation
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # Required for WebEngine to share OpenGL resources
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # Create the application object that manages the GUI control flow and settings
    app = QApplication(sys.argv)
    log.info("QApplication initialized.")
    
    # Set the 'Fusion' style for a modern, consistent look across different operating systems
    app.setStyle("Fusion")
    
    # --- UI THEME ---
    app.setStyleSheet(Theme.get_main_qss())
    
    # 3. MainWindow Initialization
    log.info("Initializing MainWindow...")
    window = MainWindow()
    window.setWindowTitle("WARGAME ENGINE: STRATEGIC COMMAND")
    
    # Reveal the window to the user
    log.info("Showing Window...")
    window.show()
    
    # Execute the application and wait for the user to close it. 
    # sys.exit ensures the script closes cleanly with the right exit code.
    log.info("Entering event loop.")
    sys.exit(app.exec_())

# Standard Python idiom: only run main() if this file is executed directly.
if __name__ == "__main__":
    main()
