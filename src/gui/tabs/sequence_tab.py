"""
Sequence Components Tab
=======================

This tab displays symmetrical component analysis results.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from typing import Optional

from ...core.symmetrical_components import SymmetricalComponents, SequenceComponents


class SequenceTab(QWidget):
    """
    Tab for displaying symmetrical component analysis.
    
    Features:
    - Positive, negative, zero sequence phasor diagrams
    - Sequence component magnitude bar charts
    - Imbalance factor calculations
    - Fault type identification
    
    Attributes:
        symmetrical_components (SymmetricalComponents): Reference to symmetrical components calculator
        figure (Figure): Matplotlib figure for plotting
        canvas (FigureCanvas): Qt canvas widget
    """
    
    def __init__(self, symmetrical_components: SymmetricalComponents):
        """
        Initialize the sequence components tab.
        
        Args:
            symmetrical_components (SymmetricalComponents): Symmetrical components instance
        """
        super().__init__()
        
        self.symmetrical_components = symmetrical_components
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvas] = None
        
        self.voltage_sequence: Optional[SequenceComponents] = None
        self.current_sequence: Optional[SequenceComponents] = None
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Horizontal layout for plots and results
        content_layout = QHBoxLayout()
        
        # Matplotlib canvas (left side)
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_widget.setLayout(plot_layout)
        
        self._create_plot_canvas()
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)
        
        content_layout.addWidget(plot_widget, stretch=2)
        
        # Results panel (right side)
        results_panel = self._create_results_panel()
        content_layout.addWidget(results_panel, stretch=1)
        
        layout.addLayout(content_layout)
    
    def _create_control_panel(self) -> QWidget:
        """
        Create control panel.
        
        Returns:
            QWidget: Control panel widget
        """
        control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_widget.setLayout(control_layout)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate Sequence Components")
        self.calculate_button.clicked.connect(self.calculate_sequence)
        control_layout.addWidget(self.calculate_button)
        
        # Fault identification button
        self.identify_button = QPushButton("Identify Fault Type")
        self.identify_button.clicked.connect(self.identify_fault)
        control_layout.addWidget(self.identify_button)
        
        control_layout.addStretch()
        
        return control_widget
    
    def _create_plot_canvas(self) -> None:
        """Create matplotlib figure and canvas."""
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create subplots
        # Top row: Voltage sequence phasors (polar)
        self.ax_v_seq_polar = self.figure.add_subplot(2, 2, 1, projection='polar')
        self.ax_v_seq_polar.set_title("Voltage Sequence Phasors")
        
        # Top right: Voltage sequence magnitudes (bar chart)
        self.ax_v_seq_bar = self.figure.add_subplot(2, 2, 2)
        self.ax_v_seq_bar.set_title("Voltage Sequence Magnitudes")
        
        # Bottom row: Current sequence phasors (polar)
        self.ax_i_seq_polar = self.figure.add_subplot(2, 2, 3, projection='polar')
        self.ax_i_seq_polar.set_title("Current Sequence Phasors")
        
        # Bottom right: Current sequence magnitudes (bar chart)
        self.ax_i_seq_bar = self.figure.add_subplot(2, 2, 4)
        self.ax_i_seq_bar.set_title("Current Sequence Magnitudes")
        
        self.figure.tight_layout()
    
    def _create_results_panel(self) -> QWidget:
        """
        Create results panel with tables and labels.
        
        Returns:
            QWidget: Results panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Voltage sequence results
        v_group = QGroupBox("Voltage Sequence Components")
        v_layout = QVBoxLayout()
        v_group.setLayout(v_layout)
        
        self.voltage_table = QTableWidget()
        self.voltage_table.setColumnCount(3)
        self.voltage_table.setHorizontalHeaderLabels(["Sequence", "Magnitude", "Angle (°)"])
        self.voltage_table.setRowCount(3)
        self.voltage_table.setVerticalHeaderLabels(["V1 (Pos)", "V2 (Neg)", "V0 (Zero)"])
        v_layout.addWidget(self.voltage_table)
        
        layout.addWidget(v_group)
        
        # Current sequence results
        i_group = QGroupBox("Current Sequence Components")
        i_layout = QVBoxLayout()
        i_group.setLayout(i_layout)
        
        self.current_table = QTableWidget()
        self.current_table.setColumnCount(3)
        self.current_table.setHorizontalHeaderLabels(["Sequence", "Magnitude", "Angle (°)"])
        self.current_table.setRowCount(3)
        self.current_table.setVerticalHeaderLabels(["I1 (Pos)", "I2 (Neg)", "I0 (Zero)"])
        i_layout.addWidget(self.current_table)
        
        layout.addWidget(i_group)
        
        # Imbalance factors
        imbalance_group = QGroupBox("Imbalance Factors")
        imbalance_layout = QVBoxLayout()
        imbalance_group.setLayout(imbalance_layout)
        
        self.v_neg_imbalance_label = QLabel("Voltage Neg Seq: -- %")
        self.v_zero_imbalance_label = QLabel("Voltage Zero Seq: -- %")
        self.i_neg_imbalance_label = QLabel("Current Neg Seq: -- %")
        self.i_zero_imbalance_label = QLabel("Current Zero Seq: -- %")
        
        imbalance_layout.addWidget(self.v_neg_imbalance_label)
        imbalance_layout.addWidget(self.v_zero_imbalance_label)
        imbalance_layout.addWidget(self.i_neg_imbalance_label)
        imbalance_layout.addWidget(self.i_zero_imbalance_label)
        
        layout.addWidget(imbalance_group)
        
        # Fault type
        fault_group = QGroupBox("Fault Identification")
        fault_layout = QVBoxLayout()
        fault_group.setLayout(fault_layout)
        
        self.fault_type_label = QLabel("Fault Type: Unknown")
        fault_layout.addWidget(self.fault_type_label)
        
        layout.addWidget(fault_group)
        
        layout.addStretch()
        
        return panel
    
    def calculate_sequence(self) -> None:
        """Calculate symmetrical components."""
        # TODO: Get phasors from phasor calculator
        # TODO: Calculate sequence components for voltage and current
        # TODO: Update plots and tables
        
        pass
    
    def identify_fault(self) -> None:
        """Identify fault type from sequence pattern."""
        # TODO: Use symmetrical_components.identify_fault_type()
        # TODO: Update fault_type_label
        
        pass
    
    def update_plot(self) -> None:
        """Update sequence component plots."""
        # TODO: Clear plots
        # TODO: Plot sequence phasors on polar plots
        # TODO: Plot magnitude bar charts
        # TODO: Update canvas
        
        self.ax_v_seq_polar.clear()
        self.ax_v_seq_bar.clear()
        self.ax_i_seq_polar.clear()
        self.ax_i_seq_bar.clear()
        
        # TODO: Implement actual plotting
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_results(self) -> None:
        """Update results tables and labels."""
        # TODO: Update voltage sequence table
        # TODO: Update current sequence table
        # TODO: Update imbalance labels
        
        if self.voltage_sequence:
            # TODO: Populate voltage table
            imbalance = self.voltage_sequence.get_imbalance_factors()
            self.v_neg_imbalance_label.setText(
                f"Voltage Neg Seq: {imbalance['negative_imbalance']:.2f} %"
            )
            self.v_zero_imbalance_label.setText(
                f"Voltage Zero Seq: {imbalance['zero_imbalance']:.2f} %"
            )
        
        if self.current_sequence:
            # TODO: Populate current table
            imbalance = self.current_sequence.get_imbalance_factors()
            self.i_neg_imbalance_label.setText(
                f"Current Neg Seq: {imbalance['negative_imbalance']:.2f} %"
            )
            self.i_zero_imbalance_label.setText(
                f"Current Zero Seq: {imbalance['zero_imbalance']:.2f} %"
            )
