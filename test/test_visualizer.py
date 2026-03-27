import sys
from PyQt5.QtWidgets import QApplication
from ui.core.visualizer import Visualizer

class DummyHexWidget:
    def __init__(self):
        self.hex_size = 50
        self.camera_x = 0
        self.camera_y = 0
    def width(self): return 800
    def height(self): return 600

app = QApplication(sys.argv)
vis = Visualizer(DummyHexWidget())
print("Visualizer methods:", dir(vis))
