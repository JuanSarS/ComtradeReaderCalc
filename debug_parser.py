#!/usr/bin/env python3
"""Debug COMTRADE parser."""

from src.core.analysis.comtrade_reader import COMTRADEReader

cfg_path = r'data/sample/resultadosSNV.cfg'
reader = COMTRADEReader()
reader.load(cfg_path)

print(f"Station: {reader.station_name}")
print(f"Num analog: {reader.num_analog}")
print(f"Num digital: {reader.num_digital}")
print(f"Line frequency: {reader._line_frequency}")
print(f"Sampling rate: {reader.sampling_rate}")
print(f"Total samples: {reader.total_samples}")
print(f"Data format: {reader._data_format}")
print(f"Time stamps: {len(reader.time_stamps)} values")
if len(reader.time_stamps) > 0:
    dt = reader.time_stamps[1] - reader.time_stamps[0] if len(reader.time_stamps) > 1 else 0
    print(f"Time step: {dt:.6f} sec")
    if dt > 0:
        print(f"Implied fs: {1/dt:.1f} Hz")
