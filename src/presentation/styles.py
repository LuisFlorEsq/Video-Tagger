class AppTheme:
    # Brand colors
    PRIMARY       = "#0078D4"
    PRIMARY_HOVER = "#106EBE"
    SUCCESS       = "#10893E"
    SUCCESS_HOVER = "#0E7B38"
    WARNING       = "#F59E0B"
    WARNING_HOVER = "#D97706"
    DANGER        = "#D13438"
    DANGER_HOVER  = "#B02A2E"
    NEUTRAL       = "#6C757D"
    NEUTRAL_HOVER = "#5A6268"

    # Surfaces
    BG_PRIMARY    = "#FFFFFF"
    BG_SECONDARY  = "#F8F9FA"
    BG_TERTIARY   = "#F1F3F5"
    BORDER        = "#DEE2E6"
    BORDER_FOCUS  = "#0078D4"

    # Text
    TEXT_PRIMARY   = "#1A1D21"
    TEXT_SECONDARY = "#6C757D"
    TEXT_MUTED     = "#ADB5BD"
    TEXT_SUCCESS   = "#10893E"
    TEXT_WARNING   = "#92400E"

    # Shape
    RADIUS_SM = "4px"
    RADIUS_MD = "6px"
    RADIUS_LG = "10px"

    # Typography
    FONT_XS   = "11px"
    FONT_SM   = "12px"
    FONT_BASE = "13px"
    FONT_LG   = "15px"
    FONT_XL   = "20px"


# ============================================================
# Component style builders — called once per widget, not inline
# ============================================================

def btn_primary() -> str:
    return f"""
        QPushButton {{
            background-color: {AppTheme.PRIMARY};
            color: white;
            border: none;
            border-radius: {AppTheme.RADIUS_MD};
            padding: 8px 16px;
            font-size: {AppTheme.FONT_BASE};
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {AppTheme.PRIMARY_HOVER};
        }}
        QPushButton:disabled {{
            background-color: {AppTheme.BORDER};
            color: {AppTheme.TEXT_MUTED};
        }}
    """

def btn_success() -> str:
    return f"""
        QPushButton {{
            background-color: {AppTheme.SUCCESS};
            color: white;
            border: none;
            border-radius: {AppTheme.RADIUS_MD};
            padding: 8px 16px;
            font-size: {AppTheme.FONT_BASE};
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {AppTheme.SUCCESS_HOVER}; }}
        QPushButton:disabled {{ background-color: {AppTheme.BORDER}; color: {AppTheme.TEXT_MUTED}; }}
    """

def btn_warning() -> str:
    return f"""
        QPushButton {{
            background-color: {AppTheme.WARNING};
            color: white;
            border: none;
            border-radius: {AppTheme.RADIUS_MD};
            padding: 8px 16px;
            font-size: {AppTheme.FONT_BASE};
        }}
        QPushButton:hover:enabled {{ background-color: {AppTheme.WARNING_HOVER}; }}
        QPushButton:disabled {{ background-color: #FDE68A; color: {AppTheme.TEXT_MUTED}; }}
    """

def btn_danger() -> str:
    return f"""
        QPushButton {{
            background-color: {AppTheme.DANGER};
            color: white;
            border: none;
            border-radius: {AppTheme.RADIUS_MD};
            padding: 8px 16px;
            font-size: {AppTheme.FONT_BASE};
        }}
        QPushButton:hover:enabled {{ background-color: {AppTheme.DANGER_HOVER}; }}
        QPushButton:disabled {{ background-color: {AppTheme.BORDER}; color: {AppTheme.TEXT_MUTED}; }}
    """

def btn_ghost() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {AppTheme.TEXT_SECONDARY};
            border: 1px solid {AppTheme.BORDER};
            border-radius: {AppTheme.RADIUS_MD};
            padding: 8px 16px;
            font-size: {AppTheme.FONT_BASE};
        }}
        QPushButton:hover {{ background-color: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_PRIMARY}; }}
    """

def list_widget() -> str:
    return f"""
        QListWidget {{
            border: 1px solid {AppTheme.BORDER};
            border-radius: {AppTheme.RADIUS_MD};
            background-color: {AppTheme.BG_PRIMARY};
            font-size: {AppTheme.FONT_SM};
            outline: none;
        }}
        QListWidget::item {{
            padding: 10px 14px;
            border-bottom: 1px solid {AppTheme.BG_TERTIARY};
            color: {AppTheme.TEXT_PRIMARY};
        }}
        QListWidget::item:selected {{
            background-color: {AppTheme.PRIMARY};
            color: white;
            border-bottom-color: {AppTheme.PRIMARY_HOVER};
        }}
        QListWidget::item:hover:!selected {{
            background-color: {AppTheme.BG_SECONDARY};
        }}
    """

def label_tag_labeled() -> str:
    return f"""
        padding: 8px 12px;
        background-color: #D1FAE5;
        border: 1px solid #6EE7B7;
        border-radius: {AppTheme.RADIUS_MD};
        font-weight: bold;
        font-size: {AppTheme.FONT_BASE};
        color: {AppTheme.TEXT_SUCCESS};
    """

def label_tag_unlabeled() -> str:
    return f"""
        padding: 8px 12px;
        background-color: {AppTheme.BG_TERTIARY};
        border: 1px solid {AppTheme.BORDER};
        border-radius: {AppTheme.RADIUS_MD};
        font-size: {AppTheme.FONT_BASE};
        color: {AppTheme.TEXT_MUTED};
    """

def app_stylesheet() -> str:
    """Global stylesheet applied to QApplication — sets baseline for all widgets."""
    return f"""
        QMainWindow, QWidget {{
            background-color: {AppTheme.BG_SECONDARY};
            color: {AppTheme.TEXT_PRIMARY};
            font-family: "Segoe UI", system-ui, sans-serif;
            font-size: {AppTheme.FONT_BASE};
        }}
        QGroupBox {{
            border: 1px solid {AppTheme.BORDER};
            border-radius: {AppTheme.RADIUS_LG};
            margin-top: 8px;
            padding-top: 8px;
            font-weight: bold;
            color: {AppTheme.TEXT_SECONDARY};
            font-size: {AppTheme.FONT_SM};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }}
        QStatusBar {{
            background-color: {AppTheme.BG_TERTIARY};
            color: {AppTheme.TEXT_SECONDARY};
            border-top: 1px solid {AppTheme.BORDER};
            font-size: {AppTheme.FONT_XS};
            padding: 2px 8px;
        }}
        QScrollBar:vertical {{
            width: 6px;
            background: transparent;
        }}
        QScrollBar::handle:vertical {{
            background: {AppTheme.BORDER};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """