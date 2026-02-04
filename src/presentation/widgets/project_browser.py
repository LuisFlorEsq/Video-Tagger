from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QGroupBox, QListWidgetItem,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QSizePolicy


from src.application.services.project_service import ProjectService
from src.domain.models.project import Project
from src.domain.models.fragment import Fragment


class ProjectBrowser(QWidget):
    """
    Project browser widget - Only handles UI presentation.
    Business logic delegated to ProjectService (SRP + DIP).
    """
    
    # Signals
    project_loaded = Signal(Project)  # Emits when project is loaded
    fragment_selected = Signal(Fragment)  # Emits when fragment is selected
    
    def __init__(self, project_service: ProjectService, parent=None):
        """
        Initialize with injected dependencies (DIP).
        
        Args:
            project_service: Service for project operations
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Inject dependency
        self._project_service = project_service
        
        # State
        self._current_project: Project = None
        
        # UI
        self._init_ui()
        self._connect_signals()
        self._update_view()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Title
        self.title_label = QLabel("Herramienta de etiquetado de vídeos")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Selecciona una carpeta con fragmentos de video para continuar")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.subtitle_label)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        self.new_project_btn = QPushButton("📁 Nuevo proyecto")
        self.new_project_btn.setMinimumHeight(50)
        self.new_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #0078D4;
                color: white;
                border-radius: 5px;
                padding: 8px 18px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        # button_layout.addWidget(self.new_project_btn)
        
        self.load_project_btn = QPushButton("💾 Abrir proyecto existente")
        self.load_project_btn.setMinimumHeight(50)
        self.load_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #10893E;
                color: white;
                border-radius: 5px;
                padding: 8px 18px;

            }
            QPushButton:hover {
                background-color: #0E7B38;
            }
        """)
        # button_layout.addWidget(self.load_project_btn)
        
        for btn in (self.new_project_btn, self.load_project_btn):
            btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            btn.setFixedHeight(60)
            btn.adjustSize()
            
        button_layout.addWidget(self.new_project_btn, alignment=Qt.AlignHCenter)
        button_layout.addWidget(self.load_project_btn, alignment=Qt.AlignHCenter)

        
        layout.addLayout(button_layout)
        
        # Project info group
        self.project_info_group = QGroupBox("Proyecto actual")
        self.project_info_group.setVisible(False)
        info_layout = QVBoxLayout()
        
        self.project_name_label = QLabel("")
        self.project_name_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        info_layout.addWidget(self.project_name_label)
        
        self.project_stats_label = QLabel("")
        self.project_stats_label.setStyleSheet("font-size: 11px; color: #666;")
        info_layout.addWidget(self.project_stats_label)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Regresar al menu principal")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        nav_layout.addWidget(self.back_btn)
        
        self.save_project_btn = QPushButton("💾 Guardar proyecto")
        self.save_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        nav_layout.addWidget(self.save_project_btn)
        
        info_layout.addLayout(nav_layout)
        
        self.project_info_group.setLayout(info_layout)
        layout.addWidget(self.project_info_group)
        
        # Fragment list
        self.fragment_list_group = QGroupBox("Fragmentos de video")
        self.fragment_list_group.setVisible(False)
        fragment_list_layout = QVBoxLayout()
        
        search_label = QLabel("Selecciona un fragmento para etiquetar:")
        search_label.setStyleSheet("font-size: 11px; color: #666;")
        fragment_list_layout.addWidget(search_label)
        
        self.fragment_list = QListWidget()
        self.fragment_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #DDD;
                border-radius: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #EEE;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #E8F4FD;
            }
        """)
        fragment_list_layout.addWidget(self.fragment_list)
        
        self.fragment_list_group.setLayout(fragment_list_layout)
        layout.addWidget(self.fragment_list_group)
            
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Project options
        self.new_project_btn.clicked.connect(self._on_new_project_clicked)
        self.load_project_btn.clicked.connect(self._on_load_project_clicked)
        self.save_project_btn.clicked.connect(self._on_save_clicked)

        # Fragment and back to menu options
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.fragment_list.itemDoubleClicked.connect(self._on_fragment_double_clicked)
    
    # === Command Handlers (UI Logic Only) ===
    
    def _on_new_project_clicked(self):
        """Handle new project button click."""
        folder_path = self._select_folder()
        if not folder_path:
            return
        
        try:
            # Delegate to service (business logic)
            project = self._project_service.create_project_from_folder(folder_path)
            self._load_project(project)
            self.project_loaded.emit(project)
        except ValueError as e:
            self._show_error("Error al crear proyecto", str(e))
        except Exception as e:
            self._show_error("Error inesperado", f"No se pudo crear el proyecto: {str(e)}")
    
    def _on_load_project_clicked(self):
        """Handle load project button click."""
        file_path = self._select_project_file()
        if not file_path:
            return
        
        try:
            # Delegate to service (business logic)
            project = self._project_service.load_project(file_path)
            self._load_project(project)
            self.project_loaded.emit(project)
        except ValueError as e:
            self._show_error("No se pudo cargar el proyecto", str(e))
        except Exception as e:
            self._show_error("Error inesperado", f"No se pudo cargar el proyecto: {str(e)}")
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self._current_project = None
        self._update_view()
    
    def _on_save_clicked(self):
        """Handle save button click."""
        if not self._current_project:
            return
        
        file_path = self._select_save_path(
            f"{self._current_project.name}.json",
            "JSON Files (*.json)"
        )
        if not file_path:
            return
        
        try:
            # Delegate to service (business logic)
            self._project_service.save_project(self._current_project, file_path)
            
            # Get summary from service
            summary = self._project_service.get_project_summary(self._current_project)
            
            self._show_info(
                "Éxito",
                f"¡El proyecto se guardo correctamente!\n\n"
                f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
                f"({summary['progress_percentage']:.1f}%)"
            )
        except Exception as e:
            self._show_error("Error al guardar", str(e))
    
    def _on_fragment_double_clicked(self, item):
        """Handle fragment double-click."""
        if not self._current_project:
            return
        
        fragment_id = item.data(Qt.UserRole)
        fragment = self._current_project.get_fragment(fragment_id)
        
        if fragment:
            self.fragment_selected.emit(fragment)
    
    # === Public Methods ===
    
    def set_project(self, project: Project):
        """
        Set the current project.
        
        Args:
            project: Project to display
        """
        self._load_project(project)
    
    def refresh(self):
        """Refresh the current view."""
        if self._current_project:
            self._populate_fragment_list()
            self._update_project_stats()
    
    def get_current_project(self) -> Project:
        """Get the currently loaded project."""
        return self._current_project
    
    # === Private Helper Methods (UI Only) ===
    
    def _load_project(self, project: Project):
        """Load a project into the UI."""
        self._current_project = project
        self._update_view()
    
    def _update_view(self):
        """Update the view based on current state."""
        has_project = self._current_project is not None
        
        # Toggle visibility
        self.project_info_group.setVisible(has_project)
        self.fragment_list_group.setVisible(has_project)
        
        self.new_project_btn.setVisible(not has_project)
        self.load_project_btn.setVisible(not has_project)
        
        if has_project:
            self.subtitle_label.setText(f"Proyecto: {self._current_project.name}")
            self.project_name_label.setText(f"📁 {self._current_project.name}")
            self._populate_fragment_list()
            self._update_project_stats()
        else:
            self.subtitle_label.setText("Selecciona una carpeta con fragmentos de video para continuar")
    
    def _populate_fragment_list(self):
        """Populate the fragment list from current project."""
        self.fragment_list.clear()
        
        if not self._current_project:
            return
        
        for fragment in self._current_project.fragments:
            video_name = fragment.get_video_name()
            
            # Create display text
            if fragment.is_labeled():
                text = f"✓ {fragment.fragment_id} - {video_name} [{fragment.label}]"
                item = QListWidgetItem(text)
                item.setForeground(Qt.darkGreen)
            else:
                text = f"⭘ {fragment.fragment_id} - {video_name}"
                item = QListWidgetItem(text)
            
            item.setData(Qt.UserRole, fragment.fragment_id)
            self.fragment_list.addItem(item)
    
    def _update_project_stats(self):
        """Update project statistics display."""
        if not self._current_project:
            return
        
        # Use service for statistics
        summary = self._project_service.get_project_summary(self._current_project)
        
        self.project_stats_label.setText(
            f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
            f"fragmentos etiquetados ({summary['progress_percentage']:.1f}%)"
        )
    
    def _select_folder(self) -> Path:
        """Show folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleciona la carpeta con los fragmentos",
            "",
            QFileDialog.ShowDirsOnly
        )
        return Path(folder) if folder else None
    
    def _select_project_file(self) -> Path:
        """Show project file selection dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar proyecto",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        return Path(file_path) if file_path else None
    
    def _select_save_path(self, default_name: str, filter: str) -> Path:
        """Show save file dialog."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar proyecto",
            default_name,
            filter
        )
        return Path(file_path) if file_path else None
    
    def _show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def _show_info(self, title: str, message: str):
        """Show info message dialog."""
        QMessageBox.information(self, title, message)