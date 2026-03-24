"""callbacks.py — All Dash callbacks for the COMTRADE Pro dashboard."""
from pathlib import Path
import numpy as np
from dash import Input, Output, State, callback, html, dcc, ALL, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from src.core.analysis.phasor_calculator import Phasor, PhasorCalculator
from src.core.analysis.rms_calculator import RMSCalculator
from src.core.analysis.symmetrical_components import SymmetricalComponents
from src.core.analysis.triangle_analyzer import TriangleAnalyzer
from src.ui.web.state import desktop_state

if __package__:
    from src.ui.pages.processing import process_comtrade_files
    from src.ui.pages.charts import (
        make_instantaneous_fig, make_rms_fig, make_phasor_fig,
        make_sequence_waveform_fig, make_sequence_phasors_fig,
        make_combined_seq_phasor_fig,
        make_barycenter_vector_fig,
    )
    from src.ui.pages.pages import (
        page_instantaneous, page_rms, page_phasors,
        page_sequence_components, page_seq_phasors,
        page_text_results, page_barycenter, page_no_file,
    )
else:
    from src.ui.pages.processing import process_comtrade_files
    from src.ui.pages.charts import (
        make_instantaneous_fig, make_rms_fig, make_phasor_fig,
        make_sequence_waveform_fig, make_sequence_phasors_fig,
        make_combined_seq_phasor_fig,
        make_barycenter_vector_fig,
    )
    from src.ui.pages.pages import (
        page_instantaneous, page_rms, page_phasors,
        page_sequence_components, page_seq_phasors,
        page_text_results, page_barycenter, page_no_file,
    )

_PAGE_MAP = {
    "instantaneous":  page_instantaneous,
    "rms":            page_rms,
    "phasors":        page_phasors,
    "sequence_comp":  page_sequence_components,
    "seq_phasors":    page_seq_phasors,
    "text_results":   page_text_results,
    "barycenter":     page_barycenter,
}


def _selected_names(selected, key: str, fallback: list[str]) -> list[str]:
    if not selected:
        return fallback
    values = selected.get(f"{key}_channels") or []
    return values or fallback


def _filter_by_names(data_dict: dict, names: list[str]) -> dict:
    if not names:
        return data_dict
    return {name: data_dict[name] for name in names if name in data_dict}


def _build_selection_message(data: dict | None, selected: dict | None):
    if not data:
        return html.Div("Sin archivo cargado.")

    warnings = list(data.get("warnings", []))
    suggestions = data.get("phase_group_suggestions", [])
    selected_voltage = _selected_names(selected, "voltage", [])
    selected_current = _selected_names(selected, "current", [])

    if selected_voltage and len(selected_voltage) != 3:
        warnings.append("Symmetrical component calculation requires 3-phase signals.")
    if selected_current and len(selected_current) != 3:
        warnings.append("Symmetrical component calculation requires 3-phase signals.")

    children = []
    if suggestions:
        suggestion_text = "; ".join(
            f"Possible 3-phase group detected: [{', '.join(item.get('channels', []))}]"
            for item in suggestions
        )
        children.append(html.Div(suggestion_text, style={"color": "#4B9EFF", "marginBottom": "4px"}))
    for warning in warnings:
        children.append(html.Div(warning, style={"color": "#FFB800", "marginBottom": "4px"}))
    if not children:
        children.append(html.Div("Selección lista para análisis.", style={"color": "#00FF88"}))
    return html.Div(children)


def _phasor_from_dict(data: dict, name: str) -> Phasor:
    return Phasor(
        magnitude=data.get("magnitude", 0.0),
        angle_deg=data.get("angle_deg", 0.0),
        angle_rad=float(np.radians(data.get("angle_deg", 0.0))),
        real=data.get("real", 0.0),
        imag=data.get("imag", 0.0),
        name=name,
    )


def _cursor_idx(time_ms_list: list, target_ms: float) -> int:
    """Return index of sample nearest to target_ms."""
    arr = np.array(time_ms_list, dtype=float)
    return int(np.argmin(np.abs(arr - target_ms)))


def _build_sequence_from_phasors(phasor_dict: dict, component_type: str) -> dict:
    if len(phasor_dict) < 3:
        return {}

    names = list(phasor_dict.keys())[:3]
    phasors = [_phasor_from_dict(phasor_dict[name], name) for name in names]
    symmetrical_components = SymmetricalComponents()
    sequence = symmetrical_components.calculate_sequence_components(
        phasors[0],
        phasors[1],
        phasors[2],
        component_type=component_type,
    )
    imbalance = sequence.get_imbalance_factors()
    return {
        "positive": {
            "magnitude": round(sequence.positive.magnitude, 3),
            "angle_deg": round(sequence.positive.angle_deg, 2),
            "real": round(sequence.positive.real, 3),
            "imag": round(sequence.positive.imag, 3),
        },
        "negative": {
            "magnitude": round(sequence.negative.magnitude, 3),
            "angle_deg": round(sequence.negative.angle_deg, 2),
            "real": round(sequence.negative.real, 3),
            "imag": round(sequence.negative.imag, 3),
        },
        "zero": {
            "magnitude": round(sequence.zero.magnitude, 3),
            "angle_deg": round(sequence.zero.angle_deg, 2),
            "real": round(sequence.zero.real, 3),
            "imag": round(sequence.zero.imag, 3),
        },
        "neg_imbalance_pct": round(imbalance.get("negative_imbalance", 0.0), 2),
        "zero_imbalance_pct": round(imbalance.get("zero_imbalance", 0.0), 2),
        "severity": symmetrical_components.calculate_unbalance_severity(sequence),
    }


def _require_three_phase_or_empty(signals: dict) -> tuple[bool, str]:
    if len(signals) != 3:
        return False, "Symmetrical component calculation requires 3-phase signals."
    return True, ""


def _phasors_from_cursor(
    signal_dict: dict,
    time_ms: list,
    cursor_ms: float | None,
    sampling_rate_hz: float,
    system_freq_hz: float,
) -> dict:
    """Compute per-phase phasors centered at cursor using one-cycle window."""
    if not signal_dict or not time_ms:
        return {}

    t_s = np.array(time_ms, dtype=float) / 1000.0
    if len(t_s) < 4:
        return {}

    calc = PhasorCalculator(system_frequency=float(system_freq_hz), sampling_rate=float(sampling_rate_hz))
    samples_per_cycle = max(4, int(round(float(sampling_rate_hz) / float(system_freq_hz))))

    if cursor_ms is None:
        center_idx = len(t_s) // 2
    else:
        center_idx = _cursor_idx(time_ms, float(cursor_ms))

    start = max(0, center_idx - samples_per_cycle // 2)
    end = min(len(t_s), start + samples_per_cycle)
    start = max(0, end - samples_per_cycle)

    if end - start < 4:
        return {}

    out = {}
    for name, vals in signal_dict.items():
        arr = np.array(vals, dtype=float)
        if len(arr) != len(t_s):
            n = min(len(arr), len(t_s))
            arr = arr[:n]
            t_local = t_s[:n]
            s = min(start, max(0, n - 4))
            e = min(n, max(s + 4, end))
            if e - s < 4:
                continue
            ph = calc.calculate_phasor(arr[s:e], t_local[s:e], name=name)
        else:
            ph = calc.calculate_phasor(arr[start:end], t_s[start:end], name=name)
        out[name] = {
            "magnitude": float(ph.magnitude),
            "angle_deg": float(ph.angle_deg),
            "real": float(ph.real),
            "imag": float(ph.imag),
            "name": name,
        }
    return out


def _sequence_rms_trends(signal_dict: dict, system_freq_hz: float, sampling_rate_hz: float) -> dict:
    """Compute RMS trends of sequence components V1/V2/V0 or I1/I2/I0 from 3-phase signals."""
    ok, _ = _require_three_phase_or_empty(signal_dict)
    if not ok:
        return {}

    names = list(signal_dict.keys())
    a = np.exp(1j * 2 * np.pi / 3)
    va = np.array(signal_dict[names[0]], dtype=float)
    vb = np.array(signal_dict[names[1]], dtype=float)
    vc = np.array(signal_dict[names[2]], dtype=float)
    n = min(len(va), len(vb), len(vc))
    if n < 8:
        return {}
    va = va[:n]
    vb = vb[:n]
    vc = vc[:n]

    seq0 = (va + vb + vc) / 3.0
    seq1 = (va + a * vb + (a ** 2) * vc) / 3.0
    seq2 = (va + (a ** 2) * vb + a * vc) / 3.0

    rms_calc = RMSCalculator(system_frequency=float(system_freq_hz), sampling_rate=float(sampling_rate_hz))
    return {
        "positive": rms_calc.calculate_sliding_rms(np.abs(seq1)).tolist(),
        "negative": rms_calc.calculate_sliding_rms(np.abs(seq2)).tolist(),
        "zero": rms_calc.calculate_sliding_rms(np.abs(seq0)).tolist(),
    }


def _detect_steady_state_region(time_ms: list, rms_channels: dict) -> tuple[int, int]:
    """Detect low-variation RMS segment as steady-state region."""
    if not time_ms or not rms_channels:
        return 0, 0
    arrays = [np.array(v, dtype=float) for v in rms_channels.values() if len(v) > 4]
    if not arrays:
        return 0, max(0, len(time_ms) - 1)
    min_len = min(len(a) for a in arrays)
    mat = np.vstack([a[:min_len] for a in arrays])
    mean_rms = np.mean(mat, axis=0)
    grad = np.abs(np.gradient(mean_rms))
    smooth = np.convolve(grad, np.ones(15) / 15.0, mode="same")
    thresh = np.percentile(smooth, 35)
    stable_mask = smooth <= thresh
    if not np.any(stable_mask):
        return 0, min_len - 1

    best_start = 0
    best_len = 1
    cur_start = None
    for i, flag in enumerate(stable_mask):
        if flag and cur_start is None:
            cur_start = i
        if (not flag or i == len(stable_mask) - 1) and cur_start is not None:
            end_i = i if not flag else i + 1
            seg_len = end_i - cur_start
            if seg_len > best_len:
                best_len = seg_len
                best_start = cur_start
            cur_start = None

    s = best_start
    e = min(min_len - 1, best_start + best_len - 1)
    return s, e


def _phasors_relative_to_phase_a(phasor_dict: dict) -> dict:
    """Re-reference phasor angles so phase A is 0 degrees."""
    if not phasor_dict:
        return phasor_dict
    names = list(phasor_dict.keys())
    a_name = next((n for n in names if n.upper().endswith("A") or "A" in n.upper()), names[0])
    ref = float(phasor_dict[a_name].get("angle_deg", 0.0))
    out = {}
    for n, ph in phasor_dict.items():
        ang = float(ph.get("angle_deg", 0.0)) - ref
        while ang > 180:
            ang -= 360
        while ang <= -180:
            ang += 360
        mag = float(ph.get("magnitude", 0.0))
        out[n] = {
            **ph,
            "angle_deg": ang,
            "real": float(mag * np.cos(np.radians(ang))),
            "imag": float(mag * np.sin(np.radians(ang))),
        }
    return out


def _voltage_reference_mode(meta: dict) -> str:
    return str((meta or {}).get("voltage_reference_mode", "unknown") or "unknown")


def _voltage_axis_label(mode: str, rms: bool = False) -> str:
    if rms:
        if mode == "line_to_line":
            return "Voltaje RMS Linea-Linea (V)"
        if mode == "line_to_neutral":
            return "Voltaje RMS Fase-Tierra (V)"
        if mode == "mixed":
            return "Voltaje RMS (V) [Mixto LL/LN]"
        return "Voltaje RMS (V)"
    if mode == "line_to_line":
        return "Voltaje Linea-Linea (V)"
    if mode == "line_to_neutral":
        return "Voltaje Fase-Tierra (V)"
    if mode == "mixed":
        return "Voltaje (V) [Mixto LL/LN]"
    return "Voltaje (V)"


def _extract_line_pair_token(name: str, data: dict) -> str | None:
    voltage_info = data.get("available_channels", {}).get("voltage", [])
    by_name = {item.get("name", ""): item for item in voltage_info}
    info = by_name.get(name, {})
    phase = "".join(ch for ch in str(info.get("phase", "")).upper() if ch.isalnum())
    clean_name = "".join(ch for ch in str(name).upper() if ch.isalnum())
    for src in (phase, clean_name):
        for pair in ("AB", "BC", "CA", "BA", "CB", "AC"):
            if src == pair or src.endswith(pair):
                return pair
    return None


def _convert_line_voltage_phasors_to_phase_equivalent(phasor_dict: dict, data: dict, tab_type: str) -> dict:
    if tab_type != "voltage" or len(phasor_dict) < 3:
        return phasor_dict

    line_map: dict[str, complex] = {}
    for name, ph in phasor_dict.items():
        pair = _extract_line_pair_token(name, data)
        if not pair:
            continue
        cval = complex(float(ph.get("real", 0.0)), float(ph.get("imag", 0.0)))
        if pair == "AB":
            line_map["AB"] = cval
        elif pair == "BC":
            line_map["BC"] = cval
        elif pair == "CA":
            line_map["CA"] = cval
        elif pair == "BA":
            line_map["AB"] = -cval
        elif pair == "CB":
            line_map["BC"] = -cval
        elif pair == "AC":
            line_map["CA"] = -cval

    if not all(key in line_map for key in ("AB", "BC", "CA")):
        return phasor_dict

    vab = line_map["AB"]
    vbc = line_map["BC"]
    vca = line_map["CA"]
    va = (vab - vca) / 3.0
    vb = (vbc - vab) / 3.0
    vc = (vca - vbc) / 3.0

    def _pack(value: complex, name: str) -> dict:
        return {
            "magnitude": float(np.abs(value)),
            "angle_deg": float(np.degrees(np.angle(value))),
            "real": float(value.real),
            "imag": float(value.imag),
            "name": name,
        }

    return {
        "VA(eq)": _pack(va, "VA(eq)"),
        "VB(eq)": _pack(vb, "VB(eq)"),
        "VC(eq)": _pack(vc, "VC(eq)"),
    }


def _convert_line_voltage_signals_to_phase_equivalent(signal_dict: dict, data: dict, tab_type: str) -> dict:
    if tab_type != "voltage" or len(signal_dict) < 3:
        return signal_dict

    line_map: dict[str, np.ndarray] = {}
    for name, vals in signal_dict.items():
        pair = _extract_line_pair_token(name, data)
        if not pair:
            continue
        arr = np.array(vals, dtype=float)
        if pair == "AB":
            line_map["AB"] = arr
        elif pair == "BC":
            line_map["BC"] = arr
        elif pair == "CA":
            line_map["CA"] = arr
        elif pair == "BA":
            line_map["AB"] = -arr
        elif pair == "CB":
            line_map["BC"] = -arr
        elif pair == "AC":
            line_map["CA"] = -arr

    if not all(key in line_map for key in ("AB", "BC", "CA")):
        return signal_dict

    n = min(len(line_map["AB"]), len(line_map["BC"]), len(line_map["CA"]))
    vab = line_map["AB"][:n]
    vbc = line_map["BC"][:n]
    vca = line_map["CA"][:n]

    va = (vab - vca) / 3.0
    vb = (vbc - vab) / 3.0
    vc = (vca - vbc) / 3.0
    return {
        "VA(eq)": va.tolist(),
        "VB(eq)": vb.tolist(),
        "VC(eq)": vc.tolist(),
    }

# ─── File upload → parse → store ────────────────────────────────────────────

@callback(
    Output("store-data",     "data"),
    Output("store-filename", "data"),
    Output("tb-filename",    "children"),
    Output("tb-status",      "children"),
    Output("tb-status",      "className"),
    Output("loaded-file-indicator", "children"),
    Input("upload-comtrade", "contents"),
    State("upload-comtrade", "filename"),
    prevent_initial_call=True,
)
def ingest_file(contents, filename):
    if not contents:
        return None, None, "—", "Listo", "tb-value accent-blue", html.Div()

    result = process_comtrade_files(contents, filename)

    # When multiple=True, filename is a list; get a display name from it
    if isinstance(filename, list):
        display_name = ", ".join(filename)
        primary_name = next(
            (f for f in filename if Path(f).suffix.lower() in (".cfg", ".zip")),
            filename[0],
        )
    else:
        display_name = primary_name = filename or "—"

    if "error" in result:
        indicator = html.Div([
            html.Span("✗ ", style={"color": "#FF4B4B"}),
            html.Span(display_name, style={"color": "#FF4B4B", "fontWeight": "500"}),
            html.Div(result["error"], style={"color": "#FF4B4B", "fontSize": "11px"}),
        ], className="file-indicator-content")
        return None, None, display_name, "Error", "tb-value accent-red", indicator

    meta = result.get("metadata", {})
    freq_txt = f"{meta.get('system_freq_hz', 60)} Hz"
    vref_txt = str(meta.get("voltage_reference_label", "Desconocido"))
    indicator = html.Div([
        html.Span("● ", style={"color": "#00FF88"}),
        html.Span(display_name, style={"color": "#e0e0e0", "fontWeight": "500"}),
        html.Div(f"Cargado • {freq_txt} • {vref_txt}", style={"color": "#888", "fontSize": "11px"}),
    ], className="file-indicator-content")

    return result, primary_name, display_name, "Procesado", "tb-value accent-green", indicator


@callback(
    Output("store-data", "data", allow_duplicate=True),
    Output("store-filename", "data", allow_duplicate=True),
    Output("tb-filename", "children", allow_duplicate=True),
    Output("tb-status", "children", allow_duplicate=True),
    Output("tb-status", "className", allow_duplicate=True),
    Output("loaded-file-indicator", "children", allow_duplicate=True),
    Output("store-sync-token", "data"),
    Input("desktop-sync-interval", "n_intervals"),
    State("store-sync-token", "data"),
    prevent_initial_call="initial_duplicate",
)
def sync_desktop_selection(_n_intervals, current_revision):
    snapshot = desktop_state.get_snapshot()
    revision = snapshot.get("revision", 0)
    if not revision or revision == current_revision:
        raise PreventUpdate

    result = snapshot.get("analysis") or {}
    display_name = snapshot.get("display_name") or "—"
    source_path = snapshot.get("source_path") or display_name

    if result.get("error"):
        indicator = html.Div([
            html.Span("✗ ", style={"color": "#FF4B4B"}),
            html.Span(display_name, style={"color": "#FF4B4B", "fontWeight": "500"}),
            html.Div(result["error"], style={"color": "#FF4B4B", "fontSize": "11px"}),
        ], className="file-indicator-content")
        return None, source_path, display_name, "Error", "tb-value accent-red", indicator, revision

    meta = result.get("metadata", {})
    freq_txt = f"{meta.get('system_freq_hz', 60)} Hz"
    vref_txt = str(meta.get("voltage_reference_label", "Desconocido"))
    indicator = html.Div([
        html.Span("● ", style={"color": "#00FF88"}),
        html.Span(display_name, style={"color": "#e0e0e0", "fontWeight": "500"}),
        html.Div(f"Cargado • {freq_txt} • {vref_txt}", style={"color": "#888", "fontSize": "11px"}),
    ], className="file-indicator-content")
    return result, source_path, display_name, "Procesado", "tb-value accent-green", indicator, revision


@callback(
    Output("select-voltage-channels", "options"),
    Output("select-voltage-channels", "value"),
    Output("select-current-channels", "options"),
    Output("select-current-channels", "value"),
    Output("tb-freq", "children"),
    Input("store-data", "data"),
    prevent_initial_call=False,
)
def populate_channel_selectors(data):
    if not data:
        return [], [], [], [], "60 Hz"

    voltage_channels = data.get("available_channels", {}).get("voltage", [])
    current_channels = data.get("available_channels", {}).get("current", [])
    selected = data.get("selected_signals", {})
    voltage_options = [{"label": item.get("name", "—"), "value": item.get("name", "")} for item in voltage_channels]
    current_options = [{"label": item.get("name", "—"), "value": item.get("name", "")} for item in current_channels]
    freq_text = f"{data.get('metadata', {}).get('system_freq_hz', 60)} Hz"
    return (
        voltage_options,
        selected.get("voltage_channels", []),
        current_options,
        selected.get("current_channels", []),
        freq_text,
    )


@callback(
    Output("store-selected-signals", "data"),
    Output("channel-selection-message", "children"),
    Input("select-voltage-channels", "value"),
    Input("select-current-channels", "value"),
    Input("store-data", "data"),
    prevent_initial_call=False,
)
def update_selected_signals(voltage_values, current_values, data):
    if not data:
        return None, html.Div("Sin archivo cargado.")

    selected = {
        "voltage_channels": voltage_values or data.get("selected_signals", {}).get("voltage_channels", []),
        "current_channels": current_values or data.get("selected_signals", {}).get("current_channels", []),
    }
    return selected, _build_selection_message(data, selected)


# ─── Navigation → render page content ────────────────────────────────────────

@callback(
    Output("page-content", "children"),
    Input({"type": "nav-btn", "page": ALL}, "n_clicks"),
    State("store-data", "data"),
    State("store-tab-type", "data"),
    prevent_initial_call=False,
)
def navigate(n_clicks_list, data, stored_type):
    triggered = ctx.triggered_id
    default_type = stored_type or "voltage"
    if triggered is None or not isinstance(triggered, dict):
        return page_instantaneous(default_type=default_type) if data else page_no_file()

    page_id = triggered.get("page", "instantaneous")
    builder = _PAGE_MAP.get(page_id, page_no_file)
    if page_id in ("instantaneous", "rms", "phasors", "sequence_comp", "seq_phasors"):
        return builder(default_type=default_type)
    return builder()


# ─── Active nav button highlighting ─────────────────────────────────────────

@callback(
    Output({"type": "nav-btn", "page": ALL}, "className"),
    Input({"type": "nav-btn", "page": ALL}, "n_clicks"),
    prevent_initial_call=False,
)
def highlight_nav(n_clicks_list):
    triggered = ctx.triggered_id
    pages = [
        "instantaneous", "rms", "phasors",
        "sequence_comp", "seq_phasors", "text_results", "barycenter",
    ]
    active_page = triggered.get("page") if triggered and isinstance(triggered, dict) else None
    return [
        "nav-item active" if p == active_page else "nav-item"
        for p in pages
    ]


@callback(
    Output("global-time-card", "style"),
    Input({"type": "nav-btn", "page": ALL}, "n_clicks"),
    Input("store-data", "data"),
    prevent_initial_call=False,
)
def toggle_global_graph_visibility(n_clicks_list, data):
    base_style = {"marginBottom": "16px", "padding": "14px 16px"}
    if not data:
        return {**base_style, "display": "none"}

    triggered = ctx.triggered_id
    if triggered is None or not isinstance(triggered, dict):
        active_page = "instantaneous"
    else:
        active_page = triggered.get("page", "instantaneous")

    if active_page in ("instantaneous", "rms", "sequence_comp", "text_results"):
        return {**base_style, "display": "none"}
    return {**base_style, "display": "block"}


# ─── Tab-type sync (persist V/I selection across page changes) ───────────────

@callback(
    Output("store-tab-type", "data"),
    Input("global-tab-type",  "value"),
    prevent_initial_call=True,
)
def save_tab_type(v_global):
    if ctx.triggered:
        return ctx.triggered[0]["value"]
    raise PreventUpdate


@callback(
    Output("global-tab-type", "value"),
    Input("store-tab-type", "data"),
    prevent_initial_call=False,
)
def sync_global_type_control(tab_type):
    return tab_type or "voltage"


# ─── Cursor Play/Pause controls ─────────────────────────────────────────────

@callback(
    Output("store-cursor-play", "data"),
    Output("btn-cursor-play-toggle", "children"),
    Output("btn-cursor-play-toggle", "className"),
    Output("btn-cursor-play-toggle", "disabled"),
    Input("btn-cursor-play-toggle", "n_clicks"),
    Input("store-data", "data"),
    State("store-cursor-play", "data"),
    prevent_initial_call=False,
)
def toggle_cursor_play(_n_clicks, data, playing_state):
    time_ms = (data or {}).get("time_ms", []) if data else []
    has_data = bool(time_ms)
    if not has_data:
        return False, "▶ Play Cursor", "btn-secondary", True

    playing = bool(playing_state) if playing_state is not None else False
    if ctx.triggered_id == "btn-cursor-play-toggle":
        playing = not playing

    if playing:
        return True, "⏸ Pausar Cursor", "btn-secondary", False
    return False, "▶ Play Cursor", "btn-secondary", False


@callback(
    Output("cursor-play-interval", "disabled"),
    Output("cursor-play-interval", "interval"),
    Output("cursor-play-badge", "children"),
    Input("store-cursor-play", "data"),
    Input("cursor-play-fps", "value"),
    prevent_initial_call=False,
)
def configure_cursor_interval(playing_state, fps_value):
    fps = int(fps_value or 8)
    fps = max(1, fps)
    interval_ms = int(round(1000.0 / fps))
    playing = bool(playing_state)
    return (not playing), interval_ms, ("PLAY" if playing else "PAUSA")


@callback(
    Output("store-cursor-ms", "data", allow_duplicate=True),
    Input("cursor-play-interval", "n_intervals"),
    State("store-cursor-play", "data"),
    State("store-data", "data"),
    State("store-cursor-ms", "data"),
    State("cursor-play-step", "value"),
    prevent_initial_call=True,
)
def autoplay_cursor(_n_intervals, playing_state, data, cursor_ms, step_value):
    if not playing_state or not data:
        raise PreventUpdate

    time_ms = np.array(data.get("time_ms", []), dtype=float)
    if len(time_ms) == 0:
        raise PreventUpdate

    step = int(step_value or 1)
    step = max(1, step)

    if cursor_ms is None:
        idx = 0
    else:
        idx = _cursor_idx(time_ms.tolist(), float(cursor_ms))

    next_idx = (idx + step) % len(time_ms)
    return float(time_ms[next_idx])


# ─── Cursor: save position from any time-domain graph ────────────────────────

@callback(
    Output("store-cursor-ms", "data", allow_duplicate=True),
    Input("graph-instantaneous", "clickData"),
    prevent_initial_call=True,
)
def cursor_from_inst(click_data):
    if click_data and click_data.get("points"):
        x = click_data["points"][0].get("x")
        if x is not None:
            return x
    raise PreventUpdate


@callback(
    Output("store-cursor-ms", "data", allow_duplicate=True),
    Input("graph-rms", "clickData"),
    prevent_initial_call=True,
)
def cursor_from_rms_click(click_data):
    if click_data and click_data.get("points"):
        x = click_data["points"][0].get("x")
        if x is not None:
            return x
    raise PreventUpdate


@callback(
    Output("store-cursor-ms", "data", allow_duplicate=True),
    Input("graph-sequence-wave", "clickData"),
    prevent_initial_call=True,
)
def cursor_from_seq_wave(click_data):
    if click_data and click_data.get("points"):
        x = click_data["points"][0].get("x")
        if x is not None:
            return x
    raise PreventUpdate


@callback(
    Output("store-cursor-ms", "data", allow_duplicate=True),
    Input("graph-global-time", "clickData"),
    prevent_initial_call=True,
)
def cursor_from_global(click_data):
    if click_data and click_data.get("points"):
        x = click_data["points"][0].get("x")
        if x is not None:
            return x
    raise PreventUpdate


@callback(
    Output("store-cursor-ms", "data"),
    Input("store-data", "data"),
    State("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def init_cursor_on_load(data, existing_cursor):
    if not data:
        return None
    time_ms = data.get("time_ms", [])
    if not time_ms:
        raise PreventUpdate
    if existing_cursor is None:
        return float(time_ms[0])
    return existing_cursor


@callback(
    Output("graph-global-time", "figure"),
    Input("store-data", "data"),
    Input("store-selected-signals", "data"),
    Input("store-tab-type", "data"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_global_time_graph(data, selected, tab_type, cursor_ms):
    if not data:
        return make_instantaneous_fig([], {}, y_label="Señal Filtrada")
    tab = tab_type or "voltage"
    sig_dict = data.get("voltages", {}) if tab == "voltage" else data.get("currents", {})
    names = _selected_names(selected, "voltage" if tab == "voltage" else "current", list(sig_dict.keys()))
    sig_dict = _filter_by_names(sig_dict, names)
    y_label = "Voltaje Filtrado (V)" if tab == "voltage" else "Corriente Filtrada (A)"
    ui_token = f"global-{data.get('analysis_id', 'na')}-{tab}"
    return make_instantaneous_fig(
        data.get("time_ms", []),
        sig_dict,
        y_label=y_label,
        cursor_ms=cursor_ms,
        uirevision=ui_token,
    )


# ─── Cursor: top-bar time display ─────────────────────────────────────────────

@callback(
    Output("tb-cursor-time", "children"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_tb_cursor(cursor_ms):
    if cursor_ms is None:
        return "— ms"
    return f"{float(cursor_ms):.3f} ms"


# ─── Cursor: value readouts for each time-domain page ────────────────────────

@callback(
    Output("cursor-time-inst",   "children"),
    Output("cursor-values-inst", "children"),
    Input("store-cursor-ms",  "data"),
    Input("inst-tab-type",    "value"),
    State("store-data",             "data"),
    State("store-selected-signals", "data"),
    prevent_initial_call=False,
)
def update_cursor_inst_display(cursor_ms, tab_type, data, selected):
    if cursor_ms is None or not data:
        return "— ms", []
    time_ms = data.get("time_ms", [])
    if not time_ms:
        return "— ms", []
    idx = _cursor_idx(time_ms, float(cursor_ms))
    actual_ms = time_ms[idx]
    tab = tab_type or "voltage"
    signals = data["voltages"] if tab == "voltage" else data["currents"]
    names = _selected_names(selected, "voltage" if tab == "voltage" else "current", list(signals.keys()))
    signals = _filter_by_names(signals, names)
    unit = "V" if tab == "voltage" else "A"
    phase_colors = {"A": "#FF4B4B", "B": "#FFB800", "C": "#4B9EFF"}
    spans = []
    for nm, vals in signals.items():
        arr = np.array(vals)
        val = float(arr[idx]) if idx < len(arr) else 0.0
        label = nm[-1].upper() if nm else nm
        color = phase_colors.get(label, "#e0e0e0")
        spans.append(html.Span([
            html.Span(f"{nm}: ", style={"color": "#666", "fontSize": "11px"}),
            html.Span(f"{val:.2f} {unit}", style={"color": color, "fontWeight": "600"}),
        ], style={"whiteSpace": "nowrap"}))
    return f"{actual_ms:.3f} ms", spans


@callback(
    Output("cursor-time-rms",   "children"),
    Output("cursor-values-rms", "children"),
    Input("store-cursor-ms", "data"),
    Input("rms-tab-type",    "value"),
    State("store-data",             "data"),
    State("store-selected-signals", "data"),
    prevent_initial_call=False,
)
def update_cursor_rms_display(cursor_ms, tab_type, data, selected):
    if cursor_ms is None or not data:
        return "— ms", []
    time_ms = data.get("time_ms", [])
    if not time_ms:
        return "— ms", []
    idx = _cursor_idx(time_ms, float(cursor_ms))
    actual_ms = time_ms[idx]
    tab = tab_type or "voltage"
    rms_dict = data["rms_v"] if tab == "voltage" else data["rms_i"]
    names = _selected_names(selected, "voltage" if tab == "voltage" else "current", list(rms_dict.keys()))
    rms_dict = _filter_by_names(rms_dict, names)
    unit = "V" if tab == "voltage" else "A"
    phase_colors = {"A": "#FF4B4B", "B": "#FFB800", "C": "#4B9EFF"}
    spans = []
    for nm, vals in rms_dict.items():
        arr = np.array(vals)
        val = float(arr[idx]) if idx < len(arr) else 0.0
        label = nm[-1].upper() if nm else nm
        color = phase_colors.get(label, "#e0e0e0")
        spans.append(html.Span([
            html.Span(f"{nm}: ", style={"color": "#666", "fontSize": "11px"}),
            html.Span(f"{val:.2f} {unit} RMS", style={"color": color, "fontWeight": "600"}),
        ], style={"whiteSpace": "nowrap"}))
    return f"{actual_ms:.3f} ms", spans


@callback(
    Output("cursor-time-seq", "children"),
    Input("store-cursor-ms",  "data"),
    prevent_initial_call=False,
)
def update_cursor_seq_display(cursor_ms):
    if cursor_ms is None:
        return "— ms"
    return f"{float(cursor_ms):.3f} ms"


# ─── Instantaneous waveforms ─────────────────────────────────────────────────

@callback(
    Output("graph-instantaneous", "figure"),
    Output("inst-stat-row", "children"),
    Input("inst-tab-type", "value"),
    Input("store-data", "data"),
    Input("store-selected-signals", "data"),
    Input("store-cursor-ms", "data"),
    State("inst-show-raw", "value"),
    prevent_initial_call=False,
)
def update_instantaneous(tab_type, data, selected, cursor_ms, show_raw):
    if __package__:
        from src.ui.pages.pages import _stat_card
    else:
        from src.ui.pages.pages import _stat_card
    if not data:
        return make_instantaneous_fig([], {}), []

    time_ms = data["time_ms"]
    signals = data["voltages"] if tab_type == "voltage" else data["currents"]
    names = _selected_names(selected, "voltage" if tab_type == "voltage" else "current", list(signals.keys()))
    signals = _filter_by_names(signals, names)
    mode = _voltage_reference_mode(data.get("metadata", {}))
    y_label = _voltage_axis_label(mode, rms=False) if tab_type == "voltage" else "Corriente (A)"

    raw_signals_dict = None
    if show_raw and "show" in (show_raw or []):
        raw_key = "voltages_raw" if (tab_type or "voltage") == "voltage" else "currents_raw"
        raw_data = data.get(raw_key, {})
        raw_signals_dict = _filter_by_names(raw_data, names)

    fig = make_instantaneous_fig(
        time_ms, signals, y_label,
        raw_signals=raw_signals_dict,
        cursor_ms=cursor_ms,
    )

    meta = data.get("metadata", {})
    stats = [
        _stat_card("Muestras Totales",      str(meta.get("total_samples", "—"))),
        _stat_card("Muestras Graficadas",   str(meta.get("plot_sample_count", len(time_ms)))),
        _stat_card("Frecuencia de Muestreo", str(meta.get("sampling_rate_hz", "—")), "Hz"),
        _stat_card("Referencia de Voltaje", str(meta.get("voltage_reference_label", "—"))),
        _stat_card("Duración",               str(meta.get("duration_s", "—")), "s"),
    ]
    return fig, stats


# ─── RMS view ────────────────────────────────────────────────────────────────

@callback(
    Output("graph-rms", "figure"),
    Output("rms-phase-cards", "children"),
    Input("rms-tab-type", "value"),
    Input("store-data", "data"),
    Input("store-selected-signals", "data"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_rms(tab_type, data, selected, cursor_ms):
    if not data:
        return make_rms_fig([], {}), []

    time_ms = data["time_ms"]
    rms_dict = data["rms_v"] if tab_type == "voltage" else data["rms_i"]
    names = _selected_names(selected, "voltage" if tab_type == "voltage" else "current", list(rms_dict.keys()))
    rms_dict = _filter_by_names(rms_dict, names)
    mode = _voltage_reference_mode(data.get("metadata", {}))
    y_label  = _voltage_axis_label(mode, rms=True) if tab_type == "voltage" else "Corriente RMS (A)"
    unit     = "V" if tab_type == "voltage" else "A"
    fig = make_rms_fig(time_ms, rms_dict, y_label, cursor_ms=cursor_ms)

    # Phase summary cards: pre-fault / post vs max
    phase_colors = {"A": "#FF4B4B", "B": "#FFB800", "C": "#4B9EFF"}
    cards = []
    for nm, vals in rms_dict.items():
        arr = np.array(vals)
        if len(arr) == 0:
            continue
        n = len(arr)
        pre  = float(np.mean(arr[:n // 4]))   if n >= 4 else float(arr[0])
        post = float(np.mean(arr[3 * n // 4:])) if n >= 4 else float(arr[-1])
        mx   = float(np.max(arr))
        chg  = ((post - pre) / pre * 100) if pre != 0 else 0.0
        sign = "+" if chg >= 0 else ""
        label = nm[-1].upper() if nm else nm
        color = phase_colors.get(label, "#e0e0e0")
        cards.append(html.Div(className="phase-card", children=[
            html.Div([html.Span("● ", style={"color": color}),
                      html.Span(f"Fase {label}", className="phase-card-title")]),
            html.Div([html.Span("Pre-falla:",  className="pc-lbl"),
                      html.Span(f"{pre:.2f} {unit}", className="pc-val")]),
            html.Div([html.Span("Post-falla:", className="pc-lbl"),
                      html.Span(f"{post:.2f} {unit}", className="pc-val")]),
            html.Div([html.Span("Cambio:",     className="pc-lbl"),
                      html.Span(f"{sign}{chg:.1f}%",
                                style={"color": "#FF4B4B" if chg > 5 else
                                               "#00FF88" if chg < -5 else "#FFB800",
                                       "fontWeight": "600"})]),
            html.Div([html.Span("Máximo:",     className="pc-lbl"),
                      html.Span(f"{mx:.2f} {unit}", className="pc-val")]),
        ]))
    return fig, cards


# ─── Phase phasors ──────────────────────────────────────────────────────────

@callback(
    Output("graph-phasors",       "figure"),
    Output("phasor-values-panel", "children"),
    Input("phasor-tab-type", "value"),
    Input("store-data", "data"),
    Input("store-selected-signals", "data"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_phasors(tab_type, data, selected, cursor_ms):
    if not data:
        return make_phasor_fig({}), html.Div("Carga un archivo")

    ph_static = data.get("phasors_v_all", {}) if tab_type == "voltage" else data.get("phasors_i_all", {})
    sig_dict = data.get("voltages", {}) if tab_type == "voltage" else data.get("currents", {})
    names = _selected_names(selected, "voltage" if tab_type == "voltage" else "current", list(ph_static.keys()))
    sig_dict = _filter_by_names(sig_dict, names)
    ph_dict = _phasors_from_cursor(
        sig_dict,
        data.get("time_ms", []),
        cursor_ms,
        float(data.get("metadata", {}).get("sampling_rate_hz", 1.0)),
        float(data.get("metadata", {}).get("system_freq_hz", 60.0)),
    )
    if not ph_dict:
        ph_dict = _filter_by_names(ph_static, names)
    ph_dict = _phasors_relative_to_phase_a(ph_dict)
    unit   = "V" if tab_type == "voltage" else "A"
    if tab_type == "voltage":
        mode = _voltage_reference_mode(data.get("metadata", {}))
        mode_lbl = {
            "line_to_line": "LL",
            "line_to_neutral": "LN",
            "mixed": "Mixto",
            "unknown": "Desconocido",
        }.get(mode, "Desconocido")
        title = f"Fasores de Fase ({mode_lbl})"
        if cursor_ms is not None:
            title += f" • t = {float(cursor_ms):.3f} ms"
        fig = make_phasor_fig(ph_dict, title=title)
    else:
        title = "Fasores de Fase (Corriente)"
        if cursor_ms is not None:
            title += f" • t = {float(cursor_ms):.3f} ms"
        fig = make_phasor_fig(ph_dict, title=title)

    phase_colors = {"A": "#FF4B4B", "B": "#FFB800", "C": "#4B9EFF"}
    cards = []
    ph_list = list(ph_dict.values())
    for i, (nm, ph) in enumerate(ph_dict.items()):
        label = nm[-1].upper() if nm else nm
        color = phase_colors.get(label, "#e0e0e0")
        lead_lag = "Leading" if ph["angle_deg"] > 0 else "Lagging"
        cards.append(html.Div(className="phasor-val-card", children=[
            html.Div([html.Span("● ", style={"color": color}),
                      html.Span(f"Fase {label}", className="pv-title")]),
            html.Div(className="pv-grid", children=[
                html.Span("Magnitud", className="pv-lbl"),
                html.Span(f"{ph['magnitude']:.2f}", className="pv-val"),
                html.Span(unit, className="pv-unit"),
                html.Span("Ángulo", className="pv-lbl"),
                html.Span(f"{ph['angle_deg']:.2f}°", className="pv-val"),
                html.Span(lead_lag, className="pv-unit",
                          style={"color": "#888", "fontSize": "10px"}),
            ]),
            html.Div(f"Forma Polar: {ph['magnitude']:.2f} ∠ {ph['angle_deg']:.2f}°",
                     className="pv-polar", style={"color": "#4B9EFF"}),
            html.Div(
                f"Forma Rectangular: {ph['real']:.2f} + j{ph['imag']:.2f}",
                className="pv-rect", style={"color": "#00FF88"},
            ),
        ]))

    # Phase differences (A–B, B–C, C–A)
    if len(ph_list) >= 3:
        diff_section = _phase_diff_panel(ph_list)
        return fig, html.Div([*cards, diff_section])

    return fig, html.Div(cards)


def _phase_diff_panel(ph_list):
    pairs = [("A–B", 0, 1), ("B–C", 1, 2), ("C–A", 2, 0)]
    rows = []
    for label, i, j in pairs:
        if i < len(ph_list) and j < len(ph_list):
            diff = ph_list[i]["angle_deg"] - ph_list[j]["angle_deg"]
            rows.append(html.Div(className="pdiff-row", children=[
                html.Span(label, className="pdiff-lbl"),
                html.Span(f"{diff:.2f}°", className="pdiff-val"),
            ]))
    return html.Div(className="pdiff-panel", children=[
        html.Div("Diferencias de Fase", className="pdiff-title"),
        *rows,
    ])


# ─── Sequence component waveforms ────────────────────────────────────────────

@callback(
    Output("graph-sequence-wave", "figure"),
    Output("seq-cards",           "children"),
    Output("seq-interpretation",  "children"),
    Input("seq-tab-type", "value"),
    Input("store-data",   "data"),
    Input("store-selected-signals", "data"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_sequence(tab_type, data, selected, cursor_ms):
    if not data:
        return make_sequence_waveform_fig([], {}, {}), [], html.Div()

    signal_key = "voltages" if tab_type == "voltage" else "currents"
    sigs_all = data.get(signal_key, {})
    ph_dict = data.get("phasors_v_all", {}) if tab_type == "voltage" else data.get("phasors_i_all", {})
    names = _selected_names(selected, "voltage" if tab_type == "voltage" else "current", list(ph_dict.keys()))
    sigs = _filter_by_names(sigs_all, names)
    ok, warn = _require_three_phase_or_empty(sigs)
    ui_token = f"seq-wave-{data.get('analysis_id', 'na')}-{tab_type or 'voltage'}"

    if not ok:
        warning = html.Div(warn, style={"color": "#FFB800"})
        return make_sequence_waveform_fig(
            data.get("time_ms", []),
            {},
            sigs,
            system_freq=data.get("metadata", {}).get("system_freq_hz", 60.0),
            cursor_ms=cursor_ms,
            uirevision=ui_token,
        ), [], warning

    dyn_phase_ph = _phasors_from_cursor(
        sigs,
        data.get("time_ms", []),
        cursor_ms,
        float(data.get("metadata", {}).get("sampling_rate_hz", 1.0)),
        float(data.get("metadata", {}).get("system_freq_hz", 60.0)),
    )
    if dyn_phase_ph:
        ph_dict = dyn_phase_ph
    else:
        ph_dict = _filter_by_names(ph_dict, names)

    mode = _voltage_reference_mode(data.get("metadata", {}))
    seq_input_ph = ph_dict
    seq_input_sig = sigs
    if tab_type == "voltage" and mode == "line_to_line":
        seq_input_ph = _convert_line_voltage_phasors_to_phase_equivalent(ph_dict, data, tab_type)
        seq_input_sig = _convert_line_voltage_signals_to_phase_equivalent(sigs, data, tab_type)

    seq = _build_sequence_from_phasors(seq_input_ph, "voltage" if tab_type == "voltage" else "current")
    meta  = data.get("metadata", {})
    freq  = meta.get("system_freq_hz", 60.0)
    fs_hz = meta.get("sampling_rate_hz", 1.0)
    unit  = "V" if tab_type == "voltage" else "A"
    t     = data["time_ms"]
    seq_rms = _sequence_rms_trends(seq_input_sig, float(freq), float(fs_hz))

    if not seq:
        warning = html.Div("Symmetrical component calculation requires 3-phase signals.", style={"color": "#FFB800"})
        return make_sequence_waveform_fig(
            t,
            {},
            sigs,
            system_freq=freq,
            cursor_ms=cursor_ms,
            seq_rms=seq_rms,
            y_label=("Voltaje RMS (V)" if tab_type == "voltage" else "Corriente RMS (A)"),
            uirevision=ui_token,
        ), [], warning

    fig = make_sequence_waveform_fig(
        t,
        seq,
        sigs,
        system_freq=freq,
        cursor_ms=cursor_ms,
        seq_rms=seq_rms,
        y_label=(_voltage_axis_label(mode, rms=True) if tab_type == "voltage" else "Corriente RMS (A)"),
        uirevision=ui_token,
    )

    total = (seq.get("positive", {}).get("magnitude", 0) +
             seq.get("negative", {}).get("magnitude", 0) +
             seq.get("zero",     {}).get("magnitude", 0))

    def _pct(key):
        mag = seq.get(key, {}).get("magnitude", 0)
        return round(mag / total * 100, 1) if total > 0 else 0.0

    neg_pct  = seq.get("neg_imbalance_pct",  0.0)
    zero_pct = seq.get("zero_imbalance_pct", 0.0)
    severity = seq.get("severity", "—")

    colors = {"positive": "#00FF88", "negative": "#FF6B35", "zero": "#CC44FF"}
    labels = {"positive": "SECUENCIA POSITIVA",
              "negative": "SECUENCIA NEGATIVA",
              "zero":     "SECUENCIA CERO"}
    cards = []
    for key in ["positive", "negative", "zero"]:
        ph   = seq.get(key, {})
        mag  = ph.get("magnitude", 0)
        pct  = _pct(key)
        color = colors[key]
        cards.append(html.Div(className="seq-card", style={"borderColor": color}, children=[
            html.Div(className="seq-card-header",
                     style={"backgroundColor": f"{color}22"}, children=[
                html.Span("● ", style={"color": color}),
                html.Span(labels[key], className="seq-card-title", style={"color": color}),
            ]),
            html.Div(f"{mag:.2f}", className="seq-card-value", style={"color": color}),
            html.Div(f"{unit} RMS", className="seq-card-unit"),
            html.Div(f"{pct}% del total", className="seq-card-pct",
                     style={"color": "#888"}),
        ]))

    # Desbalance card
    sev_color = "#FF4B4B" if severity in ("Severe", "Moderate") else "#FFB800"
    cards.append(html.Div(className="seq-card", children=[
        html.Div("DESBALANCE", className="seq-card-title",
                 style={"color": "#e0e0e0", "padding": "8px"}),
        html.Div(f"{neg_pct:.2f}%", className="seq-card-value"),
        html.Div("Negativa / Positiva", className="seq-card-unit"),
        html.Div(f"{severity}", style={"color": sev_color, "fontWeight": "600",
                                       "padding": "4px 8px"}),
    ]))

    interp = html.Div([
        html.H4("Interpretación de Componentes Simétricas",
                className="interp-title"),
        html.Div(
            "Referencia de voltaje detectada: LL (conversion a fase equivalente para calculos)"
            if tab_type == "voltage" and mode == "line_to_line"
            else "Referencia de voltaje detectada: LN"
            if tab_type == "voltage" and mode == "line_to_neutral"
            else "Referencia de voltaje detectada: Mixta LL/LN"
            if tab_type == "voltage" and mode == "mixed"
            else "Referencia de voltaje: no aplica para corrientes"
            if tab_type != "voltage"
            else "Referencia de voltaje detectada: Desconocida",
            style={"color": "#4B9EFF", "marginBottom": "10px"},
        ),
        html.Div(className="interp-grid", children=[
            html.Div([
                html.Span("● ", style={"color": "#00FF88"}),
                html.Strong("Secuencia Positiva"),
                html.P("Representa el sistema balanceado normal. Rota en sentido ABC (horario). "
                       "Indica la magnitud de operación normal del sistema."),
            ]),
            html.Div([
                html.Span("● ", style={"color": "#FF6B35"}),
                html.Strong("Secuencia Negativa"),
                html.P("Indica desbalance del sistema. Rota en sentido ACB (antihorario). "
                       "Presente en fallas asimétricas y condiciones anormales."),
            ]),
            html.Div([
                html.Span("● ", style={"color": "#CC44FF"}),
                html.Strong("Secuencia Cero"),
                html.P("Todas las fases en fase. Indica falla a tierra; puede circular si "
                       "existe camino de retorno por tierra."),
            ]),
        ]),
    ])

    return fig, cards, interp


# ─── Sequence phasors ───────────────────────────────────────────────────────

@callback(
    Output("graph-seq-phasors-3", "figure"),
    Output("graph-seq-combined",  "figure"),
    Output("seq-summary-table",   "children"),
    Input("seq-ph-tab-type", "value"),
    Input("store-data",      "data"),
    Input("store-selected-signals", "data"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_seq_phasors(tab_type, data, selected, cursor_ms):
    empty_3 = make_sequence_phasors_fig({})
    empty_c = make_combined_seq_phasor_fig({})
    if not data:
        return empty_3, empty_c, html.Div()

    ph_dict = data.get("phasors_v_all", {}) if tab_type == "voltage" else data.get("phasors_i_all", {})
    signal_key = "voltages" if tab_type == "voltage" else "currents"
    sigs = data.get(signal_key, {})
    names = _selected_names(selected, "voltage" if tab_type == "voltage" else "current", list(ph_dict.keys()))
    sigs = _filter_by_names(sigs, names)
    dyn_ph = _phasors_from_cursor(
        sigs,
        data.get("time_ms", []),
        cursor_ms,
        float(data.get("metadata", {}).get("sampling_rate_hz", 1.0)),
        float(data.get("metadata", {}).get("system_freq_hz", 60.0)),
    )
    if dyn_ph:
        ph_dict = dyn_ph
    else:
        ph_dict = _filter_by_names(ph_dict, names)
    ph_dict = _phasors_relative_to_phase_a(ph_dict)
    mode = _voltage_reference_mode(data.get("metadata", {}))
    seq_input_ph = ph_dict
    if tab_type == "voltage" and mode == "line_to_line":
        seq_input_ph = _convert_line_voltage_phasors_to_phase_equivalent(ph_dict, data, tab_type)

    seq = _build_sequence_from_phasors(seq_input_ph, "voltage" if tab_type == "voltage" else "current")
    if not seq:
        return empty_3, empty_c, html.Div("Symmetrical component calculation requires 3-phase signals.", style={"color": "#FFB800"})

    fig3  = make_sequence_phasors_fig(seq)
    figc  = make_combined_seq_phasor_fig(seq)
    time_tag = f"t = {float(cursor_ms):.3f} ms" if cursor_ms is not None else "t = —"
    fig3.update_layout(title=dict(text=f"Fasores de Secuencia (3 planos) • {time_tag}", x=0.5))
    figc.update_layout(title=dict(text=f"Fasores de Secuencia (combinado) • {time_tag}", x=0.5))

    unit = "V" if tab_type == "voltage" else "A"
    neg_pct  = seq.get("neg_imbalance_pct",  0.0)
    zero_pct = seq.get("zero_imbalance_pct", 0.0)

    rows = []
    for key, lbl, color in [
        ("positive", "Positiva", "#00FF88"),
        ("negative", "Negativa", "#FF6B35"),
        ("zero",     "Cero",     "#CC44FF"),
    ]:
        ph = seq.get(key, {})
        rows.append(html.Tr([
            html.Td([html.Span("● ", style={"color": color}), lbl]),
            html.Td(f"{ph.get('magnitude', 0):.3f}"),
            html.Td(f"{ph.get('angle_deg', 0):.2f}°"),
        ]))

    table = html.Div([
        html.Div("Resumen de Componentes", className="pdiff-title"),
        html.Table(className="summary-table", children=[
            html.Thead(html.Tr([html.Th("Componente"), html.Th("Magnitud"), html.Th("Ángulo")])),
            html.Tbody(rows),
        ]),
        html.Div("Relaciones", className="pdiff-title", style={"marginTop": "16px"}),
        html.Div(className="pdiff-row", children=[
            html.Span("I₂/I₁ (Desbalance):", className="pdiff-lbl"),
            html.Span(f"{neg_pct:.2f}%", className="pdiff-val"),
        ]),
        html.Div(className="pdiff-row", children=[
            html.Span("I₀/I₁ (Falla a tierra):", className="pdiff-lbl"),
            html.Span(f"{zero_pct:.2f}%", className="pdiff-val"),
        ]),
        html.Div(className="interp-note",
                 children=("Referencia de voltaje LL detectada: se usa conversion a fase equivalente en el calculo de secuencias. "
                           if tab_type == "voltage" and mode == "line_to_line" else "") +
                          "Nota: Las componentes de secuencia son fundamentales para el análisis "
                          "de fallas. La presencia significativa de secuencia negativa indica "
                          "desbalance, mientras que la secuencia cero indica fallas a tierra."),
    ])

    return fig3, figc, table


# ─── Text results ─────────────────────────────────────────────────────────────

@callback(
    Output("txt-tab-content", "children"),
    Input("txt-tabs",  "active_tab"),
    Input("store-data", "data"),
    Input("store-selected-signals", "data"),
    prevent_initial_call=False,
)
def update_text_results(active_tab, data, selected):
    if not data:
        return html.Div("Carga un archivo COMTRADE para ver resultados.", className="no-data")

    meta = data.get("metadata",  {})
    ph_v = _filter_by_names(data.get("phasors_v_all", {}), _selected_names(selected, "voltage", list(data.get("phasors_v_all", {}).keys())))
    ph_i = _filter_by_names(data.get("phasors_i_all", {}), _selected_names(selected, "current", list(data.get("phasors_i_all", {}).keys())))
    mode = _voltage_reference_mode(meta)
    if mode == "line_to_line":
        ph_v_seq = _convert_line_voltage_phasors_to_phase_equivalent(ph_v, data, "voltage")
    else:
        ph_v_seq = ph_v
    seq_v = _build_sequence_from_phasors(ph_v_seq, "voltage")
    seq_i = _build_sequence_from_phasors(ph_i, "current")

    if active_tab == "txt-summary":
        return _summary_section(meta, seq_v, seq_i, data, selected)
    elif active_tab == "txt-phasors":
        return _phase_phasors_section(ph_v, ph_i)
    elif active_tab == "txt-sequence":
        return _sequence_section(seq_v, seq_i)
    return html.Div()


def _summary_section(meta, seq_v, seq_i, data, selected):
    def _row(label, value, color="#4B9EFF"):
        return html.Div(className="info-row", children=[
            html.Span(label + ":", className="info-lbl"),
            html.Span(str(value), className="info-val", style={"color": color}),
        ])

    neg_pct = seq_v.get("neg_imbalance_pct", 0.0) if seq_v else 0.0
    zero_pct = seq_v.get("zero_imbalance_pct", 0.0) if seq_v else 0.0

    steady_state_block = _steady_state_results_block(data, selected)

    return html.Div([
        html.Div(className="info-section", children=[
            html.H4("Información del Archivo", className="info-section-title"),
            _row("Archivo",                  meta.get("filename", "—")),
            _row("Frecuencia nominal",        f"{meta.get('system_freq_hz', '—')} Hz"),
            _row("Frecuencia de muestreo",    f"{meta.get('sampling_rate_hz', '—')} Hz"),
            _row("Referencia de voltaje",      meta.get("voltage_reference_label", "Desconocida")),
            _row("Número de muestras",        meta.get("total_samples", "—")),
            _row("Duración",                  f"{meta.get('duration_s', '—')} s"),
            _row("Muestras por ciclo",        meta.get("samples_per_cycle", "—")),
        ]),
        html.Div(className="info-section", children=[
            html.H4("Estado del Sistema", className="info-section-title"),
            html.Div("● Sistema procesado correctamente",
                     style={"color": "#00FF88", "margin": "4px 0"}),
            html.Div("● Componentes fundamentales extraídos",
                     style={"color": "#00FF88", "margin": "4px 0"}),
            html.Div("● Componentes de secuencia calculadas",
                     style={"color": "#00FF88", "margin": "4px 0"}),
        ]),
        html.Div(className="info-section", children=[
            html.H4("Diagnóstico Rápido", className="info-section-title"),
            html.Div(className="diag-card warning", children=[
                html.Strong("⚠ Desbalance de Sistema:"),
                html.P(f"Secuencia negativa / Secuencia positiva = {neg_pct:.2f}%"),
            ]) if neg_pct > 1 else html.Div(className="diag-card ok", children=[
                html.Strong("✓ Sistema Balanceado"),
                html.P(f"Desbalance: {neg_pct:.2f}%"),
            ]),
            html.Div(className="diag-card info", children=[
                html.Strong("ℹ Tipo de Falla:"),
                html.P(f"Presencia de secuencia cero: {zero_pct:.2f}% — "
                       + ("Posible falla a tierra" if zero_pct > 5 else "No indica falla a tierra")),
            ]),
        ]),
        steady_state_block,
    ])


def _steady_state_results_block(data, selected):
    time_ms = data.get("time_ms", [])
    voltages = _filter_by_names(
        data.get("voltages", {}),
        _selected_names(selected, "voltage", list(data.get("voltages", {}).keys())),
    )
    currents = _filter_by_names(
        data.get("currents", {}),
        _selected_names(selected, "current", list(data.get("currents", {}).keys())),
    )
    rms_v = _filter_by_names(
        data.get("rms_v", {}),
        list(voltages.keys()),
    )
    rms_i = _filter_by_names(
        data.get("rms_i", {}),
        list(currents.keys()),
    )

    sv0, sv1 = _detect_steady_state_region(time_ms, rms_v)
    si0, si1 = _detect_steady_state_region(time_ms, rms_i)

    fs = float(data.get("metadata", {}).get("sampling_rate_hz", 1.0))
    f0 = float(data.get("metadata", {}).get("system_freq_hz", 60.0))
    t_s = np.array(time_ms, dtype=float) / 1000.0 if time_ms else np.array([])
    calc = PhasorCalculator(system_frequency=f0, sampling_rate=fs)

    def _phasor_table_rows(sig_dict, s0, s1):
        rows = []
        ph = {}
        if len(t_s) < 4:
            return rows, ph
        s0 = max(0, min(s0, len(t_s) - 2))
        s1 = max(s0 + 1, min(s1, len(t_s) - 1))
        for name, vals in sig_dict.items():
            arr = np.array(vals, dtype=float)
            n = min(len(arr), len(t_s))
            if n < 4:
                continue
            e0 = min(s0, n - 2)
            e1 = max(e0 + 1, min(s1, n - 1))
            p = calc.calculate_phasor(arr[e0:e1 + 1], t_s[e0:e1 + 1], name=name)
            ph[name] = {
                "magnitude": float(p.magnitude),
                "angle_deg": float(p.angle_deg),
                "real": float(p.real),
                "imag": float(p.imag),
                "name": name,
            }
            rows.append(html.Tr([
                html.Td(name),
                html.Td(f"{p.magnitude:.3f}"),
                html.Td(f"{p.angle_deg:.2f}°"),
            ]))
        return rows, ph

    v_rows, v_ph = _phasor_table_rows(voltages, sv0, sv1)
    i_rows, i_ph = _phasor_table_rows(currents, si0, si1)
    seq_v = _build_sequence_from_phasors(v_ph, "voltage") if len(v_ph) == 3 else {}
    seq_i = _build_sequence_from_phasors(i_ph, "current") if len(i_ph) == 3 else {}

    def _seq_rows(seq):
        out = []
        for key, lbl in [("positive", "Positiva"), ("negative", "Negativa"), ("zero", "Cero")]:
            p = seq.get(key, {})
            out.append(html.Tr([
                html.Td(lbl),
                html.Td(f"{p.get('magnitude', 0.0):.3f}"),
                html.Td(f"{p.get('angle_deg', 0.0):.2f}°"),
            ]))
        return out

    s0_ms = time_ms[sv0] if time_ms else 0.0
    s1_ms = time_ms[sv1] if time_ms else 0.0

    return html.Div(className="info-section", children=[
        html.H4("Resultados en Estado Estable", className="info-section-title"),
        html.Div(f"Ventana detectada automaticamente: {s0_ms:.3f} ms - {s1_ms:.3f} ms", className="interp-note"),
        html.Div(className="phasor-layout", children=[
            html.Div(className="phasor-values", children=[
                html.H4("Magnitud y Angulo de Fases (Voltaje)", className="info-section-title"),
                html.Table(className="summary-table", children=[
                    html.Thead(html.Tr([html.Th("Fase"), html.Th("Magnitud"), html.Th("Angulo")])),
                    html.Tbody(v_rows),
                ]),
                html.H4("Magnitud y Angulo de Fases (Corriente)", className="info-section-title"),
                html.Table(className="summary-table", children=[
                    html.Thead(html.Tr([html.Th("Fase"), html.Th("Magnitud"), html.Th("Angulo")])),
                    html.Tbody(i_rows),
                ]),
            ]),
            html.Div(className="phasor-values", children=[
                html.H4("Componentes de Secuencia (Voltaje)", className="info-section-title"),
                html.Table(className="summary-table", children=[
                    html.Thead(html.Tr([html.Th("Secuencia"), html.Th("Magnitud"), html.Th("Angulo")])),
                    html.Tbody(_seq_rows(seq_v) if seq_v else [html.Tr([html.Td("-"), html.Td("-"), html.Td("-")])]),
                ]),
                html.H4("Componentes de Secuencia (Corriente)", className="info-section-title"),
                html.Table(className="summary-table", children=[
                    html.Thead(html.Tr([html.Th("Secuencia"), html.Th("Magnitud"), html.Th("Angulo")])),
                    html.Tbody(_seq_rows(seq_i) if seq_i else [html.Tr([html.Td("-"), html.Td("-"), html.Td("-")])]),
                ]),
            ]),
        ]),
    ])


def _phase_phasors_section(ph_v, ph_i):
    def _ph_table(ph_dict, title, unit):
        rows = []
        for nm, ph in ph_dict.items():
            rows.append(html.Tr([
                html.Td(nm),
                html.Td(f"{ph['magnitude']:.3f} {unit}"),
                html.Td(f"{ph['angle_deg']:.2f}°"),
                html.Td(f"{ph['real']:.3f} + j{ph['imag']:.3f}"),
            ]))
        return html.Div([
            html.H4(title, className="info-section-title"),
            html.Table(className="summary-table full-width", children=[
                html.Thead(html.Tr([
                    html.Th("Canal"), html.Th("Magnitud"), html.Th("Ángulo"), html.Th("Rectangular")])),
                html.Tbody(rows),
            ]),
        ])
    return html.Div([
        _ph_table(ph_v, "Fasores de Voltaje", "V"),
        _ph_table(ph_i, "Fasores de Corriente", "A"),
    ])


def _sequence_section(seq_v, seq_i):
    def _seq_table(seq, title, unit):
        if not seq:
            return html.Div(f"No hay datos de {title.lower()}.")
        rows = []
        for key, lbl in [("positive","Positiva"),("negative","Negativa"),("zero","Cero")]:
            ph = seq.get(key, {})
            rows.append(html.Tr([
                html.Td(lbl),
                html.Td(f"{ph.get('magnitude', 0):.3f} {unit}"),
                html.Td(f"{ph.get('angle_deg', 0):.2f}°"),
                html.Td(f"{ph.get('real', 0):.3f} + j{ph.get('imag', 0):.3f}"),
            ]))
        rows.append(html.Tr([
            html.Td("Desbalance neg."), html.Td(f"{seq.get('neg_imbalance_pct',0):.2f}%"),
            html.Td(""), html.Td(""),
        ]))
        rows.append(html.Tr([
            html.Td("Desbalance cero"), html.Td(f"{seq.get('zero_imbalance_pct',0):.2f}%"),
            html.Td(""), html.Td(""),
        ]))
        return html.Div([
            html.H4(title, className="info-section-title"),
            html.Table(className="summary-table full-width", children=[
                html.Thead(html.Tr([
                    html.Th("Secuencia"), html.Th("Magnitud"), html.Th("Ángulo"), html.Th("Rectangular")])),
                html.Tbody(rows),
            ]),
        ])

    return html.Div([
        _seq_table(seq_v, "Secuencias de Voltaje", "V"),
        _seq_table(seq_i, "Secuencias de Corriente", "A"),
    ])


# ─── Barycenter ──────────────────────────────────────────────────────────────

@callback(
    Output("graph-bary-vector",     "figure"),
    Output("bary-coords-panel",     "children"),
    Output("bary-stats-panel",      "children"),
    Output("bary-interp-panel",     "children"),
    Output("bary-complex-panel",    "children"),
    Input("bary-tab-type", "value"),
    Input("store-data", "data"),
    Input("store-selected-signals", "data"),
    Input("store-cursor-ms", "data"),
    prevent_initial_call=False,
)
def update_barycenter(tab_type, data, selected, cursor_ms):
    empty_v = make_barycenter_vector_fig(0.0, 0.0)
    empty_panels = [html.Div(), html.Div(), html.Div(), html.Div()]

    if not data:
        return empty_v, *empty_panels

    active_type = tab_type or "voltage"
    signal_key = "voltages" if active_type == "voltage" else "currents"
    selected_names = _selected_names(
        selected,
        "voltage" if active_type == "voltage" else "current",
        list(data.get(signal_key, {}).keys()),
    )
    selected_signals = _filter_by_names(data.get(signal_key, {}), selected_names)
    ok, _ = _require_three_phase_or_empty(selected_signals)
    if not ok:
        return empty_v, *empty_panels

    signal_arrays = [np.array(values, dtype=float) for values in selected_signals.values()][:3]

    size = min(len(array) for array in signal_arrays)
    bary = (signal_arrays[0][:size] + signal_arrays[1][:size] + signal_arrays[2][:size]) / 3.0
    bary_r = bary.real.tolist()
    bary_i_ = bary.imag.tolist()

    time_ms = data.get("time_ms", [])[:size]
    idx = _cursor_idx(time_ms, float(cursor_ms)) if (cursor_ms is not None and time_ms) else (len(time_ms) - 1 if time_ms else 0)
    idx = max(0, min(idx, len(bary_r) - 1)) if bary_r else 0

    points_plotted = idx + 1 if bary_r else 0
    cr = float(bary_r[idx]) if bary_r else 0.0
    ci = float(bary_i_[idx]) if bary_i_ else 0.0

    dyn_ph = _phasors_from_cursor(
        selected_signals,
        time_ms,
        float(time_ms[idx]) if time_ms else cursor_ms,
        float(data.get("metadata", {}).get("sampling_rate_hz", 1.0)),
        float(data.get("metadata", {}).get("system_freq_hz", 60.0)),
    )

    triangle_analyzer = TriangleAnalyzer()
    if len(dyn_ph) >= 3:
        ph_names = list(dyn_ph.keys())[:3]
        p1 = _phasor_from_dict(dyn_ph[ph_names[0]], ph_names[0])
        p2 = _phasor_from_dict(dyn_ph[ph_names[1]], ph_names[1])
        p3 = _phasor_from_dict(dyn_ph[ph_names[2]], ph_names[2])
        tri = triangle_analyzer.analyze_triangle(p1, p2, p3)
        cr = float(tri.barycenter.real)
        ci = float(tri.barycenter.imag)

    fig_v = make_barycenter_vector_fig(cr, ci, phase_phasors=dyn_ph)
    if cursor_ms is not None:
        fig_v.update_layout(title=dict(text=f"Baricentro Geometrico • t = {float(cursor_ms):.3f} ms", x=0.5))
    else:
        fig_v.update_layout(title=dict(text="Baricentro Geometrico", x=0.5))

    dist   = float(np.sqrt(cr ** 2 + ci ** 2))
    angle  = float(np.degrees(np.arctan2(ci, cr)))
    arr_r  = np.array(bary_r, dtype=float)
    arr_i  = np.array(bary_i_, dtype=float)
    distances = np.sqrt(arr_r**2 + arr_i**2) if len(arr_r) else np.array([0.0])
    max_dist = float(np.max(distances))
    avg_dist = float(np.mean(distances))

    # ── coord panel ─────────────────────────────────────────────────────
    v_unit = "Voltios" if active_type == "voltage" else "Amperios"
    i_unit = "Componente Imag"

    coords = html.Div([
        html.Div("COORDENADAS DEL CENTRO", className="bary-panel-title"),
        html.Div("Componente X (Real)", className="bary-lbl"),
        html.Div(f"{cr:.4f}", className="bary-big-val"),
        html.Div(v_unit, className="bary-unit"),
        html.Div("Componente Y (Imag)", className="bary-lbl", style={"marginTop": "10px"}),
        html.Div(f"{ci:.4f}", className="bary-big-val"),
        html.Div(i_unit, className="bary-unit"),
    ])

    stats = html.Div([
        html.Div("DISTANCIA DESDE ORIGEN", className="bary-panel-title"),
        html.Div(f"{dist:.2f}", className="bary-big-val accent-green",
                 style={"fontSize": "2.2em"}),
        html.Div(v_unit, className="bary-unit"),
        html.Div(className="bary-stat-row", children=[
            html.Span("Ángulo:", className="bary-lbl"),
            html.Span(f"{angle:.2f}°", className="bary-val"),
        ]),
        html.Div("ESTADÍSTICAS", className="bary-panel-title",
                 style={"marginTop": "12px"}),
        html.Div(className="bary-stat-row", children=[
            html.Span("Dist. Máxima:",  className="bary-lbl"),
            html.Span(f"{max_dist:.2f}", className="bary-val"),
        ]),
        html.Div(className="bary-stat-row", children=[
            html.Span("Dist. Promedio:", className="bary-lbl"),
            html.Span(f"{avg_dist:.2f}", className="bary-val"),
        ]),
        html.Div(className="bary-stat-row", children=[
            html.Span("Puntos trazados:", className="bary-lbl"),
            html.Span(str(points_plotted), className="bary-val"),
        ]),
    ])

    interp = html.Div([
        html.Div("Interpretación", className="bary-panel-title",
                 style={"color": "#4B9EFF"}),
        html.P("El baricentro representa el centro geométrico de las tres señales trifásicas. "
               "Su posicion y trayectoria indican el balance del sistema y pueden revelar patrones "
               "de falla y comportamiento transitorio.",
               className="bary-interp-text"),
    ])

    complex_panel = html.Div([
        html.Div("FORMATO COMPLEJO", className="bary-panel-title"),
        html.Div("Polar:", className="bary-lbl"),
        html.Div(f"{dist:.4f} ∠ {angle:.2f}°",
                 style={"color": "#00FF88", "fontFamily": "monospace", "fontSize": "13px"}),
        html.Div("Rectangular:", className="bary-lbl", style={"marginTop": "8px"}),
        html.Div(f"{cr:.4f} {'+ ' if ci >= 0 else '- '}j{abs(ci):.4f}",
                 style={"color": "#4B9EFF", "fontFamily": "monospace", "fontSize": "13px"}),
    ])

    return fig_v, coords, stats, interp, complex_panel
