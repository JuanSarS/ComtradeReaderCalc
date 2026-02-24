# Sample Data Directory

This directory is for storing sample COMTRADE files for testing and demonstration.

## Directory Structure

```
data/
└── sample/
    ├── fault_case_1/
    │   ├── fault_record.cfg
    │   └── fault_record.dat
    ├── fault_case_2/
    │   ├── fault_record.cfg
    │   └── fault_record.dat
    └── README.md (this file)
```

## COMTRADE File Pairs

Each COMTRADE recording consists of two files:
- `.cfg` - Configuration file (ASCII text) containing channel definitions and metadata
- `.dat` - Data file (ASCII or binary) containing the actual sample values

## Sample Files

Place your COMTRADE sample files here for testing the application.

### Suggested Test Cases

1. **Balanced Three-Phase Load**
   - All three phases balanced
   - No fault condition
   - Used for validating normal operation

2. **Single Line-to-Ground Fault**
   - Fault on one phase
   - Used for testing sequence component calculation

3. **Line-to-Line Fault**
   - Fault between two phases
   - Different sequence pattern

4. **Three-Phase Fault**
   - Balanced fault condition
   - Voltage sag on all phases

5. **ATPDraw Simulation**
   - Files from ATPDraw simulation
   - Validates compatibility with simulation tools

## File Sources

COMTRADE files can be obtained from:
- Protection relay fault records
- Power quality monitors
- Digital fault recorders
- Simulation tools (ATPDraw, PSCAD, EMTP)
- IEEE COMTRADE test files
- Educational repositories

## Notes

- Ensure files follow IEEE C37.111 standard
- Both ASCII and binary formats are supported
- File names should match (same base name for .cfg and .dat)
- Keep original file names when possible for traceability

## Example File Naming Convention

```
station_date_time_event.cfg
station_date_time_event.dat

Example:
substation_20260223_143015_singleLG.cfg
substation_20260223_143015_singleLG.dat
```
