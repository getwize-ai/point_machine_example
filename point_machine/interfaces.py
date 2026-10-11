"""The hardware the controller talks to, as interfaces.

The real point machine has a drive motor, two independent end-position
detectors and a track section that reports whether a train occupies it.
Tests replace them with fakes (tests/fakes.py).
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol


class Position(str, Enum):
    """An end position of the point blades."""

    LEFT = "left"
    RIGHT = "right"


class Drive(Protocol):
    """The motor that throws the point."""

    def start(self, target: Position) -> None: ...

    def stop(self) -> None: ...


class Detector(Protocol):
    """One end-position detector: the position it senses, or None."""

    def read(self) -> Position | None: ...


class TrackSection(Protocol):
    """The track section over the point."""

    def occupied(self) -> bool: ...


class Clock(Protocol):
    """Monotonic time in seconds."""

    def now(self) -> float: ...
