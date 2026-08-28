import sys
import os
import pathlib
import datetime
import re

from PyQt6.QtCore import Qt, QProcess, QSize, QTimer, QObject, QEvent, QRectF, QDir, QPropertyAnimation
from PyQt6.QtGui import QColor, QFont, QIcon, QKeySequence, QTextCursor, QAction, QFileSystemModel
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QFileDialog, QMessageBox, QToolBar, QStatusBar, QLineEdit, QPushButton,
    QLabel, QToolButton, QMenu, QApplication, QPlainTextEdit, QTreeView, QTextBrowser,
    QListWidget, QListWidgetItem, QGraphicsOpacityEffect
)

from utils.theme import THEME, QSS, THEMES
from utils.helpers import app_dir, bundled_python, icon_path
from core.config import load_config, save_config
from core.crash import handle_exception
from utils.snippets import SNIPPETS

from ui.editor import CodeEditor
from ui.console import PythonConsole
from ui.dialogs import SettingsDialog, AboutDialog, BugReportDialog
from ui.variables_panel import LiveVariablesPanel

class HoverMenuManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._active_menu = None
        QApplication.instance().installEventFilter(self)

    def register(self, button, menu):
        self._entries.append((button, menu))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove:
            pos = event.globalPosition().toPoint()
            for button, menu in self._entries:
                if not button.isVisible():
                    continue
                local = button.mapFromGlobal(pos)
                if button.rect().contains(local):
                    if self._active_menu is not menu:
                        if self._active_menu is not None:
                            self._active_menu.hide()
                        menu.popup(button.mapToGlobal(button.rect().bottomLeft()))
                        self._active_menu = menu
                    return False
            if self._active_menu is not None and self._active_menu.isVisible():
                if not self._active_menu.geometry().contains(pos):
                    self._active_menu.hide()
                    self._active_menu = None
        elif event.type() == QEvent.Type.MouseButtonPress:
            if self._active_menu is not None and self._active_menu.isVisible():
                pos = event.globalPosition().toPoint()
                if not self._active_menu.geometry().contains(pos):
                    over_a_button = any(
                        b.isVisible() and b.rect().contains(b.mapFromGlobal(pos))
                        for b, _ in self._entries)
                    if not over_a_button:
                        self._active_menu.hide()
                        self._active_menu = None
        return False


class PycoreIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.proc = None
        self.last_error_text = ""
        self.ai_thread = None
        self.debug_proc = None
        self._debug_buffer = ""
        self._debug_phase = None
        self._debug_setup_queue = []
        self._debug_path = None
        self._find_dialog = None
        
        self._is_visual_run = False
        self._visual_run_timer = QTimer(self)
        self._visual_run_timer.timeout.connect(self._visual_run_step)

        self.setWindowTitle("Nova IDE — Standalone Python")
        self.resize(1180, 760)
        self.setStyleSheet(QSS)
        self.setAcceptDrops(True)
        _ic = icon_path()
        if _ic:
            self.setWindowIcon(QIcon(_ic))

        self._build_ui()
        self._build_toolbar()
        self.new_tab()
        self._update_status()
        self.console.start()
        
        self.setWindowOpacity(0.0)
        QTimer.singleShot(50, self._animate_startup)

    def _animate_startup(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(600)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(self.splitter)

        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.h_splitter)

        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath("")
        self.fs_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.fs_model)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.doubleClicked.connect(self._tree_double_clicked)
        self.file_tree.hide()
        self.h_splitter.addWidget(self.file_tree)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.h_splitter.addWidget(self.tabs)

        self.cheatsheet = QTextBrowser()
        self.cheatsheet.setHtml(self._get_cheatsheet_html())
        self.cheatsheet.hide()
        self.h_splitter.addWidget(self.cheatsheet)
        self.h_splitter.setSizes([200, 780, 200])

        bottom = QWidget()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(6, 4, 6, 6)

        self.bottom_tabs = QTabWidget()
        bl.addWidget(self.bottom_tabs)

        out_tab = QWidget()
        ol = QVBoxLayout(out_tab)
        ol.setContentsMargins(2, 2, 2, 2)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        of = QFont("Consolas", self.cfg.get("font_size", 13))
        self.output.setFont(of)
        ol.addWidget(self.output)
        self.bottom_tabs.addTab(out_tab, "Output")

        self.console = PythonConsole(self.cfg.get("font_size", 13), cfg=self.cfg)
        self.bottom_tabs.addTab(self.console, "Python Console")

        var_tab = QWidget()
        vl = QVBoxLayout(var_tab)
        vl.setContentsMargins(2, 2, 2, 2)
        vhint = QLabel("Live Variables Viewer. Shows name, type and value with animations.")
        vhint.setStyleSheet(f"color:{THEME['comment']};font-size:11px;")
        vl.addWidget(vhint)
        self.var_table = LiveVariablesPanel()
        vl.addWidget(self.var_table)
        self.bottom_tabs.addTab(var_tab, "Variables")

        row = QHBoxLayout()
        self.input_label = QLabel("💤 idle")
        self.input_label.setStyleSheet(f"color:{THEME['comment']};font-size:12px;padding:0 6px;")
        self.input_label.setMinimumWidth(160)
        row.addWidget(self.input_label)
        
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Program input goes here when running  •  or type:  pip install <package>")
        self.cmd_input.returnPressed.connect(self.handle_cmd_input)
        row.addWidget(self.cmd_input)
        
        pip_btn = QPushButton("Run pip")
        pip_btn.clicked.connect(self.run_pip_from_input)
        row.addWidget(pip_btn)
        bl.addLayout(row)

        self.splitter.addWidget(bottom)
        self.splitter.setSizes([520, 240])

        self.setStatusBar(QStatusBar())

    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)

        self._hover_menu_manager = HoverMenuManager(self)

        def dropdown(text):
            btn = QToolButton()
            btn.setText(text)
            btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu = QMenu(btn)
            btn.setMenu(menu)
            tb.addWidget(btn)
            self._hover_menu_manager.register(btn, menu)
            return menu

        def item(menu, text, slot, shortcut=None):
            a = menu.addAction(text)
            a.triggered.connect(slot)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
                a.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
                self.addAction(a)
            return a

        file_menu = dropdown("📁 File")
        item(file_menu, "New", self.new_tab_action, "Ctrl+N")
        item(file_menu, "Open File", self.open_file, "Ctrl+O")
        item(file_menu, "Open Folder", self.open_folder)
        item(file_menu, "Save", self.save_file, "Ctrl+S")
        file_menu.addSeparator()
        item(file_menu, "🔍 Find", self.open_find_replace, "Ctrl+F")

        ex_menu = dropdown("📚 Examples")
        for name in SNIPPETS:
            action = ex_menu.addAction(name)
            action.triggered.connect(lambda checked, n=name: self.load_snippet(n))

        run_menu = dropdown("▶ Run")
        item(run_menu, "▶ Run", self.run_code, "F5")
        item(run_menu, "▶ Run in Console", self.run_in_console, "Ctrl+F5")
        item(run_menu, "🐢 Visual Run (Slow Motion)", self.start_visual_run)
        run_menu.addSeparator()
        item(run_menu, "■ Stop", self.stop_code)
        run_menu.addSeparator()
        item(run_menu, "✨ Auto-Format", self.format_code, "Shift+Alt+F")

        debug_menu = dropdown("🐞 Debug")
        item(debug_menu, "🐞 Start Debug", self.start_debug)
        debug_menu.addSeparator()
        self.debug_continue_act = item(debug_menu, "▶ Continue", self.debug_continue)
        self.debug_step_over_act = item(debug_menu, "⤵ Step Over", self.debug_step_over, "F10")
        self.debug_step_into_act = item(debug_menu, "⤷ Step Into", self.debug_step_into, "F11")
        debug_menu.addSeparator()
        self.debug_stop_act = item(debug_menu, "⏹ Stop Debug", self.debug_stop)
        for a in (self.debug_continue_act, self.debug_step_over_act, self.debug_step_into_act, self.debug_stop_act):
            a.setEnabled(False)

        pip_menu = dropdown("📦 pip")
        pip_menu.addAction("pip list").triggered.connect(self.pip_list)
        pip_menu.addAction("pip freeze").triggered.connect(self.pip_freeze)

        help_menu = dropdown("❓ Help")
        item(help_menu, "📖 Cheatsheet", self.toggle_cheatsheet)
        help_menu.addSeparator()
        item(help_menu, "Report Bug / Feature", self.open_bug_report)
        item(help_menu, "Contact Developer", lambda: self._open_url("mailto:pycore.dev@gmail.com"))
        
        more_menu = dropdown("⚙ More")
        item(more_menu, "⚙ Settings", self.open_settings)
        item(more_menu, "ℹ About", self.open_about)

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def change_theme(self, name):
        from utils.theme import THEMES, THEME, get_qss
        THEME.update(THEMES[name])
        qss = get_qss()
        self.setStyleSheet(qss)
        self.cheatsheet.setHtml(self._get_cheatsheet_html())
        
        # Update existing tabs
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, CodeEditor):
                widget.apply_theme()
                
        # Update Live Variables Panel
        self.var_table.apply_theme()
        
        self.input_label.setStyleSheet(f"color:{THEME['comment']};font-size:12px;padding:0 6px;")
        if hasattr(self, "_run_path") and self._run_path:
            self._set_input_active(self.proc and self.proc.state() != QProcess.ProcessState.NotRunning)
            
        self._flash_status(f"Theme changed to {name}")

    def format_code(self):
        ed = self.current_editor()
        if not ed: return
        path = ed.property("filepath")
        if not path:
            self._flash_status("Save the file first before formatting.")
            return
        
        self._flash_status("Formatting code...")
        pathlib.Path(path).write_text(ed.toPlainText(), encoding="utf-8")
        
        py = bundled_python()
        proc = QProcess(self)
        proc.start(py, ["-m", "autopep8", "--in-place", path])
        proc.waitForFinished(5000)
        
        if proc.exitCode() != 0:
            err = bytes(proc.readAllStandardError()).decode()
            if "No module named autopep8" in err:
                QMessageBox.information(self, "Auto-Format", "To use Auto-Format, we need to install the 'autopep8' package.\nPlease type 'pip install autopep8' in the bottom input bar and press Enter.")
            else:
                QMessageBox.warning(self, "Format Error", err)
            return
            
        new_text = pathlib.Path(path).read_text(encoding="utf-8")
        ed.setPlainText(new_text)
        self._flash_status("Code formatted successfully!")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self._open_folder_path(path)
            elif path.endswith(".py") or path.endswith(".txt") or path.endswith(".json") or path.endswith(".csv"):
                self._open_file_path(path)

    def toggle_cheatsheet(self):
        self.cheatsheet.setVisible(not self.cheatsheet.isVisible())

    def _get_cheatsheet_html(self):
        from utils.theme import THEME
        return f"""
        <div style="font-family: 'Segoe UI', sans-serif; font-size: 13px; color: {THEME['fg']}; padding: 10px;">
            <h2 style="color: {THEME['accent1']};">Python Basics</h2>
            
            <h3 style="color: {THEME['accent3']};">1. Variables & Print</h3>
            <pre style="background: {THEME['bg']}; padding: 8px; border-radius: 4px; color: {THEME['fg']}">name = "Khushi"
age = 18
print(f"Hello {{name}}, age {{age}}")</pre>
            
            <h3 style="color: {THEME['accent3']};">2. If/Else</h3>
            <pre style="background: {THEME['bg']}; padding: 8px; border-radius: 4px; color: {THEME['fg']}">if age >= 18:
    print("Adult")
else:
    print("Minor")</pre>

            <h3 style="color: {THEME['accent3']};">3. Loops</h3>
            <pre style="background: {THEME['bg']}; padding: 8px; border-radius: 4px; color: {THEME['fg']}">for i in range(5):
    print(i)  # 0 to 4

colors = ["red", "blue"]
for c in colors:
    print(c)</pre>

            <h3 style="color: {THEME['accent3']};">4. Functions</h3>
            <pre style="background: {THEME['bg']}; padding: 8px; border-radius: 4px; color: {THEME['fg']}">def add(a, b):
    return a + b
res = add(5, 3)</pre>

            <h3 style="color: {THEME['accent3']};">5. Dictionaries</h3>
            <pre style="background: {THEME['bg']}; padding: 8px; border-radius: 4px; color: {THEME['fg']}">user = {{"name": "Max", "score": 10}}
print(user["name"])</pre>
        </div>
        """

    def open_bug_report(self):
        dlg = BugReportDialog(self)
        dlg.exec()

    def open_find_replace(self):
        from ui.dialogs import FindReplaceDialog
        ed = self.current_editor()
        if not ed: return
        if not self._find_dialog:
            self._find_dialog = FindReplaceDialog(self)
        self._find_dialog.set_editor(ed)
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()

    def current_editor(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def new_tab_action(self, *args):
        self.new_tab()

    def new_tab(self, content="", title="untitled.py"):
        if not isinstance(content, str): content = ""
        ed = CodeEditor(self.cfg.get("font_size", 13))
        ed.setPlainText(content)
        ed.setProperty("filepath", "")
        idx = self.tabs.addTab(ed, title)
        self.tabs.setCurrentIndex(idx)
        return ed

    def load_snippet(self, name):
        code = SNIPPETS.get(name, "")
        title = name.split("(")[0].strip().replace(" ", "_").lower() + ".py"
        self.new_tab(code, title)
        self._flash_status(f"Loaded example: {name}")

    def close_tab(self, idx):
        if self.tabs.count() <= 1:
            self.tabs.widget(idx).clear()
            return
        self.tabs.removeTab(idx)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if not path: return
        self._open_file_path(path)

    def _open_file_path(self, path):
        try:
            content = pathlib.Path(path).read_text(encoding="utf-8")
        except Exception as e:
            QMessageBox.warning(self, "Open failed", str(e))
            return
        ed = self.new_tab(content, os.path.basename(path))
        ed.setProperty("filepath", path)

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not path: return
        self._open_folder_path(path)

    def _open_folder_path(self, path):
        self.fs_model.setRootPath(path)
        self.file_tree.setRootIndex(self.fs_model.index(path))
        self.file_tree.show()
        self._flash_status(f"Opened folder: {path}")

    def _tree_double_clicked(self, index):
        path = self.fs_model.filePath(index)
        if os.path.isfile(path):
            self._open_file_path(path)

    def save_file(self):
        ed = self.current_editor()
        if not ed: return None
        path = ed.property("filepath")
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "untitled.py", "Python Files (*.py);;All Files (*)")
            if not path: return None
            ed.setProperty("filepath", path)
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
        try:
            pathlib.Path(path).write_text(ed.toPlainText(), encoding="utf-8")
            self._flash_status(f"Saved {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Save failed", str(e))
            return None
        return path

    def run_code(self):
        ed = self.current_editor()
        if not ed: return
        path = ed.property("filepath")
        if not path:
            path = self.save_file()
            if not path: return
        elif self.cfg.get("autosave", True):
            pathlib.Path(path).write_text(ed.toPlainText(), encoding="utf-8")

        self.stop_code()
        ed.clear_error_line()
        self.bottom_tabs.setCurrentIndex(0)
        self.output.clear()
        self.var_table.update_variables({})
        self.last_error_text = ""
        
        try:
            vf = self._var_file_path()
            if os.path.exists(vf): os.remove(vf)
        except: pass
        
        self._run_path = path
        py = bundled_python()
        self.output.appendPlainText(f"▸ Running with: {py}\n{'─'*60}\n")

        wrapper = self._make_var_wrapper(path)
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read_proc)
        self.proc.finished.connect(self._proc_done)
        self.proc.start(py, ["-u", wrapper])
        self._update_status(running=True)
        self._set_input_active(True)

    def _set_input_active(self, active: bool):
        if active:
            self.input_label.setText("⌨ INPUT — type & Enter")
            self.input_label.setStyleSheet(f"color:{THEME['accent3']};font-size:12px;font-weight:bold;padding:0 6px;")
            self.cmd_input.setStyleSheet(f"border:1px solid {THEME['accent3']};")
            self.cmd_input.setPlaceholderText("Program is waiting — type your input and press Enter")
            self.cmd_input.setFocus()
        else:
            self.input_label.setText("💤 idle")
            self.input_label.setStyleSheet(f"color:{THEME['comment']};font-size:12px;padding:0 6px;")
            self.cmd_input.setStyleSheet("")
            self.cmd_input.setPlaceholderText("Program input goes here when running  •  or type:  pip install <package>")

    def _var_file_path(self) -> str:
        import tempfile
        return str(pathlib.Path(tempfile.gettempdir()) / "_pycore_vars.json")

    def _make_var_wrapper(self, user_path: str) -> str:
        import tempfile
        var_file = self._var_file_path()
        wrapper_code = (
            "import runpy, json, sys, traceback\n"
            f"_user = {user_path!r}\n"
            f"_varfile = {var_file!r}\n"
            "_ns = {}\n"
            "_exc = None\n"
            "try:\n"
            "    _ns = runpy.run_path(_user, run_name='__main__')\n"
            "except SystemExit:\n"
            "    raise\n"
            "except BaseException:\n"
            "    _exc = traceback.format_exc()\n"
            "_out = {}\n"
            "for _k, _v in _ns.items():\n"
            "    if _k.startswith('__'): continue\n"
            "    _t = type(_v).__name__\n"
            "    if _t in ('module','function','type','builtin_function_or_method'): continue\n"
            "    try:\n"
            "        _s = repr(_v)\n"
            "        if len(_s) > 200: _s = _s[:200] + '...'\n"
            "    except:\n"
            "        _s = '<unrepr-able>'\n"
            "    _out[_k] = {'type': _t, 'value': _s}\n"
            "try:\n"
            "    with open(_varfile, 'w', encoding='utf-8') as _f:\n"
            "        json.dump(_out, _f)\n"
            "except: pass\n"
            "if _exc is not None:\n"
            "    sys.stderr.write(_exc)\n"
            "    sys.exit(1)\n"
        )
        tmp = pathlib.Path(tempfile.gettempdir()) / "_pycore_run_wrapper.py"
        tmp.write_text(wrapper_code, encoding="utf-8")
        return str(tmp)

    def run_in_console(self):
        ed = self.current_editor()
        if not ed: return
        self.bottom_tabs.setCurrentIndex(1)
        self.console.run_source(ed.toPlainText())

    def stop_code(self):
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            self.proc.kill()
            self.proc.waitForFinished(1500)
        self.proc = None
        if hasattr(self, "input_label"):
            self._set_input_active(False)

    def _read_proc(self):
        if not self.proc: return
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        self.output.insertPlainText(data)
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        if "Traceback" in data or "Error" in data or "File \"" in data or self.last_error_text:
            self.last_error_text += data

    def _proc_done(self, code, status):
        self._set_input_active(False)
        self.output.appendPlainText(f"\n{'─'*60}\n▸ Process finished (exit code {code})")
        self._update_status(running=False)
        self._populate_variables()
        if code != 0 and self.last_error_text.strip():
            line_no = self._extract_error_line(self.last_error_text)
            ed = self.current_editor()
            if ed and line_no > 0:
                ed.mark_error_line(line_no)
                self.output.appendPlainText(f"▸ Error is on line {line_no} (highlighted in red).")

    def _populate_variables(self):
        var_file = self._var_file_path()
        try:
            with open(var_file, "r", encoding="utf-8") as f:
                import json
                variables = json.load(f)
        except:
            self.var_table.update_variables({})
            return
        self.var_table.update_variables(variables)

    # ------------------ DEBUGGER ------------------
    
    _DEBUG_VARS_CMD = (
        "!import json; print('PYVARS_JSON:' + json.dumps({"
        "k: {'type': type(v).__name__, 'value': (lambda s: s[:200]+'...' "
        "if len(s)>200 else s)(repr(v))} for k, v in locals().items() "
        "if not k.startswith('__') and type(v).__name__ not in "
        "('module','function','type','builtin_function_or_method')}))"
    )

    def start_visual_run(self):
        self._is_visual_run = True
        self.start_debug()
        self.bottom_tabs.setCurrentIndex(2) # Switch to variables tab
        self._flash_status("Starting Visual Run (Slow Motion)...")

    def _visual_run_step(self):
        if self._debug_phase == "stopped":
            self.debug_step_over() # Step over to avoid going deep into internal modules if possible, but step_over works well.
            
    def start_debug(self):
        ed = self.current_editor()
        if not ed: return
        path = ed.property("filepath")
        if not path:
            path = self.save_file()
            if not path: return
        else:
            pathlib.Path(path).write_text(ed.toPlainText(), encoding="utf-8")

        self.debug_stop()
        ed.clear_error_line()
        ed.clear_debug_line()
        self.bottom_tabs.setCurrentIndex(0)
        self.output.clear()
        self._debug_path = path
        py = bundled_python()
        self.output.appendPlainText(f"🐞 Starting debugger for {os.path.basename(path)}...\n{'─'*60}\n")

        self.debug_proc = QProcess(self)
        self.debug_proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.debug_proc.readyReadStandardOutput.connect(self._debug_read)
        self.debug_proc.finished.connect(self._debug_finished)
        self._debug_buffer = ""
        self._debug_phase = "starting"
        self.debug_proc.start(py, ["-u", "-m", "pdb", path])
        self._set_debug_controls_enabled(False)
        self.debug_stop_act.setEnabled(True)

    def _set_debug_controls_enabled(self, enabled: bool):
        for a in (self.debug_continue_act, self.debug_step_over_act, self.debug_step_into_act):
            a.setEnabled(enabled)

    def debug_continue(self): self._debug_send("continue")
    def debug_step_over(self): self._debug_send("next")
    def debug_step_into(self): self._debug_send("step")

    def _debug_send(self, cmd):
        if not self.debug_proc or self._debug_phase != "stopped": return
        self._set_debug_controls_enabled(False)
        self._debug_phase = "running"
        self.debug_proc.write((cmd + "\n").encode("utf-8"))

    def debug_stop(self):
        self._visual_run_timer.stop()
        self._is_visual_run = False
        if self.debug_proc and self.debug_proc.state() != QProcess.ProcessState.NotRunning:
            self.debug_proc.kill()
            self.debug_proc.waitForFinished(1000)
        self.debug_proc = None
        self._debug_phase = None
        self._debug_buffer = ""
        ed = self.current_editor()
        if ed: ed.clear_debug_line()
        self._set_debug_controls_enabled(False)
        if hasattr(self, "debug_stop_act"):
            self.debug_stop_act.setEnabled(False)

    def _debug_finished(self, code, status):
        self._visual_run_timer.stop()
        self._is_visual_run = False
        if self._debug_phase not in (None,):
            self.output.appendPlainText(f"\n{'─'*60}\n🐞 Debug session ended.")
        self._debug_phase = None
        ed = self.current_editor()
        if ed: ed.clear_debug_line()
        self._set_debug_controls_enabled(False)
        self.debug_stop_act.setEnabled(False)

    def _debug_read(self):
        if not self.debug_proc: return
        data = bytes(self.debug_proc.readAllStandardOutput()).decode("utf-8", "replace")
        self._debug_buffer += data
        stripped = self._debug_buffer.rstrip()
        if not stripped.endswith("(Pdb)"): return
        buf = self._debug_buffer
        self._debug_buffer = ""
        buf_clean = re.sub(r"\(Pdb\)\s*$", "", buf).rstrip("\n")

        if self._debug_phase == "starting":
            bps = sorted(self.current_editor().breakpoints) if self.current_editor() else []
            self._debug_setup_queue = [f"break {n}" for n in bps] + ["continue"]
            self._debug_phase = "setup"
            self._debug_send_next_setup()
            return

        if self._debug_phase == "setup":
            if self._debug_setup_queue: self._debug_send_next_setup()
            return

        if self._debug_phase == "running":
            if "The program finished" in buf_clean:
                self.debug_proc.write(b"q\n")
                self._debug_phase = "ending"
                self.output.appendPlainText(f"\n{'─'*60}\n🐞 Program finished.")
                ed = self.current_editor()
                if ed: ed.clear_debug_line()
                self._set_debug_controls_enabled(False)
                return
            self._handle_debug_stop(buf_clean)
            self._debug_phase = "fetching_vars"
            self.debug_proc.write((self._DEBUG_VARS_CMD + "\n").encode("utf-8"))
            return

        if self._debug_phase == "fetching_vars":
            self._handle_debug_vars(buf_clean)
            self._debug_phase = "stopped"
            self._set_debug_controls_enabled(True)
            if self._is_visual_run:
                if not self._visual_run_timer.isActive():
                    self._visual_run_timer.start(800) # 800ms between steps
            return

    def _debug_send_next_setup(self):
        cmd = self._debug_setup_queue.pop(0)
        self.debug_proc.write((cmd + "\n").encode("utf-8"))
        if not self._debug_setup_queue:
            self._debug_phase = "running"

    def _handle_debug_stop(self, buf_clean: str):
        # Prevent pdb internal step noise
        m = re.search(r"^> (.+?)\((\d+)\)([\w<>]+)\(\)\s*\n->\s*(.*)$", buf_clean, re.MULTILINE)
        program_output = buf_clean[:m.start()] if m else buf_clean
        program_output = program_output.strip("\n")
        if program_output:
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.output.insertPlainText(program_output + "\n")
            self.output.moveCursor(QTextCursor.MoveOperation.End)
        if m:
            line_no = int(m.group(2))
            func_name = m.group(3)
            # If in visual run mode, skip highlighting internal pdb or temp files
            fname = m.group(1)
            if self._is_visual_run and not fname.endswith(".py"): 
                return
                
            ed = self.current_editor()
            if ed: ed.mark_debug_line(line_no)
            self.output.appendPlainText(f"🐞 Stopped at line {line_no} (in {func_name})")

    def _handle_debug_vars(self, buf_clean: str):
        marker = "PYVARS_JSON:"
        idx = buf_clean.find(marker)
        if idx == -1: return
        import json
        json_text = buf_clean[idx + len(marker):].strip()
        try: variables = json.loads(json_text)
        except: return
        self.var_table.update_variables(variables)

    def _extract_error_line(self, traceback_text: str) -> int:
        run_path = getattr(self, "_run_path", "")
        run_name = os.path.basename(run_path) if run_path else ""
        best = 0
        for m in re.finditer(r'File "([^"]+)", line (\d+)', traceback_text):
            fname, lno = m.group(1), int(m.group(2))
            if run_name and run_name in fname:
                best = lno
        return best

    def handle_cmd_input(self):
        text = self.cmd_input.text()
        if text.strip().startswith("pip"):
            self.run_pip_from_input()
            return
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            self.proc.write((text + "\n").encode("utf-8"))
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.output.insertPlainText(text + "\n")
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.cmd_input.clear()
            self.cmd_input.setFocus()
        else:
            self.cmd_input.clear()
            self._flash_status("Nothing is running. Press ▶ Run first, or type a pip command.")

    def _run_pip(self, args):
        prev = getattr(self, "_pip_proc", None)
        if prev is not None and prev.state() != QProcess.ProcessState.NotRunning:
            self.output.appendPlainText("\n▸ A pip command is already running — wait for it to finish.")
            return
        py = bundled_python()
        args = list(args)
        if args and args[0] == "uninstall" and "-y" not in args and "--yes" not in args:
            args.insert(1, "-y")
        full = ["-m", "pip", "--disable-pip-version-check"] + args
        self.output.appendPlainText(f"\n$ pip {' '.join(args)}\n{'─'*60}\n")
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: self.output.insertPlainText(bytes(proc.readAllStandardOutput()).decode("utf-8", "replace"))
        )
        proc.finished.connect(lambda c, s: self.output.appendPlainText(f"\n▸ pip finished (exit {c})"))
        proc.start(py, full)
        self._pip_proc = proc

    def run_pip_from_input(self):
        text = self.cmd_input.text().strip()
        if text.startswith("pip"): text = text[3:].strip()
        if not text: text = "list"
        self._run_pip(text.split())
        self.cmd_input.clear()

    def pip_list(self):
        self._run_pip(["list"])

    def pip_freeze(self):
        self._run_pip(["freeze"])

    def open_settings(self):
        from ui.dialogs import SettingsDialog
        from core.config import save_config
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec():
            vals = dlg.values()
            self.cfg.update(vals)
            save_config(self.cfg)
            if "theme" in vals:
                self.change_theme(vals["theme"])
            # Update editors based on new settings (like font size)
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, CodeEditor):
                    widget.font_size = self.cfg.get("font_size", 13)
                    widget._setup_font()
            self._flash_status("Settings saved.")

    def open_about(self):
        AboutDialog(self).exec()

    def _update_status(self, running=False):
        py = bundled_python()
        tag = "BUNDLED" if pathlib.Path(py).is_relative_to(app_dir()) else "SYSTEM"
        state = "● running" if running else "○ idle"
        self.statusBar().showMessage(f"Interpreter: {tag}  |  {state}  |  {py}")

    def _flash_status(self, msg):
        self.statusBar().showMessage(msg, 3000)

    def closeEvent(self, event):
        self.stop_code()
        self.console.stop()
        super().closeEvent(event)
        QApplication.quit()


