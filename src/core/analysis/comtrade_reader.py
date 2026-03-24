"""
COMTRADE File Reader Module
============================

This module provides functionality to read and parse COMTRADE files
(.cfg and .dat) from protection relays and simulation tools.

COMTRADE (Common Format for Transient Data Exchange) is the IEEE standard
for storing power system fault recorder data.
"""

import numpy as np
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from .signal_model import SignalSet, SignalMetadata, ChannelInfo, SelectedSignals


# === Custom Exceptions ===
class ComtradeException(Exception):
    """Base exception for COMTRADE-related errors."""
    pass


class ComtradeFileError(ComtradeException):
    """Error reading/parsing COMTRADE file."""
    pass


class ComtradeValidationError(ComtradeException):
    """COMTRADE data validation failed."""
    pass


@dataclass
class AnalogChannel:
    """
    Represents an analog channel from a COMTRADE file.
    
    Attributes:
        index (int): Channel index number
        name (str): Channel identifier (e.g., 'VA', 'IA')
        phase (str): Phase identifier (A, B, C, or N for neutral)
        component (str): Component identifier (voltage or current)
        units (str): Engineering units (V, A, kV, kA)
        multiplier (float): Conversion multiplier from recorded to engineering units
        offset (float): Offset value for conversion
        skew (float): Time skew in microseconds
        min_val (float): Minimum recorded value
        max_val (float): Maximum recorded value
        primary (float): Primary winding value (for CTs/VTs)
        secondary (float): Secondary winding value (for CTs/VTs)
        scaling (str): Scaling identifier (P for primary, S for secondary)
    """
    index: int
    name: str
    phase: str
    component: str
    units: str
    multiplier: float = 1.0
    offset: float = 0.0
    skew: float = 0.0
    min_val: float = -32768
    max_val: float = 32767
    primary: float = 1.0
    secondary: float = 1.0
    scaling: str = 'P'


@dataclass
class DigitalChannel:
    """
    Represents a digital channel from a COMTRADE file.
    
    Attributes:
        index (int): Channel index number
        name (str): Channel identifier
        phase (str): Phase identifier
        component (str): Component identifier
        normal (int): Normal state (0 or 1)
    """
    index: int
    name: str
    phase: str
    component: str
    normal: int = 0


class COMTRADEReader:
    """
    Reader class for COMTRADE files compliant with IEEE C37.111 standard.
    
    This class handles both ASCII and binary COMTRADE formats, supporting
    files from various protection relays and simulation tools like ATPDraw.
    
    Typical Usage:
        >>> reader = COMTRADEReader()
        >>> reader.load('fault_record.cfg')
        >>> instantaneous_data = reader.get_analog_data()
        >>> voltages = reader.get_voltage_channels()
        >>> currents = reader.get_current_channels()
    
    Attributes:
        cfg_path (Path): Path to the .cfg file
        dat_path (Path): Path to the .dat file
        station_name (str): Station identifier
        rec_dev_id (str): Recording device identifier
        rev_year (int): COMTRADE revision year (1991, 1999, 2013)
        sampling_rate (float): Sampling frequency in Hz
        total_samples (int): Total number of samples
        analog_channels (List[AnalogChannel]): List of analog channel objects
        digital_channels (List[DigitalChannel]): List of digital channel objects
        data (pd.DataFrame): Dataframe containing all channel data
    """
    
    def __init__(self):
        """Initialize the COMTRADE reader."""
        self.cfg_path: Optional[Path] = None
        self.dat_path: Optional[Path] = None
        self.station_name: str = ""
        self.rec_dev_id: str = ""
        self.rev_year: int = 1999
        
        # Channel information
        self.num_analog: int = 0
        self.num_digital: int = 0
        self.analog_channels: List[AnalogChannel] = []
        self.digital_channels: List[DigitalChannel] = []
        
        # Sampling information
        self.sampling_rate: float = 0.0
        self.total_samples: int = 0
        self.time_stamps: np.ndarray = np.array([])
        
        # Data storage
        self.data: Optional[pd.DataFrame] = None
        self._raw_data: Optional[np.ndarray] = None
        self._cfg_sample_count: int = 0
        
    def load(self, cfg_file_path: str) -> None:
        """
        Load a COMTRADE file pair (.cfg and .dat).
        """
        self.cfg_path = Path(cfg_file_path)
        if not self.cfg_path.exists():
            raise FileNotFoundError(f"CFG file not found: {cfg_file_path}")

        # Look for matching .dat file (case-insensitive extension)
        dat_path = self.cfg_path.with_suffix('.dat')
        if not dat_path.exists():
            dat_path = self.cfg_path.with_suffix('.DAT')
        if not dat_path.exists():
            raise FileNotFoundError(f"DAT file not found alongside: {cfg_file_path}")
        self.dat_path = dat_path

        # Reset state
        self.analog_channels = []
        self.digital_channels = []
        self.data = None
        self.time_stamps = np.array([])

        self._parse_cfg_file()
        self._parse_dat_file()
        self._validate_loaded_data()

    @staticmethod
    def _classify_analog_channel(channel: AnalogChannel) -> str:
        unit = (channel.units or "").strip().upper()
        if "KV" in unit or unit == "V" or unit.endswith("V"):
            return "voltage"
        if "KA" in unit or unit == "A" or unit.endswith("A"):
            return "current"
        return "other"

    @staticmethod
    def _normalize_channel_name(name: str) -> str:
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        return cleaned.strip()

    @staticmethod
    def _extract_voltage_pair_token(channel: AnalogChannel) -> Optional[str]:
        """Extract voltage pair token such as AB/BC/CA/AN/AG from channel info."""
        phase_token = re.sub(r"[^A-Z0-9]+", "", (channel.phase or "").upper())
        name_token = COMTRADEReader._normalize_channel_name(channel.name or "")

        for token in (phase_token, name_token):
            if not token:
                continue
            for pair in ("AB", "BC", "CA", "BA", "CB", "AC", "AN", "BN", "CN", "AG", "BG", "CG"):
                if token == pair or token.endswith(pair):
                    return pair
        return None

    def detect_voltage_reference_mode(self) -> Dict[str, object]:
        """
        Detect whether voltage channels are line-to-line (LL), line-to-neutral (LN), mixed, or unknown.

        Returns:
            Dict with keys: mode, label, ll_channels, ln_channels, pairs_detected
        """
        voltage_channels = [ch for ch in self.analog_channels if self._classify_analog_channel(ch) == "voltage"]
        if not voltage_channels:
            return {
                "mode": "unknown",
                "label": "Desconocido",
                "ll_channels": [],
                "ln_channels": [],
                "pairs_detected": [],
            }

        ll_channels: List[str] = []
        ln_channels: List[str] = []
        pairs_detected: Dict[str, str] = {}

        for channel in voltage_channels:
            token = self._extract_voltage_pair_token(channel)
            if token in {"AB", "BC", "CA", "BA", "CB", "AC"}:
                ll_channels.append(channel.name)
                pairs_detected[channel.name] = token
            elif token in {"AN", "BN", "CN", "AG", "BG", "CG"}:
                ln_channels.append(channel.name)
                pairs_detected[channel.name] = token
            elif (channel.phase or "").upper() in {"A", "B", "C"}:
                ln_channels.append(channel.name)

        ll_count = len(ll_channels)
        ln_count = len(ln_channels)
        if ll_count >= 3 and ln_count == 0:
            mode = "line_to_line"
            label = "Linea a linea (LL)"
        elif ln_count >= 3 and ll_count == 0:
            mode = "line_to_neutral"
            label = "Fase a tierra/neutro (LN)"
        elif ll_count > 0 and ln_count > 0:
            mode = "mixed"
            label = "Mixto (LL y LN)"
        else:
            mode = "unknown"
            label = "Desconocido"

        return {
            "mode": mode,
            "label": label,
            "ll_channels": ll_channels,
            "ln_channels": ln_channels,
            "pairs_detected": pairs_detected,
        }

    def _detect_phase_groups(self, channel_names: List[str]) -> List[Dict[str, object]]:
        grouped: Dict[str, Dict[str, str]] = {}
        for name in channel_names:
            candidates = [self._normalize_channel_name(name)]
            candidates.extend(self._normalize_channel_name(token) for token in re.split(r"[^A-Za-z0-9]+", name) if token)
            for candidate in candidates:
                match = re.match(r"^(.*?)(A|B|C|1|2|3)$", candidate)
                if not match:
                    continue
                base, suffix = match.groups()
                if not base:
                    continue
                key = f"{base}:{'ABC' if suffix in {'A', 'B', 'C'} else '123'}"
                grouped.setdefault(key, {})[suffix] = name

        suggestions: List[Dict[str, object]] = []
        seen = set()
        for key, members in grouped.items():
            suffix_type = key.split(":", 1)[1]
            expected = ["A", "B", "C"] if suffix_type == "ABC" else ["1", "2", "3"]
            if all(suffix in members for suffix in expected):
                channels = tuple(members[suffix] for suffix in expected)
                if channels in seen:
                    continue
                seen.add(channels)
                suggestions.append(
                    {
                        "pattern": suffix_type,
                        "channels": list(channels),
                    }
                )
        return suggestions

    def _validate_loaded_data(self) -> None:
        if self.data is None or self.data.empty:
            raise ComtradeValidationError("COMTRADE file inconsistency detected. No analog samples were loaded.")

        if len(self.time_stamps) != len(self.data.index):
            raise ComtradeValidationError(
                "COMTRADE file inconsistency detected. Time vector length does not match data rows."
            )

        if self.total_samples and self.total_samples != len(self.time_stamps):
            raise ComtradeValidationError(
                "COMTRADE file inconsistency detected. CFG/DAT sample count mismatch."
            )

        if self.sampling_rate <= 0:
            raise ComtradeValidationError(
                "COMTRADE file inconsistency detected. Sampling rate is invalid or missing."
            )

        if len(self.time_stamps) > 1:
            deltas = np.diff(self.time_stamps)
            if np.any(deltas <= 0):
                raise ComtradeValidationError(
                    "COMTRADE file inconsistency detected. Time vector is not strictly increasing."
                )

        for channel in self.analog_channels:
            if not np.isfinite(channel.multiplier) or not np.isfinite(channel.offset):
                raise ComtradeValidationError(
                    "COMTRADE file inconsistency detected. Invalid scaling factors found in CFG."
                )
    
    def _parse_cfg_file(self) -> None:
        """Parse the .cfg file following IEEE C37.111."""
        with open(self.cfg_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = [line.strip() for line in f.readlines()]

        idx = 0

        # Line 1: station name, recording device, revision year
        parts = lines[idx].split(',')
        self.station_name = parts[0].strip() if len(parts) > 0 else ""
        self.rec_dev_id = parts[1].strip() if len(parts) > 1 else ""
        self.rev_year = int(parts[2].strip()) if len(parts) > 2 else 1999
        idx += 1

        # Line 2: total channels, analog count, digital count
        parts = lines[idx].split(',')
        self.num_analog = int(parts[1].replace('A', '').strip()) if len(parts) > 1 else 0
        self.num_digital = int(parts[2].replace('D', '').strip()) if len(parts) > 2 else 0
        idx += 1

        # Analog channel definitions
        for _ in range(self.num_analog):
            parts = [p.strip() for p in lines[idx].split(',')]

            def _is_float(token: str) -> bool:
                try:
                    float(token)
                    return True
                except (TypeError, ValueError):
                    return False

            tail = parts[4:] if len(parts) > 4 else []
            first_num_rel = next((i for i, tok in enumerate(tail) if _is_float(tok)), None)

            # COMTRADE variants may include extra empty/string columns before units and scaling factors.
            if first_num_rel is None:
                units = parts[4] if len(parts) > 4 and parts[4] else "V"
                num_fields = []
            else:
                units_idx = 4 + max(0, first_num_rel - 1)
                units = parts[units_idx] if units_idx < len(parts) and parts[units_idx] else "V"
                num_fields = tail[first_num_rel:]

            def _num_at(pos: int, default: float) -> float:
                if pos < len(num_fields) and _is_float(num_fields[pos]):
                    return float(num_fields[pos])
                return default

            scaling = "P"
            if len(num_fields) > 7 and num_fields[7]:
                scaling = num_fields[7]
            elif len(parts) > 12 and parts[12]:
                scaling = parts[12]

            ch = AnalogChannel(
                index=int(parts[0]),
                name=(parts[1] if len(parts) > 1 else f"CH{_}").strip(),
                phase=parts[2] if len(parts) > 2 else "",
                component=parts[3] if len(parts) > 3 else "",
                units=units,
                multiplier=_num_at(0, 1.0),
                offset=_num_at(1, 0.0),
                skew=_num_at(2, 0.0),
                min_val=_num_at(3, -32768),
                max_val=_num_at(4, 32767),
                primary=_num_at(5, 1.0),
                secondary=_num_at(6, 1.0),
                scaling=scaling,
            )
            self.analog_channels.append(ch)
            idx += 1

        # Digital channel definitions
        for _ in range(self.num_digital):
            parts = [p.strip() for p in lines[idx].split(',')]
            ch = DigitalChannel(
                index=int(parts[0]),
                name=(parts[1] if len(parts) > 1 else f"D{_}").strip(),
                phase=parts[2] if len(parts) > 2 else "",
                component=parts[3] if len(parts) > 3 else "",
                normal=int(parts[4]) if len(parts) > 4 and parts[4] else 0,
            )
            self.digital_channels.append(ch)
            idx += 1

        # Line frequency
        self._line_frequency = float(lines[idx]) if idx < len(lines) else 60.0
        idx += 1

        # Sampling rate groups
        nrates = int(lines[idx]) if idx < len(lines) else 0
        idx += 1
        
        self.sampling_rate = 0.0
        self.total_samples = 0
        
        # Read sampling rate groups (or attempt to)
        for _ in range(max(1, nrates)):  # Always try to read at least one
            if idx < len(lines):
                parts = [p.strip() for p in lines[idx].split(',')]
                try:
                    if len(parts) >= 1:
                        val1 = float(parts[0])
                    if len(parts) >= 2:
                        val2 = int(parts[1])
                    
                    # Heuristic: if first value is >0.5, it's likely sampling rate (Hz)
                    # Otherwise it might be time offset
                    if len(parts) >= 2 and val1 >= 0.1:
                        self.sampling_rate = val1
                        self.total_samples = val2
                        self._cfg_sample_count = val2
                        idx += 1
                    elif nrates > 0:
                        # Only advance if we expected rate groups
                        idx += 1
                    else:
                        # nrates=0 and line doesn't look like valid rate → might be timestamp
                        break
                except (ValueError, IndexError):
                    if nrates > 0:
                        idx += 1
                    else:
                        break
        
        if nrates == 0:
            # Didn't find rate info, keep going
            pass

        # Skip to timestamp lines (now should be at correct position)
        # Some files have "time_start, time_end" before timestamps
        while idx < len(lines) and '/' not in lines[idx]:
            idx += 1
        
        # Skip timestamps
        if idx < len(lines) and '/' in lines[idx]:
            idx += 1
        if idx < len(lines) and '/' in lines[idx]:
            idx += 1

        # Data format
        self._data_format = lines[idx].strip().upper() if idx < len(lines) else 'ASCII'
        idx += 1
        
        # Time step (last line in some formats - used if sampling_rate not found)
        if self.sampling_rate == 0.0 and idx < len(lines):
            try:
                time_step = float(lines[idx].strip())
                if time_step > 0:
                    self.sampling_rate = 1.0 / time_step
            except (ValueError, ZeroDivisionError):
                pass
    
    def _parse_dat_file(self) -> None:
        """Parse the .dat file — supports ASCII and binary formats."""
        fmt = getattr(self, '_data_format', 'ASCII')
        n_analog = self.num_analog
        n_digital = self.num_digital

        if fmt == 'ASCII':
            rows = []
            with open(self.dat_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    try:
                        row = [float(p) for p in parts]
                        rows.append(row)
                    except ValueError:
                        continue
            if not rows:
                return
            arr = np.array(rows)
            # Columns: sample_number, timestamp_µs, ch1..chN, d1..dM
            time_us = arr[:, 1]
            self.time_stamps = time_us / 1_000_000.0  # convert to seconds
            raw = arr[:, 2:2 + n_analog]
        else:
            # Binary: 4-byte int sample num, 4-byte int timestamp, 2-byte int per analog, 2-byte per digital word
            import struct
            n_dig_words = max(1, (n_digital + 15) // 16)
            record_size = 4 + 4 + 2 * n_analog + 2 * n_dig_words
            data_bytes = self.dat_path.read_bytes()
            n_samples = len(data_bytes) // record_size
            timestamps = []
            raw_rows = []
            for i in range(n_samples):
                offset = i * record_size
                samp_num, ts = struct.unpack_from('<II', data_bytes, offset)
                analog_vals = struct.unpack_from(f'<{n_analog}h', data_bytes, offset + 8)
                timestamps.append(ts)
                raw_rows.append(analog_vals)
            self.time_stamps = np.array(timestamps, dtype=float) / 1_000_000.0
            raw = np.array(raw_rows, dtype=float)

        dat_sample_count = len(self.time_stamps)
        if self.total_samples in (0, dat_sample_count):
            self.total_samples = dat_sample_count

        # Apply conversion: engineering_value = raw * multiplier + offset
        converted = np.zeros_like(raw, dtype=float)
        for i, ch in enumerate(self.analog_channels):
            if i < raw.shape[1]:
                converted[:, i] = raw[:, i] * ch.multiplier + ch.offset

        # Build DataFrame
        col_names = [ch.name for ch in self.analog_channels]
        self.data = pd.DataFrame(converted, columns=col_names if col_names else None)
        self.data.insert(0, 'time', self.time_stamps)

        # Infer sampling rate if not set
        if self.sampling_rate == 0.0 and len(self.time_stamps) > 1:
            dt = np.mean(np.diff(self.time_stamps))
            self.sampling_rate = 1.0 / dt if dt > 0 else 0.0
    
    def get_analog_data(self, channel_names: Optional[List[str]] = None) -> pd.DataFrame:
        """Retrieve analog channel data in engineering units."""
        if self.data is None:
            return pd.DataFrame()
        if channel_names is None:
            return self.data
        cols = ['time'] + [c for c in channel_names if c in self.data.columns]
        return self.data[cols]

    def get_voltage_channels(self) -> List[str]:
        """Get list of voltage channel names."""
        return [ch.name for ch in self.analog_channels if self._classify_analog_channel(ch) == "voltage"]

    def get_current_channels(self) -> List[str]:
        """Get list of current channel names."""
        return [ch.name for ch in self.analog_channels if self._classify_analog_channel(ch) == "current"]

    def get_other_analog_channels(self) -> List[str]:
        """Get analog channels that are neither voltage nor current."""
        return [ch.name for ch in self.analog_channels if self._classify_analog_channel(ch) == "other"]

    def get_channel_info(self, channel_name: str) -> Optional[AnalogChannel]:
        """Get detailed information about a specific analog channel."""
        for ch in self.analog_channels:
            if ch.name == channel_name:
                return ch
        return None

    def get_sampling_info(self) -> Dict[str, float]:
        """Get sampling rate and time information."""
        duration = float(self.time_stamps[-1] - self.time_stamps[0]) if len(self.time_stamps) > 1 else 0.0
        dt = 1.0 / self.sampling_rate if self.sampling_rate > 0 else 0.0
        return {
            'sampling_rate': self.sampling_rate,
            'total_samples': float(self.total_samples),
            'duration': duration,
            'time_step': dt,
        }
    
    def get_time_axis(self) -> np.ndarray:
        """
        Get the time axis for the recorded data.
        
        Returns:
            np.ndarray: Time values in seconds
        """
        return self.time_stamps
    
    def export_to_csv(self, output_path: str, channels: Optional[List[str]] = None) -> None:
        """
        Export channel data to CSV file.
        
        Args:
            output_path (str): Path for output CSV file
            channels (List[str], optional): Specific channels to export
        """
        # TODO: Implement CSV export functionality
        pass
    
    def to_signal_set(self, system_frequency: float = 60.0) -> SignalSet:
        """
        Convert loaded COMTRADE data to SignalSet data model.
        
        Args:
            system_frequency (float): System frequency in Hz (50 or 60)
        
        Returns:
            SignalSet: Structured dataset ready for analysis
            
        Raises:
            ComtradeValidationError: If data validation fails
        """
        if self.data is None or len(self.data) == 0:
            raise ComtradeValidationError("No data loaded. Call load() first.")
        
        # Validate sampling rate (flexible for legacy/field recordings)
        samples_per_cycle = self.sampling_rate / system_frequency if system_frequency > 0 else 0.0
        low_sampling_warning = None
        if samples_per_cycle < 2.0:
            raise ComtradeValidationError(
                f"Sampling rate {self.sampling_rate} Hz is too low for {system_frequency} Hz "
                f"(samples/cycle={samples_per_cycle:.2f})."
            )
        if samples_per_cycle < 10.0:
            low_sampling_warning = (
                f"Low sampling rate detected ({self.sampling_rate} Hz, "
                f"{samples_per_cycle:.2f} samples/cycle). Analysis may be less accurate."
            )
        
        # Validate sample count
        if self.total_samples < 2 * self.sampling_rate / system_frequency:
            raise ComtradeValidationError(
                f"Duration is too short ({self.total_samples / self.sampling_rate:.3f}s). "
                f"Minimum 2 cycles recommended."
            )
        
        # Classify channels
        volt_channels = []
        curr_channels = []
        other_channels = []
        
        for ch in self.analog_channels:
            classification = self._classify_analog_channel(ch)
            channel_info = ChannelInfo(
                index=ch.index,
                name=ch.name,
                phase=ch.phase,
                component=ch.component,
                units=ch.units,
                multiplier=ch.multiplier,
                offset=ch.offset,
                min_val=ch.min_val,
                max_val=ch.max_val,
                primary=ch.primary,
                secondary=ch.secondary,
                classification=classification,
            )

            if classification == "voltage":
                volt_channels.append(channel_info)
            elif classification == "current":
                curr_channels.append(channel_info)
            else:
                other_channels.append(channel_info)
        
        if not volt_channels and not curr_channels:
            raise ComtradeValidationError(
                "No voltage or current channels detected. "
                "Check channel naming/units in .cfg file."
            )
        
        # Build metadata
        duration = float(self.time_stamps[-1] - self.time_stamps[0]) if len(self.time_stamps) > 1 else 0.0
        metadata = SignalMetadata(
            filename=self.cfg_path.name if self.cfg_path else "unknown.cfg",
            station_name=self.station_name,
            recording_device=self.rec_dev_id,
            comtrade_revision=self.rev_year,
            system_frequency=system_frequency,
            sampling_rate=self.sampling_rate,
            num_analog_channels=self.num_analog,
            num_digital_channels=self.num_digital,
            total_samples=self.total_samples,
            duration=duration,
        )
        
        # Extract raw signals
        raw_signals = {}
        for ch in self.analog_channels:
            if ch.name in self.data.columns:
                raw_signals[ch.name] = self.data[ch.name].values.astype(float)

        voltage_names = [channel.name for channel in volt_channels]
        current_names = [channel.name for channel in curr_channels]
        logical_names = [channel.name for channel in self.digital_channels]
        voltage_groups = self._detect_phase_groups(voltage_names)
        current_groups = self._detect_phase_groups(current_names)
        suggestions = voltage_groups + current_groups

        default_selection = SelectedSignals(
            voltage_channels=voltage_groups[0]["channels"] if voltage_groups else voltage_names,
            current_channels=current_groups[0]["channels"] if current_groups else current_names,
        )
        warnings: List[str] = []
        if low_sampling_warning:
            warnings.append(low_sampling_warning)
        if logical_names:
            warnings.append("Logical/status channels detected. Visualization not yet supported.")
        
        # Create SignalSet
        signal_set = SignalSet(
            metadata=metadata,
            voltage_channels=volt_channels,
            current_channels=curr_channels,
            other_analog_channels=other_channels,
            logical_channel_names=logical_names,
            logical_channels=self.num_digital,
            selected_signals=default_selection,
            phase_group_suggestions=suggestions,
            warnings=warnings,
            time_vector=self.time_stamps.astype(float),
            raw_signals=raw_signals,
        )
        
        return signal_set
    
    def __repr__(self) -> str:
        """String representation of the COMTRADE reader state."""
        return (f"COMTRADEReader(station='{self.station_name}', "
                f"analog_channels={self.num_analog}, "
                f"digital_channels={self.num_digital}, "
                f"samples={self.total_samples})")
