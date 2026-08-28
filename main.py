#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
import pathlib

from core.crash import setup_crash_reporter
from utils.helpers import icon_path, app_dir
from ui.splash import SplashScreen
from ui.main_window import PycoreIDE

def main():
    # Setup global crash reporter for Microsoft Store Compliance
    setup_crash_reporter()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    _ic = icon_path()
    if _ic:
        app.setWindowIcon(QIcon(_ic))

    shown = {"done": False}

    def open_main_window():
        win = PycoreIDE()
        win.show()
        # Keep references alive if needed by adding to app properties
        app._main_window = win

    def proceed_to_app():
        open_main_window()

    def show_main():
        if shown["done"]:
            return
        shown["done"] = True
        proceed_to_app()

    splash = SplashScreen(on_done=show_main)
    splash.show()

    QTimer.singleShot(8000, show_main)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
