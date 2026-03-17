"""
Phase Triangle and Barycenter Analyzer Module
==============================================

This module analyzes the geometric properties of phase voltage/current triangles
and tracks the barycenter (centroid) motion during fault transitions.
"""

import numpy as np
from typing import Tuple, List, Optional
from dataclasses import dataclass
from src.core.analysis.phasor_calculator import Phasor


@dataclass
class TriangleProperties:
    """
    Geometric properties of a three-phase triangle.
    
    Attributes:
        vertices (np.ndarray): Complex coordinates of triangle vertices [Va, Vb, Vc]
        barycenter (complex): Triangle centroid (average of vertices)
        area (float): Triangle area
        perimeter (float): Triangle perimeter
        side_lengths (Tuple[float, float, float]): Lengths of sides AB, BC, CA
        is_balanced (bool): True if triangle is equilateral (balanced system)
        asymmetry_factor (float): Measure of departure from equilateral shape
    """
    vertices: np.ndarray
    barycenter: complex
    area: float
    perimeter: float
    side_lengths: Tuple[float, float, float]
    is_balanced: bool
    asymmetry_factor: float
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"TriangleProperties(area={self.area:.2f}, "
                f"balanced={self.is_balanced}, "
                f"barycenter={abs(self.barycenter):.2f}∠{np.angle(self.barycenter, deg=True):.1f}°)")


class TriangleAnalyzer:
    """
    Analyzer for phase triangle geometry and barycenter motion.
    
    In three-phase systems, plotting the three phasors as vertices of a triangle
    provides visual insight into system balance and fault conditions:
    - Balanced system: Equilateral triangle with barycenter at origin
    - Unbalanced system: Irregular triangle with shifted barycenter
    - Fault condition: Distorted triangle showing fault characteristics
    
    The barycenter motion from pre-fault to fault condition reveals the
    nature and severity of the disturbance.
    
    Typical Usage:
        >>> analyzer = TriangleAnalyzer()
        >>> prefault_props = analyzer.analyze_triangle(Va_pre, Vb_pre, Vc_pre)
        >>> fault_props = analyzer.analyze_triangle(Va_fault, Vb_fault, Vc_fault)
        >>> trajectory = analyzer.calculate_barycenter_trajectory(
        ...     prefault_props, fault_props, num_steps=50)
    
    Attributes:
        history (List[TriangleProperties]): Historical triangle states
    """
    
    def __init__(self):
        """Initialize the triangle analyzer."""
        self.history: List[TriangleProperties] = []
        self._balance_tolerance: float = 0.02  # 2% tolerance for balance detection
    
    def analyze_triangle(self,
                        phase_a: Phasor,
                        phase_b: Phasor,
                        phase_c: Phasor,
                        store_history: bool = False) -> TriangleProperties:
        """
        Analyze geometric properties of phase triangle.
        
        Args:
            phase_a (Phasor): Phase A phasor
            phase_b (Phasor): Phase B phasor
            phase_c (Phasor): Phase C phasor
            store_history (bool): If True, store in history list
        
        Returns:
            TriangleProperties: Complete geometric analysis
        
        The triangle vertices are the phasor tips in the complex plane.
        """
        va = phase_a.to_complex()
        vb = phase_b.to_complex()
        vc = phase_c.to_complex()
        vertices = np.array([va, vb, vc])
        barycenter = (va + vb + vc) / 3.0
        area = self.calculate_triangle_area(vertices)
        ab = abs(vb - va)
        bc = abs(vc - vb)
        ca = abs(va - vc)
        side_lengths = (ab, bc, ca)
        perimeter = ab + bc + ca
        balanced = self.is_balanced_triangle(side_lengths)
        asym = self.calculate_asymmetry_factor(side_lengths)
        props = TriangleProperties(
            vertices=vertices,
            barycenter=barycenter,
            area=area,
            perimeter=perimeter,
            side_lengths=side_lengths,
            is_balanced=balanced,
            asymmetry_factor=asym,
        )
        if store_history:
            self.history.append(props)
        return props
    
    def calculate_barycenter(self,
                           phase_a: Phasor,
                           phase_b: Phasor,
                           phase_c: Phasor) -> complex:
        """
        Calculate triangle barycenter (centroid).
        
        Args:
            phase_a (Phasor): Phase A phasor
            phase_b (Phasor): Phase B phasor
            phase_c (Phasor): Phase C phasor
        
        Returns:
            complex: Barycenter position in complex plane
        
        Formula: G = (Va + Vb + Vc) / 3
        
        Note: For balanced systems, barycenter = 0 (origin)
              For unbalanced systems, barycenter ≠ 0
        """
        return (phase_a.to_complex() + phase_b.to_complex() + phase_c.to_complex()) / 3.0
    
    def calculate_triangle_area(self, vertices: np.ndarray) -> float:
        """
        Calculate area of triangle using cross product method.
        
        Args:
            vertices (np.ndarray): Array of 3 complex numbers [Va, Vb, Vc]
        
        Returns:
            float: Triangle area
        
        Formula: Area = 0.5 * |Im((Vb - Va) * conj(Vc - Va))|
        """
        if len(vertices) < 3:
            return 0.0
        va, vb, vc = vertices[0], vertices[1], vertices[2]
        return 0.5 * abs(((vb - va) * np.conj(vc - va)).imag)
    
    def is_balanced_triangle(self, 
                           side_lengths: Tuple[float, float, float],
                           tolerance: float = 0.02) -> bool:
        """
        Check if triangle is balanced (equilateral within tolerance).
        
        Args:
            side_lengths (Tuple[float, float, float]): Triangle side lengths
            tolerance (float): Relative tolerance for equality (default: 2%)
        
        Returns:
            bool: True if triangle is balanced
        
        A balanced three-phase system forms an equilateral triangle.
        """
        if max(side_lengths) == 0:
            return False
        mean_side = sum(side_lengths) / 3.0
        return all(abs(s - mean_side) / mean_side < tolerance for s in side_lengths)
    
    def calculate_asymmetry_factor(self,
                                  side_lengths: Tuple[float, float, float]) -> float:
        """
        Calculate triangle asymmetry factor.
        
        Args:
            side_lengths (Tuple[float, float, float]): Side lengths
        
        Returns:
            float: Asymmetry factor (0 = perfect equilateral, higher = more asymmetric)
        
        Defined as standard deviation of side lengths normalized by mean.
        """
        sides = np.array(side_lengths, dtype=float)
        mean_s = np.mean(sides)
        if mean_s == 0:
            return 0.0
        return float(np.std(sides) / mean_s)
    
    def calculate_barycenter_trajectory(self,
                                       initial_state: TriangleProperties,
                                       final_state: TriangleProperties,
                                       num_steps: int = 50,
                                       interpolation: str = 'linear') -> np.ndarray:
        """
        Calculate barycenter trajectory from initial to final state.
        
        Args:
            initial_state (TriangleProperties): Pre-fault triangle state
            final_state (TriangleProperties): Fault triangle state
            num_steps (int): Number of interpolation steps
            interpolation (str): 'linear' or 'smooth'
        
        Returns:
            np.ndarray: Array of complex barycenter positions along trajectory
        
        Used for animation of triangle transition during fault.
        """
        b0 = initial_state.barycenter
        b1 = final_state.barycenter
        t = np.linspace(0, 1, num_steps)
        if interpolation == 'smooth':
            t = t * t * (3 - 2 * t)  # smoothstep
        return b0 + (b1 - b0) * t
    
    def animate_triangle_transition(self,
                                   initial_phasors: Tuple[Phasor, Phasor, Phasor],
                                   final_phasors: Tuple[Phasor, Phasor, Phasor],
                                   num_frames: int = 50) -> List[TriangleProperties]:
        """
        Generate animation frames for triangle transition.
        
        Args:
            initial_phasors (Tuple[Phasor, Phasor, Phasor]): Pre-fault phasors (Va, Vb, Vc)
            final_phasors (Tuple[Phasor, Phasor, Phasor]): Fault phasors (Va, Vb, Vc)
            num_frames (int): Number of animation frames
        
        Returns:
            List[TriangleProperties]: List of triangle states for each frame
        
        Each vertex interpolates independently from initial to final position.
        """
        frames = []
        for i in range(num_frames):
            alpha = i / max(num_frames - 1, 1)
            # Interpolate each phasor complex value
            def interp_phasor(p0, p1, a, nm):
                c = p0.to_complex() * (1 - a) + p1.to_complex() * a
                return Phasor.from_complex(c, nm)
            pa = interp_phasor(initial_phasors[0], final_phasors[0], alpha, 'Va')
            pb = interp_phasor(initial_phasors[1], final_phasors[1], alpha, 'Vb')
            pc = interp_phasor(initial_phasors[2], final_phasors[2], alpha, 'Vc')
            frames.append(self.analyze_triangle(pa, pb, pc))
        return frames
    
    def calculate_barycenter_displacement(self,
                                         state1: TriangleProperties,
                                         state2: TriangleProperties) -> Tuple[float, float]:
        """
        Calculate barycenter displacement between two states.
        
        Args:
            state1 (TriangleProperties): First state
            state2 (TriangleProperties): Second state
        
        Returns:
            Tuple[float, float]: (magnitude of displacement, angle in degrees)
        
        Quantifies how far the barycenter moved during transition.
        """
        disp = state2.barycenter - state1.barycenter
        return float(abs(disp)), float(np.degrees(np.angle(disp)))
    
    def identify_fault_from_triangle(self, 
                                    triangle: TriangleProperties,
                                    balanced_reference: TriangleProperties) -> str:
        """
        Identify potential fault type from triangle deformation.
        
        Args:
            triangle (TriangleProperties): Current triangle state
            balanced_reference (TriangleProperties): Reference balanced state
        
        Returns:
            str: Fault type indication based on geometric analysis
        
        Different fault types produce characteristic triangle deformations:
        - SLG: One vertex collapses toward origin
        - LL: Two vertices move closer together
        - 3-phase: Triangle shrinks uniformly
        """
        # TODO: Analyze triangle deformation pattern
        # TODO: Compare with known fault signatures
        return "Unknown"
    
    def get_history(self) -> List[TriangleProperties]:
        """
        Get historical triangle states.
        
        Returns:
            List[TriangleProperties]: History of analyzed triangles
        """
        return self.history
    
    def clear_history(self) -> None:
        """Clear stored triangle history."""
        self.history.clear()
    
    def export_trajectory_data(self, trajectory: np.ndarray) -> np.ndarray:
        """
        Export trajectory data for plotting.
        
        Args:
            trajectory (np.ndarray): Array of complex barycenter positions
        
        Returns:
            np.ndarray: Nx2 array with columns [real, imaginary]
        """
        # TODO: Convert complex array to real/imag columns
        return np.column_stack((np.real(trajectory), np.imag(trajectory)))
    
    def __repr__(self) -> str:
        """String representation."""
        return f"TriangleAnalyzer(history_length={len(self.history)})"
