THEMES = {
    "VS Code Dark": {
        "bg":        "#1e1e1e",
        "bg_alt":    "#252526",
        "bg_panel":  "#2d2d30",
        "fg":        "#cccccc",
        "accent1":   "#007acc",
        "accent2":   "#0098ff",
        "accent3":   "#4ec9b0",
        "keyword":   "#c586c0",
        "string":    "#ce9178",
        "comment":   "#6a9955",
        "number":    "#b5cea8",
        "func":      "#dcdcaa",
        "builtin":   "#4ec9b0",
        "error":     "#f44747",
        "gutter":    "#1e1e1e",
        "gutter_fg": "#858585",
        "current":   "#2a2d2e",
        "border":    "#3c3c3c",
    },
    "Light Mode": {
        "bg":        "#ffffff",
        "bg_alt":    "#f3f3f3",
        "bg_panel":  "#e8e8e8",
        "fg":        "#333333",
        "accent1":   "#005fb8",
        "accent2":   "#0078d4",
        "accent3":   "#005fb8",
        "keyword":   "#0000ff",
        "string":    "#a31515",
        "comment":   "#008000",
        "number":    "#098658",
        "func":      "#795e26",
        "builtin":   "#0000ff",
        "error":     "#e51400",
        "gutter":    "#ffffff",
        "gutter_fg": "#2b91af",
        "current":   "#f3f3f3",
        "border":    "#cccccc",
    },
    "Dracula": {
        "bg":        "#282a36",
        "bg_alt":    "#21222c",
        "bg_panel":  "#44475a",
        "fg":        "#f8f8f2",
        "accent1":   "#bd93f9",
        "accent2":   "#ff79c6",
        "accent3":   "#8be9fd",
        "keyword":   "#ff79c6",
        "string":    "#f1fa8c",
        "comment":   "#6272a4",
        "number":    "#bd93f9",
        "func":      "#50fa7b",
        "builtin":   "#8be9fd",
        "error":     "#ff5555",
        "gutter":    "#282a36",
        "gutter_fg": "#6272a4",
        "current":   "#44475a",
        "border":    "#191a21",
    }
}

THEME = THEMES["Dracula"].copy()

def get_qss():
    return f"""
/* Global */
QWidget {{
    background-color: {THEME['bg']};
    color: {THEME['fg']};
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    font-size: 13px;
}}
QMainWindow {{
    background-color: {THEME['bg']};
}}

/* Editors and Consoles */
QPlainTextEdit, QTextEdit {{
    background-color: {THEME['bg']};
    color: {THEME['fg']};
    border: none;
    selection-background-color: {THEME['accent1']};
    selection-color: #ffffff;
}}

/* Tab Widget (Main and Bottom) */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {THEME['border']};
}}
QTabBar::tab {{
    background: {THEME['bg_alt']};
    color: {THEME['gutter_fg']};
    padding: 8px 16px;
    border: none;
    border-right: 1px solid {THEME['bg']};
    border-top: 2px solid transparent;
}}
QTabBar::tab:hover {{
    background: {THEME['bg_panel']};
    color: {THEME['fg']};
}}
QTabBar::tab:selected {{
    background: {THEME['bg']};
    color: {THEME['accent1']};
    border-top: 2px solid {THEME['accent1']};
}}

/* Toolbar */
QToolBar {{
    background-color: {THEME['bg_alt']};
    border: none;
    border-bottom: 1px solid {THEME['border']};
    padding: 4px;
    spacing: 4px;
}}
QToolBar::separator {{
    background-color: {THEME['border']};
    width: 1px;
    margin: 4px 8px;
}}
QToolButton {{
    background: transparent;
    color: {THEME['fg']};
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid transparent;
}}
QToolButton:hover {{
    background: {THEME['bg_panel']};
    border: 1px solid {THEME['border']};
}}
QToolButton:pressed {{
    background: {THEME['bg']};
}}
QToolButton::menu-indicator {{
    image: none;
}}

/* Menus */
QMenu {{
    background-color: {THEME['bg_alt']};
    color: {THEME['fg']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 4px 0px;
}}
QMenu::item {{
    padding: 6px 32px 6px 20px;
    margin: 0px 4px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {THEME['accent1']};
    color: #ffffff;
}}
QMenu::separator {{
    height: 1px;
    background: {THEME['border']};
    margin: 4px 12px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {THEME['accent1']};
    color: #ffffff;
    border: none;
}}
QStatusBar::item {{
    border: none;
}}
QStatusBar QLabel {{
    color: #ffffff;
    padding: 0px 4px;
    background-color: transparent;
}}

/* Buttons */
QPushButton {{
    background-color: {THEME['accent1']};
    color: #ffffff;
    border: 1px solid {THEME['accent1']};
    padding: 6px 16px;
    border-radius: 4px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {THEME['accent2']};
    border-color: {THEME['accent2']};
}}
QPushButton:pressed {{
    background-color: {THEME['accent1']};
}}
QPushButton:disabled {{
    background-color: {THEME['bg_panel']};
    color: {THEME['gutter_fg']};
    border: 1px solid {THEME['border']};
}}

/* Inputs */
QLineEdit, QComboBox {{
    background-color: {THEME['bg_alt']};
    color: {THEME['fg']};
    border: 1px solid {THEME['border']};
    padding: 6px;
    border-radius: 4px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {THEME['accent1']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

/* Splitters */
QSplitter::handle {{
    background-color: {THEME['border']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* Custom Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {THEME['border']};
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {THEME['gutter_fg']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 12px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {THEME['border']};
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {THEME['gutter_fg']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""

QSS = get_qss()

