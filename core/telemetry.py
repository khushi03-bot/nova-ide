import json
import urllib.request
from PyQt6.QtCore import QThread, QObject, pyqtSignal

SUPABASE_URL = "https://osxyitmpqmlxwantkopc.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9zeHlpdG1wcW1seHdhbnRrb3BjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ5OTM4ODcsImV4cCI6MjEwMDU2OTg4N30.KwlnrWynewqlfblI6y4VCFEDXqZZBkhbP6veQ5xOxeo"

class TelemetryWorker(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, endpoint: str, data: dict):
        super().__init__()
        self.endpoint = endpoint
        self.data = data

    def run(self):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{self.endpoint}"
            body = json.dumps(self.data).encode("utf-8")
            req = urllib.request.Request(
                url, data=body, method="POST",
                headers={
                    "Content-Type": "application/json",
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                    "Prefer": "return=minimal"
                })
            with urllib.request.urlopen(req, timeout=10):
                self.finished.emit(True)
        except Exception:
            self.finished.emit(False)

def _push_background(endpoint, data):
    """Fire and forget push to Supabase."""
    thread = QThread()
    worker = TelemetryWorker(endpoint, data)
    worker.moveToThread(thread)
    
    # Store references so they don't get garbage collected instantly
    if not hasattr(_push_background, "_threads"):
        _push_background._threads = []
    _push_background._threads.append((thread, worker))
    
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    
    # Cleanup memory when thread finishes
    def cleanup():
        try:
            _push_background._threads.remove((thread, worker))
        except ValueError:
            pass
    thread.finished.connect(cleanup)
    
    thread.start()

def push_crash(name: str, email: str, app_version: str, os_info: str, traceback_text: str):
    data = {
        "user_name": name,
        "user_email": email,
        "app_version": app_version,
        "os_info": os_info,
        "traceback": traceback_text
    }
    _push_background("crash_logs", data)

def push_crash_sync(name: str, email: str, app_version: str, os_info: str, traceback_text: str):
    data = {
        "user_name": name,
        "user_email": email,
        "app_version": app_version,
        "os_info": os_info,
        "traceback": traceback_text
    }
    # Send synchronously because the app is about to exit
    try:
        url = f"{SUPABASE_URL}/rest/v1/crash_logs"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={
                "Content-Type": "application/json",
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Prefer": "return=minimal"
            })
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass

def push_bug_report(name: str, email: str, issue_type: str, desc: str, sys_info: str):
    data = {
        "user_name": name,
        "user_email": email,
        "issue_type": issue_type,
        "description": desc,
        "sys_info": sys_info
    }
    _push_background("bug_reports", data)
