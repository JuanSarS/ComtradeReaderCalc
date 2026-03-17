# Src/ - Project Structure

This directory contains all source code for COMTRADE Pro 2.0, organized in a clean, professional structure.

## Directory Layout

```
Src/
├── __init__.py                      # Package initialization
├── main.py                          # Application entry point
│
├── core/                            # Core analysis engines
│   ├── __init__.py
│   ├── analysis/                    # Signal processing algorithms
│   │   ├── __init__.py
│   │   ├── comtrade_reader.py       # IEEE C37.111 COMTRADE file parsing
│   │   ├── signal_filter.py         # Butterworth bandpass filtering
│   │   ├── rms_calculator.py        # Sliding window RMS computation
│   │   ├── phasor_calculator.py     # DFT-based phasor calculation
│   │   ├── symmetrical_components.py # Fortescue transformation
│   │   ├── triangle_analyzer.py     # Geometric phase triangle analysis
│   │   └── analysis_pipeline.py     # Orchestration pipeline (entry point for all analysis)
│   │
│   └── utils/                       # Utility modules
│       ├── __init__.py
│       └── report_generator.py      # PDF report generation
│
└── ui/                              # User interface layer
    ├── __init__.py
    │
    ├── desktop/                     # PyQt6 desktop shell
    │   ├── __init__.py
    │   ├── main_window.py           # Main application window with QWebEngineView
    │   └── server.py                # Dash server lifecycle management
    │
    ├── web/                         # Dash web framework layer
    │   ├── __init__.py
    │   ├── app.py                   # Dash application factory
    │   └── state.py                 # Shared state management (desktop ↔ web sync)
    │
    └── pages/                       # Dash pages, charts, and layouts
        ├── __init__.py
        ├── layout.py                # Main layout structure
        ├── pages.py                 # Page components
        ├── charts.py                # Plotly chart functions
        ├── callbacks.py             # Dash callbacks and interactivity
        ├── processing.py            # File processing for uploads
        └── assets/
            └── style.css            # Stylesheet
```

## Running the Application

### From Project Root
```bash
python Src/main.py
```

### From This Directory
```bash
cd Src
python main.py
```

## Import Statements

All imports use absolute paths from project root:

```python
# Core analysis modules
from Src.core.analysis import COMTRADEReader, PhasorCalculator
from Src.core.analysis.analysis_pipeline import process_comtrade_path
from Src.core.utils import ReportGenerator

# Desktop UI
from Src.ui.desktop import EmbeddedMainWindow, DashServerThread
from Src.ui.desktop.server import launch_desktop_app

# Web UI
from Src.ui.web import create_dash_app, desktop_state
from Src.ui.pages import build_layout

# Relative imports within same package
from .sheets import COMTRADEReader      # Within core.analysis
from .processing import process_files    # Within ui.pages
```

## Module Responsibilities

### core/analysis/
- **Independent of any UI technology**
- Pure Python signal processing
- No dependencies on PyQt6 or Dash
- Reusable for CLI, API, or any other frontend

### ui/desktop/
- **PyQt6 native desktop shell**
- Native file dialogs
- Window management
- Lifecycle of embedded Dash server (background thread)

### ui/web/
- **Dash/Flask web framework**
- Layout and page structure
- Interactive Plotly visualizations
- Callback orchestration
- Shared state with desktop shell

## Architecture Flow

```
User opens Src/main.py
    ↓
Src.ui.desktop.server.launch_desktop_app()
    ├─→ Starts DashServerThread (background)
    │   └─→ Src.ui.web.create_dash_app() on 127.0.0.1:8050
    │
    ├─→ Creates EmbeddedMainWindow (PyQt6)
    │   └─→ Loads Dash app in QWebEngineView
    │
User clicks "Open COMTRADE"
    ├─→ Native file dialog (QFileDialog)
    │
    ├─→ Src.core.analysis.analysis_pipeline.process_comtrade_path()
    │   └─→ Runs full analysis pipeline
    │
    ├─→ Src.ui.web.state.desktop_state.set_analysis()
    │   └─→ Stores results in shared state
    │
Dash callbacks poll for changes
    └─→ Update all 7 pages with results
```

## Key Design Patterns

1. **Server-in-Thread**: Flask/Dash runs in background daemon thread
2. **Shared State**: `DesktopStateStore` bridges desktop and web UI
3. **Single Truth**: Analysis pipeline is source of truth for all computation
4. **Relative Imports**: Within-package imports use `.` notation
5. **Absolute Imports**: Cross-package imports use `Src.` prefix

## Development Notes

- Add new analysis modules to `core/analysis/`
- Add new UI pages to `ui/pages/`
- Maintain separation between core logic and UI
- All unit tests in `../../tests/`
- All configuration in `../../config/`
