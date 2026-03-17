"""
Layout builder for the COMTRADE Pro Dash application.
Replicates the dark-theme scientific dashboard from the Figma mockup.
"""
from dash import html, dcc
import dash_bootstrap_components as dbc

NAV_ITEMS = [
    ("instantaneous", "〰", "Señales Instantáneas"),
    ("rms",           "⟿", "Señales RMS"),
    ("phasors",       "◎", "Fasores de Fase"),
    ("sequence_comp", "↯", "Componentes de Secuencia"),
    ("seq_phasors",   "↔", "Fasores de Secuencia"),
    ("text_results",  "🗒", "Resultados en Texto"),
    ("barycenter",    "⊕", "Baricentro Geométrico"),
]


def build_layout():
    return html.Div(
        id="app-root",
        className="app-root",
        children=[
            # Hidden store for processed data (shared state across callbacks)
            dcc.Store(id="store-data", storage_type="memory"),
            dcc.Store(id="store-filename", storage_type="memory"),
            dcc.Store(id="store-selected-signals", storage_type="memory"),
            dcc.Store(id="store-sync-token", storage_type="memory"),
            dcc.Store(id="store-tab-type", storage_type="memory"),
            dcc.Store(id="store-cursor-ms", storage_type="memory"),
            dcc.Interval(id="desktop-sync-interval", interval=1000, n_intervals=0),

            # ── Sidebar ──────────────────────────────────────────────────
            html.Div(
                className="sidebar",
                children=[
                    # Logo / brand
                    html.Div(className="sidebar-brand", children=[
                        html.Div(className="brand-icon", children="⚡"),
                        html.Div([
                            html.Div("COMTRADE Pro", className="brand-title"),
                            html.Div("Análisis de Protecciones", className="brand-sub"),
                        ])
                    ]),

                    # Upload button
                    dcc.Upload(
                        id="upload-comtrade",
                        children=html.Div([
                            html.Span("⬆  ", style={"marginRight": "6px"}),
                               "Subir Archivos COMTRADE",
                        ]),
                        className="upload-btn",
                           accept=".cfg,.dat,.zip",
                           multiple=True,
                    ),

                       html.Div(
                           ".cfg + .dat  ó  .zip",
                           style={"fontSize": "10px", "color": "#555",
                                  "textAlign": "center", "marginTop": "4px"},
                       ),

                    # Loaded file indicator
                    html.Div(id="loaded-file-indicator", className="file-indicator"),

                    html.Hr(className="sidebar-divider"),

                    # Navigation links
                    html.Nav(
                        className="sidebar-nav",
                        children=[
                            html.Button(
                                children=[
                                    html.Span(icon, className="nav-icon"),
                                    html.Span(label, className="nav-label"),
                                ],
                                id={"type": "nav-btn", "page": page_id},
                                className="nav-item",
                                n_clicks=0,
                            )
                            for page_id, icon, label in NAV_ITEMS
                        ],
                    ),
                ],
            ),

            # ── Main content ─────────────────────────────────────────────
            html.Div(
                className="main-content",
                children=[
                    # Top info bar
                    html.Div(
                        className="top-bar",
                        id="top-bar",
                        children=[
                            html.Div([
                                html.Div("Archivo Activo", className="tb-label"),
                                html.Div("—", id="tb-filename", className="tb-value accent-green"),
                            ]),
                            html.Div([
                                html.Div("Frecuencia Fundamental", className="tb-label"),
                                html.Div("60 Hz", id="tb-freq", className="tb-value accent-green"),
                            ]),
                            html.Div([
                                html.Div("Estado", className="tb-label"),
                                html.Div("Listo", id="tb-status", className="tb-value accent-blue"),
                            ]),
                        ],
                    ),

                    html.Div(
                        className="card",
                        style={"marginBottom": "10px", "padding": "8px 12px"},
                        children=[
                            html.Div([
                                html.Div("Cursor", className="tb-label"),
                                html.Div("— ms", id="tb-cursor-time", className="tb-value accent-purple"),
                            ]),
                            html.Div("Selección de Canales", className="card-title"),
                            html.Div(
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))",
                                    "gap": "8px",
                                    "alignItems": "start",
                                },
                                children=[
                                    html.Div([
                                        html.Div("Voltajes", className="tb-label", style={"marginBottom": "4px"}),
                                        dcc.Dropdown(
                                            id="select-voltage-channels",
                                            multi=True,
                                            placeholder="Selecciona canales de voltaje",
                                            style={"fontSize": "12px", "minHeight": "34px"},
                                        ),
                                    ]),
                                    html.Div([
                                        html.Div("Corrientes", className="tb-label", style={"marginBottom": "4px"}),
                                        dcc.Dropdown(
                                            id="select-current-channels",
                                            multi=True,
                                            placeholder="Selecciona canales de corriente",
                                            style={"fontSize": "12px", "minHeight": "34px"},
                                        ),
                                    ]),
                                ],
                            ),
                            html.Div(id="channel-selection-message", style={"marginTop": "6px", "fontSize": "11px", "color": "#b8c0cc"}),
                        ],
                    ),

                    html.Div(
                        id="global-time-card",
                        className="card",
                        style={"marginBottom": "10px", "padding": "8px 12px"},
                        children=[
                            html.Div("Señal Filtrada Global (Cursor Persistente)", className="card-title"),
                            dbc.RadioItems(
                                id="global-tab-type",
                                options=[
                                    {"label": "Voltaje", "value": "voltage"},
                                    {"label": "Corriente", "value": "current"},
                                ],
                                value="voltage",
                                inline=True,
                                className="tab-toggle",
                                inputClassName="tab-toggle-input",
                                labelClassName="tab-toggle-label",
                                labelCheckedClassName="tab-toggle-label active",
                            ),
                            dcc.Graph(
                                id="graph-global-time",
                                config={"displayModeBar": True, "scrollZoom": True},
                                style={"height": "170px", "marginTop": "4px"},
                            ),
                        ],
                    ),

                    # Page container — swapped by navigation callbacks
                    html.Div(id="page-content", className="page-content"),
                ],
            ),
        ],
    )
