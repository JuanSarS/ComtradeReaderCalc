"""
Unit Tests for COMTRADE Reader
===============================

Test cases for the COMTRADE file reader module.
"""

import pytest
import numpy as np
from pathlib import Path

# Import the module under test
import sys
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.comtrade_reader import COMTRADEReader, AnalogChannel, DigitalChannel


class TestCOMTRADEReader:
    """Test suite for COMTRADEReader class."""
    
    def test_initialization(self):
        """Test that COMTRADEReader initializes correctly."""
        reader = COMTRADEReader()
        
        assert reader.cfg_path is None
        assert reader.dat_path is None
        assert reader.num_analog == 0
        assert reader.num_digital == 0
        assert len(reader.analog_channels) == 0
        assert len(reader.digital_channels) == 0
    
    def test_repr(self):
        """Test string representation."""
        reader = COMTRADEReader()
        repr_str = repr(reader)
        
        assert "COMTRADEReader" in repr_str
        assert "analog_channels=0" in repr_str
        assert "digital_channels=0" in repr_str
    
    # TODO: Add tests for file loading when implemented
    # def test_load_ascii_file(self):
    #     """Test loading ASCII format COMTRADE file."""
    #     pass
    
    # def test_load_binary_file(self):
    #     """Test loading binary format COMTRADE file."""
    #     pass
    
    # def test_get_voltage_channels(self):
    #     """Test voltage channel identification."""
    #     pass
    
    # def test_get_current_channels(self):
    #     """Test current channel identification."""
    #     pass


class TestAnalogChannel:
    """Test suite for AnalogChannel dataclass."""
    
    def test_analog_channel_creation(self):
        """Test creating an AnalogChannel instance."""
        channel = AnalogChannel(
            index=1,
            name="VA",
            phase="A",
            component="voltage",
            units="kV",
            multiplier=0.1,
            offset=0.0
        )
        
        assert channel.index == 1
        assert channel.name == "VA"
        assert channel.phase == "A"
        assert channel.component == "voltage"
        assert channel.units == "kV"
        assert channel.multiplier == 0.1


class TestDigitalChannel:
    """Test suite for DigitalChannel dataclass."""
    
    def test_digital_channel_creation(self):
        """Test creating a DigitalChannel instance."""
        channel = DigitalChannel(
            index=1,
            name="TRIP",
            phase="",
            component="status",
            normal=0
        )
        
        assert channel.index == 1
        assert channel.name == "TRIP"
        assert channel.normal == 0


# TODO: Add more comprehensive tests as implementation progresses
# Include tests for:
# - CFG file parsing
# - DAT file parsing
# - Data conversion to engineering units
# - Error handling for invalid files
# - Edge cases and boundary conditions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
