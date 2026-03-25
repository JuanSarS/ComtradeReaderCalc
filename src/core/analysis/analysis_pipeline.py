"""Shared COMTRADE analysis pipeline for desktop and embedded web UI."""

from __future__ import annotations

import base64
import io
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from src.core.analysis.analysis_cache import analysis_cache
from src.core.analysis.comtrade_reader import (
    COMTRADEReader, ComtradeValidationError
)
from src.core.analysis.phasor_calculator import Phasor, PhasorCalculator
from src.core.analysis.rms_calculator import RMSCalculator
from src.core.analysis.signal_filter import SignalFilter
from src.core.analysis.symmetrical_components import SymmetricalComponents


MAX_PLOT_POINTS = 5000


def _downsample_factor(sample_count: int) -> int:
    return max(1, int(np.ceil(sample_count / float(MAX_PLOT_POINTS))))


def _resample_1d(values: np.ndarray, target_count: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    if n == 0 or target_count <= 0:
        return np.array([], dtype=float)
    if n <= target_count:
        return arr

    x_old = np.linspace(0.0, 1.0, n)
    x_new = np.linspace(0.0, 1.0, target_count)
    return np.interp(x_new, x_old, arr)


def _downsample_signal_dict(signal_dict: dict[str, np.ndarray], target_count: int) -> dict[str, list[float]]:
    return {
        name: _resample_1d(np.asarray(values, dtype=float), target_count).tolist()
        for name, values in signal_dict.items()
    }


def _channel_info_to_dict(channel) -> dict:
    return {
        "index": channel.index,
        "name": channel.name,
        "phase": channel.phase,
        "component": channel.component,
        "units": channel.units,
        "classification": channel.classification,
    }


def _filter_selected(signal_dict: dict, selected_names: list[str]) -> dict:
    if not selected_names:
        return signal_dict
    return {name: signal_dict[name] for name in selected_names if name in signal_dict}


def _voltage_pair_from_channel(channel_info: dict) -> str | None:
    token = str(channel_info.get("phase", "") or "").upper().strip()
    token = "".join(ch for ch in token if ch.isalnum())
    name = str(channel_info.get("name", "") or "").upper().strip()
    name = "".join(ch for ch in name if ch.isalnum())
    for src in (token, name):
        for pair in ("AB", "BC", "CA", "BA", "CB", "AC"):
            if src == pair or src.endswith(pair):
                return pair
    return None


def _line_to_phase_phasor_dict(phasor_dict: dict, available_voltage_channels: list[dict]) -> dict:
    """Convert Vab/Vbc/Vca phasors to equivalent phase phasors Va/Vb/Vc (V0 assumed 0)."""
    if len(phasor_dict) < 3:
        return phasor_dict

    by_name = {item.get("name"): item for item in available_voltage_channels}
    line_map: dict[str, complex] = {}

    for name, ph in phasor_dict.items():
        info = by_name.get(name, {"name": name})
        pair = _voltage_pair_from_channel(info)
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

    def _pack(val: complex, name: str) -> dict:
        mag = float(np.abs(val))
        ang = float(np.degrees(np.angle(val)))
        return {
            "magnitude": round(mag, 3),
            "angle_deg": round(ang, 2),
            "real": round(float(val.real), 3),
            "imag": round(float(val.imag), 3),
            "name": name,
        }

    return {
        "VA(eq)": _pack(va, "VA(eq)"),
        "VB(eq)": _pack(vb, "VB(eq)"),
        "VC(eq)": _pack(vc, "VC(eq)"),
    }


def process_comtrade_files(contents_list, filenames_list, system_frequency: float = 60.0) -> dict:
    """Process uploaded COMTRADE files from the web UI."""
    if not isinstance(contents_list, list):
        contents_list = [contents_list]
        filenames_list = [filenames_list]

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        cfg_entry = dat_entry = zip_entry = None

        for content, filename in zip(contents_list, filenames_list):
            ext = Path(filename).suffix.lower()
            if ext == ".cfg":
                cfg_entry = (content, filename)
            elif ext == ".dat":
                dat_entry = (content, filename)
            elif ext == ".zip":
                zip_entry = (content, filename)

        if zip_entry is not None:
            content, filename = zip_entry
            _, b64 = content.split(",", 1)
            try:
                with zipfile.ZipFile(io.BytesIO(base64.b64decode(b64))) as archive:
                    cfg_name = None
                    for member in archive.namelist():
                        low = member.lower()
                        if low.endswith(".cfg") or low.endswith(".dat"):
                            destination = tmp_dir / Path(member).name
                            destination.write_bytes(archive.read(member))
                            if low.endswith(".cfg"):
                                cfg_name = Path(member).name
                    if cfg_name is None:
                        return {"error": "El .zip no contiene ningún archivo .cfg"}
            except zipfile.BadZipFile:
                return {"error": "Archivo .zip inválido o corrupto"}

            return _run_analysis(tmp_dir / cfg_name, system_frequency, Path(filename).stem)

        if cfg_entry is not None:
            content, filename = cfg_entry
            _, b64 = content.split(",", 1)
            stem = Path(filename).stem
            cfg_path = tmp_dir / f"{stem}.cfg"
            cfg_path.write_bytes(base64.b64decode(b64))
            if dat_entry is not None:
                _, dat_b64 = dat_entry[0].split(",", 1)
                (tmp_dir / f"{stem}.dat").write_bytes(base64.b64decode(dat_b64))
            return _run_analysis(cfg_path, system_frequency, filename)

    return {"error": "Sube un par .cfg + .dat, o un archivo .zip que los contenga."}


def process_comtrade(content: str, filename: str, system_frequency: float = 60.0) -> dict:
    """Backward-compatible single-file entry point."""
    return process_comtrade_files(content, filename, system_frequency)


def process_comtrade_path(cfg_file_path: str, system_frequency: float = 60.0) -> dict:
    """Process a COMTRADE pair selected from the local desktop shell."""
    cfg_path = Path(cfg_file_path)
    if not cfg_path.exists():
        return {"error": f"CFG file not found: {cfg_file_path}"}
    return _run_analysis(cfg_path, system_frequency, cfg_path.name)


def _run_analysis(cfg_path: Path, system_frequency: float, display_filename: str) -> dict:
    """
    Run complete signal analysis pipeline.
    
    REFACTORED: Now uses SignalSet internally for structured data management.
    Returns legacy dict format for UI compatibility.
    
    Args:
        cfg_path (Path): Path to .cfg file
        system_frequency (float): System frequency (50 or 60 Hz)
        display_filename (str): Filename for display in reports
    
    Returns:
        dict: Analysis results compatible with existing UI callbacks
              Will contain error key if processing failed
    
    Raises:
        (Does not raise - errors are returned in dict)
    """
    reader = COMTRADEReader()
    
    # === STEP 1: Load and validate COMTRADE file ===
    try:
        reader.load(str(cfg_path))
    except FileNotFoundError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Failed to load COMTRADE file: {str(exc)}"}

    voltage_reference = reader.detect_voltage_reference_mode()
    
    # === STEP 2: Convert to SignalSet (validates structure) ===
    try:
        signal_set = reader.to_signal_set(system_frequency=system_frequency)
    except ComtradeValidationError as exc:
        return {"error": f"COMTRADE validation failed: {str(exc)}"}
    except Exception as exc:
        return {"error": f"Failed to process COMTRADE data: {str(exc)}"}
    
    if not signal_set.is_valid:
        return {"error": signal_set.error or "Invalid signal set"}
    
    # === STEP 3: Design and apply filters ===
    sampling_rate = signal_set.metadata.sampling_rate
    samples_per_cycle = sampling_rate / system_frequency if system_frequency > 0 else 0.0

    # Detect dominant frequency near nominal from first voltage channel when available.
    detected_fundamental = float(system_frequency)
    try:
        voltage_candidates = [ch.name for ch in signal_set.voltage_channels]
        probe_name = voltage_candidates[0] if voltage_candidates else next(iter(signal_set.raw_signals.keys()))
        probe = np.asarray(signal_set.raw_signals.get(probe_name, np.array([])), dtype=float)
        if len(probe) > 16 and sampling_rate > 0:
            probe = probe - np.mean(probe)
            freqs = np.fft.rfftfreq(len(probe), d=1.0 / sampling_rate)
            spec = np.abs(np.fft.rfft(probe))
            band = (freqs >= 40.0) & (freqs <= 75.0)
            if np.any(band):
                peak_idx = np.argmax(spec[band])
                detected_fundamental = float(freqs[band][peak_idx])
    except Exception:
        detected_fundamental = float(system_frequency)

    signal_filter = SignalFilter(
        system_frequency=detected_fundamental,
        sampling_rate=sampling_rate
    )

    # For low-resolution recordings, a narrow band-pass distorts transients and magnitude.
    # Keep waveform fidelity by using DC-removal only.
    use_bandpass = samples_per_cycle >= 12.0
    if use_bandpass:
        adaptive_bw = max(8.0, min(20.0, detected_fundamental * 0.25))
        signal_filter.design_bandpass_filter(bandwidth=adaptive_bw)
    
    filter_diagnostics = {}
    try:
        for channel_name, signal_data in signal_set.raw_signals.items():
            try:
                if use_bandpass:
                    filtered = signal_filter.apply(signal_data)
                else:
                    filtered = signal_filter.remove_dc_offset(np.asarray(signal_data, dtype=float))
                signal_set.filtered_signals[channel_name] = filtered
                raw_rms = float(np.sqrt(np.mean(np.asarray(signal_data, dtype=float) ** 2)))
                fil_rms = float(np.sqrt(np.mean(np.asarray(filtered, dtype=float) ** 2)))
                ratio = (fil_rms / raw_rms) if raw_rms > 1e-12 else 1.0
                filter_diagnostics[channel_name] = {
                    "rms_raw": raw_rms,
                    "rms_filtered": fil_rms,
                    "rms_ratio": ratio,
                }
            except Exception as e:
                # Fallback: remove DC if filter fails
                signal_set.filtered_signals[channel_name] = signal_data - np.mean(signal_data)
    except Exception as exc:
        return {"error": f"Signal filtering failed: {str(exc)}"}
    
    # === STEP 4: Precompute RMS time-series (ONCE) ===
    rms_calculator = RMSCalculator(
        system_frequency=system_frequency,
        sampling_rate=sampling_rate
    )
    try:
        # Precompute RMS for filtered signals
        signal_set.rms_signals = rms_calculator.calculate_rms_timeseries(
            signal_set.filtered_signals
        )
    except Exception as exc:
        return {"error": f"RMS calculation failed: {str(exc)}"}
    
    # === STEP 5: Compute phasors (for entire cycle range) ===
    phasor_calculator = PhasorCalculator(
        system_frequency=detected_fundamental,
        sampling_rate=sampling_rate
    )
    samples_per_cycle = max(4, int(round(sampling_rate / detected_fundamental)))
    time_s = signal_set.time_vector
    
    try:
        # Phasor using middle cycle window
        def get_phasor_window(total_len: int) -> tuple[int, int]:
            mid = total_len // 2
            half = samples_per_cycle // 2
            start = max(0, mid - half)
            end = min(total_len, start + samples_per_cycle)
            return start, end
        
        for channel_name, filtered_signal in signal_set.filtered_signals.items():
            start, end = get_phasor_window(len(filtered_signal))
            phasor = phasor_calculator.calculate_phasor(
                filtered_signal,
                time_s,
                time_s[start],
                time_s[end - 1],
                name=channel_name
            )
            # Cache phasor magnitude and angle over time
            if channel_name not in signal_set.phasor_cache:
                signal_set.phasor_cache[channel_name] = {}
            signal_set.phasor_cache[channel_name] = {
                'magnitude': phasor.magnitude,
                'angle_deg': phasor.angle_deg,
                'real': phasor.real,
                'imag': phasor.imag,
            }
    except Exception as exc:
        return {"error": f"Phasor calculation failed: {str(exc)}"}
    
    # === STEP 6: Format output for legacy UI compatibility ===
    analysis_id = analysis_cache.put(signal_set)
    time_ms_full = signal_set.time_vector * 1000.0
    original_count = len(time_ms_full)
    target_count = min(original_count, MAX_PLOT_POINTS)
    factor = _downsample_factor(original_count)
    time_ms = _resample_1d(time_ms_full, target_count).tolist()

    voltage_names = [ch.name for ch in signal_set.voltage_channels]
    current_names = [ch.name for ch in signal_set.current_channels]
    selected_voltage_names = signal_set.selected_signals.voltage_channels or voltage_names
    selected_current_names = signal_set.selected_signals.current_channels or current_names

    all_voltage_signals = {
        name: signal_set.filtered_signals.get(name, np.array([]))
        for name in voltage_names
    }
    all_current_signals = {
        name: signal_set.filtered_signals.get(name, np.array([]))
        for name in current_names
    }
    all_rms_v = {
        name: signal_set.rms_signals.get(name, np.array([]))
        for name in voltage_names
    }
    all_rms_i = {
        name: signal_set.rms_signals.get(name, np.array([]))
        for name in current_names
    }

    voltages = _downsample_signal_dict(all_voltage_signals, target_count)
    currents = _downsample_signal_dict(all_current_signals, target_count)

    # Raw (unfiltered) signals for "show pre-filtered" overlay
    all_voltage_signals_raw = {
        name: signal_set.raw_signals.get(name, np.array([]))
        for name in voltage_names
    }
    all_current_signals_raw = {
        name: signal_set.raw_signals.get(name, np.array([]))
        for name in current_names
    }
    voltages_raw = _downsample_signal_dict(all_voltage_signals_raw, target_count)
    currents_raw = _downsample_signal_dict(all_current_signals_raw, target_count)
    rms_v = _downsample_signal_dict(all_rms_v, target_count)
    rms_i = _downsample_signal_dict(all_rms_i, target_count)

    phasors_v_all = {}
    for name in voltage_names:
        if name in signal_set.phasor_cache:
            cache = signal_set.phasor_cache[name]
            phasors_v_all[name] = {
                "magnitude": round(cache["magnitude"], 3),
                "angle_deg": round(cache["angle_deg"], 2),
                "real": round(cache["real"], 3),
                "imag": round(cache["imag"], 3),
                "name": name,
            }

    phasors_i_all = {}
    for name in current_names:
        if name in signal_set.phasor_cache:
            cache = signal_set.phasor_cache[name]
            phasors_i_all[name] = {
                "magnitude": round(cache["magnitude"], 3),
                "angle_deg": round(cache["angle_deg"], 2),
                "real": round(cache["real"], 3),
                "imag": round(cache["imag"], 3),
                "name": name,
            }

    phasors_v = _filter_selected(phasors_v_all, selected_voltage_names)
    phasors_i = _filter_selected(phasors_i_all, selected_current_names)
    
    # === STEP 7: Compute sequence components (if 3-phase) ===
    symmetrical_components = SymmetricalComponents()
    
    def build_sequence_components(phasor_dict: dict, component_type: str) -> dict:
        phasor_values = list(phasor_dict.values())
        if len(phasor_values) < 3:
            phasor_values += [
                {"magnitude": 0, "angle_deg": 0, "real": 0, "imag": 0, "name": "?"}
            ] * (3 - len(phasor_values))

        def build_phasor(data: dict) -> Phasor:
            return Phasor(
                magnitude=data["magnitude"],
                angle_deg=data["angle_deg"],
                angle_rad=float(np.radians(data["angle_deg"])),
                real=data["real"],
                imag=data["imag"],
                name=data["name"],
            )

        phase_a, phase_b, phase_c = [build_phasor(value) for value in phasor_values[:3]]
        sequence = symmetrical_components.calculate_sequence_components(
            phase_a,
            phase_b,
            phase_c,
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

    voltage_mode = str(voltage_reference.get("mode", "unknown"))
    available_voltage_channels = [_channel_info_to_dict(channel) for channel in signal_set.voltage_channels]
    phasors_for_seq_v = phasors_v
    if voltage_mode == "line_to_line":
        phasors_for_seq_v = _line_to_phase_phasor_dict(phasors_v, available_voltage_channels)

    seq_v = build_sequence_components(phasors_for_seq_v, "voltage") if len(phasors_for_seq_v) >= 3 else {}
    seq_i = build_sequence_components(phasors_i, "current") if len(phasors_i) >= 3 else {}

    # Barycenter (3-phase average)
    def compute_barycenter_series(signal_dict: dict) -> tuple[list[float], list[float]]:
        names = list(signal_dict.keys())
        if len(names) < 3:
            return [], []
        phase_a = np.array(signal_dict[names[0]], dtype=float)
        phase_b = np.array(signal_dict[names[1]], dtype=float)
        phase_c = np.array(signal_dict[names[2]], dtype=float)
        size = min(len(phase_a), len(phase_b), len(phase_c))
        barycenter = (phase_a[:size] + phase_b[:size] + phase_c[:size]) / 3.0
        return barycenter.real.tolist(), barycenter.imag.tolist()

    bary_real, bary_imag = compute_barycenter_series(_filter_selected(voltages, selected_voltage_names))

    # Pre/Post fault phasors
    pre_phasors = {}
    post_phasors = {}
    if len(voltage_names) >= 3 and len(time_s) > samples_per_cycle * 2:
        for name in voltage_names[:3]:
            array = np.asarray(all_voltage_signals.get(name, np.array([])), dtype=float)
            if len(array) != len(time_s) or len(array) < samples_per_cycle:
                continue
            pre = phasor_calculator.calculate_phasor(
                array, time_s, time_s[0], time_s[samples_per_cycle - 1], name=name
            )
            post = phasor_calculator.calculate_phasor(
                array, time_s, time_s[-samples_per_cycle], time_s[-1], name=name
            )
            pre_phasors[name] = {
                "mag": pre.magnitude,
                "ang": pre.angle_deg,
                "real": pre.real,
                "imag": pre.imag,
            }
            post_phasors[name] = {
                "mag": post.magnitude,
                "ang": post.angle_deg,
                "real": post.real,
                "imag": post.imag,
            }

    # Metadata
    warnings = list(signal_set.warnings)
    if voltage_mode == "line_to_line":
        warnings.append(
            "Se detectaron voltajes linea-linea (LL). Se aplico conversion a fase equivalente para componentes simetricas."
        )
    elif voltage_mode == "mixed":
        warnings.append(
            "Se detectaron canales de voltaje mixtos (LL/LN). Verifica la seleccion de 3 fases para analisis consistente."
        )
    if not use_bandpass:
        warnings.append(
            f"Band-pass filter skipped due to low sampling resolution ({samples_per_cycle:.2f} samples/cycle). "
            "Using DC-offset removal to preserve waveform magnitude."
        )
    attenuated = [name for name, d in filter_diagnostics.items() if d.get("rms_ratio", 1.0) < 0.80]
    if attenuated:
        warnings.append(
            "Filtering attenuation warning: RMS drop >20% detected in " + ", ".join(attenuated[:6])
        )
    if selected_voltage_names and len(selected_voltage_names) != 3:
        warnings.append("Symmetrical component calculation requires 3-phase signals.")
    if selected_current_names and len(selected_current_names) != 3:
        warnings.append("Symmetrical component calculation requires 3-phase signals.")

    metadata = {
        "filename": display_filename,
        "station": signal_set.metadata.station_name,
        "sampling_rate_hz": round(signal_set.metadata.sampling_rate, 1),
        "total_samples": signal_set.metadata.total_samples,
        "duration_s": round(signal_set.metadata.duration, 6),
        "samples_per_cycle": samples_per_cycle,
        "system_freq_hz": system_frequency,
        "detected_fundamental_hz": round(detected_fundamental, 3),
        "voltage_channels": voltage_names,
        "current_channels": current_names,
        "voltage_reference_mode": voltage_mode,
        "voltage_reference_label": str(voltage_reference.get("label", "Desconocido")),
        "voltage_pairs_detected": dict(voltage_reference.get("pairs_detected", {})),
        "other_analog_channels": [channel.name for channel in signal_set.other_analog_channels],
        "logical_channel_names": list(signal_set.logical_channel_names),
        "downsample_factor": factor,
        "plot_sample_count": len(time_ms),
        "analysis_id": analysis_id,
        "has_full_resolution_internal": True,
    }

    return {
        "analysis_id": analysis_id,
        "time_ms": time_ms,
        "voltages": voltages,
        "currents": currents,
        "voltages_raw": voltages_raw,
        "currents_raw": currents_raw,
        "rms_v": rms_v,
        "rms_i": rms_i,
        "phasors_v": phasors_v,
        "phasors_i": phasors_i,
        "phasors_v_all": phasors_v_all,
        "phasors_i_all": phasors_i_all,
        "seq_v": seq_v,
        "seq_i": seq_i,
        "bary_real": bary_real,
        "bary_imag": bary_imag,
        "pre_phasors": pre_phasors,
        "post_phasors": post_phasors,
        "available_channels": {
            "voltage": available_voltage_channels,
            "current": [_channel_info_to_dict(channel) for channel in signal_set.current_channels],
            "other": [_channel_info_to_dict(channel) for channel in signal_set.other_analog_channels],
        },
        "selected_signals": {
            "voltage_channels": list(selected_voltage_names),
            "current_channels": list(selected_current_names),
        },
        "phase_group_suggestions": list(signal_set.phase_group_suggestions),
        "filter_diagnostics": filter_diagnostics,
        "warnings": warnings,
        "metadata": metadata,
    }