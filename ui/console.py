import sys
import os
import pathlib
import json
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit,
    QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QProcess, QTimer
from PyQt6.QtGui import QFont, QTextCursor
from utils.theme import THEME
from utils.helpers import bundled_python

class PythonConsole(QWidget):
    def __init__(self, font_size=13, cfg=None, parent=None):
        super().__init__(parent)
        self.proc = None
        self.cfg = cfg or {}
        self._buffer = ""
        self._last_traceback = ""
        self._ai_thread = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        bar = QHBoxLayout()
        lbl = QLabel("▸ PYTHON CONSOLE  (interactive REPL)")
        lbl.setStyleSheet(f"color:{THEME['accent3']};font-weight:bold;")
        bar.addWidget(lbl)
        bar.addStretch()
        restart = QPushButton("⟳ Restart")
        restart.clicked.connect(self.restart)
        bar.addWidget(restart)
        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear_all)
        bar.addWidget(clear)
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_session)
        bar.addWidget(save_btn)
        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self.open_session)
        bar.addWidget(open_btn)
        layout.addLayout(bar)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        f = QFont("Consolas", font_size)
        self.view.setFont(f)
        layout.addWidget(self.view)

        row = QHBoxLayout()
        prompt = QLabel(">>>")
        prompt.setStyleSheet(f"color:{THEME['accent1']};font-weight:bold;")
        row.addWidget(prompt)
        self.input = QLineEdit()
        self.input.setFont(f)
        self.input.setPlaceholderText("Type Python here and press Enter…")
        self.input.returnPressed.connect(self.send_line)
        row.addWidget(self.input)
        layout.addLayout(row)

        self._hist = []
        self._hist_pos = 0
        self._full_history = []
        self._replay_queue = []
        self._replay_timer = None
        self.input.installEventFilter(self)

    def start(self):
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            return
        py = bundled_python()
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._on_finished)
        self.proc.start(py, ["-i", "-u", "-q"])
        self.view.appendPlainText(f"▸ Console started: {py}\n")

    def restart(self):
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            self.proc.kill()
            self.proc.waitForFinished(1500)
        self.proc = None
        self.view.appendPlainText("\n▸ Restarting console...\n")
        self.start()

    def stop(self):
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            self.proc.kill()
            self.proc.waitForFinished(1000)
        self.proc = None

    def _on_finished(self, code, status):
        self.view.appendPlainText(f"\n▸ Console exited (code {code}). Click ⟳ Restart.")

    def _clear_all(self):
        self.view.clear()
        self._buffer = ""
        self._last_traceback = ""

    PPS_FORMAT_TAG = "NOVA_PPS"

    def save_session(self):
        if not self._full_history:
            QMessageBox.information(self, "Nothing to save", "You haven't typed anything yet.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Console Session", "session.pycs", "NOVA Console Session (*.pycs)")
        if not path:
            return
        if not path.lower().endswith(".pycs"):
            path += ".pycs"
        data = {
            "format": self.PPS_FORMAT_TAG,
            "version": 1,
            "saved_at": datetime.datetime.now().isoformat(),
            "lines": self._full_history,
        }
        try:
            pathlib.Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.view.appendPlainText(f"\n▸ Session saved: {os.path.basename(path)}\n")
        except Exception as e:
            QMessageBox.warning(self, "Save failed", str(e))

    def open_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Console Session", "", "NOVA Console Session (*.pycs);;All Files (*)")
        if not path:
            return
        try:
            raw = pathlib.Path(path).read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception as e:
            QMessageBox.warning(self, "Open failed", f"Couldn't read file:\n{e}")
            return
        if data.get("format") != self.PPS_FORMAT_TAG or "lines" not in data:
            QMessageBox.warning(self, "Invalid file", "This isn't a NOVA .pycs session file.")
            return
        lines = data.get("lines", [])
        if not lines:
            return

        self._clear_all()
        self.restart()
        self.view.appendPlainText(f"▸ Reopening session ({len(lines)} lines) — replaying live so you can continue...\n")
        self._replay_queue = list(lines)
        self._full_history = []
        QTimer.singleShot(500, self._start_replay)

    def _start_replay(self):
        if self._replay_timer:
            self._replay_timer.stop()
        self._replay_timer = QTimer(self)
        self._replay_timer.timeout.connect(self._replay_tick)
        self._replay_timer.start(35)

    def _replay_tick(self):
        if not self._replay_queue:
            self._replay_timer.stop()
            self.view.appendPlainText("\n▸ Session restored — continue typing below.\n")
            return
        line = self._replay_queue.pop(0)
        self.view.moveCursor(QTextCursor.MoveOperation.End)
        self.view.insertPlainText(f">>> {line}\n")
        self.view.moveCursor(QTextCursor.MoveOperation.End)
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            self.proc.write((line + "\n").encode("utf-8"))
        self._full_history.append(line)
        if line.strip():
            self._hist.append(line)
            self._hist_pos = len(self._hist)

    def _read(self):
        if not self.proc:
            return
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        import re
        data = re.sub(r'(^|\n)(?:>>> ?|\.\.\. ?)+', r'\1', data)
        self.view.moveCursor(QTextCursor.MoveOperation.End)
        self.view.insertPlainText(data)
        self.view.moveCursor(QTextCursor.MoveOperation.End)
        self._buffer = (self._buffer + data)[-8000:]
        if "Traceback (most recent call last)" in data or "Error" in data:
            idx = self._buffer.rfind("Traceback (most recent call last)")
            if idx == -1:
                idx = max(0, len(self._buffer) - 1500)
            self._last_traceback = self._buffer[idx:].strip()

    def send_line(self):
        line = self.input.text()
        if self.proc is None or self.proc.state() == QProcess.ProcessState.NotRunning:
            self.start()
        self.view.moveCursor(QTextCursor.MoveOperation.End)
        self.view.insertPlainText(f">>> {line}\n")
        self.view.moveCursor(QTextCursor.MoveOperation.End)
        if self.proc:
            self.proc.write((line + "\n").encode("utf-8"))
        if line.strip():
            self._hist.append(line)
            self._hist_pos = len(self._hist)
        self._full_history.append(line)
        self.input.clear()

    def run_source(self, source: str):
        if self.proc is None or self.proc.state() == QProcess.ProcessState.NotRunning:
            self.start()
        if self.proc:
            payload = "exec(compile(%r, '<editor>', 'exec'))\n" % source
            self.proc.write(payload.encode("utf-8"))
            self.view.moveCursor(QTextCursor.MoveOperation.End)
            self.view.insertPlainText("▸ [ran current file in console]\n")

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                if self._hist:
                    self._hist_pos = max(0, self._hist_pos - 1)
                    self.input.setText(self._hist[self._hist_pos])
                return True
            if event.key() == Qt.Key.Key_Down:
                if self._hist:
                    self._hist_pos = min(len(self._hist), self._hist_pos + 1)
                    self.input.setText(self._hist[self._hist_pos] if self._hist_pos < len(self._hist) else "")
                return True
        return super().eventFilter(obj, event)

