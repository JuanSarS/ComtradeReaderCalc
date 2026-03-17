"""
Cursor Movement Handler
=======================

Handles cursor position synchronization across charts.
Enables RMS lookup and phasor updates without recomputation.
"""

import numpy as np
from typing import Optional, Dict, Tuple


class CursorState:
    """Manages cursor position across dashboard."""
    
    def __init__(self):
        self.current_sample_index: Optional[int] = None
        self.current_time_ms: Optional[float] = None
        self.last_rms_lookup: Dict[str, float] = {}
        self.last_phasor_lookup: Dict[str, Dict] = {}
    
    def set_cursor_from_time(self, time_ms: float, time_axis_ms: np.ndarray) -> bool:
        """
        Set cursor position from time value.
        
        Args:
            time_ms: Time in milliseconds
            time_axis_ms: Full time axis in milliseconds
        
        Returns:
            True if cursor position changed, False otherwise
        """
        # Find nearest sample index
        if len(time_axis_ms) == 0:
            return False
        
        idx = int(np.argmin(np.abs(time_axis_ms - time_ms)))
        
        if idx != self.current_sample_index:
            self.current_sample_index = idx
            self.current_time_ms = float(time_axis_ms[idx])
            return True
        
        return False
    
    def lookup_rms_at_cursor(self, rms_signals: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Extract RMS values at current cursor position.
        
        Args:
            rms_signals: Dict of {channel_name: rms_array} (precomputed)
        
        Returns:
            Dict of {channel_name: rms_value_at_cursor}
        """
        result = {}
        
        if self.current_sample_index is None:
            return result
        
        idx = min(self.current_sample_index, len(rms_signals) - 1)
        
        for channel_name, rms_array in rms_signals.items():
            if idx < len(rms_array):
                result[channel_name] = float(rms_array[idx])
        
        self.last_rms_lookup = result
        return result
    
    def reset(self):
        """Reset cursor state."""
        self.current_sample_index = None
        self.current_time_ms = None
        self.last_rms_lookup = {}
        self.last_phasor_lookup = {}


def extract_cursor_time_from_hoverdata(hoverData: Dict) -> Optional[float]:
    """
    Extract time (x-value) from Plotly hoverData.
    
    Args:
        hoverData: Output from dcc.Graph hover event
    
    Returns:
        Time in ms, or None if not available
    """
    if not hoverData or 'points' not in hoverData:
        return None
    
    points = hoverData['points']
    if not points:
        return None
    
    point = points[0]
    xval = point.get('x')
    
    if xval is not None:
        try:
            return float(xval)
        except (ValueError, TypeError):
            return None
    
    return None


def extract_cursor_time_from_clickdata(clickData: Dict) -> Optional[float]:
    """
    Extract time (x-value) from Plotly clickData.
    
    Similar to hoverData extraction.
    """
    return extract_cursor_time_from_hoverdata(clickData)


def create_cursor_marker_vline(time_ms: float, label: str = "Cursor") -> Dict:
    """
    Create a vertical line spec for adding to Plotly figure.
    
    Args:
        time_ms: Time position in milliseconds
        label: Label for the line
    
    Returns:
        Dict with add_vline parameters
    """
    return {
        'x': time_ms,
        'line_dash': 'solid',
        'line_color': 'rgba(255, 200, 0, 0.8)',
        'line_width': 2,
        'annotation_text': label,
        'annotation_position': 'top right',
    }
