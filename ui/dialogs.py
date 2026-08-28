import datetime
import urllib.parse
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QCheckBox, QTextEdit, QComboBox, QFormLayout, QDialogButtonBox,
    QApplication, QWidget, QStackedWidget, QListWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QTextCursor, QTextDocument
from utils.theme import THEME, QSS
from utils.helpers import icon_path
from core.config import APP_VERSION

class FindReplaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find & Replace")
        self.setMinimumWidth(420)
        self.setStyleSheet(QSS)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.editor = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.returnPressed.connect(self.find_next)
        find_row.addWidget(self.find_input)
        lay.addLayout(find_row)

        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        replace_row.addWidget(self.replace_input)
        lay.addLayout(replace_row)

        opts_row = QHBoxLayout()
        self.case_check = QCheckBox("Match case")
        opts_row.addWidget(self.case_check)
        opts_row.addStretch()
        lay.addLayout(opts_row)

        self.status_label = QLabel(" ")
        self.status_label.setStyleSheet(f"color:{THEME['comment']};font-size:11px;")
        lay.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self.find_next)
        btn_row.addWidget(find_btn)
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace_one)
        btn_row.addWidget(replace_btn)
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        btn_row.addWidget(replace_all_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)

    def set_editor(self, editor):
        self.editor = editor
        self.find_input.setFocus()
        self.find_input.selectAll()

    def _flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_check.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self):
        if not self.editor:
            return
        text = self.find_input.text()
        if not text:
            return
        found = self.editor.find(text, self._flags())
        if not found:
            cur = self.editor.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cur)
            found = self.editor.find(text, self._flags())
        self.status_label.setText("" if found else "Not found.")

    def replace_one(self):
        if not self.editor:
            return
        cur = self.editor.textCursor()
        if cur.hasSelection() and cur.selectedText() == self.find_input.text():
            cur.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self):
        if not self.editor:
            return
        text = self.find_input.text()
        if not text:
            return
        cur = self.editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cur)
        count = 0
        while self.editor.find(text, self._flags()):
            c = self.editor.textCursor()
            c.insertText(self.replace_input.text())
            count += 1
        self.status_label.setText(f"Replaced {count} occurrence(s).")


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Nova IDE")
        self.setMinimumWidth(440)
        self.setStyleSheet(QSS)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 22)
        lay.setSpacing(6)

        ic = icon_path()
        if ic:
            logo = QLabel()
            logo.setPixmap(QIcon(ic).pixmap(72, 72))
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(logo)

        title = QLabel("NOVA IDE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color:{THEME['accent1']};font-size:22px;font-weight:bold;")
        lay.addWidget(title)

        ver = QLabel(f"Version {APP_VERSION}  ·  Standalone Python IDE")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color:{THEME['comment']};font-size:12px;")
        lay.addWidget(ver)

        lay.addSpacing(14)

        made = QLabel("DESIGNED & DEVELOPED BY")
        made.setAlignment(Qt.AlignmentFlag.AlignCenter)
        made.setStyleSheet(f"color:{THEME['comment']};font-size:11px;letter-spacing:2px;")
        lay.addWidget(made)

        name = QLabel("Khushi Mittal")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(f"color:{THEME['accent2']};font-size:20px;font-weight:bold;")
        lay.addWidget(name)
        
        

        lay.addSpacing(14)

        contacts = [
            ("Website", "nova-ide.web.app", "https://nova-ide.web.app/"),
            ("GitHub", "github.com/khushi03-bot", "https://github.com/khushi03-bot"),
            
            
        ]
        for label, shown, url in contacts:
            r = QHBoxLayout()
            r.setSpacing(6)
            open_btn = QPushButton(label)
            open_btn.setFixedWidth(96)
            open_btn.setStyleSheet(
                f"background:{THEME['accent1']};color:#0d1117;"
                "border:none;padding:8px 10px;border-radius:6px;font-weight:700;")
            open_btn.clicked.connect(lambda _, u=url: self._open(u))
            r.addWidget(open_btn)

            field = QLineEdit(shown)
            field.setReadOnly(True)
            field.setCursorPosition(0)
            field.setStyleSheet(
                f"background:{THEME['bg_alt']};color:{THEME['fg']};"
                "border:1px solid #30363d;padding:7px;border-radius:6px;")
            r.addWidget(field)

            copy_btn = QPushButton("Copy")
            copy_btn.setFixedWidth(64)
            copy_btn.setStyleSheet(
                f"background:{THEME['bg_alt']};color:{THEME['fg']};"
                "border:1px solid #30363d;padding:8px 10px;border-radius:6px;font-weight:600;")
            copy_btn.clicked.connect(lambda _, t=shown, b=copy_btn: self._copy(t, b))
            r.addWidget(copy_btn)
            lay.addLayout(r)

        lay.addSpacing(10)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        lay.addWidget(close)

    def _copy(self, text, btn):
        QApplication.clipboard().setText(text)
        old = btn.text()
        btn.setText("Copied!")
        QTimer.singleShot(1200, lambda: btn.setText(old))

    def _open(self, url):
        import webbrowser
        webbrowser.open(url)


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova IDE — Settings")
        self.setMinimumWidth(500)
        self.cfg = cfg
        self.setStyleSheet(QSS)
        
        main_layout = QHBoxLayout(self)
        
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        self.sidebar.addItems(["General", "Editor"])
        self.sidebar.currentRowChanged.connect(self.switch_tab)
        
        self.pages = QStackedWidget()
        
        # General Page
        page_gen = QWidget()
        lay_gen = QFormLayout(page_gen)
        
        self.autosave_check = QCheckBox("Auto-save file before every Run")
        self.autosave_check.setChecked(cfg.get("autosave", True))
        lay_gen.addRow(self.autosave_check)
        
        self.theme_combo = QComboBox()
        from utils.theme import THEMES
        for theme_name in THEMES:
            self.theme_combo.addItem(theme_name)
        current_theme = cfg.get("theme", "VS Code Dark")
        self.theme_combo.setCurrentText(current_theme)
        lay_gen.addRow("UI Theme:", self.theme_combo)
        
        self.pages.addWidget(page_gen)
        
        # Editor Page
        page_ed = QWidget()
        lay_ed = QFormLayout(page_ed)
        self.font_size_input = QLineEdit(str(cfg.get("font_size", 13)))
        lay_ed.addRow("Editor Font Size:", self.font_size_input)
        self.pages.addWidget(page_ed)
        
        main_layout.addWidget(self.sidebar)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.pages)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        right_layout.addWidget(btns)
        
        main_layout.addLayout(right_layout)
        self.sidebar.setCurrentRow(0)

    def switch_tab(self, index):
        self.pages.setCurrentIndex(index)

    def values(self):
        try:
            fsize = int(self.font_size_input.text())
        except ValueError:
            fsize = 13
        return {
            "autosave": self.autosave_check.isChecked(),
            "font_size": fsize,
            "theme": self.theme_combo.currentText(),
        }



class BugReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Issue or Suggest Feature")
        self.setMinimumWidth(500)
        self.setStyleSheet(QSS)
        
        lay = QVBoxLayout(self)
        
        title = QLabel("Report Issue / Feature Suggestion")
        title.setStyleSheet(f"color:{THEME['accent1']};font-size:18px;font-weight:bold;")
        lay.addWidget(title)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Bug Report", "Feature Suggestion", "General Improvement"])
        lay.addWidget(QLabel("Type:"))
        lay.addWidget(self.type_combo)
        
        lay.addWidget(QLabel("Name (Optional):"))
        self.name_input = QLineEdit()
        lay.addWidget(self.name_input)
        
        lay.addWidget(QLabel("Email (Optional):"))
        self.email_input = QLineEdit()
        lay.addWidget(self.email_input)
        
        lay.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        lay.addWidget(self.desc_input)
        
        self.attach_sys_info = QCheckBox("Attach System Diagnostics (OS, Python Version, App Version)")
        self.attach_sys_info.setChecked(True)
        lay.addWidget(self.attach_sys_info)
        
        btns = QHBoxLayout()
        submit_btn = QPushButton("Submit to Developers")
        submit_btn.clicked.connect(self.submit)
        submit_btn.setStyleSheet(f"background:{THEME['accent1']};color:#000;font-weight:bold;")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btns.addWidget(submit_btn)
        btns.addWidget(cancel_btn)
        lay.addLayout(btns)
        
    def submit(self):
        import platform
        from utils.helpers import bundled_python
        from core.telemetry import push_bug_report
        
        issue_type = self.type_combo.currentText()
        name = self.name_input.text().strip() or "Anonymous"
        email = self.email_input.text().strip() or "Anonymous"
        desc = self.desc_input.toPlainText()
        
        sys_info = "Not provided"
        if self.attach_sys_info.isChecked():
            sys_info = f"App: {APP_VERSION} | Py: {bundled_python()} | OS: {platform.system()} {platform.release()}"
            
        push_bug_report(name, email, issue_type, desc, sys_info)
        
        QMessageBox.information(self, "Submitted", "Thank you! Your report has been submitted to the developers.")
        self.accept()

