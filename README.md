# COMTRADE Analysis Tool

A professional desktop application for COMTRADE file analysis, focused on power system fault analysis and protection engineering.

## Overview

This application provides comprehensive analysis capabilities for COMTRADE (Common Format for Transient Data Exchange) files recorded by protection relays and fault recorders. It is designed for power system protection engineers to analyze fault conditions, compute symmetrical components, and generate professional reports.

## Features

### File Reading
- Read COMTRADE files (.cfg and .dat) from protection relays
- Support for files from simulation tools like ATPDraw
- Compatible with IEEE C37.111 standard (1991, 1999, 2013 revisions)
- ASCII and binary format support

### Signal Processing
- Configurable band-pass filtering (50/60 Hz)
- Sliding window RMS calculation (one-cycle window)
- Fundamental frequency phasor computation using DFT
- DC offset removal

### Symmetrical Component Analysis
- Fortescue transformation implementation
- Positive, negative, and zero sequence components
- Voltage and current imbalance calculation
- Fault type identification from sequence patterns

### Visualization
- Instantaneous waveform plots (voltage and current)
- RMS trend visualization
- Phasor diagrams (polar plots)
- Sequence component plots
- Phase triangle visualization with barycenter tracking
- Animated triangle transition from pre-fault to fault state

### Reporting
- Comprehensive PDF report generation
- Customizable report content
- Comparative analysis for two files
- Professional engineering documentation format

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
cd src
python main.py
```

### Basic Workflow

1. **Load File**: Click "Load COMTRADE File" and select a .cfg file
2. **View Signals**: Navigate through tabs to view different analyses
3. **Configure Settings**: Set system frequency (50/60 Hz) and analysis parameters
4. **Generate Report**: Go to Report tab and export PDF

### Tabs Overview

- **Instantaneous Signals**: View raw voltage and current waveforms
- **RMS Signals**: Analyze RMS trends with sliding window
- **Phasors**: View phasor diagrams and magnitude/angle tables
- **Sequence Components**: Analyze symmetrical components and identify fault type
- **Triangle Visualization**: Examine phase triangle geometry and barycenter motion
- **Report**: Generate and export PDF reports

## Project Structure

```
Proy1/
├── src/
│   ├── main.py                 # Application entry point
│   ├── core/                   # Core processing modules
│   │   ├── comtrade_reader.py
│   │   ├── signal_filter.py
│   │   ├── rms_calculator.py
│   │   ├── phasor_calculator.py
│   │   ├── symmetrical_components.py
│   │   └── triangle_analyzer.py
│   ├── gui/                    # GUI components
│   │   ├── main_window.py
│   │   └── tabs/               # Individual tab widgets
│   └── utils/                  # Utility modules
│       └── report_generator.py
├── tests/                      # Unit tests
├── data/                       # Sample data files
├── requirements.txt
└── README.md
```

## Architecture

The application follows a clean separation of concerns:

- **Core Layer**: Signal processing and analysis algorithms
- **GUI Layer**: PyQt6-based user interface
- **Utils Layer**: Report generation and file management

All core processing modules are independent of the GUI, allowing for:
- Easy testing and validation
- Potential CLI or web interface in the future
- Reusable components for other projects

## Development Status

**Current Version**: 1.0.0 (Architecture and Skeleton)

This release provides:
- ✓ Complete project structure
- ✓ Class skeletons with comprehensive docstrings
- ✓ GUI layout and tab organization
- ✓ Architecture ready for implementation

**Next Steps**: Implement mathematical algorithms and plotting logic in TODO sections

## Technical Details

### Signal Processing
- **RMS Calculation**: One-cycle sliding window (configurable: centered, forward, backward)
- **Phasor Calculation**: Discrete Fourier Transform at fundamental frequency
- **Filtering**: Butterworth band-pass filter centered at system frequency

### Symmetrical Components
- **Transformation Matrix**: Fortescue's method with 'a' operator
- **Imbalance Factors**: (V2/V1) and (V0/V1) percentages
- **Fault Identification**: Pattern matching on sequence magnitudes

### Triangle Analysis
- **Barycenter**: Centroid of three phasor vertices
- **Properties**: Area, perimeter, side lengths, asymmetry factor
- **Animation**: Linear interpolation between states

## For Developers

### Adding New Features

1. Core processing: Add modules in `src/core/`
2. GUI components: Add tabs in `src/gui/tabs/`
3. Follow existing class structure and docstring style
4. Update this README with new capabilities

### Testing

```bash
# Run tests (when implemented)
pytest tests/
```

### Packaging for Distribution

```bash
# Using PyInstaller (when ready)
pyinstaller --onefile --windowed src/main.py
```

## Engineering Notes

### COMTRADE Standard Compliance
- IEEE C37.111-1991, 1999, 2013
- Supports both analog and digital channels
- Handles multiple sampling rates

### Power System Conventions
- Phasor angles in degrees (0-360° or ±180°)
- RMS values for magnitude representation
- Three-phase ABC sequence
- Positive sequence rotation: counter-clockwise

### Coordinate Systems
- Phasor diagrams: Complex plane (real, imaginary)
- Phase angles: Referenced to phase A (typically 0°)
- Symmetrical components: Zero, positive, negative sequence

## License

Academic/Educational Use

## Authors

Power Systems Protection Engineering Team

## Support

For issues, questions, or contributions, please refer to the course materials or contact the development team.

---

**Note**: This application is designed for educational and professional use in power system protection engineering. Always validate results against known test cases before using for critical applications.
