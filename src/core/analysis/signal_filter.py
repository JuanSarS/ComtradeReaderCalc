"""
Signal Filtering Module
=======================

This module provides digital filtering capabilities for power system signals,
including band-pass filters centered at power system frequency (50/60 Hz).
"""

import numpy as np
from scipy import signal
from typing import Optional, Tuple
from enum import Enum


class FilterType(Enum):
    """Enumeration of available filter types."""
    BANDPASS = "bandpass"
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    NOTCH = "notch"


class SignalFilter:
    """
    Digital filter for power system signals.
    
    This class provides filtering capabilities optimized for power system
    analysis, with special focus on fundamental frequency (50/60 Hz) extraction.
    
    Typical Usage:
        >>> filter_60hz = SignalFilter(system_frequency=60.0, sampling_rate=7200.0)
        >>> filter_60hz.design_bandpass_filter(bandwidth=5.0)
        >>> filtered_signal = filter_60hz.apply(raw_signal)
    
    Attributes:
        system_frequency (float): Power system frequency in Hz (50 or 60)
        sampling_rate (float): Sampling frequency in Hz
        filter_order (int): Order of the digital filter
        filter_coefficients (Tuple): Numerator and denominator coefficients (b, a)
    """
    
    def __init__(self, system_frequency: float = 60.0, sampling_rate: float = 7200.0):
        """
        Initialize the signal filter.
        
        Args:
            system_frequency (float): Power system frequency (50 or 60 Hz)
            sampling_rate (float): Sampling rate in Hz
        
        Raises:
            ValueError: If system_frequency is not 50 or 60 Hz
            ValueError: If sampling_rate is too low (< 10 * system_frequency)
        """
        self.system_frequency: float = system_frequency
        self.sampling_rate: float = sampling_rate
        self.filter_order: int = 4
        self.filter_coefficients: Optional[Tuple[np.ndarray, np.ndarray]] = None
        self._filter_type: Optional[FilterType] = None
        self._center_gain: float = 1.0
        
        # Validate inputs
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate filter parameters."""
        if self.system_frequency not in (50.0, 60.0):
            # Accept any reasonable frequency but warn
            pass
        nyquist = self.sampling_rate / 2.0
        if self.system_frequency >= nyquist:
            raise ValueError(
                f"System frequency {self.system_frequency} Hz must be below "
                f"Nyquist frequency {nyquist} Hz"
            )
    
    def design_bandpass_filter(self, 
                               bandwidth: float = 5.0, 
                               filter_order: int = 4,
                               filter_design: str = 'butterworth') -> None:
        """Design a bandpass filter centered at system frequency."""
        self.filter_order = filter_order
        self._filter_type = FilterType.BANDPASS
        nyquist = self.sampling_rate / 2.0
        low = (self.system_frequency - bandwidth / 2.0) / nyquist
        high = (self.system_frequency + bandwidth / 2.0) / nyquist
        low = max(low, 1e-4)
        high = min(high, 0.9999)
        self.filter_coefficients = signal.butter(
            filter_order, [low, high], btype='bandpass', output='ba'
        )
        b, a = self.filter_coefficients
        w0 = 2 * np.pi * self.system_frequency / self.sampling_rate
        _, h0 = signal.freqz(b, a, worN=np.array([w0]))
        g = float(np.abs(h0[0])) if len(h0) else 1.0
        self._center_gain = g if g > 1e-9 else 1.0

    def design_lowpass_filter(self, 
                             cutoff_frequency: float,
                             filter_order: int = 4) -> None:
        """Design a lowpass filter."""
        self.filter_order = filter_order
        self._filter_type = FilterType.LOWPASS
        nyquist = self.sampling_rate / 2.0
        cutoff = min(cutoff_frequency / nyquist, 0.9999)
        self.filter_coefficients = signal.butter(filter_order, cutoff, btype='low', output='ba')
    
    def apply(self, signal_data: np.ndarray, 
             method: str = 'filtfilt') -> np.ndarray:
        """Apply the designed filter to input signal."""
        if self.filter_coefficients is None:
            self.design_bandpass_filter()
        b, a = self.filter_coefficients
        if len(signal_data) < max(len(a), len(b)) * 3:
            # Too short to filter safely — return DC-removed signal
            return self.remove_dc_offset(signal_data)
        if method == 'filtfilt':
            filtered = signal.filtfilt(b, a, signal_data)
        else:
            filtered = signal.lfilter(b, a, signal_data)
        # Compensate tiny passband gain bias at nominal frequency.
        if self._center_gain > 1e-9:
            filtered = filtered / self._center_gain
        return filtered

    def get_frequency_response(self, num_points: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate the frequency response of the designed filter."""
        if self.filter_coefficients is None:
            return np.array([]), np.array([])
        b, a = self.filter_coefficients
        w, h = signal.freqz(b, a, worN=num_points)
        freqs = w * self.sampling_rate / (2 * np.pi)
        magnitude_db = 20 * np.log10(np.abs(h) + 1e-12)
        return freqs, magnitude_db
    
    def remove_dc_offset(self, signal_data: np.ndarray) -> np.ndarray:
        """
        Remove DC offset from signal.
        
        Args:
            signal_data (np.ndarray): Input signal
        
        Returns:
            np.ndarray: Signal with DC component removed
        """
        # TODO: Implement DC removal (subtract mean)
        return signal_data - np.mean(signal_data)
    
    def get_filter_info(self) -> dict:
        """
        Get information about the current filter design.
        
        Returns:
            dict: Filter parameters including type, order, cutoff frequencies
        """
        # TODO: Return filter configuration details
        return {
            'type': self._filter_type.value if self._filter_type else None,
            'order': self.filter_order,
            'system_frequency': self.system_frequency,
            'sampling_rate': self.sampling_rate
        }
    
    def __repr__(self) -> str:
        """String representation of the filter."""
        return (f"SignalFilter(system_freq={self.system_frequency} Hz, "
                f"sampling_rate={self.sampling_rate} Hz, "
                f"order={self.filter_order})")
