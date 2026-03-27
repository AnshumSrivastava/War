from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

s1 = QKeySequence("V")
s2 = QKeySequence(Qt.Key_V)
s3 = QKeySequence("v")

print(f"s1: {s1.toString()} is {s1[0]}")
print(f"s2: {s2.toString()} is {s2[0]}")
print(f"s3: {s3.toString()} is {s3[0]}")
