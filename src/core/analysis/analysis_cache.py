"""In-memory cache for full-resolution analysis results."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional
from uuid import uuid4

from src.core.analysis.signal_model import SignalSet


@dataclass
class CachedAnalysis:
    analysis_id: str
    signal_set: SignalSet


class AnalysisCache:
    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: Dict[str, CachedAnalysis] = {}

    def put(self, signal_set: SignalSet) -> str:
        analysis_id = uuid4().hex
        with self._lock:
            self._entries[analysis_id] = CachedAnalysis(analysis_id=analysis_id, signal_set=signal_set)
        return analysis_id

    def get(self, analysis_id: str) -> Optional[SignalSet]:
        with self._lock:
            entry = self._entries.get(analysis_id)
            return entry.signal_set if entry else None


analysis_cache = AnalysisCache()