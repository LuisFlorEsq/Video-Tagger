from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer

from src.presentation.widgets.video_player import VideoPlayer
from src.presentation.widgets.label_panel import LabelPanel
from src.application.services.labeling_service import LabelingService
from src.application.services.navigation_service import NavigationService
from src.application.services.project_service import ProjectService

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment


class FragmentViewer(QWidget):
    """
    Fragment viewer widget - Only handles UI presentation.
    Business logic delegated to services (SRP + DIP).
    """
    
    # Signals
    fragment_labeled = Signal(Fragment)  # Emits when fragment is labeled
    prev_requested = Signal()  # Emits when user wants previous fragment
    next_requested = Signal()  # Emits when user wants next fragment
    back_requested = Signal()  # Emits when user wants to go back
    
    def __init__(
        self, 
        labeling_service: LabelingService,
        project_service: ProjectService,
        navigation_service: NavigationService = None,
        available_labels: list = None,
        parent=None
    ):
        """
        Initialize with injected dependencies (DIP).
        
        Args:
            labeling_service: Service for labeling operations
            navigation_service: Service for navigation (optional, can be set later)
            available_labels: List of available labels
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Inject dependencies
        self._labeling_service = labeling_service
        self._navigation_service = navigation_service
        self._project_service = project_service
        
        # State
        self._current_fragment: Fragment = None
        self._current_project: Project = None
        
        # Default labels
        if available_labels is None:
            self.available_labels = [
                "Etiqueta 1", "Etiqueta 2", "Etiqueta 3", 
                "Etiqueta 4", "Otro"
            ]
        else:
            self.available_labels = available_labels
        
        # UI
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with navigation
        header_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Regresar")
        self.back_btn.setMaximumWidth(200)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        header_layout.addWidget(self.back_btn)
        
        header_layout.addStretch()
        
        self.fragment_info_label = QLabel("No se ha cargado ningun fragmento")
        self.fragment_info_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        header_layout.addWidget(self.fragment_info_label)
        
        header_layout.addStretch()
        
        # Position indicator
        self.position_label = QLabel("")
        self.position_label.setStyleSheet("font-size: 11px; color: #666;")
        header_layout.addWidget(self.position_label)
        
        layout.addLayout(header_layout)
        
        # Main content area - split into video and controls
        content_layout = QHBoxLayout()
        
        # Left: Video player
        video_group = QGroupBox("Fragmento de video (1 segundo)")
        video_layout = QVBoxLayout()
        
        self.video_player = VideoPlayer()
        video_layout.addWidget(self.video_player)
        
        # Playback info
        playback_info = QLabel("Da click al botón > para iniciar")
        playback_info.setStyleSheet("font-size: 10px; color: #666; padding: 5px;")
        playback_info.setAlignment(Qt.AlignCenter)
        video_layout.addWidget(playback_info)
        
        video_group.setLayout(video_layout)
        content_layout.addWidget(video_group, 2)  # 2/3 of space
        
        # Right: Labeling controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Fragment details
        details_group = QGroupBox("Detalles")
        details_layout = QVBoxLayout()
        
        self.video_name_label = QLabel("Fuente(video): -")
        self.video_name_label.setWordWrap(True)
        self.video_name_label.setStyleSheet("font-size: 11px; padding: 3px;")
        details_layout.addWidget(self.video_name_label)
        
        self.duration_label = QLabel("Duración: -")
        self.duration_label.setStyleSheet("font-size: 11px; padding: 3px;")
        details_layout.addWidget(self.duration_label)
        
        self.status_label = QLabel("Estatus: No etiquetado")
        self.status_label.setStyleSheet("font-size: 11px; padding: 3px;")
        details_layout.addWidget(self.status_label)
        
        details_group.setLayout(details_layout)
        controls_layout.addWidget(details_group)
        
        # Label panel
        label_group = QGroupBox("Asignar etiqueta")
        label_layout = QVBoxLayout()
        
        self.label_panel = LabelPanel(self.available_labels)
        label_layout.addWidget(self.label_panel)
        
        label_group.setLayout(label_layout)
        controls_layout.addWidget(label_group)
        
        # Action buttons
        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Atras")
        self.prev_btn.setMinimumHeight(45)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                background-color: #0078D4;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover:enabled {
                background-color: #106EBE;
            }
            QPushButton:disabled {
                background-color: #CCC;
                color: #888;
            }
        """)
        actions_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Siguiente →")
        self.next_btn.setMinimumHeight(45)
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                background-color: #0078D4;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover:enabled {
                background-color: #106EBE;
            }
            QPushButton:disabled {
                background-color: #CCC;
                color: #888;
            }
        """)
        actions_layout.addWidget(self.next_btn)
                
        actions_group.setLayout(actions_layout)
        controls_layout.addWidget(actions_group)
        
        controls_layout.addStretch()
        
        content_layout.addWidget(controls_widget, 1)  # 1/3 of space
        
        layout.addLayout(content_layout)
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.next_btn.clicked.connect(self._on_next_clicked)
        self.label_panel.label_assigned.connect(self._on_label_assigned)
    
    # === Command Handlers (UI Logic Only) ===
    
    def _on_label_assigned(self, label: str):
        """Handle label assignment from label panel."""
        if not self._current_fragment:
            return
        
        try:
            # Delegate to service (business logic)
            self._labeling_service.assign_label(self._current_fragment, label)
            
            # Update UI
            self._update_fragment_status()
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            
            # Emit signal
            self.fragment_labeled.emit(self._current_fragment)
            
        except ValueError as e:
            self._show_error("No se pudo etiquetar", str(e))
    
    def _on_prev_clicked(self):
        """Handle previous button click."""
        if not self._current_fragment:
            return
        
        # Check if current fragment is labeled
        if not self._current_fragment.is_labeled():
            reply = QMessageBox.question(
                self,
                "Fragmento saltado",
                "Este fragmento aun no ha sido etiquetado ¿Desea saltarlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
        # Check if we can navigate (avoid out of bonds)
        if self._navigation_service and self._navigation_service.has_previous():
            # Let the parent handle navigation
            self.prev_requested.emit()
        else:
            self.prev_requested.emit()
            
    
    def _on_next_clicked(self):
        """Handle next button click."""
        if not self._current_fragment:
            return
        
        # Check if current fragment is labeled
        if not self._current_fragment.is_labeled():
            reply = QMessageBox.question(
                self,
                "Fragmento saltado",
                "Este fragmento aun no ha sido etiquetado. ¿Desea saltarlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Check if we can navigate
        if self._navigation_service and self._navigation_service.has_next():
            # Let the parent handle navigation
            self.next_requested.emit()
        else:
            # Just emit the signal, parent will handle
            self.next_requested.emit()
    
    def _on_back_clicked(self):
        """Handle back button click."""
        if self._current_fragment and not self._current_fragment.is_labeled():
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Este fragmento no ha sido etiquetado. ¿Estas seguro de regresar?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Stop video using threaded cleanup
        self.back_requested.emit()
    
    # === Public Methods ===
    
    def load_fragment(self, fragment: Fragment, project: Project = None):
        """
        Load a fragment for viewing and labeling.
        
        Args:
            fragment: Fragment to load
            project: Parent project (optional, for context)
        """        
        self._current_fragment = fragment
        self._current_project = project
        
        # Check if video exists
        if not Path(fragment.video_path).exists():
            self._show_error(
                "Archivo no encontrado",
                f"No se encontro el archivo de video:\n{fragment.video_path}"
            )
            return
        
        # Set callback for when media is ready and first frame is visible — safe to seek
        self.video_player.on_ready_callback = self._on_video_ready_for_fragment
        
        # Load video asynchronously
        self.video_player.load_video(fragment.video_path)
        
        # Update UI
        self._update_fragment_info()
        self._update_fragment_status()
        
        # Update position if navigation service is available
        self._update_position_display()
        
        # Enable controls
        self.label_panel.set_enabled(True)
        self.next_btn.setEnabled(fragment.is_labeled())
        self.prev_btn.setEnabled(fragment.is_labeled())

    
    def _on_video_ready_for_fragment(self):
        """Callback when media is ready and first frame is rendered — safe to seek."""
        if self._current_fragment:
            start_ms = int(self._current_fragment.start_time * 1000)
            self.video_player.seek_position(start_ms)
        
    
    def set_navigation_service(self, navigation_service: NavigationService):
        """
        Set the navigation service.
        
        Args:
            navigation_service: Navigation service to use
        """
        self._navigation_service = navigation_service
        self._update_position_display()
    
    def get_current_fragment(self) -> Fragment:
        """Get the currently loaded fragment."""
        return self._current_fragment
    
    # === Private Helper Methods (UI Only) ===
    
    def _update_fragment_info(self):
        """Update fragment information display."""
        if not self._current_fragment:
            return
        
        self.fragment_info_label.setText(
            f"Fragmento: {self._current_fragment.fragment_id}"
        )
        
        video_name = self._current_fragment.get_video_name()
        self.video_name_label.setText(f"Fuente(video): {video_name}")
        self.duration_label.setText(
            f"Duración: {self._current_fragment.duration:.1f} segundos"
        )
    
    def _update_fragment_status(self):
        """Update fragment status display."""
        if not self._current_fragment:
            return
        
        if self._current_fragment.is_labeled():
            self.status_label.setText(
                f"Estatus: ✓ Etiquetado como '{self._current_fragment.label}'"
            )
            self.status_label.setStyleSheet(
                "font-size: 11px; padding: 3px; color: #10893E; font-weight: bold;"
            )
            self.label_panel.set_current_label(self._current_fragment.label)
        else:
            self.status_label.setText("Estatus: No etiquetado")
            self.status_label.setStyleSheet(
                "font-size: 11px; padding: 3px; color: #856404; font-weight: bold;"
            )
            self.label_panel.set_current_label(None)
    
    def _update_position_display(self):
        """Update position indicator."""
        if self._navigation_service:
            current, total = self._navigation_service.get_position()
            self.position_label.setText(f"{current}/{total}")
        else:
            self.position_label.setText("")
    
    def _show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def _show_info(self, title: str, message: str):
        """Show info message dialog."""
        QMessageBox.information(self, title, message)