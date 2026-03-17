#!/usr/bin/env python3
"""Quick test of refactored analysis pipeline."""

from src.core.analysis.analysis_pipeline import process_comtrade_path

cfg_path = r'data/sample/resultadosSNV.cfg'
result = process_comtrade_path(cfg_path, system_frequency=60.0)

if 'error' in result:
    print(f'ERROR: {result["error"]}')
    exit(1)
else:
    print('✓ Pipeline successful')
    meta = result.get('metadata', {})
    print(f'  File: {meta.get("filename")}')
    print(f'  Voltages: {meta.get("voltage_channels")}')
    print(f'  Currents: {meta.get("current_channels")}')
    print(f'  Samples: {len(result.get("time_ms", []))}')
    print(f'  Duration: {meta.get("duration_s"):.3f} sec')
    
    # Check internal SignalSet
    if '__signal_set__' in result:
        signal_set = result['__signal_set__']
        print(f'  ✓ SignalSet created internally')
        print(f'    Raw signals: {len(signal_set.raw_signals)} channels')
        print(f'    Filtered signals: {len(signal_set.filtered_signals)} channels')
        print(f'    RMS precomputed: {len(signal_set.rms_signals)} channels')
        print(f'    Phasor cache: {len(signal_set.phasor_cache)} channels')
