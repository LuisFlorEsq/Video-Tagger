from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import QSize

from src.ui.helpers.dividers import make_hline
from src.ui.styles import (
    sidebar_panel, sidebar_btn, sidebar_btn_warning, sidebar_btn_danger,
    sidebar_section_label,
)
from src.core.config import ICON_SIZE
from src.core.resources import icon


class SidebarPanel(QWidget):
    """Left sidebar containing project action buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(sidebar_panel())
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(2)

        # ── Welcome state (no project loaded) ────────────────────────────────
        self.welcome_section = QWidget()
        ws = QVBoxLayout(self.welcome_section)
        ws.setContentsMargins(0, 0, 0, 0)
        ws.setSpacing(2)

        ws_header = QLabel("Inicio")
        ws_header.setStyleSheet(sidebar_section_label())
        ws.addWidget(ws_header)

        self.new_project_btn = QPushButton("Nuevo proyecto")
        self.new_project_btn.setIcon(icon("new_project.png"))
        self.new_project_btn.setIconSize(QSize(*ICON_SIZE))
        self.new_project_btn.setStyleSheet(sidebar_btn())
        self.new_project_btn.setMinimumHeight(36)
        ws.addWidget(self.new_project_btn)

        self.load_project_btn = QPushButton("Abrir proyecto")
        self.load_project_btn.setIcon(icon("open_project.png"))
        self.load_project_btn.setIconSize(QSize(*ICON_SIZE))
        self.load_project_btn.setStyleSheet(sidebar_btn())
        self.load_project_btn.setMinimumHeight(36)
        ws.addWidget(self.load_project_btn)

        layout.addWidget(self.welcome_section)

        # ── Project state (project loaded) ───────────────────────────────────
        self.project_section = QWidget()
        self.project_section.setVisible(False)
        ps = QVBoxLayout(self.project_section)
        ps.setContentsMargins(0, 0, 0, 0)
        ps.setSpacing(2)

        ps_header = QLabel("Proyecto")
        ps_header.setStyleSheet(sidebar_section_label())
        ps.addWidget(ps_header)

        self.save_project_btn = QPushButton("Guardar")
        self.save_project_btn.setIcon(icon("save_project.png"))
        self.save_project_btn.setIconSize(QSize(*ICON_SIZE))
        self.save_project_btn.setStyleSheet(sidebar_btn())
        self.save_project_btn.setMinimumHeight(34)
        ps.addWidget(self.save_project_btn)

        self.export_csv_btn = QPushButton("Exportar CSV")
        self.export_csv_btn.setIcon(icon("export_csv.png"))
        self.export_csv_btn.setIconSize(QSize(*ICON_SIZE))
        self.export_csv_btn.setStyleSheet(sidebar_btn())
        self.export_csv_btn.setMinimumHeight(34)
        ps.addWidget(self.export_csv_btn)

        ps.addWidget(make_hline())

        labels_header = QLabel("Etiquetas")
        labels_header.setStyleSheet(sidebar_section_label())
        ps.addWidget(labels_header)

        self.config_labels_btn = QPushButton("Configurar etiquetas")
        self.config_labels_btn.setIcon(icon("config_labels.png"))
        self.config_labels_btn.setIconSize(QSize(*ICON_SIZE))
        self.config_labels_btn.setStyleSheet(sidebar_btn())
        self.config_labels_btn.setMinimumHeight(34)
        ps.addWidget(self.config_labels_btn)

        ps.addWidget(make_hline())

        sync_header = QLabel("Sincronización")
        sync_header.setStyleSheet(sidebar_section_label())
        ps.addWidget(sync_header)

        self.sync_btn = QPushButton("Sincronizar archivos")
        self.sync_btn.setIcon(icon("sync_content.png"))
        self.sync_btn.setIconSize(QSize(*ICON_SIZE))
        self.sync_btn.setStyleSheet(sidebar_btn_warning())
        self.sync_btn.setMinimumHeight(34)
        self.sync_btn.setEnabled(False)
        ps.addWidget(self.sync_btn)

        ps.addSpacing(8)
        ps.addWidget(make_hline())

        self.back_btn = QPushButton("Cerrar proyecto")
        self.back_btn.setIcon(icon("close_project.png"))
        self.back_btn.setIconSize(QSize(*ICON_SIZE))
        self.back_btn.setStyleSheet(sidebar_btn_danger())
        self.back_btn.setMinimumHeight(34)
        ps.addWidget(self.back_btn)

        layout.addWidget(self.project_section)
        layout.addStretch()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def show_project_state(self, project_name: str):
        """Switch to project-loaded appearance."""
        self.welcome_section.setVisible(False)
        self.project_section.setVisible(True)

    def show_welcome_state(self):
        """Switch back to no-project appearance."""
        self.welcome_section.setVisible(True)
        self.project_section.setVisible(False)

    def set_sync_pending(self, count: int):
        """Update sync button to show pending file count."""
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText(f"  Sincronizar ({count} nuevos)")

    def set_sync_idle(self):
        """Reset sync button to default idle state."""
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("Sincronizar archivos")
