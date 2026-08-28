import sys
import os
import pathlib
import platform

def app_dir() -> pathlib.Path:
    """Directory the app lives in (handles PyInstaller onedir/onefile)."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys.executable).parent
    return pathlib.Path(__file__).parent.parent.resolve()

def local_app_data_dir() -> pathlib.Path:
    """Directory for storing databases and logs in an MSIX compliant way."""
    path = pathlib.Path(os.getenv('LOCALAPPDATA', os.path.expanduser('~'))) / "NovaIDE"
    path.mkdir(parents=True, exist_ok=True)
    return path

def bundled_python() -> str:
    """
    Locate the bundled interpreter. Looks for ./python/python.exe (Windows)
    or ./python/bin/python3 (Linux dev). Falls back to current interpreter.
    """
    base = app_dir()
    candidates = [
        base / "_internal" / "python" / "python.exe",
        base / "python" / "python.exe",
        base / "python" / "bin" / "python3",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return sys.executable

def icon_path() -> str:
    """Find the app icon whether running from source or a PyInstaller bundle."""
    base = app_dir()
    candidates = [
        base / "nova.ico",
        base / "_internal" / "nova.ico",
        base / "icon" / "nova.ico",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return ""
