# Quick Start Guide

## Installation and First Run

### Step 1: Verify Python Installation

Open a terminal and check Python version:
```bash
python --version
```

You need Python 3.9 or higher.

### Step 2: Set Up Virtual Environment

Navigate to the project directory:
```bash
cd "c:\Universidad Juandi\10mo semestre\Fallas\Proy1"
```

Create virtual environment:
```bash
python -m venv venv
```

Activate it:
```bash
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- PyQt6 (GUI framework)
- PyQt6-WebEngine (embedded browser used by QWebEngineView)
- NumPy (numerical computing)
- SciPy (scientific computing)
- Pandas (data structures)
- Matplotlib (plotting)

### Step 4: Run the Application

**Option A - Using the batch file** (Windows):
```bash
run.bat
```

**Option B - Manually**:
```bash
cd src
python main.py
```

The embedded desktop window should appear and load the dashboard internally.

---

## First Time Usage

### 1. Load a COMTRADE File

1. Click **"Open COMTRADE"** in the desktop toolbar
2. Navigate to a .cfg file
3. Select and open it

The application will read both `.cfg` and `.dat` files and push the results into the embedded dashboard.

### 2. View Instantaneous Signals

1. Go to the **"Instantaneous Signals"** tab
2. Select channels to display (when implemented)
3. Click **"Update Plot"**

### 3. Calculate RMS Values

1. Go to the **"RMS Signals"** tab
2. Select RMS window type (centered recommended)
3. Click **"Calculate RMS"**

### 4. Compute Phasors

1. Go to the **"Phasors"** tab
2. Set time range for steady-state analysis:
   - Pre-fault: typically 0.0 to 0.1 seconds
   - Fault: depends on fault occurrence time
3. Click **"Calculate Phasors"**

### 5. Analyze Sequence Components

1. Go to the **"Sequence Components"** tab
2. Click **"Calculate Sequence Components"**
3. Click **"Identify Fault Type"** to see fault analysis

### 6. Visualize Phase Triangle

1. Go to the **"Triangle Visualization"** tab
2. Click **"Calculate Triangles"**
3. Use **"Play"** button to animate transition
4. Use slider to navigate frames manually

### 7. Generate Report

1. Go to the **"Report"** tab
2. Edit title and author if desired
3. Select content to include (checkboxes)
4. Click **"Generate Preview"** to see what will be included
5. Click **"Export to PDF"** to save report

---

## Understanding the Interface

### Main Window Components

```
┌────────────────────────────────────────────────────┐
│ Toolbar: Open COMTRADE | Reload UI                 │
├────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────┐ │
│ │ Embedded Dash UI (local, no external browser) │ │
│ │                                                │ │
│ │  [Signals | RMS | Phasors | Sequence | ...]  │ │
│ │                                                │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────┤
│ Status Bar: Ready / Loading / Processing...        │
└────────────────────────────────────────────────────┘
```

### Embedded Views

1. **Instantaneous Signals**: Raw waveforms from the recording
2. **RMS Signals**: Time-varying RMS values (one-cycle window)
3. **Phasors**: Vector representation of fundamental component
4. **Sequence Components**: Positive, negative, zero sequence analysis
5. **Triangle Visualization**: Geometric phasor analysis with animation
6. **Report**: PDF generation and export

---

## Sample Workflow: Analyzing a Fault

### Scenario: Single Line-to-Ground Fault

**Step 1**: Load the fault recording
- File → Load COMTRADE File
- Select your fault_record.cfg

**Step 2**: Examine the raw data
- Go to Instantaneous tab
- Observe voltage dip on faulted phase
- Note current increase on faulted phase

**Step 3**: Calculate RMS trends
- Go to RMS tab
- Calculate RMS with centered window
- Identify fault inception time (voltage drop)

**Step 4**: Compute pre-fault phasors
- Go to Phasors tab
- Set time range: 0.0 to 0.05 s (before fault)
- Calculate phasors
- Note balanced three-phase system

**Step 5**: Compute fault phasors
- Set time range: 0.15 to 0.20 s (during fault)
- Calculate phasors
- Observe voltage imbalance

**Step 6**: Sequence component analysis
- Go to Sequence tab
- Calculate sequence components
- Observe significant V0, V2 (indicates SLG fault)
- Click Identify Fault Type

**Step 7**: Triangle visualization
- Go to Triangle tab
- Observe triangle collapse toward origin on one vertex
- Play animation to see transition
- Note barycenter displacement

**Step 8**: Generate report
- Go to Report tab
- Enter meaningful title: "Fault Analysis - SLG Fault on Phase A"
- Select all relevant plots
- Export to PDF

---

## Keyboard Shortcuts

- **Ctrl+O**: Load COMTRADE file
- **Ctrl+Q**: Quit application

---

## Troubleshooting

### Application won't start
- Check Python version (must be 3.9+)
- Verify all dependencies installed: `pip list`
- Try reinstalling: `pip install -r requirements.txt --force-reinstall`

### File won't load
- Ensure both .cfg and .dat files exist
- Check COMTRADE file format (IEEE C37.111)
- Try opening .cfg file in text editor to verify format

### Plots are empty
- Check that file is loaded successfully
- Verify data processing (TODO markers indicate unimplemented features)
- Check status bar for error messages

### PDF export fails
- Ensure write permissions in output directory
- Check that matplotlib backend is installed correctly

---

## Where to Get Sample Files

1. **From Protection Relays**: Export fault records in COMTRADE format
2. **From ATPDraw**: 
   - Run simulation
   - File → Export → COMTRADE
3. **IEEE Test Files**: Search for "COMTRADE sample files"
4. **Educational Resources**: Course materials or online repositories

---

## Configuration Options

### System Frequency
- Default: 60 Hz (North America)
- Can be changed to 50 Hz (Europe, Asia, etc.)
- Affects filter design and RMS window size

### Sampling Rate
- Automatically detected from COMTRADE file
- Typical values: 7200 Hz, 15360 Hz
- Higher sampling rate = better resolution

---

## Next Steps

After familiarizing yourself with the interface:

1. **Try different fault types**: SLG, LL, 3-phase
2. **Compare pre-fault vs fault**: Note sequence component changes
3. **Generate comparative reports**: Load two different fault cases
4. **Experiment with settings**: Window types, time ranges
5. **Validate with known cases**: Use simulated data with known results

---

## Getting Help

- **About Dialog**: Help → About (shows version and features)
- **Status Bar**: Watch for messages and errors
- **README.md**: Comprehensive project documentation
- **ARCHITECTURE.md**: Technical implementation details

---

## Development Mode

If you want to modify or extend the application:

1. Read ARCHITECTURE.md for design details
2. Core algorithms are in `Src/core/analysis/`
3. GUI components are in `(legacy)`
4. Look for `# TODO:` comments for unimplemented features
5. Run tests: `pytest tests/` (when implemented)

---

**Happy analyzing! ⚡**

For questions or issues, refer to the full documentation in README.md and ARCHITECTURE.md.
