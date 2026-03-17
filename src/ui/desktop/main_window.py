"""Main PyQt window embedding the local Dash web UI in QWebEngineView."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QUrl, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStatusBar, QToolBar
from PyQt6.QtGui import QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.core.analysis.analysis_pipeline import process_comtrade_path
from src.ui.web.state import desktop_state


class _ComtradeLoadWorker(QObject):
    finished = pyqtSignal(str, dict)

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path

    def run(self) -> None:
        result = process_comtrade_path(self.file_path)
        self.finished.emit(self.file_path, result)


class EmbeddedMainWindow(QMainWindow):
    def __init__(self, web_ui_url: str) -> None:
        super().__init__()
        self.web_ui_url = web_ui_url
        self.current_file_path = ""
        self._load_thread: QThread | None = None
        self._load_worker: _ComtradeLoadWorker | None = None

        self.setWindowTitle("COMTRADE Pro - Embedded Desktop")
        self.setGeometry(80, 80, 1600, 980)

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)
        self._create_toolbar()
        self._create_status_bar()
        self._load_web_ui()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("Open COMTRADE", self)
        open_action.triggered.connect(self.open_comtrade_file)
        toolbar.addAction(open_action)

        reload_action = QAction("Reload UI", self)
        reload_action.triggered.connect(self._load_web_ui)
        toolbar.addAction(reload_action)

    def _create_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Embedded web UI ready")

    def _load_web_ui(self) -> None:
        self.web_view.setUrl(QUrl(self.web_ui_url))

    def open_comtrade_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select COMTRADE Configuration File",
            self.current_file_path or "",
            "COMTRADE Config Files (*.cfg);;All Files (*.*)",
        )
        if not file_path:
            return

        self.status_bar.showMessage(f"Processing {Path(file_path).name}...")
        self._set_loading_state(True)
        self._load_thread = QThread(self)
        self._load_worker = _ComtradeLoadWorker(file_path)
        self._load_worker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.finished.connect(self._on_comtrade_loaded)
        self._load_worker.finished.connect(self._load_thread.quit)
        self._load_worker.finished.connect(self._load_worker.deleteLater)
        self._load_thread.finished.connect(self._load_thread.deleteLater)
        self._load_thread.finished.connect(self._clear_loader_refs)
        self._load_thread.start()

    def _set_loading_state(self, is_loading: bool) -> None:
        for toolbar in self.findChildren(QToolBar):
            toolbar.setEnabled(not is_loading)

    def _clear_loader_refs(self) -> None:
        self._load_thread = None
        self._load_worker = None

    def _on_comtrade_loaded(self, file_path: str, result: dict) -> None:
        self._set_loading_state(False)
        desktop_state.set_analysis(file_path, Path(file_path).name, result)

        if result.get("error"):
            QMessageBox.critical(self, "COMTRADE Load Error", result["error"])
            self.status_bar.showMessage("Error loading COMTRADE file", 5000)
            return

        self.current_file_path = file_path
        self.status_bar.showMessage(f"Loaded {Path(file_path).name}", 5000)