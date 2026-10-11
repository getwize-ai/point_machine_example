"""Fake hardware for the tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from point_machine import Position


@dataclass
class FakeClock:
    time: float = 0.0

    def now(self) -> float:
        return self.time

    def advance(self, seconds: float) -> None:
        self.time += seconds


@dataclass
class FakeDetector:
    position: Position | None = Position.LEFT

    def read(self) -> Position | None:
        return self.position


@dataclass
class FakeDrive:
    started: list[Position] = field(default_factory=list)
    stops: int = 0

    def start(self, target: Position) -> None:
        self.started.append(target)

    def stop(self) -> None:
        self.stops += 1


@dataclass
class FakeTrack:
    is_occupied: bool = False

    def occupied(self) -> bool:
        return self.is_occupied
