"""
FILE: ui/styles/theme.py
ROLE: The "Designer" (Visual System & Branding).

DESCRIPTION:
This module defines the high-fidelity 'Cyber-Tactical' design system.
It uses HSL-tailored colors and glassmorphism tokens to create a premium, 
military command deck aesthetic.
"""
from PyQt5.QtGui import QFont

class Theme:
    # --- CORE PALETTE (Modern Flat Dark - Zinc/Blue) ---
    BG_DEEP    = "#09090b"         # Zinc 950
    BG_SURFACE = "#18181b"         # Zinc 900
    BG_INPUT   = "#27272a"         # Zinc 800

    ACCENT_ALLY    = "#3b82f6"     # Blue 500
    ACCENT_ENEMY   = "#ef4444"     # Red 500
    ACCENT_WARN    = "#f59e0b"     # Amber 500
    ACCENT_GOOD    = "#10b981"     # Emerald 500
    ACCENT_NEUTRAL = "#71717a"     # Zinc 400

    # --- TERRAIN COLORS (Tactical Palette) ---
    TERRAIN_COLORS = {
        "plains":    "#2e7d32",    # Forest Green / Grass
        "forest":    "#1b5e20",    # Dark Green
        "urban":     "#475569",    # Slate Blue / Concrete
        "water":     "#0c4a6e",    # Deep Ocean Blue
        "mountain":  "#404040",    # Charcoal Grey
        "road":      "#52525b",    # Zinc 700 / Asphalt
        "mud":       "#451a03",    # Dark Brown
        "slope":     "#3f6212",    # Lime 800
        "elevation": "#a8a29e"     # Stone 400
    }

    DARK_GLASS = "rgba(9, 9, 11, 0.8)"

    # Legacy fallbacks
    OLIVE_DRAB  = "#6b705c"
    SAND_DESERT = "#e9c46a"

    TEXT_PRIMARY = "#f4f4f5"    # Zinc 100
    TEXT_DIM     = "#a1a1aa"    # Zinc 400

    BORDER_STRONG = "#27272a"   # Zinc 800
    BORDER_SUBTLE = "#3f3f46"   # Zinc 700

    # Cross-platform font stacks
    FONT_HEADER = "Inter, Segoe UI, Arial, sans-serif"
    FONT_BODY   = "Inter, Segoe UI, Arial, sans-serif"
    FONT_MONO   = "JetBrains Mono, Consolas, Courier New, monospace"

    # --- LIGHT MODE PALETTE (Slate/Blue) ---
    LIGHT_BG_DEEP    = "#f8fafc"   # Slate 50
    LIGHT_BG_SURFACE = "#f1f5f9"   # Slate 100
    LIGHT_BG_INPUT   = "#e2e8f0"   # Slate 200
    LIGHT_TEXT       = "#0f172a"   # Slate 900
    LIGHT_TEXT_DIM   = "#64748b"   # Slate 500
    LIGHT_BORDER     = "#cbd5e1"   # Slate 300

    # -------------------------------------------------------------------------
    @staticmethod
    def get_font(family, size=10, bold=False):
        """
        Creates a QFont object with the specified family, size, and weight.
        Used throughout the UI to ensure consistent typography.
        """
        font = QFont(family, size)
        if bold:
            font.setBold(True)
        return font

    @staticmethod
    def get_main_qss():
        """
        Returns the primary 'Dark Mode' tactical stylesheet.
        
        Style Highlights:
        - Cyber-Tactical Palette: Deep zinc backgrounds with vibrant blue/red accents.
        - Strategic Dock Headers: Visual separation of tool windows using neon accent borders.
        - Input Focus: High-contrast blue rings when users interact with fields.
        - Glassmorphism: Subtle transparency on overlays and menus.
        """
        T = Theme
        return f"""
            QMainWindow {{ background-color: {T.BG_DEEP}; }}
            QWidget {{ color: {T.TEXT_PRIMARY}; font-family: "{T.FONT_BODY}"; font-size: 10pt; }}

            /* Tool Panels (Docks) */
            QDockWidget {{
                color: {T.TEXT_PRIMARY};
                background-color: {T.BG_SURFACE};
                border: 1px solid {T.BORDER_STRONG};
            }}
            QDockWidget::title {{
                background: {T.BG_INPUT};
                padding: 8px 12px;
                font-weight: 600;
                border-bottom: 2px solid {T.ACCENT_ALLY};
            }}

            /* Tab Containers */
            QTabWidget::pane {{ border: 1px solid {T.BG_INPUT}; background: {T.BG_SURFACE}; border-radius: 6px; }}
            QTabBar::tab {{
                background: {T.BG_INPUT};
                color: {T.TEXT_DIM};
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{ background: {T.ACCENT_ALLY}; color: #ffffff; }}
            QTabBar::tab:hover:!selected {{ background: {T.BORDER_SUBTLE}; color: white; }}

            /* Toolbars & ToolButtons */
            QToolBar {{ background: {T.BG_SURFACE}; border: none; border-bottom: 1px solid {T.BORDER_STRONG}; spacing: 4px; padding: 4px; }}
            QToolButton {{ background: transparent; border: none; border-radius: 4px; padding: 4px; }}
            QToolButton:hover {{ background-color: {T.BG_INPUT}; }}
            QToolButton:checked {{ background-color: {T.ACCENT_ALLY}; color: white; }}

            /* Tactical Buttons (Primary Actions) */
            QPushButton {{ background-color: {T.ACCENT_ALLY}; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 500; }}
            QPushButton:hover {{ background-color: #2563eb; }}
            QPushButton:pressed {{ background-color: #1d4ed8; }}

            /* Input Fields (Forms) */
            QLineEdit, QSpinBox, QComboBox {{ background-color: {T.BG_INPUT}; border: 1px solid {T.BORDER_SUBTLE}; color: {T.TEXT_PRIMARY}; padding: 6px; border-radius: 6px; }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {T.ACCENT_ALLY}; }}

            /* Content Groups */
            QGroupBox {{ border: 1px solid {T.BORDER_SUBTLE}; border-radius: 6px; margin-top: 20px; padding-top: 10px; font-weight: 600; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: {T.ACCENT_ALLY}; }}

            /* Custom Styled Scrollbars */
            QScrollBar:vertical {{ border: none; background: transparent; width: 10px; }}
            QScrollBar::handle:vertical {{ background: {T.BORDER_SUBTLE}; border-radius: 5px; }}

            /* Contextual Popups */
            QMenu {{ background-color: {T.BG_SURFACE}; border: 1px solid {T.BORDER_SUBTLE}; color: {T.TEXT_PRIMARY}; }}
            QMenu::item:selected {{ background-color: {T.ACCENT_ALLY}; color: white; border-radius: 4px; }}
            QMenu::separator {{ height: 1px; background: {T.BORDER_STRONG}; margin: 4px 8px; }}
        """

    @staticmethod
    def get_light_qss():
        """
        Returns the 'Light Mode' (High-Visibility) stylesheet.
        Built with a clean slate/blue palette for daytime use.
        """
        L = Theme
        return f"""
            QMainWindow {{ background-color: {L.LIGHT_BG_DEEP}; }}
            QWidget {{ color: {L.LIGHT_TEXT}; font-family: "{L.FONT_BODY}"; font-size: 10pt; background-color: {L.LIGHT_BG_DEEP}; }}

            QDockWidget {{
                color: {L.LIGHT_TEXT};
                background-color: {L.LIGHT_BG_SURFACE};
                border: 1px solid {L.LIGHT_BORDER};
            }}
            QDockWidget::title {{
                background: {L.LIGHT_BG_INPUT};
                padding: 8px 12px;
                font-weight: 600;
                border-bottom: 2px solid {L.ACCENT_ALLY};
                color: {L.LIGHT_TEXT};
            }}

            QTabWidget::pane {{ border: 1px solid {L.LIGHT_BORDER}; background: {L.LIGHT_BG_SURFACE}; border-radius: 6px; }}
            QTabBar::tab {{
                background: {L.LIGHT_BG_INPUT};
                color: {L.LIGHT_TEXT_DIM};
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{ background: {L.ACCENT_ALLY}; color: white; }}
            QTabBar::tab:hover:!selected {{ background: {L.LIGHT_BORDER}; color: {L.LIGHT_TEXT}; }}

            QToolBar {{ background: {L.LIGHT_BG_SURFACE}; border: none; border-bottom: 1px solid {L.LIGHT_BORDER}; spacing: 4px; padding: 4px; }}
            QToolButton {{ background: transparent; border: none; border-radius: 4px; padding: 4px; color: {L.LIGHT_TEXT}; }}
            QToolButton:hover {{ background-color: {L.LIGHT_BG_INPUT}; }}
            QToolButton:checked {{ background-color: {L.ACCENT_ALLY}; color: white; }}

            QPushButton {{ background-color: {L.ACCENT_ALLY}; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 500; }}
            QPushButton:hover {{ background-color: #2563eb; }}
            QPushButton:pressed {{ background-color: #1d4ed8; }}

            QLineEdit, QSpinBox, QComboBox {{ background-color: white; border: 1px solid {L.LIGHT_BORDER}; color: {L.LIGHT_TEXT}; padding: 6px; border-radius: 6px; }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {L.ACCENT_ALLY}; }}

            QGroupBox {{ border: 1px solid {L.LIGHT_BORDER}; border-radius: 6px; margin-top: 20px; padding-top: 10px; font-weight: 600; color: {L.LIGHT_TEXT}; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: {L.ACCENT_ALLY}; }}

            QScrollBar:vertical {{ border: none; background: transparent; width: 10px; }}
            QScrollBar::handle:vertical {{ background: {L.LIGHT_BORDER}; border-radius: 5px; }}

            QMenu {{ background-color: white; border: 1px solid {L.LIGHT_BORDER}; color: {L.LIGHT_TEXT}; }}
            QMenu::item:selected {{ background-color: {L.ACCENT_ALLY}; color: white; border-radius: 4px; }}
            QMenu::separator {{ height: 1px; background: {L.LIGHT_BORDER}; margin: 4px 8px; }}
        """

    @staticmethod
    def get_qss(mode: str = "dark") -> str:
        """
        Global Fetch: Gets either the light or dark tactical stylesheet 
        depending on the user's preference found in UI settings.
        """
        return Theme.get_light_qss() if mode == "light" else Theme.get_main_qss()

    @staticmethod
    def get_dialog_style():
        """Returns the fallback style for setup/startup dialogs."""
        return Theme.get_main_qss()

