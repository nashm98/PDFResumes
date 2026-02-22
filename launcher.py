import threading
import time
import webbrowser

import pypdf  # noqa: F401 - required so PyInstaller bundles PDF parser
from app import run


def open_browser_delayed() -> None:
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    threading.Thread(target=open_browser_delayed, daemon=True).start()
    run()
