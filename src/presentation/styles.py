# ─────────────────────────────────────────────
# Design tokens
# ─────────────────────────────────────────────

class AppTheme:
    # Brand
    PRIMARY         = "#0078D4"
    PRIMARY_HOVER   = "#106EBE"
    PRIMARY_LIGHT   = "#EFF6FF"

    SUCCESS         = "#10893E"
    SUCCESS_HOVER   = "#0E7B38"
    SUCCESS_LIGHT   = "#D1FAE5"
    SUCCESS_TEXT    = "#065F46"

    WARNING         = "#F59E0B"
    WARNING_HOVER   = "#D97706"
    WARNING_LIGHT   = "#FEF3C7"
    WARNING_TEXT    = "#92400E"

    DANGER          = "#D13438"
    DANGER_HOVER    = "#B02A2E"

    NEUTRAL         = "#6C757D"
    NEUTRAL_HOVER   = "#5A6268"

    # Surfaces
    BG_APP          = "#F1F3F5"
    BG_PANEL        = "#FFFFFF"
    BG_SUBTLE       = "#F8F9FA"
    BORDER          = "#DEE2E6"
    BORDER_FOCUS    = "#0078D4"

    # Text
    TEXT_PRIMARY    = "#1A1D21"
    TEXT_SECONDARY  = "#6C757D"
    TEXT_MUTED      = "#ADB5BD"

    # Shape
    RADIUS_SM       = "4px"
    RADIUS_MD       = "6px"
    RADIUS_LG       = "10px"

    # Typography
    FONT_XS         = "10px"
    FONT_SM         = "11px"
    FONT_BASE       = "13px"
    FONT_LG         = "15px"
    FONT_TITLE      = "20px"

def app_stylesheet() -> str:
    t = AppTheme
    return f"""
        QMainWindow, QWidget {{
            background-color: {t.BG_APP};
            color: {t.TEXT_PRIMARY};
            font-family: "Segoe UI", system-ui, sans-serif;
            font-size: {t.FONT_BASE};
        }}
        QGroupBox {{
            border: 1px solid {t.BORDER};
            border-radius: {t.RADIUS_LG};
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
            color: {t.TEXT_SECONDARY};
            font-size: {t.FONT_SM};
            background-color: {t.BG_PANEL};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            background-color: {t.BG_PANEL};
        }}
        QStatusBar {{
            background-color: {t.BG_SUBTLE};
            color: {t.TEXT_SECONDARY};
            border-top: 1px solid {t.BORDER};
            font-size: {t.FONT_SM};
            padding: 2px 12px;
        }}
        QMenuBar {{
            background-color: {t.BG_PANEL};
            color: {t.TEXT_PRIMARY};
            border-bottom: 1px solid {t.BORDER};
            padding: 2px 4px;
            font-size: {t.FONT_BASE};
        }}
        QMenuBar::item:selected {{
            background-color: {t.BG_APP};
            border-radius: {t.RADIUS_SM};
        }}
        QMenu {{
            background-color: {t.BG_PANEL};
            border: 1px solid {t.BORDER};
            border-radius: {t.RADIUS_MD};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px 6px 12px;
            border-radius: {t.RADIUS_SM};
        }}
        QMenu::item:selected {{
            background-color: {t.PRIMARY_LIGHT};
            color: {t.PRIMARY};
        }}
        QScrollBar:vertical {{
            width: 6px;
            background: transparent;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t.BORDER};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            height: 6px;
            background: transparent;
        }}
        QScrollBar::handle:horizontal {{
            background: {t.BORDER};
            border-radius: 3px;
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{ width: 0; }}
        QToolTip {{
            background-color: {t.TEXT_PRIMARY};
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: {t.RADIUS_SM};
            font-size: {t.FONT_SM};
        }}
    """


# ─────────────────────────────────────────────
# Top bar / header panel
# ─────────────────────────────────────────────

def topbar_panel() -> str:
    t = AppTheme
    return f"""
        QWidget {{
            background-color: {t.BG_PANEL};
            border-bottom: 1px solid {t.BORDER};
        }}
    """


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

def sidebar_panel() -> str:
    t = AppTheme
    return f"""
        QWidget {{
            background-color: {t.BG_PANEL};
            border-right: 1px solid {t.BORDER};
        }}
    """

def sidebar_section_label() -> str:
    t = AppTheme
    return (
        f"font-size: {t.FONT_XS}; font-weight: bold; color: {t.TEXT_MUTED}; "
        f"letter-spacing: 0.08em; text-transform: uppercase; "
        f"padding: 8px 8px 4px 8px;"
    )

def sidebar_btn() -> str:
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {t.TEXT_SECONDARY};
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 7px 10px;
            font-size: {t.FONT_BASE};
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {t.BG_APP};
            color: {t.TEXT_PRIMARY};
        }}
    """

def sidebar_btn_active() -> str:
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: {t.PRIMARY_LIGHT};
            color: {t.PRIMARY};
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 7px 10px;
            font-size: {t.FONT_BASE};
            font-weight: bold;
            text-align: left;
        }}
    """

def sidebar_btn_warning() -> str:
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {t.WARNING_TEXT};
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 7px 10px;
            font-size: {t.FONT_BASE};
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {t.WARNING_LIGHT};
        }}
        QPushButton:disabled {{
            color: {t.TEXT_MUTED};
            background-color: transparent;
        }}
    """


# ─────────────────────────────────────────────
# Buttons
# ─────────────────────────────────────────────

def btn_primary() -> str:
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: {t.PRIMARY};
            color: white;
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 8px 18px;
            font-size: {t.FONT_BASE};
            font-weight: bold;
        }}
        QPushButton:hover:enabled {{ background-color: {t.PRIMARY_HOVER}; }}
        QPushButton:disabled {{ background-color: {t.BORDER}; color: {t.TEXT_MUTED}; }}
    """

def btn_primary_sm() -> str:
    """Compact primary button for top-bar navigation."""
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: {t.PRIMARY};
            color: white;
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 5px 14px;
            font-size: {t.FONT_BASE};
            font-weight: bold;
        }}
        QPushButton:hover:enabled {{ background-color: {t.PRIMARY_HOVER}; }}
        QPushButton:disabled {{ background-color: {t.BORDER}; color: {t.TEXT_MUTED}; }}
    """

def btn_ghost() -> str:
    """Outlined/ghost button — secondary actions."""
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {t.TEXT_SECONDARY};
            border: 1px solid {t.BORDER};
            border-radius: {t.RADIUS_MD};
            padding: 5px 14px;
            font-size: {t.FONT_BASE};
        }}
        QPushButton:hover:enabled {{
            background-color: {t.BG_APP};
            color: {t.TEXT_PRIMARY};
            border-color: {t.NEUTRAL};
        }}
        QPushButton:disabled {{ color: {t.TEXT_MUTED}; border-color: {t.BORDER}; }}
    """

def btn_success() -> str:
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: {t.SUCCESS};
            color: white;
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 8px 18px;
            font-size: {t.FONT_BASE};
            font-weight: bold;
        }}
        QPushButton:hover:enabled {{ background-color: {t.SUCCESS_HOVER}; }}
        QPushButton:disabled {{ background-color: {t.BORDER}; color: {t.TEXT_MUTED}; }}
    """

def btn_warning() -> str:
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: {t.WARNING};
            color: white;
            border: none;
            border-radius: {t.RADIUS_MD};
            padding: 8px 18px;
            font-size: {t.FONT_BASE};
        }}
        QPushButton:hover:enabled {{ background-color: {t.WARNING_HOVER}; }}
        QPushButton:disabled {{ background-color: #FDE68A; color: {t.TEXT_MUTED}; }}
    """

def btn_danger_link() -> str:
    """Understated delete/danger action — link style, turns red on hover."""
    t = AppTheme
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {t.TEXT_MUTED};
            border: none;
            padding: 4px 0px;
            font-size: {t.FONT_SM};
            text-decoration: underline;
            text-align: left;
        }}
        QPushButton:hover:enabled {{ color: {t.DANGER}; }}
        QPushButton:disabled {{ color: {t.BORDER}; }}
    """


# ─────────────────────────────────────────────
# Lists
# ─────────────────────────────────────────────

def fragment_list() -> str:
    t = AppTheme
    return f"""
        QListWidget {{
            border: none;
            background-color: transparent;
            font-size: {t.FONT_BASE};
            outline: none;
        }}
        QListWidget::item {{
            padding: 9px 12px;
            border-radius: {t.RADIUS_MD};
            color: {t.TEXT_PRIMARY};
            margin: 1px 0;
        }}
        QListWidget::item:selected {{
            background-color: {t.PRIMARY_LIGHT};
            color: {t.PRIMARY};
        }}
        QListWidget::item:hover:!selected {{
            background-color: {t.BG_APP};
        }}
    """

def label_list() -> str:
    t = AppTheme
    return f"""
        QListWidget {{
            border: 1px solid {t.BORDER};
            border-radius: {t.RADIUS_MD};
            background-color: {t.BG_PANEL};
            font-size: {t.FONT_BASE};
            outline: none;
        }}
        QListWidget::item {{
            padding: 10px 14px;
            border-bottom: 1px solid {t.BG_APP};
            color: {t.TEXT_PRIMARY};
        }}
        QListWidget::item:last {{
            border-bottom: none;
        }}
        QListWidget::item:selected {{
            background-color: {t.PRIMARY};
            color: white;
        }}
        QListWidget::item:hover:enabled:!selected {{
            background-color: {t.PRIMARY_LIGHT};
            color: {t.PRIMARY};
        }}
        QListWidget:disabled {{
            background-color: {t.BG_SUBTLE};
            color: {t.TEXT_MUTED};
        }}
    """


# ─────────────────────────────────────────────
# Info / status chips (used on QLabel)
# ─────────────────────────────────────────────

def chip_labeled() -> str:
    t = AppTheme
    return (
        f"padding: 2px 10px; background-color: {t.SUCCESS_LIGHT}; "
        f"border-radius: 10px; font-size: {t.FONT_SM}; font-weight: bold; "
        f"color: {t.SUCCESS_TEXT};"
    )

def chip_unlabeled() -> str:
    t = AppTheme
    return (
        f"padding: 2px 10px; background-color: {t.BG_APP}; "
        f"border: 1px solid {t.BORDER}; border-radius: 10px; "
        f"font-size: {t.FONT_SM}; color: {t.TEXT_MUTED};"
    )

def chip_warning() -> str:
    t = AppTheme
    return (
        f"padding: 2px 10px; background-color: {t.WARNING_LIGHT}; "
        f"border-radius: 10px; font-size: {t.FONT_SM}; font-weight: bold; "
        f"color: {t.WARNING_TEXT};"
    )

def chip_info() -> str:
    t = AppTheme
    return (
        f"padding: 2px 10px; background-color: {t.PRIMARY_LIGHT}; "
        f"border-radius: 10px; font-size: {t.FONT_SM}; font-weight: bold; "
        f"color: {t.PRIMARY};"
    )


# ─────────────────────────────────────────────
# Text helpers (used on QLabel)
# ─────────────────────────────────────────────

def text_title() -> str:
    t = AppTheme
    return f"font-size: {t.FONT_TITLE}; font-weight: bold; color: {t.TEXT_PRIMARY};"

def text_section_header() -> str:
    t = AppTheme
    return (
        f"font-size: {t.FONT_XS}; font-weight: bold; color: {t.TEXT_MUTED}; "
        f"letter-spacing: 0.08em; text-transform: uppercase;"
    )

def text_body() -> str:
    t = AppTheme
    return f"font-size: {t.FONT_BASE}; color: {t.TEXT_PRIMARY};"

def text_secondary() -> str:
    t = AppTheme
    return f"font-size: {t.FONT_SM}; color: {t.TEXT_SECONDARY};"

def text_muted() -> str:
    t = AppTheme
    return f"font-size: {t.FONT_SM}; color: {t.TEXT_MUTED};"

def text_breadcrumb() -> str:
    t = AppTheme
    return f"font-size: {t.FONT_BASE}; color: {t.TEXT_MUTED};"

def text_success_bold() -> str:
    t = AppTheme
    return f"font-size: {t.FONT_BASE}; font-weight: bold; color: {t.SUCCESS};"

def divider() -> str:
    """Thin horizontal rule as a QFrame or QWidget background."""
    return f"background-color: {AppTheme.BORDER}; max-height: 1px;"