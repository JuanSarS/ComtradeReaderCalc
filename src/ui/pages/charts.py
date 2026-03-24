"""
charts.py — Plotly figure factory for every view of the dashboard.
All functions return a plotly.graph_objects.Figure.
"""
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Optional

# ─── colour palette (matches dark mockup) ───────────────────────────────────
PHASE_COLORS = {"A": "#FF4B4B", "B": "#FFB800", "C": "#4B9EFF"}
SEQ_COLORS   = {"positive": "#00FF88", "negative": "#FF6B35", "zero": "#CC44FF"}
GRID_COLOR   = "rgba(255,255,255,0.07)"
BG_COLOR     = "#0d1117"
PAPER_COLOR  = "#0d1117"
FONT_COLOR   = "#e0e0e0"

_DARK_LAYOUT = dict(
    paper_bgcolor=PAPER_COLOR,
    plot_bgcolor=BG_COLOR,
    font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
    margin=dict(l=60, r=20, t=40, b=50),
    xaxis=dict(
        gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
        showline=False, tickfont=dict(size=10),
    ),
    yaxis=dict(
        gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
        showline=False, tickfont=dict(size=10),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1, font=dict(size=11),
        orientation="h", y=-0.15,
    ),
    hovermode="x unified",
)


def _base_fig(**kwargs):
    fig = go.Figure()
    layout = {**_DARK_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig


def _phase_color(channel_name: str, idx: int) -> str:
    name_up = channel_name.upper()
    for letter, color in PHASE_COLORS.items():
        if letter in name_up:
            return color
    return ["#FF4B4B", "#FFB800", "#4B9EFF", "#CC44FF", "#00FF88"][idx % 5]


# ─── instantaneous waveforms ────────────────────────────────────────────────

def make_instantaneous_fig(
    time_ms: List[float],
    signals: Dict[str, List[float]],
    y_label: str = "Voltaje (V)",
    fault_time_ms: Optional[float] = None,
    pre_region: Optional[tuple] = None,
    post_region: Optional[tuple] = None,
    raw_signals: Optional[Dict[str, List[float]]] = None,
    cursor_ms: Optional[float] = None,
    uirevision: Optional[str] = None,
) -> go.Figure:
    fig = _base_fig()
    fig.update_layout(
        xaxis_title="Tiempo (ms)",
        yaxis_title=y_label,
        uirevision=uirevision,
    )

    for idx, (name, vals) in enumerate(signals.items()):
        color = _phase_color(name, idx)
        label = f"Fase {name[-1].upper()}" if name else name
        fig.add_trace(go.Scatter(
            x=time_ms, y=vals, mode="lines", name=label,
            line=dict(color=color, width=1.5),
            hovertemplate=f"{label}: %{{y:.1f}}<extra></extra>",
        ))

    if fault_time_ms is not None:
        fig.add_vline(
            x=fault_time_ms, line_dash="dash",
            line_color="rgba(255,200,0,0.6)", line_width=1,
            annotation_text="Falla", annotation_font_color="rgba(255,200,0,0.9)",
        )

    if pre_region:
        fig.add_vrect(x0=pre_region[0], x1=pre_region[1],
                      fillcolor="rgba(0,255,136,0.05)", line_width=0,
                      annotation_text="Pre-Falla", annotation_position="top left",
                      annotation_font_color="#00FF88")
    if post_region:
        fig.add_vrect(x0=post_region[0], x1=post_region[1],
                      fillcolor="rgba(75,158,255,0.05)", line_width=0,
                      annotation_text="Durante Falla", annotation_position="top left",
                      annotation_font_color="#4B9EFF")

    if raw_signals:
        for idx, (name, vals) in enumerate(raw_signals.items()):
            color = _phase_color(name, idx)
            label = f"Fase {name[-1].upper()} (sin filtrar)" if name else f"{name} (sin filtrar)"
            fig.add_trace(go.Scatter(
                x=time_ms, y=vals, mode="lines", name=label,
                line=dict(color=color, width=1.0, dash="dot"),
                opacity=0.40,
                hoverinfo="skip",
            ))

    if cursor_ms is not None:
        fig.add_vline(
            x=cursor_ms, line_dash="solid",
            line_color="rgba(204,68,255,0.85)", line_width=1.5,
        )

    return fig


# ─── RMS trends ─────────────────────────────────────────────────────────────

def make_rms_fig(
    time_ms: List[float],
    rms_signals: Dict[str, List[float]],
    y_label: str = "Voltaje RMS (V)",
    cursor_ms: Optional[float] = None,
) -> go.Figure:
    fig = _base_fig()
    fig.update_layout(xaxis_title="Tiempo (ms)", yaxis_title=y_label)
    for idx, (name, vals) in enumerate(rms_signals.items()):
        color = _phase_color(name, idx)
        label = f"Fase {name[-1].upper()}"
        fig.add_trace(go.Scatter(
            x=time_ms, y=vals, mode="lines", name=label,
            line=dict(color=color, width=2),
        ))
    if cursor_ms is not None:
        fig.add_vline(
            x=cursor_ms, line_dash="solid",
            line_color="rgba(204,68,255,0.85)", line_width=1.5,
        )
    return fig


# ─── Phasor diagram ──────────────────────────────────────────────────────────

def make_phasor_fig(
    phasors: Dict,
    title: str = "Diagrama Fasorial",
) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=PAPER_COLOR,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
        polar=dict(
            bgcolor=BG_COLOR,
            radialaxis=dict(
                showticklabels=True, tickfont=dict(size=9, color=FONT_COLOR),
                gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
            ),
            angularaxis=dict(
                direction="counterclockwise", rotation=0,
                tickfont=dict(size=9, color=FONT_COLOR),
                gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
                tickmode="array",
                tickvals=list(range(0, 360, 30)),
                ticktext=[f"{a}°" for a in range(0, 360, 30)],
            ),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
        title=dict(text=title, font=dict(size=14, color=FONT_COLOR), x=0.5),
        showlegend=False,
        transition=dict(duration=140, easing="cubic-in-out"),
    )

    for idx, (name, ph) in enumerate(phasors.items()):
        color = _phase_color(name, idx)
        mag   = ph["magnitude"]
        ang   = ph["angle_deg"]
        label = f"Fase {name[-1].upper()}" if name else name

        # Draw arrow from origin to tip using a line + marker trick
        fig.add_trace(go.Scatterpolar(
            r=[0, mag], theta=[0, ang],
            mode="lines+markers+text",
            line=dict(color=color, width=2.5),
            marker=dict(color=color, size=[0, 8], symbol=["circle", "arrow"],
                        angleref="previous"),
            text=["", label],
            textposition="top right",
            textfont=dict(color=color, size=11),
            name=label,
        ))

    return fig


# ─── Sequence phasors (3 separate subplots) ──────────────────────────────────

def make_sequence_phasors_fig(seq_data: dict) -> go.Figure:
    """Three polar subplots: positive, negative, zero sequence."""
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "polar"}, {"type": "polar"}, {"type": "polar"}]],
        subplot_titles=["Secuencia Positiva", "Secuencia Negativa", "Secuencia Cero"],
    )

    entries = [
        ("positive", SEQ_COLORS["positive"]),
        ("negative", SEQ_COLORS["negative"]),
        ("zero",     SEQ_COLORS["zero"]),
    ]
    for col_idx, (key, color) in enumerate(entries, start=1):
        ph = seq_data.get(key, {"magnitude": 0, "angle_deg": 0})
        mag, ang = ph["magnitude"], ph["angle_deg"]
        fig.add_trace(
            go.Scatterpolar(r=[0, mag], theta=[0, ang],
                            mode="lines+markers",
                            line=dict(color=color, width=2.5),
                            marker=dict(color=color, size=[0, 8]),
                            name=key.capitalize()),
            row=1, col=col_idx,
        )

    polar_style = dict(
        bgcolor=BG_COLOR,
        radialaxis=dict(showticklabels=True, tickfont=dict(size=8, color=FONT_COLOR),
                        gridcolor=GRID_COLOR, linecolor=GRID_COLOR),
        angularaxis=dict(tickfont=dict(size=8, color=FONT_COLOR),
                         gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
                         direction="counterclockwise"),
    )
    fig.update_polars(**polar_style)
    fig.update_layout(
        paper_bgcolor=PAPER_COLOR,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=11),
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
        transition=dict(duration=140, easing="cubic-in-out"),
    )
    return fig


# ─── Combined sequence phasor diagram ────────────────────────────────────────

def make_combined_seq_phasor_fig(seq_data: dict) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=PAPER_COLOR,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
        polar=dict(
            bgcolor=BG_COLOR,
            radialaxis=dict(showticklabels=True, tickfont=dict(size=9, color=FONT_COLOR),
                            gridcolor=GRID_COLOR, linecolor=GRID_COLOR),
            angularaxis=dict(direction="counterclockwise", rotation=0,
                             tickfont=dict(size=9, color=FONT_COLOR),
                             gridcolor=GRID_COLOR, linecolor=GRID_COLOR),
        ),
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        transition=dict(duration=140, easing="cubic-in-out"),
    )
    labels = {"positive": ("Pos", SEQ_COLORS["positive"]),
              "negative": ("Neg", SEQ_COLORS["negative"]),
              "zero":     ("Cero", SEQ_COLORS["zero"])}
    for key, (lbl, color) in labels.items():
        ph = seq_data.get(key, {"magnitude": 0, "angle_deg": 0})
        fig.add_trace(go.Scatterpolar(
            r=[0, ph["magnitude"]], theta=[0, ph["angle_deg"]],
            mode="lines+markers+text",
            line=dict(color=color, width=2.5),
            marker=dict(color=color, size=[0, 8]),
            text=["", lbl],
            textposition="top right",
            textfont=dict(color=color, size=11),
            name=lbl,
        ))
    return fig


# ─── Sequence component waveforms (time-domain instantaneous) ────────────────

def make_sequence_waveform_fig(
    time_ms: List[float],
    seq_data: dict,
    voltages: dict,
    system_freq: float = 60.0,
    cursor_ms: Optional[float] = None,
    seq_rms: Optional[Dict[str, List[float]]] = None,
    y_label: str = "Voltaje RMS (V)",
    uirevision: Optional[str] = None,
) -> go.Figure:
    """
    Plot sequence trends.
    Preferred mode: RMS trends for V1/V2/V0 or I1/I2/I0.
    Fallback mode: sinusoidal reconstruction from sequence phasors.
    """
    fig = _base_fig()
    fig.update_layout(
        xaxis_title="Tiempo (ms)",
        yaxis_title=y_label,
        uirevision=uirevision,
    )

    entries = [
        ("positive", "Secuencia Positiva",  SEQ_COLORS["positive"]),
        ("negative", "Secuencia Negativa",  SEQ_COLORS["negative"]),
        ("zero",     "Secuencia Cero",       SEQ_COLORS["zero"]),
    ]
    if seq_rms:
        for key, label, color in entries:
            vals = seq_rms.get(key, [])
            if not vals:
                continue
            n = min(len(time_ms), len(vals))
            fig.add_trace(go.Scatter(
                x=time_ms[:n], y=vals[:n], mode="lines", name=label,
                line=dict(color=color, width=2.0),
            ))
    else:
        t = np.array(time_ms) / 1000.0
        omega = 2 * np.pi * system_freq
        for key, label, color in entries:
            ph = seq_data.get(key, {"magnitude": 0, "angle_deg": 0})
            mag = ph["magnitude"] * np.sqrt(2)
            ang = np.radians(ph["angle_deg"])
            wave = mag * np.sin(omega * t + ang)
            fig.add_trace(go.Scatter(
                x=time_ms, y=wave.tolist(), mode="lines", name=label,
                line=dict(color=color, width=1.8),
            ))
    if cursor_ms is not None:
        fig.add_vline(
            x=cursor_ms, line_dash="solid",
            line_color="rgba(204,68,255,0.85)", line_width=1.5,
        )
    return fig


# ─── Barycenter trajectory ───────────────────────────────────────────────────

def make_barycenter_trajectory_fig(
    bary_real: List[float],
    bary_imag: List[float],
    current_index: Optional[int] = None,
) -> go.Figure:
    fig = _base_fig()
    fig.update_layout(
        xaxis_title="Componente Real (V)",
        yaxis_title="Componente Imaginaria (A)",
        hovermode="closest",
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    n = len(bary_real)
    if n == 0:
        return fig

    idx = n - 1 if current_index is None else int(max(0, min(current_index, n - 1)))
    traj_x = bary_real[:idx + 1]
    traj_y = bary_imag[:idx + 1]
    n_visible = len(traj_x)

    fig.add_trace(go.Scatter(
        x=traj_x,
        y=traj_y,
        mode="markers",
        marker=dict(
            color=list(range(n_visible)),
            colorscale="Blues",
            size=4,
            opacity=0.8,
        ),
        name="Trayectoria",
        hovertemplate="Re: %{x:.3e}<br>Im: %{y:.3e}<extra></extra>",
    ))

    # Keep marker anchored to the most recent visible sample.
    fig.add_trace(go.Scatter(
        x=[traj_x[-1]],
        y=[traj_y[-1]],
        mode="markers+text",
        marker=dict(color="#FF4B4B", size=12, symbol="circle"),
        text=["Centro"],
        textposition="top right",
        textfont=dict(color="#FF4B4B", size=11),
        name="Baricentro actual",
    ))

    return fig


# ─── Barycenter vector plane ─────────────────────────────────────────────────

def make_barycenter_vector_fig(
    center_real: float,
    center_imag: float,
    phase_phasors: Optional[Dict[str, Dict[str, float]]] = None,
) -> go.Figure:
    fig = _base_fig()
    fig.update_layout(
        xaxis_title="Real",
        yaxis_title="Imag",
        xaxis=dict(**_DARK_LAYOUT["xaxis"], scaleanchor="y", scaleratio=1),
        hovermode=False,
        transition=dict(duration=2000, easing="bounce-in-out"),
    )
    # Axes
    for x0, y0, x1, y1 in [(-1, 0, 1, 0), (0, -1, 0, 1)]:
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                      line=dict(color="rgba(150,150,150,0.4)", width=1))
    if phase_phasors and len(phase_phasors) >= 3:
        names = list(phase_phasors.keys())[:3]
        points = []
        for idx, nm in enumerate(names):
            ph = phase_phasors[nm]
            xr = ph.get("real", 0.0)
            yi = ph.get("imag", 0.0)
            color = _phase_color(nm, idx)
            points.append((nm, xr, yi, color))
            fig.add_trace(go.Scatter(
                x=[0.0, xr], y=[0.0, yi],
                mode="lines+markers",
                line=dict(color=color, width=3),
                marker=dict(size=[0, 8], color=color),
                name=f"Fase {nm[-1].upper() if nm else nm}",
            ))

        tri_x = [points[0][1], points[1][1], points[2][1], points[0][1]]
        tri_y = [points[0][2], points[1][2], points[2][2], points[0][2]]
        fig.add_trace(go.Scatter(
            x=tri_x, y=tri_y, mode="lines",
            line=dict(color="#ffffff", width=2),
            name="Triangulo",
        ))

        fig.add_trace(go.Scatter(
            x=[center_real], y=[center_imag], mode="markers+text",
            marker=dict(color="#A855F7", size=10),
            text=["Baricentro"], textposition="top center",
            textfont=dict(color="#A855F7", size=11),
            name="Baricentro",
        ))
    else:
        # Fallback arrow-only mode
        fig.add_annotation(
            ax=0, ay=0, x=center_real or 1e-30, y=center_imag or 1e-30,
            xref="x", yref="y", axref="x", ayref="y",
            arrowhead=2, arrowwidth=2, arrowcolor="#FF4B4B",
        )
        fig.add_trace(go.Scatter(
            x=[center_real], y=[center_imag],
            mode="markers+text",
            marker=dict(color="#FF4B4B", size=10),
            text=["Centro"], textposition="top right",
            textfont=dict(color="#FF4B4B", size=11),
            showlegend=False,
        ))
    return fig
