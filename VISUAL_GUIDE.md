# Visual Project Overview

## Application Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMTRADE ANALYSIS TOOL                       │
│                   Professional Desktop Application              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │         USER LOADS COMTRADE FILE            │
        │              (.cfg + .dat)                   │
        └──────────────────┬──────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────────┐
        │         COMTRADEReader Module               │
        │  • Parse .cfg metadata                      │
        │  • Parse .dat sample data                   │
        │  • Convert to engineering units             │
        │  • Store in pandas DataFrame                │
        └──────────────────┬──────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────────┐
        │         USER NAVIGATES TO TABS              │
        └──────────────────┬──────────────────────────┘
                           │
        ┌──────────────────┴─────────────────────────────────┐
        │                                                     │
        ▼                                                     ▼
┌───────────────────┐                            ┌───────────────────┐
│ Instantaneous Tab │                            │    RMS Tab        │
│ • Plot voltages   │                            │ • Filter signals  │
│ • Plot currents   │                            │ • Calculate RMS   │
│ • Zoom/pan        │                            │ • Plot trends     │
└───────────────────┘                            └─────────┬─────────┘
                                                           │
                                                           ▼
                                                 ┌───────────────────┐
                                                 │   Phasor Tab      │
                                                 │ • Select time     │
                                                 │ • Calculate DFT   │
                                                 │ • Polar plot      │
                                                 └─────────┬─────────┘
                                                           │
                                                           ▼
                                                 ┌───────────────────┐
                                                 │  Sequence Tab     │
                                                 │ • Fortescue       │
                                                 │ • V0, V1, V2      │
                                                 │ • Fault identify  │
                                                 └─────────┬─────────┘
                                                           │
                                                           ▼
                                                 ┌───────────────────┐
                                                 │  Triangle Tab     │
                                                 │ • Plot triangle   │
                                                 │ • Barycenter      │
                                                 │ • Animation       │
                                                 └─────────┬─────────┘
                                                           │
                                                           ▼
                                                 ┌───────────────────┐
                                                 │   Report Tab      │
                                                 │ • Collect figures │
                                                 │ • Add tables      │
                                                 │ • Export PDF      │
                                                 └───────────────────┘
```

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ Main Window│  │   Tabs     │  │  Dialogs   │  │   Menus    │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ Qt Signals/Slots
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          BUSINESS LOGIC LAYER                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  COMTRADE   │  │   Signal    │  │     RMS      │  │  Phasor  │  │
│  │   Reader    │──│   Filter    │──│  Calculator  │──│Calculator│  │
│  └─────────────┘  └─────────────┘  └──────────────┘  └──────────┘  │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐                │
│  │Symmetrical  │  │  Triangle   │  │    Report    │                │
│  │ Components  │  │  Analyzer   │  │  Generator   │                │
│  └─────────────┘  └─────────────┘  └──────────────┘                │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ NumPy/SciPy/Pandas
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              pandas DataFrame (Time-Series Data)               │ │
│  │  Columns: Time | Va | Vb | Vc | Ia | Ib | Ic | ...            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │           Phasor Objects (Complex Numbers)                     │ │
│  │  Va: 120∠0°  |  Vb: 120∠-120°  |  Vc: 120∠120°               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
                    main.py
                       │
                       ▼
                 MainWindow ──────────────┐
                    │                     │
        ┌───────────┼───────────┐         │
        │           │           │         │
        ▼           ▼           ▼         │
   Instant.    RMS Tab    Phasor Tab     │
     Tab                                  │
        │           │           │         │
        └───────────┼───────────┘         │
                    │                     │
                    ▼                     ▼
            ┌───────────────┐     ┌──────────────┐
            │  COMTRADE     │     │   Report     │
            │   Reader      │     │  Generator   │
            └───────┬───────┘     └──────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   Signal      RMS Calc    Phasor Calc
   Filter                       │
                    │           │
                    └─────┬─────┘
                          │
                          ▼
                   Symmetrical
                    Components
                          │
                          ▼
                     Triangle
                     Analyzer
```

## Class Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        MainWindow                            │
│  • Owns all processing objects                              │
│  • Coordinates tab communication                            │
│  • Manages application state                                │
└───────────┬──────────────────────────────────────────────────┘
            │
            │ creates and passes references
            │
    ┌───────┴────────┬──────────┬──────────┬──────────┐
    │                │          │          │          │
    ▼                ▼          ▼          ▼          ▼
┌────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│COMTRADE│  │SignalFilter  │  │RMSCalculator │  │ Phasor   │
│Reader  │  │              │  │              │  │Calculator│
└────────┘  └──────────────┘  └──────────────┘  └──────────┘
    │                │              │                │
    │                │              │                │
    ├────────────────┴──────────────┴────────────────┘
    │          provides data to
    │
    ▼
┌──────────────────────────────────────────────────┐
│                Tab Widgets                        │
│  • Receive references to processing objects      │
│  • Call methods to perform calculations          │
│  • Display results in matplotlib canvases        │
└──────────────────────────────────────────────────┘
```

## Signal Processing Pipeline

```
Raw COMTRADE Data
       │
       ▼
┌─────────────┐
│  DC Offset  │  (Remove mean)
│   Removal   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Band-Pass  │  (60 Hz ± 2.5 Hz)
│   Filter    │  (4th order Butterworth)
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
┌────────────┐    ┌────────────┐    ┌────────────┐
│ Sliding    │    │   Phasor   │    │ Sequence   │
│ RMS        │    │ Calculation│    │ Components │
│ (1-cycle)  │    │   (DFT)    │    │ (Fortescue)│
└────────────┘    └────────────┘    └────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Visualization│
                  │   & Reports   │
                  └───────────────┘
```

## Phasor Analysis Workflow

```
Filtered Signal (Va, Vb, Vc)
         │
         │ Select steady-state time window
         ▼
   ┌─────────────┐
   │    DFT      │  (Discrete Fourier Transform)
   │  at 60 Hz   │  (Fundamental frequency only)
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Phasors    │  Va∠θa, Vb∠θb, Vc∠θc
   │  (Complex)  │
   └──────┬──────┘
          │
          ├──────────────┬──────────────┐
          │              │              │
          ▼              ▼              ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  Polar   │   │Fortescue │   │ Triangle │
   │  Plot    │   │Transform │   │ Geometry │
   └──────────┘   └─────┬────┘   └─────┬────┘
                        │              │
                        ▼              ▼
                 ┌────────────┐  ┌────────────┐
                 │ V0, V1, V2 │  │ Barycenter │
                 │Sequence    │  │  Motion    │
                 └────────────┘  └────────────┘
```

## Fortescue Transformation

```
     Phase Domain (ABC)              Sequence Domain (012)
                                     
    Va ──┐                               ┌── V0 (Zero)
         │                               │
    Vb ──┼──→ [Transformation] ──→───────┼── V1 (Positive)
         │         Matrix               │
    Vc ──┘                               └── V2 (Negative)
         
         
  ┌───────────────────────────────────────────────────┐
  │   [V0]   [1  1   1 ]   [Va]                       │
  │   [V1] = [1  a   a²] · [Vb]  / 3                  │
  │   [V2]   [1  a²  a ]   [Vc]                       │
  │                                                    │
  │   where a = exp(j·2π/3) = 1∠120°                 │
  └───────────────────────────────────────────────────┘
```

## File Format Structure

```
COMTRADE File Pair
│
├── filename.cfg (Configuration - ASCII text)
│   ├── Line 1: Station, Device, Revision
│   ├── Line 2: Channel counts (Analog, Digital)
│   ├── Lines 3-N: Analog channel definitions
│   │   Format: Index, Name, Phase, Units, a, b, ...
│   ├── Lines N+1-M: Digital channel definitions
│   ├── Line M+1: Power frequency (50 or 60 Hz)
│   ├── Line M+2: Sampling rate information
│   └── Lines M+3-end: Time stamps, trigger info
│
└── filename.dat (Data - ASCII or Binary)
    ├── Sample 1: n, t, Ch1, Ch2, ..., ChN
    ├── Sample 2: n, t, Ch1, Ch2, ..., ChN
    ├── ...
    └── Sample M: n, t, Ch1, Ch2, ..., ChN
```

## Report Generation Flow

```
User Selects Content
       │
       ▼
┌─────────────────┐
│ Collect Figures │
│  • Waveforms    │
│  • RMS plots    │
│  • Phasor plots │
│  • Seq plots    │
│  • Triangles    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Collect Tables  │
│  • Phasor vals  │
│  • Sequence     │
│  • Metadata     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Format Report  │
│  • Title page   │
│  • TOC          │
│  • Sections     │
│  • Page numbers │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Generate PDF     │
│ (matplotlib     │
│  PdfPages)      │
└────────┬────────┘
         │
         ▼
   fault_report.pdf
```

## Animation System

```
Pre-Fault State          Transition Frames         Fault State
  (Triangle 1)          (Interpolated)            (Triangle 2)
       │                                                │
       │                                                │
       ▼                                                ▼
  ┌────────┐                                       ┌────────┐
  │   /\   │                                       │   /\   │
  │  /  \  │         ┌──────────┐                 │  /  \  │
  │ /    \ │  ──→    │Frame 1   │  ──→  ...  ──→  │ /    \ │
  │/______\│         │Frame 2   │                  │/______\│
  │   G1   │         │  ...     │                  │   G2   │
  └────────┘         │Frame N   │                  └────────┘
                     └──────────┘
       │                  │                              │
       │                  │                              │
       └──────────────────┴──────────────────────────────┘
                          │
                          ▼
                 Barycenter Trajectory
                (G1 → ... → G2)
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────┐
│              Application Layer                  │
│                                                 │
│  Python 3.9+    PyQt6         Matplotlib       │
│  (Language)    (GUI)          (Plotting)        │
└─────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────┐
│           Scientific Computing Layer            │
│                                                 │
│  NumPy          SciPy         Pandas           │
│  (Arrays)    (Signal Proc)  (DataFrames)       │
└─────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────┐
│              Operating System                   │
│                                                 │
│  Windows        Linux         macOS             │
│  (Primary)    (Secondary)   (Secondary)         │
└─────────────────────────────────────────────────┘
```

---

This visual overview complements the technical documentation and provides
a quick reference for understanding the application architecture.
