"""Event log of the point machine (PM.31)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Event:
    timestamp: float
    kind: str  # "command", "end_position", "fault"
    detail: str


@dataclass
class EventLog:
    """Events in the order they happened, each with its timestamp."""

    events: list[Event] = field(default_factory=list)

    def record(self, timestamp: float, kind: str, detail: str) -> None:
        self.events.append(Event(timestamp, kind, detail))

    def of_kind(self, kind: str) -> list[Event]:
        return [event for event in self.events if event.kind == kind]
