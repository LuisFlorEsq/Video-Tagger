from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget
)

from src.domain.models.media.media_item import MediaType
from src.ui.styles import (
    AppTheme,
    btn_primary,
    btn_ghost,
    text_section_header, text_secondary,
    media_card, text_label, text_desc
)

_TYPES: list[tuple[MediaType, str, str, str]] = [
    (
        MediaType.VIDEO,
        "Video",
        "Fragmentos de video (.mp4, .avi, .mov, mkv...)",
        AppTheme.SUCCESS
    ),
    (
        MediaType.IMAGE,
        "Imagen",
        "Imágenes estáticas (.jpg, .png, .bmp, .webp...)",
        AppTheme.SUCCESS
    ),
    (
        MediaType.AUDIO,
        "Audio",
        "Clips de audio (.mp3, .wav, .flac, .ogg...)",
        AppTheme.SUCCESS
    ),
    (
        MediaType.TEXT,
        "Texto",
        "Documentos de texto (.txt, .csv, .json, .md...)",
        AppTheme.SUCCESS
    )
]


class MediaCard(QWidget):
    """Interactive media card which selects an internal QRadioButton"""

    def __init__(self, radio: QRadioButton, parent=None):
        super().__init__(parent)
        self._radio = radio

    def mousePressEvent(self, event):
        self._radio.setChecked(True)
        super().mousePressEvent(event)


class MediaTypeDialog(QDialog):
    """Small dialog presented before the folder picker when creating a new project"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tipo de medio")
        self.setFixedWidth(420)
        self.setModal(True)

        self._chosen: MediaType = MediaType.VIDEO
        self._radio_map: dict[MediaType, QRadioButton] = {}

        self._init_ui()

    @property
    def chosen(self) -> MediaType:
        return self._chosen

    # ---------------------------------------------
    # UI construction
    # ---------------------------------------------

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        title = QLabel("¿Qué tipos de archivos vas a etiquetar?")
        title.setStyleSheet(text_section_header())
        title.setWordWrap(True)
        root.addWidget(title)

        sub = QLabel("Selecciona el tipo de medio para el nuevo proyecto.")
        sub.setStyleSheet(text_secondary())
        root.addWidget(sub)

        # Radio cards
        group = QButtonGroup(self)
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(8)

        for i, (mt, label, desc, accent) in enumerate(_TYPES):
            card = self._make_card(mt, label, desc, accent, group)
            cards_layout.addWidget(card)
            if i == 0:
                self._radio_map[mt].setChecked(True)

        root.addLayout(cards_layout)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(btn_ghost())
        cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Seleccionar carpeta")
        ok_btn.setStyleSheet(btn_primary())
        ok_btn.setFixedHeight(34)
        ok_btn.clicked.connect(self._accept)
        btn_row.addWidget(ok_btn)

        root.addLayout(btn_row)

    def _make_card(
        self,
        mt: MediaType,
        label: str,
        desc: str,
        accent: str,
        group: QButtonGroup,
    ) -> QWidget:

        radio = QRadioButton()

        radio.setStyleSheet(f"""
            QRadioButton {{
                background: transparent;
                border: none;
            }}
            QRadioButton::indicator {{
                width: 9px;
                height: 9px;
                border: 1px solid #a0a0a0;
                border-radius: 5px; /* La mitad del ancho/alto aproximado para hacerlo circular */
            }}
            QRadioButton::indicator:checked {{
                background-color: {accent};
                border: 1px solid {accent};
            }}
        """)

        group.addButton(radio)
        self._radio_map[mt] = radio

        card = MediaCard(radio=radio)
        card.setStyleSheet(media_card(accent))

        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(text_label())

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(text_desc())

        text_col.addWidget(name_lbl)
        text_col.addWidget(desc_lbl)

        row.addWidget(radio)
        row.addLayout(text_col)
        row.addStretch()

        return card

    # ------ Slots -----
    def _accept(self) -> None:
        for mt, radio in self._radio_map.items():
            if radio.isChecked():
                self._chosen = mt
                break
        self.accept()
