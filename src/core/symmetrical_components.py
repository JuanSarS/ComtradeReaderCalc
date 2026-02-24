"""
Symmetrical Components Analysis Module
=======================================

This module implements Fortescue's symmetrical components transformation
for three-phase power system analysis.
"""

import numpy as np
from typing import Tuple, Dict
from dataclasses import dataclass
from .phasor_calculator import Phasor


@dataclass
class SequenceComponents:
    """
    Container for positive, negative, and zero sequence components.
    
    Attributes:
        positive (Phasor): Positive sequence component (V1 or I1)
        negative (Phasor): Negative sequence component (V2 or I2)
        zero (Phasor): Zero sequence component (V0 or I0)
        component_type (str): 'voltage' or 'current'
    """
    positive: Phasor
    negative: Phasor
    zero: Phasor
    component_type: str = 'voltage'
    
    def get_magnitudes(self) -> Dict[str, float]:
        """Get RMS magnitudes of sequence components."""
        return {
            'positive': self.positive.magnitude,
            'negative': self.negative.magnitude,
            'zero': self.zero.magnitude
        }
    
    def get_imbalance_factors(self) -> Dict[str, float]:
        """
        Calculate voltage/current imbalance factors.
        
        Returns:
            Dict with negative and zero sequence imbalance percentages
        
        Negative sequence imbalance = (V2/V1) × 100%
        Zero sequence imbalance = (V0/V1) × 100%
        """
        if self.positive.magnitude == 0:
            return {'negative_imbalance': 0.0, 'zero_imbalance': 0.0}
        
        return {
            'negative_imbalance': (self.negative.magnitude / self.positive.magnitude) * 100,
            'zero_imbalance': (self.zero.magnitude / self.positive.magnitude) * 100
        }
    
    def __repr__(self) -> str:
        """String representation of sequence components."""
        return (f"SequenceComponents({self.component_type}):\n"
                f"  Positive: {self.positive}\n"
                f"  Negative: {self.negative}\n"
                f"  Zero: {self.zero}")


class SymmetricalComponents:
    """
    Symmetrical components calculator using Fortescue's transformation.
    
    Decomposes unbalanced three-phase voltages/currents into three balanced
    sets: positive, negative, and zero sequence components.
    
    Mathematical Foundation:
        [V0]   [1  1   1 ] [Va]
        [V1] = [1  a   a²] [Vb] / 3
        [V2]   [1  a²  a ] [Vc]
        
        where a = 1∠120° = exp(j*2π/3)
    
    Typical Usage:
        >>> sym_calc = SymmetricalComponents()
        >>> sequence = sym_calc.calculate_sequence_components(Va, Vb, Vc)
        >>> print(f"Positive seq: {sequence.positive.magnitude:.2f} V")
        >>> imbalance = sequence.get_imbalance_factors()
    
    Attributes:
        a_operator (complex): Unit phasor at 120° (Fortescue operator)
        transformation_matrix (np.ndarray): Forward transformation matrix
        inverse_matrix (np.ndarray): Inverse transformation matrix
    """
    
    def __init__(self):
        """Initialize symmetrical components calculator."""
        # Fortescue operator: a = 1∠120° = exp(j*2π/3)
        self.a_operator: complex = np.exp(1j * 2 * np.pi / 3)
        self.transformation_matrix: np.ndarray = np.array([])
        self.inverse_matrix: np.ndarray = np.array([])
        
        self._build_transformation_matrices()
    
    def _build_transformation_matrices(self) -> None:
        """
        Build Fortescue transformation matrices.
        
        Forward transformation: [V012] = [T] * [Vabc]
        Inverse transformation: [Vabc] = [T]^-1 * [V012]
        """
        # TODO: Build transformation matrix using a_operator
        # TODO: Build inverse transformation matrix
        pass
    
    def calculate_sequence_components(self,
                                     phase_a: Phasor,
                                     phase_b: Phasor,
                                     phase_c: Phasor,
                                     component_type: str = 'voltage') -> SequenceComponents:
        """
        Calculate positive, negative, and zero sequence components.
        
        Args:
            phase_a (Phasor): Phase A phasor
            phase_b (Phasor): Phase B phasor
            phase_c (Phasor): Phase C phasor
            component_type (str): 'voltage' or 'current'
        
        Returns:
            SequenceComponents: Object containing V0, V1, V2 (or I0, I1, I2)
        
        Formulas:
            V0 = (Va + Vb + Vc) / 3
            V1 = (Va + a*Vb + a²*Vc) / 3
            V2 = (Va + a²*Vb + a*Vc) / 3
        """
        # TODO: Convert phasors to complex numbers
        # TODO: Apply Fortescue transformation
        # TODO: Calculate sequence components
        # TODO: Convert results to Phasor objects
        
        v0 = Phasor.from_complex(0.0 + 0.0j, "V0" if component_type == 'voltage' else "I0")
        v1 = Phasor.from_complex(0.0 + 0.0j, "V1" if component_type == 'voltage' else "I1")
        v2 = Phasor.from_complex(0.0 + 0.0j, "V2" if component_type == 'voltage' else "I2")
        
        return SequenceComponents(
            positive=v1,
            negative=v2,
            zero=v0,
            component_type=component_type
        )
    
    def reconstruct_phase_components(self,
                                    sequence: SequenceComponents) -> Tuple[Phasor, Phasor, Phasor]:
        """
        Reconstruct phase components from sequence components (inverse transform).
        
        Args:
            sequence (SequenceComponents): Sequence components
        
        Returns:
            Tuple[Phasor, Phasor, Phasor]: Reconstructed phase A, B, C
        
        Formulas:
            Va = V0 + V1 + V2
            Vb = V0 + a²*V1 + a*V2
            Vc = V0 + a*V1 + a²*V2
        
        Used for validation and understanding sequence contribution to each phase.
        """
        # TODO: Convert sequence phasors to complex
        # TODO: Apply inverse transformation
        # TODO: Convert results to Phasor objects
        
        va = Phasor.from_complex(0.0, "Va")
        vb = Phasor.from_complex(0.0, "Vb")
        vc = Phasor.from_complex(0.0, "Vc")
        
        return va, vb, vc
    
    def identify_fault_type(self, 
                           voltage_seq: SequenceComponents,
                           current_seq: SequenceComponents,
                           threshold: float = 0.1) -> str:
        """
        Identify fault type based on sequence component patterns.
        
        Args:
            voltage_seq (SequenceComponents): Voltage sequence components
            current_seq (SequenceComponents): Current sequence components
            threshold (float): Per-unit threshold for component significance
        
        Returns:
            str: Fault type description
        
        Fault Type Identification:
            - Three-phase: I2≈0, I0≈0, I1>0
            - Single line-to-ground: I0>0, I2>0, I1>0
            - Line-to-line: I0≈0, I2>0, I1>0
            - Double line-to-ground: I0>0, I2>0, I1>0 (different pattern)
        """
        # TODO: Analyze sequence component patterns
        # TODO: Apply fault identification logic
        # TODO: Return fault type string
        return "Unknown"
    
    def calculate_sequence_impedances(self,
                                     voltage_seq: SequenceComponents,
                                     current_seq: SequenceComponents) -> Dict[str, complex]:
        """
        Calculate sequence impedances from voltage and current components.
        
        Args:
            voltage_seq (SequenceComponents): Voltage sequences
            current_seq (SequenceComponents): Current sequences
        
        Returns:
            Dict[str, complex]: Positive, negative, zero sequence impedances
        
        Z1 = V1 / I1
        Z2 = V2 / I2  
        Z0 = V0 / I0
        
        Important for system characterization and fault analysis.
        """
        # TODO: Calculate impedances for each sequence
        # TODO: Handle division by zero
        return {
            'Z1': 0.0 + 0.0j,
            'Z2': 0.0 + 0.0j,
            'Z0': 0.0 + 0.0j
        }
    
    def calculate_unbalance_severity(self, sequence: SequenceComponents) -> str:
        """
        Assess the severity of voltage/current unbalance.
        
        Args:
            sequence (SequenceComponents): Sequence components
        
        Returns:
            str: Severity classification ('Balanced', 'Minor', 'Moderate', 'Severe')
        
        Based on IEEE and NEMA standards for voltage unbalance:
            - <1%: Balanced
            - 1-2%: Minor
            - 2-5%: Moderate  
            - >5%: Severe
        """
        # TODO: Calculate imbalance factors
        # TODO: Classify severity based on standards
        return "Balanced"
    
    def get_a_operator(self) -> complex:
        """
        Get the Fortescue 'a' operator.
        
        Returns:
            complex: a = 1∠120° = exp(j*2π/3)
        """
        return self.a_operator
    
    def __repr__(self) -> str:
        """String representation."""
        return "SymmetricalComponents(Fortescue Transformation)"
