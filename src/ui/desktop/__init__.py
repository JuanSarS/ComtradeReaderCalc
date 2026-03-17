"""Desktop shell components using PyQt6 and QWebEngineView."""

from .server import launch_desktop_app, DashServerThread
from .main_window import EmbeddedMainWindow

__all__ = ['launch_desktop_app', 'DashServerThread', 'EmbeddedMainWindow']
