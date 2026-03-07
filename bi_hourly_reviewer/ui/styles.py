"""
Application-wide styling.

Responsibilities:
    - Define the color palette, fonts, and spacing.
    - Apply a cohesive stylesheet to the entire app.
    - Provide reusable style constants for individual widgets.

Design direction: Industrial/utilitarian — clean, high-contrast,
data-dense interface suited for factory floor review stations.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt


# =============================================================================
# COLOR PALETTE — Industrial/utilitarian
# =============================================================================
COLORS = {
    "bg_primary": "#1A1D23",       # Deep charcoal — main background
    "bg_secondary": "#22262E",     # Slightly lighter — panels, cards
    "bg_tertiary": "#2A2F38",      # Input fields, hover states
    "bg_header": "#15171C",        # Tab bar, headers

    "text_primary": "#E8EAED",     # Main text — high contrast
    "text_secondary": "#9AA0A6",   # Labels, hints
    "text_muted": "#5F6368",       # Disabled, timestamps

    "accent_blue": "#4A9EF5",      # Primary action buttons
    "accent_green": "#34A853",     # Success states
    "accent_red": "#EA4335",       # Errors, NG highlights
    "accent_orange": "#F5A623",    # Warnings, DLNG highlights
    "accent_yellow": "#FBBC04",    # C-NG highlights

    "border": "#363B44",           # Subtle borders
    "border_focus": "#4A9EF5",     # Focused input borders

    "scrollbar_bg": "#22262E",
    "scrollbar_handle": "#3C4149",
}

# Judge-specific colors for cell list badges
JUDGE_COLORS = {
    "NG": COLORS["accent_red"],
    "DLNG": COLORS["accent_orange"],
    "C-NG": COLORS["accent_yellow"],
}

# =============================================================================
# FONTS
# =============================================================================
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"
FONT_SIZE_NORMAL = 10
FONT_SIZE_SMALL = 9
FONT_SIZE_LARGE = 12
FONT_SIZE_HEADER = 14

# =============================================================================
# SPACING
# =============================================================================
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24

# =============================================================================
# STYLESHEET
# =============================================================================

def get_stylesheet() -> str:
    """Return the full application stylesheet."""
    return f"""
        /* ---- Global ---- */
        QWidget {{
            background-color: {COLORS['bg_primary']};
            color: {COLORS['text_primary']};
            font-family: "{FONT_FAMILY}";
            font-size: {FONT_SIZE_NORMAL}pt;
        }}

        /* ---- Tab Widget ---- */
        QTabWidget::pane {{
            border: none;
            background-color: {COLORS['bg_primary']};
        }}
        QTabBar {{
            background-color: {COLORS['bg_header']};
        }}
        QTabBar::tab {{
            background-color: {COLORS['bg_header']};
            color: {COLORS['text_secondary']};
            padding: 10px 24px;
            border: none;
            border-bottom: 2px solid transparent;
            font-size: {FONT_SIZE_LARGE}pt;
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            color: {COLORS['text_primary']};
            border-bottom: 2px solid {COLORS['accent_blue']};
        }}
        QTabBar::tab:hover:!selected {{
            color: {COLORS['text_primary']};
            background-color: {COLORS['bg_secondary']};
        }}

        /* ---- Buttons ---- */
        QPushButton {{
            background-color: {COLORS['accent_blue']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 20px;
            font-weight: 600;
            font-size: {FONT_SIZE_NORMAL}pt;
        }}
        QPushButton:hover {{
            background-color: #5BABE6;
        }}
        QPushButton:pressed {{
            background-color: #3A8AD4;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
        }}

        /* Secondary button style via object name */
        QPushButton#secondary {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
        }}
        QPushButton#secondary:hover {{
            background-color: {COLORS['border']};
        }}

        /* ---- Inputs ---- */
        QLineEdit {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px 10px;
            font-family: "{FONT_FAMILY_MONO}";
        }}
        QLineEdit:focus {{
            border-color: {COLORS['border_focus']};
        }}

        /* ---- Labels ---- */
        QLabel {{
            background-color: transparent;
            color: {COLORS['text_primary']};
        }}
        QLabel#sectionHeader {{
            font-size: {FONT_SIZE_HEADER}pt;
            font-weight: 700;
            color: {COLORS['text_primary']};
        }}
        QLabel#hint {{
            color: {COLORS['text_secondary']};
            font-size: {FONT_SIZE_SMALL}pt;
        }}

        /* ---- Text Browser (log area) ---- */
        QTextBrowser, QPlainTextEdit {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            font-family: "{FONT_FAMILY_MONO}";
            font-size: {FONT_SIZE_SMALL}pt;
            padding: 8px;
        }}

        /* ---- List Widget (cell list) ---- */
        QListWidget {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 8px 12px;
            border-bottom: 1px solid {COLORS['border']};
        }}
        QListWidget::item:selected {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
        }}
        QListWidget::item:hover:!selected {{
            background-color: {COLORS['bg_tertiary']};
        }}

        /* ---- Scrollbars ---- */
        QScrollBar:vertical {{
            background: {COLORS['scrollbar_bg']};
            width: 10px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {COLORS['scrollbar_handle']};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {COLORS['scrollbar_bg']};
            height: 10px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {COLORS['scrollbar_handle']};
            border-radius: 5px;
            min-width: 30px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        /* ---- Progress Bar ---- */
        QProgressBar {{
            background-color: {COLORS['bg_tertiary']};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {COLORS['text_primary']};
            height: 22px;
        }}
        QProgressBar::chunk {{
            background-color: {COLORS['accent_blue']};
            border-radius: 4px;
        }}

        /* ---- Status Bar ---- */
        QStatusBar {{
            background-color: {COLORS['bg_header']};
            color: {COLORS['text_secondary']};
            font-size: {FONT_SIZE_SMALL}pt;
            padding: 2px 8px;
        }}

        /* ---- Splitter ---- */
        QSplitter::handle {{
            background-color: {COLORS['border']};
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* ---- Group Box ---- */
        QGroupBox {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {COLORS['text_secondary']};
        }}
    """


def apply_app_style(app: QApplication):
    """Apply the global stylesheet and palette to the application."""
    app.setStyleSheet(get_stylesheet())

    # Set application-wide font
    font = QFont(FONT_FAMILY, FONT_SIZE_NORMAL)
    app.setFont(font)