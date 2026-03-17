"""
pages.py - One function per view that returns a Dash html tree.
Each page is rendered by the navigation callback when a sidebar button is pressed.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def _section_header(title: str, subtitle: str = "") -> html.Div:
    return html.Div(
        className="page-header",
        children=[
            html.H2(title, className="page-title"),
            html.P(subtitle, className="page-subtitle") if subtitle else None,
        ],
    )


def _card(children, extra_class: str = "") -> html.Div:
    return html.Div(children=children, className=f"card {extra_class}")


def _tab_row(tab_id: str, tabs: list, default: str) -> dbc.RadioItems:
    return dbc.RadioItems(
        id=tab_id,
        options=[{"label": lbl, "value": val} for lbl, val in tabs],
        value=default,
        inline=True,
        className="tab-toggle",
        inputClassName="tab-toggle-input",
        labelClassName="tab-toggle-label",
        labelCheckedClassName="tab-toggle-label active",
    )


def _stat_card(label: str, value: str, unit: str = "", color: str = "#e0e0e0") -> html.Div:
    return html.Div(
        className="stat-card",
        children=[
            html.Div(label, className="stat-label"),
            html.Div(value, className="stat-value", style={"color": color}),
            html.Div(unit, className="stat-unit") if unit else None,
        ],
    )


def _cursor_info_bar(page_id: str) -> html.Div:
    return html.Div(
        className="cursor-panel-bar",
        children=[
            html.Span(
                "Cursor: ",
                style={"color": "#CC44FF", "fontWeight": "600", "marginRight": "8px"},
            ),
            html.Span("- ms", id=f"cursor-time-{page_id}", className="cur-val accent-purple"),
            html.Div(
                id=f"cursor-values-{page_id}",
                style={"display": "inline-flex", "gap": "16px", "marginLeft": "16px", "flexWrap": "wrap"},
            ),
            html.Span(
                " (Haz clic en la grafica para mover el cursor)",
                style={"color": "#444", "fontSize": "11px", "marginLeft": "auto"},
            ),
        ],
    )


def page_instantaneous(default_type: str = "voltage") -> html.Div:
    return html.Div(
        children=[
            _section_header("Senales Instantaneas", "Formas de onda instantaneas en el dominio del tiempo"),
            html.Div(
                className="toolbar",
                children=[
                    _tab_row(
                        "inst-tab-type",
                        [("Voltajes (Va, Vb, Vc)", "voltage"), ("Corrientes (Ia, Ib, Ic)", "current")],
                        default_type,
                    ),
                    html.Div(
                        className="toolbar-right",
                        children=[
                            dcc.Checklist(
                                id="inst-show-raw",
                                options=[{"label": " Senal sin filtrar", "value": "show"}],
                                value=[],
                                style={"fontSize": "12px", "color": "#888"},
                                inputStyle={"marginRight": "4px"},
                                labelStyle={"cursor": "pointer"},
                            ),
                            html.Button("Zoom a Falla", id="btn-zoom-fault", className="btn-secondary"),
                            html.Button("Reset Zoom", id="btn-zoom-reset", className="btn-secondary"),
                        ],
                    ),
                ],
            ),
            _card(
                dcc.Graph(
                    id="graph-instantaneous",
                    config={"displayModeBar": True, "scrollZoom": True},
                    style={"height": "420px"},
                )
            ),
            _cursor_info_bar("inst"),
            html.Div(
                className="stat-row",
                children=[
                    _stat_card("Muestras Totales", "-", "", "#e0e0e0"),
                    _stat_card("Frecuencia de Muestreo", "-", "Hz", "#e0e0e0"),
                    _stat_card("Duracion", "-", "s", "#e0e0e0"),
                ],
                id="inst-stat-row",
            ),
        ]
    )


def page_rms(default_type: str = "voltage") -> html.Div:
    return html.Div(
        children=[
            _section_header("Senales RMS", "Valor eficaz calculado con ventana deslizante de un ciclo"),
            html.Div(
                className="toolbar",
                children=[
                    _tab_row("rms-tab-type", [("Voltajes RMS", "voltage"), ("Corrientes RMS", "current")], default_type),
                ],
            ),
            _card(
                dcc.Graph(
                    id="graph-rms",
                    config={"displayModeBar": True, "scrollZoom": True},
                    style={"height": "380px"},
                )
            ),
            _cursor_info_bar("rms"),
            html.Div(className="phase-card-row", id="rms-phase-cards"),
        ]
    )


def page_phasors(default_type: str = "voltage") -> html.Div:
    return html.Div(
        children=[
            _section_header("Fasores de Fase", "Representacion fasorial de voltajes y corrientes de fase"),
            html.Div(
                className="toolbar",
                children=[
                    _tab_row("phasor-tab-type", [("Voltajes", "voltage"), ("Corrientes", "current")], default_type),
                ],
            ),
            html.Div(
                className="phasor-layout",
                children=[
                    _card(
                        dcc.Graph(
                            id="graph-phasors",
                            config={"displayModeBar": True},
                            style={"height": "440px"},
                        ),
                        "phasor-plot-card",
                    ),
                    html.Div(id="phasor-values-panel", className="phasor-values"),
                ],
            ),
        ]
    )


def page_sequence_components(default_type: str = "voltage") -> html.Div:
    return html.Div(
        children=[
            _section_header(
                "Componentes de Secuencia",
                "Descomposicion en componentes simetricos (positiva, negativa y cero)",
            ),
            html.Div(
                className="toolbar",
                children=[
                    _tab_row("seq-tab-type", [("Voltajes", "voltage"), ("Corrientes", "current")], default_type),
                ],
            ),
            _card(
                dcc.Graph(
                    id="graph-sequence-wave",
                    config={"displayModeBar": True, "scrollZoom": True},
                    style={"height": "360px"},
                )
            ),
            _cursor_info_bar("seq"),
            html.Div(className="seq-card-row", id="seq-cards"),
            _card(html.Div(id="seq-interpretation", className="seq-interpretation"), "interpretation-card"),
        ]
    )


def page_seq_phasors(default_type: str = "voltage") -> html.Div:
    return html.Div(
        children=[
            _section_header("Fasores de Secuencia", "Representacion fasorial de las componentes simetricas"),
            html.Div(
                className="toolbar",
                children=[
                    _tab_row("seq-ph-tab-type", [("Voltajes", "voltage"), ("Corrientes", "current")], default_type),
                ],
            ),
            _card(
                dcc.Graph(
                    id="graph-seq-phasors-3",
                    config={"displayModeBar": True},
                    style={"height": "460px"},
                )
            ),
            html.Div(
                className="phasor-layout",
                children=[
                    _card(
                        dcc.Graph(
                            id="graph-seq-combined",
                            config={"displayModeBar": True},
                            style={"height": "380px"},
                        ),
                        "phasor-plot-card",
                    ),
                    html.Div(id="seq-summary-table", className="phasor-values"),
                ],
            ),
        ]
    )


def page_text_results() -> html.Div:
    return html.Div(
        children=[
            _section_header("Resultados en Texto", "Valores numericos detallados del analisis COMTRADE"),
            dbc.Tabs(
                [
                    dbc.Tab(label="Resumen", tab_id="txt-summary"),
                    dbc.Tab(label="Fasores de Fase", tab_id="txt-phasors"),
                    dbc.Tab(label="Componentes de Secuencia", tab_id="txt-sequence"),
                ],
                id="txt-tabs",
                active_tab="txt-summary",
                className="txt-tabs",
            ),
            html.Div(id="txt-tab-content", className="txt-content"),
        ]
    )


def page_barycenter() -> html.Div:
    return html.Div(
        children=[
            _section_header("Baricentro Geometrico", "Centro de masa de las senales trifasicas en el plano complejo"),
            html.Div(
                className="toolbar",
                children=[
                    _tab_row("bary-tab-type", [("Voltajes", "voltage"), ("Corrientes", "current")], "voltage"),
                ],
            ),
            html.Div(
                className="bary-layout",
                children=[
                    html.Div(
                        className="bary-main",
                        children=[
                            _card(
                                [
                                    html.Div("Trayectoria del Baricentro", className="card-title"),
                                    dcc.Graph(
                                        id="graph-bary-trajectory",
                                        config={"displayModeBar": True, "scrollZoom": True},
                                        animate=True,
                                        animation_options={
                                            "transition": {"duration": 500},
                                            "frame": {"duration": 500, "redraw": True},
                                        },
                                        style={"height": "380px"},
                                    ),
                                ]
                            ),
                            _card(
                                [
                                    html.Div("Plano Vectorial Detallado", className="card-title"),
                                    dcc.Graph(
                                        id="graph-bary-vector",
                                        config={"displayModeBar": False},
                                        animate=True,
                                        animation_options={
                                            "frame": {"redraw": False, "duration": 0},
                                            "transition": {"duration": 2000, "easing": "bounce-in-out"},
                                        },
                                        style={"height": "300px"},
                                    ),
                                ]
                            ),
                        ],
                    ),
                    html.Div(
                        className="bary-sidebar",
                        children=[
                            _card(html.Div(id="bary-coords-panel"), "bary-info-card"),
                            _card(html.Div(id="bary-stats-panel"), "bary-info-card"),
                            _card(html.Div(id="bary-interp-panel"), "bary-info-card accent-panel"),
                            _card(html.Div(id="bary-complex-panel"), "bary-info-card"),
                        ],
                    ),
                ],
            ),
        ]
    )


def page_no_file() -> html.Div:
    return html.Div(
        className="no-file-page",
        children=[
            html.Div("^", className="no-file-icon"),
            html.H3("Sube un archivo COMTRADE para comenzar", className="no-file-title"),
            html.P(
                "Arrastra y suelta tu archivo .cfg en el boton lateral, o haz clic para seleccionarlo.",
                className="no-file-sub",
            ),
        ],
    )