import sys
from PyQt5.QtWidgets import QApplication
from ui.views.main_window import MainWindow

app = QApplication(sys.argv)
mw = MainWindow()
print([m for m in dir(mw) if "set_tool" in m])
