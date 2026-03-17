"""Web UI layer with Dash framework and shared state management."""

from .app import create_dash_app
from .state import desktop_state

__all__ = ['create_dash_app', 'desktop_state']
