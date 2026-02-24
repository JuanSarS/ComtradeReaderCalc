# COMTRADE Analysis Tool - Developer Documentation

## Architecture Overview

This document provides detailed information about the application architecture, design patterns, and implementation guidelines.

## Table of Contents

1. [Architecture Layers](#architecture-layers)
2. [Core Modules](#core-modules)
3. [GUI Components](#gui-components)
4. [Data Flow](#data-flow)
5. [Implementation Guidelines](#implementation-guidelines)
6. [Mathematical Algorithms](#mathematical-algorithms)

---

## Architecture Layers

The application follows a three-layer architecture:

```
┌─────────────────────────────────────┐
│         GUI Layer (PyQt6)           │
│  - Main Window                      │
│  - Tab Widgets                      │
│  - Event Handlers                   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│      Processing Layer (Core)        │
│  - COMTRADE Reader                  │
│  - Signal Processing                │
│  - Phasor Calculation               │
│  - Symmetrical Components           │
│  - Triangle Analysis                │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│      Utility Layer (Utils)          │
│  - Report Generation                │
│  - File Management                  │
└─────────────────────────────────────┘
```

### Layer Responsibilities

**GUI Layer**: 
- User interaction
- Data visualization
- Event handling
- No business logic

**Processing Layer**:
- All mathematical algorithms
- Signal processing
- Analysis computations
- Independent of GUI

**Utility Layer**:
- Cross-cutting concerns
- PDF generation
- File I/O helpers

---

## Core Modules

### COMTRADEReader

**Purpose**: Parse and load COMTRADE files

**Key Methods to Implement**:
```python
load(cfg_file_path)
├── _parse_cfg_file()
│   ├── Parse header (station, device, revision)
│   ├── Parse channel counts
│   ├── Parse analog channels
│   ├── Parse digital channels
│   └── Parse sampling rate
└── _parse_dat_file()
    ├── Detect format (ASCII/binary)
    ├── Read samples
    └── Apply conversion factors
```

**CFG File Format** (IEEE C37.111):
```
Line 1: station_name,rec_dev_id,rev_year
Line 2: TT,##A,##D  (total channels, analog, digital)
Lines 3+: Analog channel definitions
...
Digital channel definitions
...
Line frequency
Sampling rate
First/last sample time
```

### SignalFilter

**Purpose**: Digital filtering for power system signals

**Algorithm**: Butterworth band-pass filter
```python
# Centered at system frequency (60 Hz)
# Bandwidth: ±2.5 Hz (57.5 - 62.5 Hz)
# Order: 4

from scipy.signal import butter, filtfilt

# Normalize frequencies by Nyquist
nyquist = sampling_rate / 2
low = (system_freq - bandwidth/2) / nyquist
high = (system_freq + bandwidth/2) / nyquist

# Design filter
b, a = butter(order, [low, high], btype='band')

# Apply (zero-phase)
filtered = filtfilt(b, a, signal)
```

### RMSCalculator

**Purpose**: Sliding window RMS calculation

**Algorithm**: One-cycle RMS window
```python
# For centered window:
# RMS at point n = sqrt(mean(signal[n-N/2:n+N/2]^2))

N = samples_per_cycle  # e.g., 120 samples for 60 Hz at 7200 Hz
window = signal[i-N//2:i+N//2]
rms_value = np.sqrt(np.mean(window**2))
```

**Efficient Implementation**:
```python
# Use convolution for speed
kernel = np.ones(N) / N
squared_signal = signal ** 2
rms = np.sqrt(np.convolve(squared_signal, kernel, mode='same'))
```

### PhasorCalculator

**Purpose**: Compute fundamental frequency phasors

**Algorithm**: Discrete Fourier Transform at fundamental
```python
# For frequency f0 = 60 Hz
omega = 2 * np.pi * f0

# DFT at fundamental frequency
N = len(signal)
real_part = (2.0/N) * np.sum(signal * np.cos(omega * time))
imag_part = (2.0/N) * np.sum(signal * np.sin(omega * time))

phasor = real_part + 1j * imag_part
magnitude = np.abs(phasor)
angle = np.angle(phasor, deg=True)
```

### SymmetricalComponents

**Purpose**: Fortescue transformation

**Algorithm**: Symmetrical component decomposition
```python
# Fortescue operator
a = np.exp(1j * 2 * np.pi / 3)  # 1∠120°

# Transformation matrix
T = np.array([
    [1, 1, 1],
    [1, a, a**2],
    [1, a**2, a]
]) / 3

# Forward transform: [V0, V1, V2] = T @ [Va, Vb, Vc]
V_abc = np.array([Va, Vb, Vc])  # complex phasors
V_012 = T @ V_abc

V0 = V_012[0]  # Zero sequence
V1 = V_012[1]  # Positive sequence
V2 = V_012[2]  # Negative sequence

# Inverse transform: [Va, Vb, Vc] = T^-1 @ [V0, V1, V2]
T_inv = np.array([
    [1, 1, 1],
    [1, a**2, a],
    [1, a, a**2]
])
```

**Fault Identification**:
```
Three-Phase:  I0 ≈ 0,  I2 ≈ 0,  I1 >> 0
Line-Ground:  I0 > 0,  I2 > 0,  I1 > 0  (all significant)
Line-Line:    I0 ≈ 0,  I2 > 0,  I1 > 0
LL-Ground:    I0 > 0,  I2 > 0,  I1 > 0  (I0 < I1)
```

### TriangleAnalyzer

**Purpose**: Geometric analysis of phase triangle

**Algorithm**: Triangle properties
```python
# Vertices are phasor tips
vertices = np.array([Va, Vb, Vc])  # complex numbers

# Barycenter (centroid)
G = (Va + Vb + Vc) / 3

# Area using cross product
# Area = 0.5 * |Im((Vb - Va) * conj(Vc - Va))|
v1 = Vb - Va
v2 = Vc - Va
area = 0.5 * abs(np.imag(v1 * np.conj(v2)))

# Side lengths
AB = abs(Vb - Va)
BC = abs(Vc - Vb)
CA = abs(Va - Vc)

# Balanced check (equilateral)
mean_side = (AB + BC + CA) / 3
is_balanced = all(abs(side - mean_side) < tolerance * mean_side 
                  for side in [AB, BC, CA])
```

**Animation**: Linear interpolation
```python
# Interpolate each phasor independently
frames = []
for i in range(num_frames):
    t = i / (num_frames - 1)  # 0 to 1
    Va_frame = Va_init + t * (Va_final - Va_init)
    Vb_frame = Vb_init + t * (Vb_final - Vb_init)
    Vc_frame = Vc_init + t * (Vc_final - Vc_init)
    frames.append((Va_frame, Vb_frame, Vc_frame))
```

---

## GUI Components

### Main Window Structure

```
MainWindow
├── Menu Bar
│   ├── File (Load, Exit)
│   ├── Analysis (Run, Configure)
│   └── Help (About)
├── Toolbar
│   └── Quick access buttons
├── File Loading Section
│   ├── Load button
│   ├── File path label
│   └── Frequency selector
├── Tab Widget
│   ├── Instantaneous Tab
│   ├── RMS Tab
│   ├── Phasor Tab
│   ├── Sequence Tab
│   ├── Triangle Tab
│   └── Report Tab
└── Status Bar
```

### Tab Communication

Tabs communicate through shared processing objects:
```python
# Main window creates core objects
self.comtrade_reader = COMTRADEReader()
self.phasor_calculator = PhasorCalculator()

# Passes to tabs
self.phasor_tab = PhasorTab(self.phasor_calculator)

# Tab uses the shared object
self.phasor_calculator.calculate_phasor(...)
```

### Matplotlib Integration

```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Create figure
self.figure = Figure(figsize=(10, 6))
self.canvas = FigureCanvasQTAgg(self.figure)

# Add subplot
self.ax = self.figure.add_subplot(111)

# Plot
self.ax.plot(time, signal)
self.canvas.draw()

# Add to Qt layout
layout.addWidget(self.canvas)
```

---

## Data Flow

### Typical Analysis Workflow

```
1. User clicks "Load File"
   ↓
2. COMTRADEReader.load(file_path)
   ↓
3. Data loaded into pandas DataFrame
   ↓
4. User navigates to RMS tab
   ↓
5. RMS tab requests data from COMTRADE reader
   ↓
6. SignalFilter filters the signals
   ↓
7. RMSCalculator computes RMS values
   ↓
8. Results plotted on matplotlib canvas
   ↓
9. User navigates to Phasor tab
   ↓
10. User selects time range and clicks Calculate
    ↓
11. PhasorCalculator computes phasors
    ↓
12. Results displayed in polar plot and table
    ↓
13. User navigates to Sequence tab
    ↓
14. SymmetricalComponents uses phasors
    ↓
15. Sequence components calculated and displayed
    ↓
16. User generates report
    ↓
17. ReportGenerator collects all figures
    ↓
18. PDF report created and saved
```

---

## Implementation Guidelines

### Phase 1: Core Functionality
1. Implement COMTRADEReader
   - Start with ASCII format
   - Add binary format later
2. Implement basic filtering
3. Implement RMS calculation
4. Test with sample files

### Phase 2: Advanced Processing
1. Implement phasor calculation
2. Implement symmetrical components
3. Implement triangle analysis
4. Validate with known test cases

### Phase 3: GUI Integration
1. Wire up file loading
2. Implement instantaneous plot
3. Implement RMS plot
4. Implement phasor diagram

### Phase 4: Advanced Features
1. Sequence component plots
2. Triangle animation
3. Report generation
4. Comparative analysis

### Testing Strategy

```python
# Test with known sinusoid
f = 60  # Hz
fs = 7200  # Hz
t = np.arange(0, 1, 1/fs)
signal = 100 * np.sqrt(2) * np.sin(2*np.pi*f*t)

# Expected RMS = 100 V
rms = rms_calculator.calculate_steady_state_rms(signal, ...)
assert abs(rms - 100) < 0.1

# Expected phasor magnitude = 100 V, angle = 0°
phasor = phasor_calculator.calculate_phasor(signal, t)
assert abs(phasor.magnitude - 100) < 0.1
assert abs(phasor.angle_deg - 0) < 0.5
```

---

## Mathematical Algorithms

### Key Formulas

**RMS Value**:
$$\text{RMS} = \sqrt{\frac{1}{N}\sum_{i=1}^{N} x_i^2}$$

**Phasor (DFT)**:
$$X = \frac{2}{N}\sum_{n=0}^{N-1} x[n] \cdot e^{-j\omega n \Delta t}$$

**Symmetrical Components**:
$$\begin{bmatrix} V_0 \\ V_1 \\ V_2 \end{bmatrix} = \frac{1}{3}\begin{bmatrix} 1 & 1 & 1 \\ 1 & a & a^2 \\ 1 & a^2 & a \end{bmatrix} \begin{bmatrix} V_a \\ V_b \\ V_c \end{bmatrix}$$

where $a = e^{j\frac{2\pi}{3}}$

**Triangle Area**:
$$A = \frac{1}{2}|\text{Im}((V_b - V_a) \cdot \overline{(V_c - V_a)})|$$

---

## Code Style Guidelines

1. **Docstrings**: Google style, include Args, Returns, Raises
2. **Type Hints**: Use for all function signatures
3. **Naming**: 
   - Classes: PascalCase
   - Functions/methods: snake_case
   - Constants: UPPER_SNAKE_CASE
4. **Comments**: Explain why, not what
5. **Error Handling**: Use try-except with specific exceptions

---

## Next Steps for Implementation

1. ✅ Architecture complete
2. 🔄 Implement COMTRADE reader (CFG parser)
3. 🔄 Implement COMTRADE reader (DAT parser)
4. 🔄 Implement signal filter
5. 🔄 Implement RMS calculator
6. 🔄 Test with sample file
7. 🔄 Implement phasor calculator
8. 🔄 Implement symmetrical components
9. 🔄 Implement triangle analyzer
10. 🔄 Wire up GUI tabs
11. 🔄 Implement plots
12. 🔄 Implement report generation
13. 🔄 Test complete workflow
14. 🔄 Package with PyInstaller

---

**Document Version**: 1.0  
**Last Updated**: February 23, 2026  
**Author**: Power Systems Protection Engineering Team
