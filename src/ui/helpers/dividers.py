from PySide6.QtWidgets import QFrame
from src.ui.styles import AppTheme


def make_hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {AppTheme.BORDER}; border: none;")
    return line


def make_vline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFixedWidth(1)
    line.setStyleSheet(f"background-color: {AppTheme.BORDER}; border: none;")
    return line
