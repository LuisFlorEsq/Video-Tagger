from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QGroupBox, QListWidgetItem,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import cv2

from src.models.project import Project
from src.models.fragment import VideoFragment


class ProjectBrowser(QWidget):
    """Widget for browsing and selecting projects/folders."""
    
    # Signals
    project_selected = Signal(Project)  # Emits when a project is selected
    fragment_selected = Signal(VideoFragment)  # Emits when a fragment is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_project = None
        self.current_mode = "project_list"  # "project_list" or "fragment_list"
        
        self._init_ui()
        self._connect_signals()
    
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
        button_layout = QHBoxLayout()
        
        self.new_project_btn = QPushButton("Nuevo proyecto") #TODO: Implement an SVG image for this button
        self.new_project_btn.setMinimumHeight(50)
        self.new_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #0078D4;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        button_layout.addWidget(self.new_project_btn)
        
        self.load_project_btn = QPushButton("Abrir proyecto existente") #TODO: Implement an SVG image for this button
        self.load_project_btn.setMinimumHeight(50)
        self.load_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #10893E;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0E7B38;
            }
        """)
        button_layout.addWidget(self.load_project_btn)
        
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
        
        self.save_project_btn = QPushButton("Guardar progreso")
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
        """Connect signals and slots."""
        # Project options
        self.new_project_btn.clicked.connect(self._create_new_project)
        self.load_project_btn.clicked.connect(self._load_existing_project)
        self.save_project_btn.clicked.connect(self._save_current_project)

        # Fragment and Back to menu options
        self.back_btn.clicked.connect(self._back_to_menu)
        self.fragment_list.itemDoubleClicked.connect(self._on_fragment_selected)
    
    def _create_new_project(self):
        """Create a new project from a folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:
            return
        
        folder = Path(folder_path)
        
        # Find video files in folder
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(folder.glob(f'*{ext}'))
        
        if not video_files:
            QMessageBox.warning(
                self,
                "Sin vídeos",
                "No se encontraron archivos de video en la carpeta seleccionada."
            )
            return
        
        # Create project
        project_name = folder.name
        self.current_project = Project(
            name=project_name,
            folder_path=str(folder)
        )
        
        # Create fragments from video files
        for i, video_file in enumerate(sorted(video_files)):
            # Get video duration
            cap = cv2.VideoCapture(str(video_file))
            duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
            fragment = VideoFragment(
                fragment_id=f"fragment_{i+1:03d}",
                video_path=str(video_file),
                start_time=0.0,
                duration=min(1.0, duration)
            )
            self.current_project.add_fragment(fragment)
        
        self._show_project_view()
        self.project_selected.emit(self.current_project)
    
    def _load_existing_project(self):
        """Load an existing project from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar proyecto",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self.current_project = Project.load_from_file(Path(file_path))
            self._show_project_view()
            self.project_selected.emit(self.current_project)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el proyecto:\n{str(e)}"
            )
    
    def _show_project_view(self):
        """Show the project fragment list view."""
        if not self.current_project:
            return
        
        self.current_mode = "fragment_list"
        
        # Update UI
        self.subtitle_label.setText(f"Proyecto actual: {self.current_project.name}")
        self.project_info_group.setVisible(True)
        self.fragment_list_group.setVisible(True)
        
        # Project selection components
        self.new_project_btn.setVisible(False)
        self.load_project_btn.setVisible(False)
        
        # Update project info
        self.project_name_label.setText(f"📁 {self.current_project.name}")
        self._update_project_stats()
        
        # Populate fragment list
        self._populate_fragment_list()
    
    def _populate_fragment_list(self):
        """Populate the fragment list."""
        self.fragment_list.clear()
        
        for fragment in self.current_project.fragments:
            video_name = Path(fragment.video_path).name
            
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
        """Update project statistics."""
        if not self.current_project:
            return
        
        labeled = self.current_project.get_labeled_count()
        total = self.current_project.get_total_count()
        progress = self.current_project.get_progress_percentage()
        
        self.project_stats_label.setText(
            f"Progreso: {labeled}/{total} fragmentos etiquetados ({progress:.1f}%)"
        )
    
    def _on_fragment_selected(self, item):
        """Handle fragment selection."""
        fragment_id = item.data(Qt.UserRole)
        fragment = self.current_project.get_fragment(fragment_id)
        
        if fragment:
            self.fragment_selected.emit(fragment)
    
    def _back_to_menu(self):
        """Return to the main menu."""
        self.current_mode = "project_list"
        
        # Reset UI
        self.subtitle_label.setText("Selecciona una carpeta con fragmentos de video para continuar")
        self.project_info_group.setVisible(False)
        self.fragment_list_group.setVisible(False)
        
        # Project selection components
        self.new_project_btn.setVisible(True)
        self.load_project_btn.setVisible(True)
    
    def _save_current_project(self):
        """Save the current project."""
        if not self.current_project:
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
                QMessageBox.information(
                    self,
                    "Éxito",
                    "El proyecto se guardo correctamente!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo guardar el proyecto:\n{str(e)}"
                )
    
    def refresh_fragment_list(self):
        """Refresh the fragment list display."""
        if self.current_mode == "fragment_list":
            self._populate_fragment_list()
            self._update_project_stats()
    
    def get_current_project(self) -> Project:
        """Get the current project."""
        return self.current_project