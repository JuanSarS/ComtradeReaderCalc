"""
Phase Triangle Visualization Tab
=================================

This tab displays phase triangle geometry and barycenter motion.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QSlider, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from typing import Optional, List

from ...core.triangle_analyzer import TriangleAnalyzer, TriangleProperties


class TriangleTab(QWidget):
    """
    Tab for phase triangle visualization and barycenter analysis.
    
    Features:
    - Triangle plot showing phase phasor vertices
    - Barycenter (centroid) marker
    - Animation of triangle transition from pre-fault to fault
    - Triangle properties display (area, perimeter, balance)
    - Barycenter trajectory plot
    
    Attributes:
        triangle_analyzer (TriangleAnalyzer): Reference to triangle analyzer
        figure (Figure): Matplotlib figure for plotting
        canvas (FigureCanvas): Qt canvas widget
    """
    
    def __init__(self, triangle_analyzer: TriangleAnalyzer):
        """
        Initialize the triangle visualization tab.
        
        Args:
            triangle_analyzer (TriangleAnalyzer): Triangle analyzer instance
        """
        super().__init__()
        
        self.triangle_analyzer = triangle_analyzer
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvas] = None
        
        self.prefault_triangle: Optional[TriangleProperties] = None
        self.fault_triangle: Optional[TriangleProperties] = None
        self.animation_frames: List[TriangleProperties] = []
        self.current_frame: int = 0
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._advance_animation_frame)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Horizontal layout for plots and properties
        content_layout = QHBoxLayout()
        
        # Matplotlib canvas (left side)
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_widget.setLayout(plot_layout)
        
        self._create_plot_canvas()
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)
        
        content_layout.addWidget(plot_widget, stretch=2)
        
        # Properties panel (right side)
        properties_panel = self._create_properties_panel()
        content_layout.addWidget(properties_panel, stretch=1)
        
        layout.addLayout(content_layout)
    
    def _create_control_panel(self) -> QWidget:
        """
        Create control panel for triangle animation.
        
        Returns:
            QWidget: Control panel widget
        """
        control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_widget.setLayout(control_layout)
        
        # Calculate triangles button
        self.calculate_button = QPushButton("Calculate Triangles")
        self.calculate_button.clicked.connect(self.calculate_triangles)
        control_layout.addWidget(self.calculate_button)
        
        # Animation controls
        animation_group = QGroupBox("Animation")
        animation_layout = QVBoxLayout()
        animation_group.setLayout(animation_layout)
        
        # Play/pause button
        button_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_animation)
        button_layout.addWidget(self.play_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_animation)
        button_layout.addWidget(self.reset_button)
        
        animation_layout.addLayout(button_layout)
        
        # Frame slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Frame:"))
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(50)
        self.frame_slider.setValue(0)
        self.frame_slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self.frame_slider)
        animation_layout.addLayout(slider_layout)
        
        control_layout.addWidget(animation_group)
        
        # Show options
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)
        
        self.show_trajectory_check = QCheckBox("Show Barycenter Trajectory")
        self.show_trajectory_check.setChecked(True)
        options_layout.addWidget(self.show_trajectory_check)
        
        self.show_vertices_check = QCheckBox("Show Vertex Labels")
        self.show_vertices_check.setChecked(True)
        options_layout.addWidget(self.show_vertices_check)
        
        control_layout.addWidget(options_group)
        
        control_layout.addStretch()
        
        return control_widget
    
    def _create_plot_canvas(self) -> None:
        """Create matplotlib figure and canvas."""
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create subplots
        # Left: Triangle plot
        self.ax_triangle = self.figure.add_subplot(1, 2, 1)
        self.ax_triangle.set_title("Phase Triangle")
        self.ax_triangle.set_xlabel("Real")
        self.ax_triangle.set_ylabel("Imaginary")
        self.ax_triangle.grid(True)
        self.ax_triangle.axis('equal')
        
        # Right: Barycenter trajectory
        self.ax_trajectory = self.figure.add_subplot(1, 2, 2)
        self.ax_trajectory.set_title("Barycenter Trajectory")
        self.ax_trajectory.set_xlabel("Real")
        self.ax_trajectory.set_ylabel("Imaginary")
        self.ax_trajectory.grid(True)
        self.ax_trajectory.axis('equal')
        
        self.figure.tight_layout()
    
    def _create_properties_panel(self) -> QWidget:
        """
        Create panel for displaying triangle properties.
        
        Returns:
            QWidget: Properties panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Pre-fault properties
        prefault_group = QGroupBox("Pre-Fault Triangle")
        prefault_layout = QVBoxLayout()
        prefault_group.setLayout(prefault_layout)
        
        self.prefault_area_label = QLabel("Area: --")
        self.prefault_perimeter_label = QLabel("Perimeter: --")
        self.prefault_balanced_label = QLabel("Balanced: --")
        self.prefault_barycenter_label = QLabel("Barycenter: --")
        
        prefault_layout.addWidget(self.prefault_area_label)
        prefault_layout.addWidget(self.prefault_perimeter_label)
        prefault_layout.addWidget(self.prefault_balanced_label)
        prefault_layout.addWidget(self.prefault_barycenter_label)
        
        layout.addWidget(prefault_group)
        
        # Fault properties
        fault_group = QGroupBox("Fault Triangle")
        fault_layout = QVBoxLayout()
        fault_group.setLayout(fault_layout)
        
        self.fault_area_label = QLabel("Area: --")
        self.fault_perimeter_label = QLabel("Perimeter: --")
        self.fault_balanced_label = QLabel("Balanced: --")
        self.fault_barycenter_label = QLabel("Barycenter: --")
        
        fault_layout.addWidget(self.fault_area_label)
        fault_layout.addWidget(self.fault_perimeter_label)
        fault_layout.addWidget(self.fault_balanced_label)
        fault_layout.addWidget(self.fault_barycenter_label)
        
        layout.addWidget(fault_group)
        
        # Displacement
        displacement_group = QGroupBox("Barycenter Displacement")
        displacement_layout = QVBoxLayout()
        displacement_group.setLayout(displacement_layout)
        
        self.displacement_mag_label = QLabel("Magnitude: --")
        self.displacement_angle_label = QLabel("Angle: --")
        
        displacement_layout.addWidget(self.displacement_mag_label)
        displacement_layout.addWidget(self.displacement_angle_label)
        
        layout.addWidget(displacement_group)
        
        layout.addStretch()
        
        return panel
    
    def calculate_triangles(self) -> None:
        """Calculate pre-fault and fault triangles."""
        # TODO: Get phasors for pre-fault and fault states
        # TODO: Calculate triangle properties
        # TODO: Generate animation frames
        # TODO: Update display
        
        pass
    
    def update_plot(self, frame_index: Optional[int] = None) -> None:
        """
        Update triangle plot.
        
        Args:
            frame_index (int, optional): Frame to display (for animation)
        """
        # TODO: Clear plots
        # TODO: Plot triangle vertices and edges
        # TODO: Mark barycenter
        # TODO: Plot trajectory if enabled
        # TODO: Add vertex labels if enabled
        
        self.ax_triangle.clear()
        self.ax_trajectory.clear()
        
        # TODO: Implement actual plotting
        
        self.ax_triangle.set_title("Phase Triangle")
        self.ax_triangle.set_xlabel("Real")
        self.ax_triangle.set_ylabel("Imaginary")
        self.ax_triangle.grid(True)
        self.ax_triangle.axis('equal')
        
        self.ax_trajectory.set_title("Barycenter Trajectory")
        self.ax_trajectory.set_xlabel("Real")
        self.ax_trajectory.set_ylabel("Imaginary")
        self.ax_trajectory.grid(True)
        self.ax_trajectory.axis('equal')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_properties_display(self) -> None:
        """Update property labels with current values."""
        # TODO: Update pre-fault labels
        # TODO: Update fault labels
        # TODO: Calculate and display displacement
        
        if self.prefault_triangle:
            self.prefault_area_label.setText(f"Area: {self.prefault_triangle.area:.2f}")
            self.prefault_perimeter_label.setText(f"Perimeter: {self.prefault_triangle.perimeter:.2f}")
            self.prefault_balanced_label.setText(f"Balanced: {self.prefault_triangle.is_balanced}")
            # TODO: Format barycenter
        
        if self.fault_triangle:
            self.fault_area_label.setText(f"Area: {self.fault_triangle.area:.2f}")
            self.fault_perimeter_label.setText(f"Perimeter: {self.fault_triangle.perimeter:.2f}")
            self.fault_balanced_label.setText(f"Balanced: {self.fault_triangle.is_balanced}")
            # TODO: Format barycenter
    
    def toggle_animation(self) -> None:
        """Toggle animation playback."""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_button.setText("Play")
        else:
            self.animation_timer.start(50)  # 50 ms per frame
            self.play_button.setText("Pause")
    
    def reset_animation(self) -> None:
        """Reset animation to first frame."""
        self.animation_timer.stop()
        self.play_button.setText("Play")
        self.current_frame = 0
        self.frame_slider.setValue(0)
        self.update_plot(0)
    
    def _advance_animation_frame(self) -> None:
        """Advance to next animation frame."""
        if not self.animation_frames:
            return
        
        self.current_frame += 1
        if self.current_frame >= len(self.animation_frames):
            self.current_frame = 0
        
        self.frame_slider.setValue(self.current_frame)
        self.update_plot(self.current_frame)
    
    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.current_frame = value
        self.update_plot(value)
