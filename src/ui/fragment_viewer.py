from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# UI components
from src.ui.video_player import VideoPlayer
from src.ui.label_panel import LabelPanel

# Data models
from src.models.project import Project
from src.models.fragment import VideoFragment


class FragmentViewer(QWidget):
    """Widget for viewing and labeling a single video fragment."""
    
    # Signals
    save_requested = Signal()  # Emits when user wants to save
    prev_requested = Signal() # Emits when user wants previous fragment
    next_requested = Signal()  # Emits when user wants next fragment
    back_requested = Signal()  # Emits when user wants to go back (project browser)
    
    def __init__(self, available_labels=None, parent=None):
        super().__init__(parent)
        
        self.current_fragment = None
        self.current_project = None
        
        if available_labels is None:
            self.available_labels = [
                "Etiqueta 1", "Etiqueta 2", "Etiqueta 3",
                "Etiqueta 4", "Otro"
            ]
        else:
            self.available_labels = available_labels
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with navigation
        header_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Regresar a los fragmentos")
        self.back_btn.setMaximumWidth(180)
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
        
        self.fragment_info_label = QLabel("Ningun fragmento cargado")
        self.fragment_info_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        header_layout.addWidget(self.fragment_info_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Main content area - split into video and controls
        content_layout = QHBoxLayout()
        
        # Left: Video player
        video_group = QGroupBox("Reproductor de video")
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
        
        # Label panel
        label_group = QGroupBox("Asignar etiqueta")
        label_layout = QVBoxLayout()
        
        self.label_panel = LabelPanel(self.available_labels)
        label_layout.addWidget(self.label_panel)
        
        label_group.setLayout(label_layout)
        controls_layout.addWidget(label_group)
        
        # Action buttons
        actions_group = QGroupBox("Acciones")
        actions_layout = QVBoxLayout()
        
        self.save_btn = QPushButton("Guardar y continuar")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                background-color: #10893E;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover:enabled {
                background-color: #0E7B38;
            }
            QPushButton:disabled {
                background-color: #CCC;
                color: #888;
            }
        """)
        actions_layout.addWidget(self.save_btn)
        
        self.prev_btn = QPushButton("Anterior fragmento")
        self.prev_btn.setMinimumHeight(35)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setStyleSheet("""
                    QPushButton {
                font-size: 12px;
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
            }            QPushButton {
                font-size: 12px;
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
        
        self.next_btn = QPushButton("Siguiente fragmento")
        self.next_btn.setMinimumHeight(35)
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
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
        
        # Fragment details
        details_group = QGroupBox("Detalles")
        details_layout = QVBoxLayout()
        
        self.video_name_label = QLabel("Video: -")
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
        
        controls_layout.addStretch()
        
        content_layout.addWidget(controls_widget, 1)  # 1/3 of space
        
        layout.addLayout(content_layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.next_btn.clicked.connect(self._on_next_clicked)
        self.label_panel.label_assigned.connect(self._on_label_assigned)
    
    def load_fragment(self, fragment: VideoFragment, project: Project):
        """Load a fragment for viewing and labeling."""
        self.current_fragment = fragment
        self.current_project = project
        
        # Load video
        if not Path(fragment.video_path).exists():
            QMessageBox.critical(
                self,
                "Archivo no encontrado",
                f"Archivo de video no encontrado:\n{fragment.video_path}"
            )
            return
        
        self.video_player.load_video(fragment.video_path)
        
        # Seek to start time
        self.video_player.seek_position(int(fragment.start_time * 1000))
        
        # Update UI
        self.fragment_info_label.setText(f"Identificador de fragmento: {fragment.fragment_id}")
        
        video_name = Path(fragment.video_path).name
        self.video_name_label.setText(f"Video: {video_name}")
        self.duration_label.setText(f"Duración: {fragment.duration:.1f} segundos")
        
        # Update label status
        if fragment.is_labeled():
            self.status_label.setText(f"Estatus: ✓ Etiquetado como '{fragment.label}'")
            self.status_label.setStyleSheet("font-size: 11px; padding: 3px; color: #10893E; font-weight: bold;")
            self.label_panel.set_current_label(fragment.label)
            self.save_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
        else:
            self.status_label.setText("Estatus: No etiquetado")
            self.status_label.setStyleSheet("font-size: 11px; padding: 3px; color: #856404; font-weight: bold;")
            self.label_panel.set_current_label(None)
            self.save_btn.setEnabled(False)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
        
        # Enable label panel
        self.label_panel.set_enabled(True)
    
    def _on_label_assigned(self, label: str):
        """Handle label assignment."""
        if not self.current_fragment:
            return
        
        self.current_fragment.update_label(label)
        self.status_label.setText(f"Estatus: ✓ Etiquetado como '{label}'")
        self.status_label.setStyleSheet("font-size: 11px; padding: 3px; color: #10893E; font-weight: bold;")
        
        # Update the label in the label panel
        self.label_panel.set_current_label(label)
        
        # Enable save and next buttons
        self.save_btn.setEnabled(True)
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
    
    def _on_save_clicked(self):
        """Handle save button click."""
        if not self.current_fragment or not self.current_fragment.is_labeled():
            QMessageBox.warning(
                self,
                "Sin etiqueta",
                "Por favor, asigna una etiqueta antes de guardar."
            )
            return
        
        self.save_requested.emit()
        
        # Show feedback
        QMessageBox.information(
            self,
            "Guardado",
            f"Fragmento '{self.current_fragment.fragment_id}' etiquetado como '{self.current_fragment.label}'"
        )
        
    def _on_prev_clicked(self):
        """Handle previous button click."""
        if not self.current_fragment.is_labeled():
            reply = QMessageBox.question(
                self,
                "Fragmento saltado",
                "Este fragmento no ha sido etiquetado. ¿Desea saltarlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
        self.prev_requested.emit()
        
    def _on_next_clicked(self):
        """Handle next button click."""
        if not self.current_fragment.is_labeled():
            reply = QMessageBox.question(
                self,
                "Fragmento saltado",
                "Este fragmento aun no ha sido etiquetado. ¿Desea saltarlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        self.next_requested.emit()
    
    def _on_back_clicked(self):
        """Handle back button click."""
        if self.current_fragment and not self.current_fragment.is_labeled():
            reply = QMessageBox.question(
                self,
                "Fragmento sin etiquetar",
                "Este fragmento no ha sido etiquetado. ¿Estas seguro de regresar?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        self.video_player.stop()
        self.back_requested.emit()
    
    def _on_labels_changed(self, labels: list):
        """Handle label list changes."""
        self.available_labels = labels
    
    def get_available_labels(self) -> list:
        """Get the current list of available labels."""
        return self.available_labels