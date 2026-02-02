from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QMessageBox, QMenuBar, QStatusBar, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
import pandas as pd

from src.ui.project_browser import ProjectBrowser
from src.ui.fragment_viewer import FragmentViewer

from src.models.project import Project
from src.models.fragment import VideoFragment


class MainWindow(QMainWindow):
    """Main application window for video fragment tagging."""
    
    def __init__(self):
        super().__init__(parent=None)
        
        self.current_project = None
        self.current_fragment_index = -1
        
        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._connect_signals()
        
        self.setWindowTitle("Herramienta de etiquetado")
        self.resize(1400, 800)
    
    def _init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for switching between views
        self.stacked_widget = QStackedWidget()
        
        # Page 0: Project Browser
        self.project_browser = ProjectBrowser()
        self.stacked_widget.addWidget(self.project_browser)
        
        # Page 1: Fragment Viewer
        self.fragment_viewer = FragmentViewer()
        self.stacked_widget.addWidget(self.fragment_viewer)
        
        layout.addWidget(self.stacked_widget)
        
        # Start with project browser
        self.stacked_widget.setCurrentIndex(0)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Archivo")
        
        new_project_action = QAction("Nuevo Proyecto desde Carpeta", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self.project_browser._create_new_project)
        file_menu.addAction(new_project_action)
        
        load_project_action = QAction("Cargar Proyecto", self)
        load_project_action.setShortcut("Ctrl+O")
        load_project_action.triggered.connect(self.project_browser._load_existing_project)
        file_menu.addAction(load_project_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Guardar Proyecto", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Exportar a formato CSV", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_to_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Ayuda")
        
        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        #TODO: Delete this section or change the message to avoid repetition
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Todo listo, selecciona una carpeta para iniciar.")
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Project browser signals
        self.project_browser.project_selected.connect(self._on_project_selected)
        self.project_browser.fragment_selected.connect(self._on_fragment_selected)
        
        # Fragment viewer signals
        self.fragment_viewer.save_requested.connect(self._on_save_requested)
        self.fragment_viewer.prev_requested.connect(self._on_prev_requested)
        self.fragment_viewer.next_requested.connect(self._on_next_requested)
        self.fragment_viewer.back_requested.connect(self._on_back_to_browser)
    
    def _on_project_selected(self, project: Project):
        """Handle project selection."""
        self.current_project = project
        self.status_bar.showMessage(f"Proyecto cargado: {project.name} ({project.get_total_count()} fragmentos de vídeo.)")
    
    def _on_fragment_selected(self, fragment: VideoFragment):
        """Handle fragment selection from browser."""
        if not self.current_project:
            return
        
        #TODO: Change the current logic to a Hash approximation avoiding a for loop search
        # Find fragment index
        for i, frag in enumerate(self.current_project.fragments):
            if frag.fragment_id == fragment.fragment_id:
                self.current_fragment_index = i
                break
        
        # Load fragment in viewer
        self.fragment_viewer.load_fragment(fragment, self.current_project)
        
        # Switch to fragment viewer
        self.stacked_widget.setCurrentIndex(1)
        self.status_bar.showMessage(
            f"Fragmento actual: {fragment.fragment_id} "
            f"({self.current_fragment_index + 1}/{self.current_project.get_total_count()})"
        )
    
    def _on_save_requested(self):
        """Handle save request from fragment viewer."""
        if self.current_project:
            self.project_browser.refresh_fragment_list()
            self.status_bar.showMessage("✓ Fragmento etiquetado y guardado.")
             
            # Save the current status of the project
            # self.current_project.save_to_file(self.current_project.folder_path)
    
    def _on_prev_requested(self):
        """Handle previous fragment request."""
        if not self.current_project:
            return
        
        # Save current fragment if labeled        
        if self.fragment_viewer.current_fragment and self.fragment_viewer.current_fragment.is_labeled():
            self.project_browser.refresh_fragment_list()
        
        # Find previous fragment
        self.current_fragment_index -= 1
        
        if self.current_fragment_index < 0:
            # Out of bounds
            QMessageBox.information(
                self,
                "Todo listo",
                f"Haz llegado al inicio de los fragmentos.\n\n"
                f"Etiquetados: {self.current_project.get_labeled_count()}/{self.current_project.get_total_count()} "
                f"({self.current_project.get_progress_percentage():.1f}%)"          
            )
            self._on_back_to_browser()
            return
            
        # Load previous fragment
        prev_fragment = self.current_project.fragments[self.current_fragment_index]
        self.fragment_viewer.load_fragment(prev_fragment, self.current_project)
        self.status_bar.showMessage(
            f"Fragmento actual: {prev_fragment.fragment_id} "
            f"({self.current_fragment_index + 1}/{self.current_project.get_total_count()})"
        )
    
    def _on_next_requested(self):
        """Handle next fragment request."""
        if not self.current_project:
            return
        
        # Save current fragment if labeled
        if self.fragment_viewer.current_fragment and self.fragment_viewer.current_fragment.is_labeled():
            self.project_browser.refresh_fragment_list()
        
        # Find next fragment
        self.current_fragment_index += 1
        
        if self.current_fragment_index >= self.current_project.get_total_count():
            # End of fragments
            QMessageBox.information(
                self,
                "¡Todo listo!",
                f"Haz alcanzado el final de los fragmentos.\n\n"
                f"Etiquetados: {self.current_project.get_labeled_count()}/{self.current_project.get_total_count()} "
                f"({self.current_project.get_progress_percentage():.1f}%)"
            )
            self._on_back_to_browser()
            return
        
        # Load next fragment
        next_fragment = self.current_project.fragments[self.current_fragment_index]
        self.fragment_viewer.load_fragment(next_fragment, self.current_project)
        self.status_bar.showMessage(
            f"Fragmento actual: {next_fragment.fragment_id} "
            f"({self.current_fragment_index + 1}/{self.current_project.get_total_count()})"
        )
    
    def _on_back_to_browser(self):
        """Return to the project browser."""
        # Refresh the fragment list
        self.project_browser.refresh_fragment_list()
        
        # Switch to browser view
        self.stacked_widget.setCurrentIndex(0)
        self.status_bar.showMessage("Regresando al explorador de proyectos")
    
    def _show_browser(self):
        """Show the project browser."""
        self._on_back_to_browser()
    
    def _save_project(self):
        """Save the current project."""
        if not self.current_project:
            QMessageBox.information(
                self,
                "Sin proyecto",
                "No hay ningun proyecto abierto."
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar proyecto",
            f"{self.current_project.name}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.current_project.save_to_file(Path(file_path))
                self.status_bar.showMessage(f"✓ Proyecto guardado: {Path(file_path).name}")
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"El proyecto se guardo correctamente!\n\n"
                    f"Etiquetados: {self.current_project.get_labeled_count()}/"
                    f"{self.current_project.get_total_count()} fragmentos"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al guardar el proyecto:\n{str(e)}"
                )
    
    def _export_to_csv(self):
        """Export project data to CSV."""
        if not self.current_project:
            QMessageBox.information(
                self,
                "Sin proyecto",
                "No hay ningun proyecto seleccionado."
            )
            return
        
        if self.current_project.get_total_count() == 0:
            QMessageBox.information(
                self,
                "Sin datos",
                "No hay fragmentos que exportar."
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a CSV",
            f"{self.current_project.name}_export.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                # Prepare data
                data = [f.to_dict() for f in self.current_project.fragments]
                df = pd.DataFrame(data)
                
                # Add computed columns
                df['video_name'] = df['video_path'].apply(lambda x: Path(x).name)
                df['is_labeled'] = df['label'].apply(lambda x: x != '' and x is not None)
                
                # Reorder columns
                columns = [
                    'fragment_id', 'video_name', 'video_path', 
                    'start_time', 'duration', 'label', 'is_labeled',
                    'notes', 'created_at', 'modified_at'
                ]
                df = df[columns]
                
                df.to_csv(file_path, index=False)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"✓ Se exportaron {len(df)} fragmentos a CSV!\n\n"
                    f"Etiquetados: {df['is_labeled'].sum()}/{len(df)}"
                )
                self.status_bar.showMessage(f"✓ Exportados: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al exportar:\n{str(e)}"
                )
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Acerca de la herramienta de etiquetado",
            "<h2>Herramienta de etiquetado v0.01</h2>"
            "<p>Una herramienta para etiquetar fragmentos de video.</p>"
            "<p><b>Instrucciones:</b></p>"
            "<ol>"
            "<li>Selecciona la carpeta que contenga los fragmentos a etiquetar</li>"
            "<li>Da click en un fragmento para iniciar</li>"
            "<li>Asigna una etiqueta al fragmento seleccionado desde el panel de etiquetas</li>"
            "<li>Guarda tus cambios y continua con el siguiente fragmento</li>"
            "<li>Exporta todas las etiquetas a un archivo CSV cuando finalices</li>"
            "</ol>"
            "<p>Centro de Investigación en Computación - IPN</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.current_project:
            labeled = self.current_project.get_labeled_count()
            total = self.current_project.get_total_count()
            
            if labeled < total:
                reply = QMessageBox.question(
                    self,
                    "Proyecto incompleto",
                    f"Hasta el momento has etiquetado {labeled}/{total} fragmentos.\n\n"
                    f"¿Deseas guardar tu progreso antes de salir?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    self._save_project()
                    event.accept()
                elif reply == QMessageBox.Discard:
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
        else:
            event.accept()