"""Shared application state between desktop shell, API routes, and Dash callbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class _StateSnapshot:
    revision: int = 0
    source_path: str = ""
    display_name: str = ""
    analysis: dict[str, Any] | None = None
    error: str = ""


class DesktopStateStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._snapshot = _StateSnapshot()

    def set_analysis(self, source_path: str, display_name: str, analysis: dict[str, Any]) -> int:
        with self._lock:
            self._snapshot.revision += 1
            self._snapshot.source_path = source_path
            self._snapshot.display_name = display_name
            self._snapshot.analysis = analysis
            self._snapshot.error = analysis.get("error", "") if analysis else ""
            return self._snapshot.revision

    def get_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "revision": self._snapshot.revision,
                "source_path": self._snapshot.source_path,
                "display_name": self._snapshot.display_name,
                "analysis": self._snapshot.analysis,
                "error": self._snapshot.error,
            }


desktop_state = DesktopStateStore()