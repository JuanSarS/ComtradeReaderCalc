"""Embedded Dash server lifecycle management for the PyQt desktop shell."""

from __future__ import annotations

import sys
import threading
import time
import urllib.error
import urllib.request

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from werkzeug.serving import make_server

from src.ui.desktop.main_window import EmbeddedMainWindow
from src.ui.web.app import create_dash_app


class DashServerThread(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 8050) -> None:
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.app = create_dash_app()
        self._server = make_server(self.host, self.port, self.app.server, threaded=True)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def run(self) -> None:
        self._server.serve_forever()

    def stop(self) -> None:
        self._server.shutdown()

    def wait_until_ready(self, timeout: float = 10.0) -> bool:
        deadline = time.time() + timeout
        url = f"{self.base_url}/api/health"
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=1.0) as response:
                    if response.status == 200:
                        return True
            except urllib.error.URLError:
                time.sleep(0.1)
        return False


def launch_desktop_app() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("COMTRADE Pro")
    app.setOrganizationName("Power Systems Protection Engineering")
    app.setApplicationVersion("2.0.0")

    server = DashServerThread()
    server.start()
    if not server.wait_until_ready():
        raise RuntimeError("Embedded Dash server failed to start.")

    window = EmbeddedMainWindow(server.base_url)
    window.show()

    exit_code = app.exec()
    server.stop()
    return exit_code