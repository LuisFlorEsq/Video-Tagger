from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QMessageBox, QFileDialog, QStatusBar, QApplication
)
from PySide6.QtGui import QAction

from src.application.services.project_service import ProjectService
from src.application.services.labeling_service import LabelingService
from src.application.services.export_service import ExportService
from src.application.services.navigation_service import NavigationService

from src.presentation.widgets.project_browser import ProjectBrowser
from src.presentation.widgets.fragment_viewer import FragmentViewer
from src.presentation.styles import app_stylesheet

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment


class MainWindow(QMainWindow):
    """
    Main window — UI coordination only.
    All business logic delegated to services (SRP + DIP).
    """

    def __init__(
        self,
        project_service: ProjectService,
        labeling_service: LabelingService,
        export_service: ExportService
    ):
        super().__init__()

        self._project_service   = project_service
        self._labeling_service  = labeling_service
        self._export_service    = export_service

        self._current_project:    Project           = None
        self._navigation_service: NavigationService = None

        self._project_browser: ProjectBrowser = None
        self._fragment_viewer: FragmentViewer = None

        # Apply global design system to the whole application
        QApplication.instance().setStyleSheet(app_stylesheet())

        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._connect_signals()

        self.setWindowTitle("Herramienta de etiquetado - CIC IPN")
        self.resize(1400, 800)

    # ─────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        self._project_browser = ProjectBrowser(
            project_service=self._project_service,
            export_service=self._export_service
        )
        self._fragment_viewer = FragmentViewer(
            labeling_service=self._labeling_service,
            project_service=self._project_service
        )

        self.stacked_widget.addWidget(self._project_browser)
        self.stacked_widget.addWidget(self._fragment_viewer)

        layout.addWidget(self.stacked_widget)
        self._safe_switch_view(0)

    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&Archivo")

        new_action = QAction("&Nuevo proyecto desde carpeta", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._project_browser._on_new_project_clicked)
        file_menu.addAction(new_action)

        load_action = QAction("&Cargar proyecto", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._project_browser._on_load_project_clicked)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        save_action = QAction("&Guardar proyecto", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_action = QAction("&Exportar a formato CSV", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("&Ayuda")

        about_action = QAction("&Acerca de", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status("Listo — selecciona una carpeta para iniciar.")

    def _connect_signals(self):
        self._project_browser.project_loaded.connect(self._on_project_loaded)
        self._project_browser.fragment_selected.connect(self._on_fragment_selected)
        self._fragment_viewer.fragment_labeled.connect(self._on_fragment_labeled)
        self._fragment_viewer.prev_requested.connect(self._on_prev_requested)
        self._fragment_viewer.next_requested.connect(self._on_next_requested)
        self._fragment_viewer.back_requested.connect(self._show_browser)

    # ─────────────────────────────────────────────
    # Event handlers
    # ─────────────────────────────────────────────

    def _on_project_loaded(self, project: Project):
        self._current_project    = project
        self._navigation_service = NavigationService(project)

        self._fragment_viewer.set_navigation_service(self._navigation_service)

        # Always return to browser when a new project is loaded
        self._safe_switch_view(0)

        summary = self._project_service.get_project_summary(project)
        self._update_status(
            f"{project.name} — "
            f"{summary['labeled']}/{summary['total_fragments']} etiquetados"
        )

    def _on_fragment_selected(self, fragment: Fragment):
        if not self._current_project or not self._navigation_service:
            return

        self._navigation_service.set_current_fragment(fragment.fragment_id)
        self._fragment_viewer.load_fragment(fragment, self._current_project)
        self._safe_switch_view(1)

        current, total = self._navigation_service.get_position()
        self._update_status(
            f"{fragment.get_video_name()}  —  {current}/{total}"
        )

    def _on_fragment_labeled(self, fragment: Fragment):
        self._project_browser.refresh()
        if fragment.is_labeled():
            self._update_status(
                f"Etiquetado: '{fragment.label}'  —  {fragment.fragment_id}"
            )
        else:
            self._update_status(
                f"Etiqueta eliminada  —  {fragment.fragment_id}"
            )

    def _on_prev_requested(self):
        if not self._navigation_service:
            return
        self._fragment_viewer.video_player.force_stop()
        prev_fragment = self._navigation_service.move_to_previous()
        if prev_fragment:
            self._fragment_viewer.load_fragment(prev_fragment, self._current_project)
            current, total = self._navigation_service.get_position()
            self._update_status(f"{prev_fragment.get_video_name()}  —  {current}/{total}")
        else:
            summary = self._project_service.get_project_summary(self._current_project)
            QMessageBox.information(
                self, "Inicio del proyecto",
                f"Has llegado al inicio del proyecto.\n\n"
                f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
                f"({summary['progress_percentage']:.1f}%)"
            )
            self._show_browser()

    def _on_next_requested(self):
        if not self._navigation_service:
            return
        self._fragment_viewer.video_player.force_stop()
        next_fragment = self._navigation_service.move_to_next()
        if next_fragment:
            self._fragment_viewer.load_fragment(next_fragment, self._current_project)
            current, total = self._navigation_service.get_position()
            self._update_status(f"{next_fragment.get_video_name()}  —  {current}/{total}")
        else:
            summary = self._project_service.get_project_summary(self._current_project)
            QMessageBox.information(
                self, "¡Proyecto completado!",
                f"Has llegado al final del proyecto.\n\n"
                f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
                f"({summary['progress_percentage']:.1f}%)"
            )
            self._show_browser()

    def _on_save_project(self):
        if not self._current_project:
            QMessageBox.information(self, "Sin proyecto", "No hay ningún proyecto abierto.")
            return
        self._project_browser._on_save_clicked()

    def _on_export(self):
        if not self._current_project:
            QMessageBox.information(self, "Sin proyecto", "No hay ningún proyecto abierto.")
            return
        if self._current_project.get_total_count() == 0:
            QMessageBox.information(self, "Sin datos", "No hay fragmentos que exportar.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar CSV",
            f"{self._current_project.name}_export.csv",
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            self._export_service.export(self._current_project, Path(file_path), 'csv')
            summary = self._project_service.get_project_summary(self._current_project)
            QMessageBox.information(
                self, "Exportación exitosa",
                f"{summary['total_fragments']} fragmentos exportados.\n"
                f"Etiquetados: {summary['labeled']}/{summary['total_fragments']}"
            )
            self._update_status(f"Exportado: {Path(file_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))

    def _show_browser(self):
        self._project_browser.refresh()
        self._safe_switch_view(0)
        if self._current_project:
            summary = self._project_service.get_project_summary(self._current_project)
            self._update_status(
                f"{self._current_project.name} — "
                f"{summary['labeled']}/{summary['total_fragments']} etiquetados"
            )
        else:
            self._update_status("Listo.")

    def _safe_switch_view(self, index: int):
        if self._fragment_viewer and index != 1:
            player = self._fragment_viewer.video_player
            if player:
                player.force_stop()
        self.stacked_widget.setCurrentIndex(index)

    def _show_about(self):
        QMessageBox.about(
            self, "Acerca de",
            "<h2>Herramienta de etiquetado v1.0</h2>"
            "<p>Etiqueta fragmentos de video para conjuntos de datos de entrenamiento.</p>"
            "<p><b>Instrucciones:</b></p>"
            "<ol>"
            "<li>Selecciona la carpeta que contenga los fragmentos</li>"
            "<li>Haz doble clic en un fragmento para abrirlo</li>"
            "<li>Asigna una etiqueta desde el panel lateral</li>"
            "<li>Exporta a CSV al finalizar</li>"
            "</ol>"
            "<p>Centro de Investigación en Computación — IPN</p>"
        )

    def _update_status(self, message: str):
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        if self._current_project:
            unlabeled = self._current_project.get_unlabeled_count()
            if unlabeled > 0:
                reply = QMessageBox.question(
                    self, "Trabajo incompleto",
                    f"Tienes {unlabeled} fragmentos sin etiquetar.\n\n"
                    f"¿Deseas guardar tu progreso antes de salir?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                if reply == QMessageBox.Save:
                    self._on_save_project()
                    event.accept()
                elif reply == QMessageBox.Discard:
                    event.accept()
                else:
                    event.ignore()
                return
        event.accept()

# Factory function for creating MainWindow
def create_main_window(
    project_service: ProjectService,
    labeling_service: LabelingService,
    export_service: ExportService
) -> MainWindow:
    """
    Factory function for creating MainWindow with injected dependencies.
    
    Args:
        project_service: Service for project operations
        labeling_service: Service for labeling operations
        export_service: Service for export operations
    
    Returns:
        Configured MainWindow instance
    """
    return MainWindow(project_service, labeling_service, export_service)