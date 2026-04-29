from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from src.ui.styles import AppTheme, btn_danger, progress_bar, text_secondary


class ProjectCreationDialog(QDialog):
    """
    Modal progress UI shown while a ProjectCreationWorker builds a project
    on a background thread.
    """

    cancel_requested = Signal()

    def __init__(self, total_files: int, parent=None) -> None:
        super().__init__(parent)
        self._total_files = max(total_files, 1)

        self.setWindowTitle("Creando proyecto")
        self.setModal(True)
        self.setFixedWidth(420)

        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowCloseButtonHint
        )

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        self.headline_label = QLabel("Procesando archivos…")
        self.headline_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_BASE}; font-weight: bold; "
            f"color: {AppTheme.TEXT_PRIMARY};"
        )
        layout.addWidget(self.headline_label)

        self.filename_label = QLabel("")
        self.filename_label.setStyleSheet(text_secondary())
        self.filename_label.setWordWrap(True)
        layout.addWidget(self.filename_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self._total_files)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Explorando archivos…")
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet(progress_bar())
        layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setStyleSheet(btn_danger())
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self.cancel_btn)

    # ---------------------------------------------
    # Public API
    # ---------------------------------------------

    def set_progress(self, current: int, total: int, filename: str) -> None:
        if total != self.progress_bar.maximum():
            self.progress_bar.setRange(0, max(total, 1))
        if self.progress_bar.format() != "%v / %m":
            self.progress_bar.setFormat("%v / %m")
        self.progress_bar.setValue(current)
        self.filename_label.setText(filename)

    def set_cancelling_state(self) -> None:
        """Reflect that a cancel request is in flight and being honored."""
        self.headline_label.setText("Cancelando…")
        self.cancel_btn.setEnabled(False)

    # ---------------------------------------------
    # Internal
    # ---------------------------------------------

    def _on_cancel_clicked(self) -> None:
        self.set_cancelling_state()
        self.cancel_requested.emit()

    def closeEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._on_cancel_clicked()
            return
        super().keyPressEvent(event)
