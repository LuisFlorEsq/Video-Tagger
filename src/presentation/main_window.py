from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QMessageBox, QFileDialog, QStatusBar
)
from PySide6.QtGui import QAction

from src.application.services.project_service import ProjectService
from src.application.services.labeling_service import LabelingService
from src.application.services.export_service import ExportService
from src.application.services.navigation_service import NavigationService

from src.presentation.widgets.project_browser import ProjectBrowser
from src.presentation.widgets.fragment_viewer import FragmentViewer

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment


class MainWindow(QMainWindow):
    """
    Main window - Only responsible for UI coordination.
    Delegates all business logic to services (SRP + DIP).
    """
    
    def __init__(
        self,
        project_service: ProjectService,
        labeling_service: LabelingService,
        export_service: ExportService
    ):
        super().__init__()
        
        # Inject dependencies (DIP)
        self._project_service = project_service
        self._labeling_service = labeling_service
        self._export_service = export_service
        
        # State
        self._current_project: Project = None
        self._navigation_service: NavigationService = None
        
        # UI components 
        self._project_browser: ProjectBrowser = None
        self._fragment_viewer: FragmentViewer = None 
        
        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._connect_signals()
        
        self.setWindowTitle("Herramienta de etiquetado de vídeos")
        self.resize(1400, 800)

    def _init_ui(self):
        """Initialize UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for view switching
        self.stacked_widget = QStackedWidget()
        
        # Create widgets with injected services
        self._project_browser = ProjectBrowser(
            project_service=self._project_service
        )
        
        self._fragment_viewer = FragmentViewer(
            labeling_service=self._labeling_service
        )
        
        # Add to stacked widget
        self.stacked_widget.addWidget(self._project_browser)
        self.stacked_widget.addWidget(self._fragment_viewer)
        
        layout.addWidget(self.stacked_widget)
        
        # Start with project browser
        self._safe_switch_view(0)

    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
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
        
        # Help menu
        help_menu = menubar.addMenu("&Ayuda")
        
        about_action = QAction("&Acerca de", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status("Todo listo, selecciona una carpeta para iniciar.")

    def _connect_signals(self):
        """Connect widget signals."""
        # Project browser signals
        self._project_browser.project_loaded.connect(self._on_project_loaded)
        self._project_browser.fragment_selected.connect(self._on_fragment_selected)
        
        # Fragment viewer signals
        self._fragment_viewer.fragment_labeled.connect(self._on_fragment_labeled)
        self._fragment_viewer.next_requested.connect(self._on_next_requested)
        self._fragment_viewer.back_requested.connect(self._show_browser)

    # === Event Handlers ===

    def _on_project_loaded(self, project: Project):
        """Handle project loaded event."""
        self._current_project = project
        
        # Create navigation service for this project
        self._navigation_service = NavigationService(project)
        
        # Inject navigation service into fragment viewer
        self._fragment_viewer.set_navigation_service(self._navigation_service)
        
        # Update status
        summary = self._project_service.get_project_summary(project)
        self._update_status(
            f"Proyecto cargado: {project.name} "
            f"({summary['labeled']}/{summary['total_fragments']} etiquetados)"
        )

    def _on_fragment_selected(self, fragment: Fragment):
        """Handle fragment selection from browser."""
        if not self._current_project or not self._navigation_service:
            return
        
        # Update navigation service
        self._navigation_service.set_current_fragment(fragment.fragment_id)
        
        # Load fragment in viewer
        self._fragment_viewer.load_fragment(fragment, self._current_project)
        
        # Switch to viewer
        self._safe_switch_view(1)
        
        # Update status
        current, total = self._navigation_service.get_position()
        self._update_status(f"Visualizando: {fragment.fragment_id} ({current}/{total})")

    def _on_fragment_labeled(self, fragment: Fragment):
        """Handle fragment labeled event."""
        # Refresh browser to show updated status
        self._project_browser.refresh()
        
        # Update status
        self._update_status(f"Fragmento {fragment.fragment_id} etiquetado como: '{fragment.label}'")

    def _on_next_requested(self):
        """Handle next fragment request."""
        if not self._navigation_service:
            return
        
        self._fragment_viewer.video_player.force_stop()
        next_fragment = self._navigation_service.move_to_next()
        
        if next_fragment:
            # Load next fragment
            self._fragment_viewer.load_fragment(next_fragment, self._current_project)
            
            # Update status
            current, total = self._navigation_service.get_position()
            self._update_status(f"Visualizando: {next_fragment.fragment_id} ({current}/{total})")
        else:
            # End of list
            summary = self._project_service.get_project_summary(self._current_project)
            QMessageBox.information(
                self,
                "¡Todo listo!",
                f"Haz alcanzado el final del proyecto.\n\n"
                f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
                f"({summary['progress_percentage']:.1f}%)"
            )
            self._show_browser()

    def _on_save_project(self):
        """Handle save project action."""
        if not self._current_project:
            QMessageBox.information(
                self,
                "Sin proyecto",
                "No hay ningun proyecto seleccionado."
            )
            return
        
        # Delegate to project browser's save handler
        self._project_browser._on_save_clicked()

    def _on_export(self):
        """Handle export action."""
        if not self._current_project:
            QMessageBox.information(
                self,
                "Sin proyecto",
                "No hay ningun proyecto seleccionado."
            )
            return
        
        if self._current_project.get_total_count() == 0:
            QMessageBox.information(
                self,
                "Sin datos",
                "No hay fragmentos que exportar."
            )
            return
        
        file_path = self._select_save_path(
            f"{self._current_project.name}_export.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # Delegate to service
            self._export_service.export(self._current_project, file_path, 'csv')
            
            summary = self._project_service.get_project_summary(self._current_project)
            QMessageBox.information(
                self,
                "Exportación exitosa",
                f"¡Se exportaron {summary['total_fragments']} fragmentos a CSV!\n\n"
                f"Etiquetados: {summary['labeled']}/{summary['total_fragments']}"
            )
            self._update_status(f"Exportados en: {file_path.name}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Ocurrió un error al exportar:\n{str(e)}"
            )

    def _show_browser(self):
        """Show the project browser view."""
        # Refresh browser
        self._project_browser.refresh()
        
        # Switch to browser
        self._safe_switch_view(0)
        self._update_status("Regresar al explorador de fragmentos")
    
    def _safe_switch_view(self, index: int):
        """
        Safely switch stacked widget views.
        Ensures video playback is fully stopped before hiding FragmentViewer.
        """

        if self._fragment_viewer:
            player = self._fragment_viewer.video_player
            if player:
                player.force_stop()

        self.stacked_widget.setCurrentIndex(index)

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Acerca de la herramienta de etiquetado",
            "<h2>Herramienta de etiquetado v1.0</h2>"
            "<p>Una herramienta para etiquetar fragmentos de video.</p>"
            "<p><b>Instrucciones:</b></p>"
            "<ol>"
            "<li>Selecciona la carpeta que contenga los fragmentos a etiquetar</li>"
            "<li>Da click en un fragmento para iniciar</li>"
            "<li>Asigna una etiqueta al fragmento seleccionado desde el panel de etiquetas (doble click)</li>"
            "<li>Exporta todas las etiquetas a un archivo CSV cuando finalices</li>"
            "</ol>"
            "<p>Centro de Investigación en Computación - IPN</p>"
        )

    # === Helper Methods ===

    def _select_save_path(self, default_name: str, filter: str) -> Path:
        """Show save file dialog."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar",
            default_name,
            filter
        )
        return Path(file_path) if file_path else None

    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        """Handle window close event."""
        if self._current_project:
            unlabeled = self._current_project.get_unlabeled_count()
            
            if unlabeled > 0:
                reply = QMessageBox.question(
                    self,
                    "Trabajo incompleto",
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