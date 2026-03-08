from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, 
    QListWidget, QLabel, QGroupBox, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class LabelPanel(QWidget):
    """Panel for selecting and assigning labels."""
    
    # Signals
    label_assigned = Signal(str)  # Emits when user assigns a label
    
    def __init__(self, default_labels=None, parent=None):
        super().__init__(parent)
        
        if default_labels is None:
            self.labels = [
                "Etiqueta 1", "Etiqueta 2", "Etiqueta 3", 
                "Etiqueta 4", "Otro"
            ]
        else:
            self.labels = default_labels.copy()
        
        self._current_label = None
        self._enabled = False
        
        self._init_ui()
        self._connect_signals()
        self._populate_labels()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        title = QLabel("Etiquetas disponibles")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Instruction label
        instruction = QLabel("Selecciona la etiqueta para el fragmento actual")
        instruction.setStyleSheet("font-size: 10px; color: #666; margin-bottom: 5px;")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Label list
        self.label_list = QListWidget()
        self.label_list.setEnabled(False)
        self.label_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #DDD;
                border-radius: 5px;
                background-color: white;
                color: #666;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #EEE;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
                color: white;
            }
            QListWidget::item:hover:enabled {
                background-color: #E8F4FD;
            }
            QListWidget:disabled {
                background-color: #F5F5F5;
            }
        """)
        self.label_list.setMouseTracking(True)
        self.label_list.viewport().setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.label_list)
        
        # Current label display
        current_label_group = QGroupBox("Etiqueta")
        current_label_layout = QVBoxLayout()
        
        self.current_label_display = QLabel("Sin etiqueta")
        self.current_label_display.setAlignment(Qt.AlignCenter)
        self.current_label_display.setMinimumHeight(50)
        self.current_label_display.setStyleSheet("""
            padding: 10px;
            background-color: #F5F5F5;
            border-radius: 5px;
            font-weight: bold;
            font-size: 14px;
            color: #666;
        """)
        current_label_layout.addWidget(self.current_label_display)
        
        current_label_group.setLayout(current_label_layout)
        layout.addWidget(current_label_group)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.label_list.itemClicked.connect(self._on_label_clicked)
    
    def _populate_labels(self):
        """Populate the label list."""
        self.label_list.clear()
        
        for label in self.labels:
            item = QListWidgetItem(label)
            font = QFont("Arial", 12)
            font.setBold(True)
            item.setFont(font)
            self.label_list.addItem(item)
    
    def _on_label_clicked(self, item):
        """Handle label click - immediately assign the label."""
        if not self._enabled:
            return
        
        label_text = item.text()
        self._current_label = label_text
        
        # Immediately emit the label assignment
        self.label_assigned.emit(label_text)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the label panel."""
        self._enabled = enabled
        self.label_list.setEnabled(enabled)
    
    def set_current_label(self, label: str):
        """Set the current label display."""
        if label:
            self._current_label = label
            self.current_label_display.setText(f"✓ {label}")
            self.current_label_display.setStyleSheet("""
                padding: 10px;
                background-color: #D4EDDA;
                border: 2px solid #10893E;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                color: #10893E;
            """)
        else:
            self._current_label = None
            self.current_label_display.setText("Sin etiqueta asignada")
            self.current_label_display.setStyleSheet("""
                padding: 10px;
                background-color: #F5F5F5;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                color: #666;
            """)
    
    def clear_selection(self):
        """Clear the current selection."""
        self.label_list.clearSelection()
        self._current_label = None
    
    def get_labels(self) -> list:
        """Get the current list of labels."""
        return self.labels.copy()
    
    def set_labels(self, labels: list):
        """Set the label list."""
        if labels:
            self.labels = labels.copy()
            self._populate_labels()