"""Dash application factory for the embedded web UI."""

from __future__ import annotations

import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from flask import jsonify, request

from src.core.analysis.analysis_pipeline import process_comtrade_path
from src.ui.web.state import desktop_state

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_APP = None


def _register_routes(server) -> None:
    if "api_health" not in server.view_functions:
        @server.get("/api/health")
        def api_health():
            return jsonify({"status": "ok"})

    if "api_current_analysis" not in server.view_functions:
        @server.get("/api/current-analysis")
        def api_current_analysis():
            return jsonify(desktop_state.get_snapshot())

    if "api_load_comtrade" not in server.view_functions:
        @server.post("/api/load-comtrade")
        def api_load_comtrade():
            payload = request.get_json(silent=True) or {}
            cfg_path = payload.get("path", "")
            if not cfg_path:
                return jsonify({"error": "Missing COMTRADE path."}), 400
            result = process_comtrade_path(cfg_path)
            desktop_state.set_analysis(cfg_path, Path(cfg_path).name, result)
            status_code = 400 if result.get("error") else 200
            return jsonify(result), status_code


def create_dash_app():
    global _APP
    if _APP is not None:
        return _APP

    from src.ui.pages.layout import build_layout

    assets_folder = PROJECT_ROOT / "src" / "ui" / "pages" / "assets"
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        ],
        suppress_callback_exceptions=True,
        title="COMTRADE Pro",
        assets_folder=str(assets_folder),
    )
    _register_routes(app.server)
    app.layout = build_layout()

    import src.ui.pages.callbacks  # noqa: F401

    _APP = app
    return app