"""
Signal Data Model
=================

Structured data representation for COMTRADE analysis.
Centralizes all signal information and computation results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass
class SignalMetadata:
    """COMTRADE file metadata."""
    filename: str
    station_name: str
    recording_device: str
    comtrade_revision: int
    system_frequency: float  # Hz (50 or 60)
    sampling_rate: float  # Hz
    num_analog_channels: int
    num_digital_channels: int
    total_samples: int
    duration: float  # seconds
    
    @property
    def samples_per_cycle(self) -> int:
        """Number of samples per power frequency cycle."""
        return int(round(self.sampling_rate / self.system_frequency))
    
    @property
    def nyquist_frequency(self) -> float:
        """Nyquist frequency of sampling."""
        return self.sampling_rate / 2.0


@dataclass
class ChannelInfo:
    """Information about a single analog channel."""
    index: int
    name: str
    phase: str  # 'A', 'B', 'C', 'N' (neutral)
    component: str  # 'V' (voltage) or 'I' (current)
    units: str  # 'V', 'A', 'kV', 'kA'
    multiplier: float
    offset: float
    min_val: float
    max_val: float
    primary: float  # VT/CT primary
    secondary: float  # VT/CT secondary
    classification: str = "other"


@dataclass
class SelectedSignals:
    """User-selected signal channels for analysis and plotting."""

    voltage_channels: List[str] = field(default_factory=list)
    current_channels: List[str] = field(default_factory=list)


@dataclass
class SignalSet:
    """
    Complete signal dataset for COMTRADE analysis.
    Contains raw signals, filtered signals, RMS, phasors, etc.
    """
    # Metadata
    metadata: SignalMetadata
    
    # Channel information
    voltage_channels: List[ChannelInfo] = field(default_factory=list)
    current_channels: List[ChannelInfo] = field(default_factory=list)
    other_analog_channels: List[ChannelInfo] = field(default_factory=list)
    logical_channel_names: List[str] = field(default_factory=list)
    logical_channels: int = 0  # Count of digital/status channels
    selected_signals: SelectedSignals = field(default_factory=SelectedSignals)
    phase_group_suggestions: List[Dict[str, object]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Time axis
    time_vector: np.ndarray = field(default_factory=lambda: np.array([]))  # seconds
    
    # Raw signals (by channel name)
    raw_signals: Dict[str, np.ndarray] = field(default_factory=dict)
    
    # Filtered signals at fundamental (by channel name)
    filtered_signals: Dict[str, np.ndarray] = field(default_factory=dict)
    
    # RMS sliding window (precomputed, by channel name)
    rms_signals: Dict[str, np.ndarray] = field(default_factory=dict)
    
    # Phasor cache (magnitude, angle at each sample)
    # Format: {channel_name: {'magnitude': array, 'angle_deg': array}}
    phasor_cache: Dict[str, Dict[str, np.ndarray]] = field(default_factory=dict)
    
    # Error flag
    error: Optional[str] = None
    error_details: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if dataset is valid and ready for analysis."""
        return (
            self.error is None and
            len(self.time_vector) > 0 and
            len(self.raw_signals) > 0 and
            self.metadata.total_samples == len(self.time_vector)
        )
    
    @property
    def num_samples(self) -> int:
        """Total number of samples."""
        return len(self.time_vector) if len(self.time_vector) > 0 else 0
    
    @property
    def duration(self) -> float:
        """Signal duration in seconds."""
        return self.metadata.duration
    
    @property
    def all_channel_names(self) -> List[str]:
        """Get all channel names (voltages, then currents)."""
        voltage_names = [ch.name for ch in self.voltage_channels]
        current_names = [ch.name for ch in self.current_channels]
        other_names = [ch.name for ch in self.other_analog_channels]
        return voltage_names + current_names + other_names
    
    def get_signal(self, channel_name: str, signal_type: str = 'raw') -> Optional[np.ndarray]:
        """
        Get signal data for a channel.
        
        Args:
            channel_name: Channel identifier (e.g., 'VA', 'IA')
            signal_type: 'raw', 'filtered', or 'rms'
        
        Returns:
            Signal array or None if not available
        """
        if signal_type == 'raw':
            return self.raw_signals.get(channel_name)
        elif signal_type == 'filtered':
            return self.filtered_signals.get(channel_name)
        elif signal_type == 'rms':
            return self.rms_signals.get(channel_name)
        return None
    
    def to_dataframe(self, signal_type: str = 'raw') -> pd.DataFrame:
        """
        Convert signals to pandas DataFrame for easy manipulation.
        
        Args:
            signal_type: 'raw', 'filtered', or 'rms'
        
        Returns:
            DataFrame with time index and signal columns
        """
        if signal_type == 'raw':
            signals_dict = self.raw_signals
        elif signal_type == 'filtered':
            signals_dict = self.filtered_signals
        elif signal_type == 'rms':
            signals_dict = self.rms_signals
        else:
            return pd.DataFrame()
        
        data = {'time': self.time_vector}
        data.update(signals_dict)
        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        return df
    
    def set_error(self, error_message: str, details: Optional[str] = None):
        """Mark dataset as invalid with error message."""
        self.error = error_message
        self.error_details = details
