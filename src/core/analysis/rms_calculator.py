"""
RMS Calculator Module
=====================

This module provides sliding window RMS (Root Mean Square) calculation
for power system waveforms using one-cycle windows.
"""

import numpy as np
import pandas as pd
from typing import Optional, Union


class RMSCalculator:
    """
    Sliding window RMS calculator for power system signals.
    
    Implements one-cycle sliding window RMS calculation with configurable
    window positioning (half-cycle before and after each point).
    
    For power system analysis, RMS values provide the magnitude of voltages
    and currents, essential for protection relay coordination and fault analysis.
    
    Typical Usage:
        >>> rms_calc = RMSCalculator(system_frequency=60.0, sampling_rate=7200.0)
        >>> rms_values = rms_calc.calculate_sliding_rms(instantaneous_signal)
        >>> rms_calc.set_window_type('centered')  # Half-cycle before and after
    
    Attributes:
        system_frequency (float): Power system frequency in Hz
        sampling_rate (float): Sampling frequency in Hz
        samples_per_cycle (int): Number of samples in one power frequency cycle
        window_type (str): Type of RMS window ('centered', 'forward', 'backward')
    """
    
    def __init__(self, system_frequency: float = 60.0, sampling_rate: float = 7200.0):
        """
        Initialize the RMS calculator.
        
        Args:
            system_frequency (float): Power system frequency (50 or 60 Hz)
            sampling_rate (float): Sampling rate in Hz
        """
        self.system_frequency: float = system_frequency
        self.sampling_rate: float = sampling_rate
        self.samples_per_cycle: int = 0
        self.window_type: str = 'centered'  # half-cycle before and after
        
        self._calculate_window_size()
    
    def _calculate_window_size(self) -> None:
        """Calculate number of samples per power frequency cycle."""
        if self.sampling_rate > 0 and self.system_frequency > 0:
            self.samples_per_cycle = int(round(self.sampling_rate / self.system_frequency))
        else:
            self.samples_per_cycle = 0

    def update_sampling_rate(self, sampling_rate: float) -> None:
        """Update sampling rate and recalculate window."""
        self.sampling_rate = sampling_rate
        self._calculate_window_size()

    def calculate_sliding_rms(self,
                             signal_data: np.ndarray,
                             window_type: Optional[str] = None) -> np.ndarray:
        """
        Calculate sliding RMS using one full cycle window (half before, half after).
        """
        if window_type is not None:
            self.window_type = window_type

        N = self.samples_per_cycle
        if N == 0 or len(signal_data) == 0:
            return np.zeros_like(signal_data, dtype=float)

        signal_array = signal_data.astype(float)
        sq = signal_array ** 2
        n = len(signal_array)
        indices = np.arange(n)
        half = N // 2

        if self.window_type == 'centered':
            starts = np.maximum(0, indices - half)
            ends = np.minimum(n, indices + half + 1)
        elif self.window_type == 'forward':
            starts = indices
            ends = np.minimum(n, indices + N)
        else:
            starts = np.maximum(0, indices - N + 1)
            ends = indices + 1

        prefix = np.concatenate(([0.0], np.cumsum(sq)))
        window_sums = prefix[ends] - prefix[starts]
        window_lengths = np.maximum(1, ends - starts)
        return np.sqrt(window_sums / window_lengths)

    def calculate_steady_state_rms(self,
                                   signal_data: np.ndarray,
                                   start_time: float,
                                   end_time: float,
                                   time_axis: np.ndarray) -> float:
        """Calculate RMS over a specified time interval."""
        mask = (time_axis >= start_time) & (time_axis <= end_time)
        segment = signal_data[mask]
        if len(segment) == 0:
            return 0.0
        return float(np.sqrt(np.mean(segment.astype(float) ** 2)))

    def calculate_rms_dataframe(self, signals_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate sliding RMS for multiple signals in a DataFrame."""
        result = {}
        for col in signals_df.columns:
            if col == 'time':
                result[col] = signals_df[col].values
            else:
                result[col] = self.calculate_sliding_rms(signals_df[col].values)
        return pd.DataFrame(result)
    
    def calculate_rms_timeseries(self, signals_dict: dict) -> dict:
        """
        Precompute RMS time-series for all signals.
        
        This method should be called ONCE after loading COMTRADE data.
        Cursor movement must only lookup values from this precomputed array,
        NOT recalculate RMS.
        
        Args:
            signals_dict (dict): Dictionary of {channel_name: signal_array}
        
        Returns:
            dict: {channel_name: rms_array} where rms_array is precomputed
                  sliding RMS for each sample
        """
        rms_dict = {}
        for channel_name, signal_data in signals_dict.items():
            rms_dict[channel_name] = self.calculate_sliding_rms(signal_data)
        return rms_dict

    def calculate_peak_value(self, signal_data: np.ndarray) -> float:
        """Calculate peak (maximum absolute) value of signal."""
        if len(signal_data) == 0:
            return 0.0
        return float(np.max(np.abs(signal_data)))

    def verify_rms_relationship(self,
                               signal_data: np.ndarray,
                               tolerance: float = 0.01) -> bool:
        """Verify that RMS ≈ Peak/√2 for sinusoidal signals."""
        if len(signal_data) == 0:
            return False
        rms = float(np.sqrt(np.mean(signal_data.astype(float) ** 2)))
        peak = self.calculate_peak_value(signal_data)
        expected_rms = peak / np.sqrt(2)
        if expected_rms == 0:
            return rms == 0
        return abs(rms - expected_rms) / expected_rms < tolerance
    
    def __repr__(self) -> str:
        """String representation of RMS calculator."""
        return (f"RMSCalculator(freq={self.system_frequency} Hz, "
                f"fs={self.sampling_rate} Hz, "
                f"samples/cycle={self.samples_per_cycle})")
