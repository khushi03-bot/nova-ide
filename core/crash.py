import sys
import platform
import traceback
import datetime
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QHBoxLayout, QMessageBox
)
from utils.helpers import app_dir, local_app_data_dir
from core.config import APP_VERSION
from core.telemetry import push_crash_sync
from utils.theme import QSS, THEME

class CrashReportDialog(QDialog):
    def __init__(self, traceback_text):
        super().__init__()
        self.setWindowTitle("Nova IDE - Crash Reporter")
        self.setMinimumWidth(500)
        self.setStyleSheet(QSS)
        self.traceback_text = traceback_text
        
        lay = QVBoxLayout(self)
        
        title = QLabel("Oops! Nova IDE encountered a fatal error.")
        title.setStyleSheet(f"color:{THEME['accent2']};font-size:16px;font-weight:bold;")
        lay.addWidget(title)
        
        desc = QLabel("To help us fix this, please provide your details. The crash log below will be securely sent to the developers.")
        desc.setWordWrap(True)
        lay.addWidget(desc)
        
        lay.addWidget(QLabel("Name (Optional):"))
        self.name_input = QLineEdit()
        lay.addWidget(self.name_input)
        
        lay.addWidget(QLabel("Email (Optional):"))
        self.email_input = QLineEdit()
        lay.addWidget(self.email_input)
        
        lay.addWidget(QLabel("Crash Log:"))
        tb_view = QTextEdit()
        tb_view.setReadOnly(True)
        tb_view.setPlainText(traceback_text)
        lay.addWidget(tb_view)
        
        btns = QHBoxLayout()
        submit_btn = QPushButton("Submit & Close")
        submit_btn.setStyleSheet(f"background:{THEME['accent1']};color:#000;font-weight:bold;")
        submit_btn.clicked.connect(self.submit)
        
        cancel_btn = QPushButton("Don't Send & Close")
        cancel_btn.clicked.connect(self.reject)
        
        btns.addWidget(submit_btn)
        btns.addWidget(cancel_btn)
        lay.addLayout(btns)
        
    def submit(self):
        name = self.name_input.text().strip() or "Anonymous"
        email = self.email_input.text().strip() or "Anonymous"
        os_info = f"{platform.system()} {platform.release()}"
        push_crash_sync(name, email, APP_VERSION, os_info, self.traceback_text)
        self.accept()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)
    
    log_dir = local_app_data_dir() / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"crash_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        log_file.write_text(tb_text, encoding="utf-8")
    except Exception:
        pass

    app = QApplication.instance()
    if app is not None:
        try:
            dlg = CrashReportDialog(tb_text)
            dlg.exec()
        except Exception:
            pass
        
    sys.exit(1)

def setup_crash_reporter():
    sys.excepthook = handle_exception
