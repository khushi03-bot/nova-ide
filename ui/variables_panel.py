from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, QVariantAnimation, QObject
from PyQt6.QtGui import QColor

from utils.theme import THEME

class AnimatedTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, parent, data):
        super().__init__(parent, data)
        self.anim = QVariantAnimation()
        self.anim.setDuration(1000) # 1 second fade
        self.anim.valueChanged.connect(self._on_color_changed)
        self._base_color = QColor(THEME['bg'])
        
    def _on_color_changed(self, color):
        # Apply color to all columns
        for i in range(self.columnCount()):
            self.setBackground(i, color)
            
    def animate_update(self):
        # Flash accent color then fade back to base
        self.anim.stop()
        self.anim.setStartValue(QColor(THEME['accent1']).darker(150))
        self.anim.setEndValue(self._base_color)
        self.anim.start()

class LiveVariablesPanel(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Name", "Type", "Value"])
        self.setAlternatingRowColors(False)
        self.setIndentation(0)
        self.setRootIsDecorated(False)
        
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME['bg']};
                color: {THEME['fg']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {THEME['bg_alt']};
                color: {THEME['fg']};
                border: none;
                border-bottom: 1px solid {THEME['border']};
                padding: 4px;
                font-weight: bold;
            }}
            QTreeWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {THEME['border']};
            }}
        """)
        
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 100)
        
        self._current_vars = {}

    def apply_theme(self):
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME['bg']};
                color: {THEME['fg']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {THEME['bg_alt']};
                color: {THEME['fg']};
                border: none;
                border-bottom: 1px solid {THEME['border']};
                padding: 4px;
                font-weight: bold;
            }}
            QTreeWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {THEME['border']};
            }}
        """)
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if isinstance(item, AnimatedTreeWidgetItem):
                item._base_color = QColor(THEME['bg'])
                for col in range(item.columnCount()):
                    item.setBackground(col, item._base_color)
                    item.setForeground(col, QColor(THEME['fg']))

    def update_variables(self, variables: dict):
        if not variables:
            self.clear()
            self._current_vars.clear()
            return

        # Track which variables still exist
        new_keys = set(variables.keys())
        
        # Remove variables that no longer exist
        for i in reversed(range(self.topLevelItemCount())):
            item = self.topLevelItem(i)
            name = item.text(0)
            if name not in new_keys:
                self.takeTopLevelItem(i)
                self._current_vars.pop(name, None)

        # Add or update variables
        for name, info in variables.items():
            t = info.get("type", "")
            v = info.get("value", "")
            
            if name not in self._current_vars:
                # New variable
                item = AnimatedTreeWidgetItem(self, [name, t, v])
                self._current_vars[name] = item
                item.animate_update()
            else:
                # Existing variable, check if value changed
                item = self._current_vars[name]
                if item.text(2) != v or item.text(1) != t:
                    item.setText(1, t)
                    item.setText(2, v)
                    item.animate_update()

