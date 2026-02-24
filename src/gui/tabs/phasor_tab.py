"""
Phasor Diagram Tab
==================

This tab displays phasor diagrams (vector diagrams) for voltage and current.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QDoubleSpinBox, QComboBox,
                             QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from typing import Optional, List

from ...core.phasor_calculator import PhasorCalculator, Phasor


class PhasorTab(QWidget):
    """
    Tab for displaying phasor diagrams.
    
    Features:
    - Polar plots showing voltage and current phasors
    - Phasor magnitude and angle table
    - Pre-fault vs fault state comparison
    - Reference phasor selection
    
    Attributes:
        phasor_calculator (PhasorCalculator): Reference to phasor calculator
        figure (Figure): Matplotlib figure for plotting
        canvas (FigureCanvas): Qt canvas widget
    """
    
    def __init__(self, phasor_calculator: PhasorCalculator):
        """
        Initialize the phasor diagram tab.
        
        Args:
            phasor_calculator (PhasorCalculator): Phasor calculator instance
        """
        super().__init__()
        
        self.phasor_calculator = phasor_calculator
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvas] = None
        
        self.voltage_phasors: List[Phasor] = []
        self.current_phasors: List[Phasor] = []
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Horizontal layout for plots and table
        content_layout = QHBoxLayout()
        
        # Matplotlib canvas (left side)
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_widget.setLayout(plot_layout)
        
        self._create_plot_canvas()
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)
        
        content_layout.addWidget(plot_widget, stretch=2)
        
        # Results table (right side)
        self.results_table = self._create_results_table()
        content_layout.addWidget(self.results_table, stretch=1)
        
        layout.addLayout(content_layout)
    
    def _create_control_panel(self) -> QWidget:
        """
        Create control panel for phasor settings.
        
        Returns:
            QWidget: Control panel widget
        """
        # TODO: Add time range selectors for steady-state analysis
        # TODO: Add reference phasor selector
        # TODO: Add calculate button
        
        control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_widget.setLayout(control_layout)
        
        # Time range group
        time_group = QGroupBox("Analysis Time Range")
        time_layout = QHBoxLayout()
        time_group.setLayout(time_layout)
        
        time_layout.addWidget(QLabel("Start (s):"))
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setDecimals(4)
        self.start_time_spin.setMinimum(0.0)
        time_layout.addWidget(self.start_time_spin)
        
        time_layout.addWidget(QLabel("End (s):"))
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setDecimals(4)
        self.end_time_spin.setMinimum(0.0)
        time_layout.addWidget(self.end_time_spin)
        
        control_layout.addWidget(time_group)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate Phasors")
        self.calculate_button.clicked.connect(self.calculate_phasors)
        control_layout.addWidget(self.calculate_button)
        
        control_layout.addStretch()
        
        return control_widget
    
    def _create_plot_canvas(self) -> None:
        """Create matplotlib figure and canvas for polar plots."""
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create polar subplots
        self.ax_voltage_phasor = self.figure.add_subplot(1, 2, 1, projection='polar')
        self.ax_current_phasor = self.figure.add_subplot(1, 2, 2, projection='polar')
        
        self.ax_voltage_phasor.set_title("Voltage Phasors")
        self.ax_current_phasor.set_title("Current Phasors")
        
        self.figure.tight_layout()
    
    def _create_results_table(self) -> QTableWidget:
        """
        Create table for displaying phasor values.
        
        Returns:
            QTableWidget: Table widget for results
        """
        # TODO: Create table with columns: Channel, Magnitude, Angle
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Channel", "Magnitude", "Angle (°)"])
        
        return table
    
    def calculate_phasors(self) -> None:
        """Calculate phasors for selected time range."""
        # TODO: Get instantaneous data for time range
        # TODO: Calculate phasors using phasor_calculator
        # TODO: Update plots and table
        
        pass
    
    def update_plot(self) -> None:
        """Update the phasor diagrams."""
        # TODO: Clear and redraw polar plots
        # TODO: Plot voltage phasors
        # TODO: Plot current phasors
        # TODO: Add phasor labels
        
        self.ax_voltage_phasor.clear()
        self.ax_current_phasor.clear()
        
        # TODO: Implement actual phasor plotting
        # Example:
        # for phasor in self.voltage_phasors:
        #     self.ax_voltage_phasor.arrow(0, 0, phasor.angle_rad, phasor.magnitude, ...)
        
        self.ax_voltage_phasor.set_title("Voltage Phasors")
        self.ax_current_phasor.set_title("Current Phasors")
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_results_table(self) -> None:
        """Update results table with phasor values."""
        # TODO: Clear table
        # TODO: Add rows for each phasor
        # TODO: Format values appropriately
        
        self.results_table.setRowCount(0)
        
        # Add voltage phasors
        for phasor in self.voltage_phasors:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(phasor.name))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{phasor.magnitude:.2f}"))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{phasor.angle_deg:.2f}"))
        
        # Add current phasors
        for phasor in self.current_phasors:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(phasor.name))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{phasor.magnitude:.2f}"))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{phasor.angle_deg:.2f}"))
