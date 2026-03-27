from PyQt5.QtWidgets import QMessageBox

class ThemedMessageBox:
    """
    A wrapper specifically for QMessageBox to apply the application theme
    before showing.
    """
    @staticmethod
    def _apply_theme(msg_box):
        # Apply a consistent dark theme style directly
        # Ideally this should match the app's QSS, but for popups we force it
        # to ensure they don't look like native OS white dialogs.
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
        """)

    @staticmethod
    def information(parent, title, text, buttons=QMessageBox.Ok):
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        ThemedMessageBox._apply_theme(msg)
        return msg.exec_()

    @staticmethod
    def warning(parent, title, text, buttons=QMessageBox.Ok):
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        ThemedMessageBox._apply_theme(msg)
        return msg.exec_()

    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No):
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        ThemedMessageBox._apply_theme(msg)
        return msg.exec_()

    @staticmethod
    def critical(parent, title, text, buttons=QMessageBox.Ok):
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        ThemedMessageBox._apply_theme(msg)
        return msg.exec_()
