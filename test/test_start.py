import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.views.main_window import MainWindow

app = QApplication(sys.argv)
try:
    mw = MainWindow()
    print("MainWindow loaded perfectly.")
    mw.hex_widget.setFocus()
    print("Focus set.")
except Exception as e:
    import traceback
    traceback.print_exc()
