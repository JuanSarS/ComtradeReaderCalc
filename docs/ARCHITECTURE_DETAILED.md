# COMTRADE Pro - Developer Documentation

## Current Target Architecture

The project is being consolidated into a single local desktop application:

- `desktop_app/`: native PyQt6 shell, local web host lifecycle, native file dialogs
- `web_ui/`: embedded Dash application factory, local REST endpoints, shared state
- `core_engine/`: shared engineering modules and orchestration pipeline
- `dash_app/`: existing Dash pages/charts/layout retained as compatibility view layer
- `src/gui/`: legacy PyQt tab UI retained temporarily and no longer used by the main entry point

### Technology Decision

The embedded UI now uses Dash instead of the React mockup.

Reasoning:

- Dash is already fully implemented and wired to Python analysis code.
- Plotly interactivity remains intact inside QWebEngineView.
- React assets in `Front/` are still mockup-oriented and would require a new backend bridge plus production build integration.
- Dash preserves the current design and reduces migration risk.

### Runtime Flow

1. `src/main.py` launches the PyQt desktop shell.
2. `desktop_app/server.py` starts a local Dash server on `127.0.0.1` in a background thread.
3. `desktop_app/main_window.py` loads that URL in `QWebEngineView`.
4. `Open COMTRADE` uses a native desktop file dialog.
5. `core_engine/analysis_pipeline.py` processes the selected COMTRADE pair.
6. `web_ui/state.py` shares the resulting analysis with Dash callbacks.
7. The embedded dashboard refreshes itself via a lightweight polling callback.

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

The application now follows a three-layer embedded architecture:

```
┌─────────────────────────────────────┐
│      Desktop Shell Layer (PyQt6)    │
│  - Main Window                      │
│  - QWebEngineView                   │
│  - Native File Dialogs              │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│        Web UI Layer (Dash)          │
│  - Layout / Pages                   │
│  - Plotly Visualizations            │
│  - Sync Callbacks                   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│        Core Engine Layer            │
│  - COMTRADE Reader                  │
│  - Signal Processing                │
│  - Phasor Calculation               │
│  - Symmetrical Components           │
│  - Triangle Analysis                │
│  - Report Generation                │
└─────────────────────────────────────┘
```

### Layer Responsibilities

**Desktop Shell Layer**:
- Native application window
- Desktop file selection
- Embedded browser hosting
- No engineering logic

**Web UI Layer**:
- Scientific layout and navigation
- Interactive Plotly figures
- Local callback orchestration
- Consumes processed state only

**Core Engine Layer**:
- All mathematical algorithms
- COMTRADE parsing and analysis pipeline
- Report generation
- Independent of UI technology

## Refactor Notes

### Files to Refactor Next

- `src/gui/main_window.py`: legacy PyQt tab shell, no longer used by the main entry point
- `src/gui/tabs/*`: legacy desktop tabs replaced by the embedded web UI
- `dash_app/`: compatibility rendering layer; can be migrated gradually into `web_ui/`
- `Front/`: keep as design reference until a future React implementation is funded

### Packaging Notes

- PyInstaller entry point: `src/main.py`
- Required hidden imports: `PyQt6.QtWebEngineWidgets`, `PyQt6.QtWebEngineCore`, `dash`, `plotly`, `scipy`, `pandas`
- Required data inclusion: `dash_app/assets`, plus any future static resources
- Packaging target remains a single local executable that launches the embedded dashboard

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

### Signal Processing Implementation

**Algorithm**: Butterworth band-pass filter
- Centered at system frequency (50/60 Hz)
- Adaptive bandwidth based on sampling rate
- Zero-phase filtering using filtfilt

### RMS Calculation

**Algorithm**: One-cycle RMS window
- Sliding window approach for dynamic RMS
- Efficient convolution-based implementation
- Support for forward, backward, and centered windows

### Phasor Calculation

**Algorithm**: Discrete Fourier Transform at fundamental
- DFT computation at fundamental frequency
- Magnitude and angle calculation
- Support for harmonic analysis

---

## Development Status

**Current Version**: 2.0 (Full feature implementation)

This release provides:
- ✓ Complete COMTRADE file parsing
- ✓ Adaptive signal filtering
- ✓ Real-time RMS calculation  
- ✓ Phasor analysis
- ✓ Symmetrical components
- ✓ Dynamic triangle visualization
- ✓ PDF report generation
- ✓ Embedded Dash UI with PyQt6 desktop

---

**Document Version**: 2.0  
**Last Updated**: March 2026  
**Author**: Power Systems Protection Engineering Team
