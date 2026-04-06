from PyQt5.QtWidgets import QMessageBox
from ui.styles.theme import Theme

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
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_SUBTLE};
                padding: 5px 15px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BORDER_SUBTLE};
            }}
            QPushButton:pressed {{
                background-color: {Theme.BG_DEEP};
            }}
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
