import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QShortcut
from PyQt5.QtGui import QKeySequence

def on_v():
    print("V pressed!")

app = QApplication(sys.argv)
mw = QMainWindow()
shortcut = QShortcut(QKeySequence("V"), mw)
shortcut.activated.connect(on_v)

w = QWidget()
mw.setCentralWidget(w)
w.setFocus()
mw.show()
print("Shortcut initialized:", shortcut.key().toString())
