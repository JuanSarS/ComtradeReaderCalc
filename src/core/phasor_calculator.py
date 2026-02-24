"""
Phasor Calculator Module
========================

This module computes fundamental frequency phasors from time-domain signals
using discrete Fourier transform methods.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class Phasor:
    """
    Represents a phasor (complex number) with magnitude and angle.
    
    Attributes:
        magnitude (float): Phasor magnitude (RMS value)
        angle_deg (float): Phasor angle in degrees
        angle_rad (float): Phasor angle in radians
        real (float): Real component
        imag (float): Imaginary component
        name (str): Phasor identifier (e.g., 'Va', 'Ia')
    """
    magnitude: float
    angle_deg: float
    angle_rad: float
    real: float
    imag: float
    name: str = ""
    
    @classmethod
    def from_complex(cls, complex_value: complex, name: str = ""):
        """
        Create Phasor from complex number.
        
        Args:
            complex_value (complex): Complex phasor value
            name (str): Phasor identifier
        
        Returns:
            Phasor: Phasor object
        """
        magnitude = np.abs(complex_value)
        angle_rad = np.angle(complex_value)
        angle_deg = np.degrees(angle_rad)
        return cls(
            magnitude=magnitude,
            angle_deg=angle_deg,
            angle_rad=angle_rad,
            real=complex_value.real,
            imag=complex_value.imag,
            name=name
        )
    
    def to_complex(self) -> complex:
        """Convert phasor to complex number."""
        return self.real + 1j * self.imag
    
    def __repr__(self) -> str:
        """String representation in engineering format."""
        return f"{self.name}: {self.magnitude:.3f}∠{self.angle_deg:.2f}°"


class PhasorCalculator:
    """
    Calculate fundamental frequency phasors using discrete Fourier transform.
    
    The phasor represents the magnitude and phase angle of the fundamental
    frequency component, essential for power system analysis and protection.
    
    Typical Usage:
        >>> phasor_calc = PhasorCalculator(system_frequency=60.0, sampling_rate=7200.0)
        >>> va_phasor = phasor_calc.calculate_phasor(voltage_a_signal, time_axis)
        >>> print(f"Voltage A: {va_phasor.magnitude:.2f} V at {va_phasor.angle_deg:.1f}°")
    
    Attributes:
        system_frequency (float): Power system frequency in Hz
        sampling_rate (float): Sampling frequency in Hz
        reference_angle (float): Reference angle for phasor calculations (degrees)
    """
    
    def __init__(self, system_frequency: float = 60.0, sampling_rate: float = 7200.0):
        """
        Initialize the phasor calculator.
        
        Args:
            system_frequency (float): Power system frequency (50 or 60 Hz)
            sampling_rate (float): Sampling rate in Hz
        """
        self.system_frequency: float = system_frequency
        self.sampling_rate: float = sampling_rate
        self.reference_angle: float = 0.0  # degrees
        self._samples_per_cycle: int = 0
        
        self._calculate_parameters()
    
    def _calculate_parameters(self) -> None:
        """Calculate internal parameters for phasor calculation."""
        # TODO: Calculate samples per cycle
        # TODO: Calculate angular frequency (omega)
        pass
    
    def calculate_phasor(self, 
                        signal_data: np.ndarray,
                        time_axis: np.ndarray,
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None,
                        name: str = "") -> Phasor:
        """
        Calculate fundamental frequency phasor using DFT.
        
        Uses one or more complete cycles of the waveform to compute the
        fundamental phasor via discrete Fourier transform at system frequency.
        
        Args:
            signal_data (np.ndarray): Time-domain signal
            time_axis (np.ndarray): Time values in seconds
            start_time (float, optional): Start of analysis window
            end_time (float, optional): End of analysis window
            name (str): Phasor identifier
        
        Returns:
            Phasor: Computed phasor with magnitude and angle
        
        Algorithm:
            X = (2/N) * Σ[x(t) * exp(-j*ω*t)] for fundamental frequency ω
        """
        # TODO: Extract signal segment if time range specified
        # TODO: Implement DFT calculation at fundamental frequency
        # TODO: Convert to phasor representation (magnitude and angle)
        # TODO: Apply reference angle correction
        return Phasor.from_complex(0.0 + 0.0j, name)
    
    def calculate_phasor_sliding_window(self,
                                       signal_data: np.ndarray,
                                       time_axis: np.ndarray,
                                       window_cycles: int = 1) -> pd.DataFrame:
        """
        Calculate phasors using sliding window over entire signal.
        
        Provides time-varying phasor representation, useful for analyzing
        transient behavior and phasor trajectory during faults.
        
        Args:
            signal_data (np.ndarray): Time-domain signal
            time_axis (np.ndarray): Time values
            window_cycles (int): Number of cycles in sliding window (default: 1)
        
        Returns:
            pd.DataFrame: Columns: time, magnitude, angle_deg, real, imag
        """
        # TODO: Implement sliding window DFT
        # TODO: Calculate phasor at each time step
        return pd.DataFrame()
    
    def calculate_three_phase_phasors(self,
                                     phase_a: np.ndarray,
                                     phase_b: np.ndarray,
                                     phase_c: np.ndarray,
                                     time_axis: np.ndarray,
                                     start_time: Optional[float] = None,
                                     end_time: Optional[float] = None) -> Tuple[Phasor, Phasor, Phasor]:
        """
        Calculate phasors for three-phase system.
        
        Args:
            phase_a (np.ndarray): Phase A signal
            phase_b (np.ndarray): Phase B signal
            phase_c (np.ndarray): Phase C signal
            time_axis (np.ndarray): Time values
            start_time (float, optional): Analysis window start
            end_time (float, optional): Analysis window end
        
        Returns:
            Tuple[Phasor, Phasor, Phasor]: Phasors for phases A, B, C
        """
        # TODO: Calculate phasor for each phase
        va = self.calculate_phasor(phase_a, time_axis, start_time, end_time, "Va")
        vb = self.calculate_phasor(phase_b, time_axis, start_time, end_time, "Vb")
        vc = self.calculate_phasor(phase_c, time_axis, start_time, end_time, "Vc")
        return va, vb, vc
    
    def rotate_phasor(self, phasor: Phasor, angle_deg: float) -> Phasor:
        """
        Rotate a phasor by specified angle.
        
        Args:
            phasor (Phasor): Input phasor
            angle_deg (float): Rotation angle in degrees
        
        Returns:
            Phasor: Rotated phasor
        
        Used for reference frame transformations.
        """
        # TODO: Convert to complex, rotate, convert back
        return phasor
    
    def set_reference_angle(self, angle_deg: float) -> None:
        """
        Set reference angle for phasor calculations.
        
        Args:
            angle_deg (float): Reference angle in degrees
        
        Typically, phase A voltage is used as 0° reference.
        """
        self.reference_angle = angle_deg
    
    def phasor_difference(self, phasor1: Phasor, phasor2: Phasor) -> Phasor:
        """
        Calculate the difference between two phasors.
        
        Args:
            phasor1 (Phasor): First phasor
            phasor2 (Phasor): Second phasor
        
        Returns:
            Phasor: Resulting phasor (phasor1 - phasor2)
        
        Used for calculating line-to-line voltages from line-to-neutral voltages.
        """
        # TODO: Convert to complex, subtract, convert back
        return Phasor.from_complex(0.0, "difference")
    
    def get_phasor_array(self, phasors: List[Phasor]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert list of phasors to magnitude and angle arrays.
        
        Args:
            phasors (List[Phasor]): List of phasor objects
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: Arrays of magnitudes and angles
        
        Useful for plotting and further analysis.
        """
        # TODO: Extract magnitudes and angles into arrays
        return np.array([]), np.array([])
    
    def __repr__(self) -> str:
        """String representation of phasor calculator."""
        return (f"PhasorCalculator(freq={self.system_frequency} Hz, "
                f"fs={self.sampling_rate} Hz)")
