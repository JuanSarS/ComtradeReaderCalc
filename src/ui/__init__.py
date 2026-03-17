"""User interface modules for desktop and web components."""

from .desktop.server import launch_desktop_app, DashServerThread
from .desktop.main_window import EmbeddedMainWindow
from .web.app import create_dash_app
from .web.state import desktop_state

__all__ = [
    'launch_desktop_app',
    'DashServerThread',
    'EmbeddedMainWindow',
    'create_dash_app',
    'desktop_state',
]
