"""
GUI Tabs Package
================

This package contains all tab widgets for the main application window.
"""

from .instantaneous_tab import InstantaneousTab
from .rms_tab import RMSTab
from .phasor_tab import PhasorTab
from .sequence_tab import SequenceTab
from .triangle_tab import TriangleTab
from .report_tab import ReportTab

__all__ = [
    'InstantaneousTab',
    'RMSTab',
    'PhasorTab',
    'SequenceTab',
    'TriangleTab',
    'ReportTab'
]
