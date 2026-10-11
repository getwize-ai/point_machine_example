"""The point machine controller.

Requirement IDs are those of the Lastenheft (DOORS IDs, e.g. PM.13).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from point_machine.events import EventLog
from point_machine.interfaces import Clock, Detector, Drive, Position, TrackSection

#: Maximum time to throw the point, in seconds (PM.71).
MAX_THROW_TIME_S = 6.0


class State(str, Enum):
    """States of the point machine (state machine of PM.25)."""

    UNKNOWN = "UNBEKANNT"
    IN_END_POSITION = "IN_ENDLAGE"
    MOVING = "UMSTELLUNG"
    FAULT = "STOERUNG"


@dataclass(frozen=True)
class CommandResult:
    """The acknowledgement of a throw command (PM.18)."""

    accepted: bool
    reason: str | None = None


class PointMachine:
    """Throws the point on command and supervises its end position."""

    def __init__(
        self,
        drive: Drive,
        detector_a: Detector,
        detector_b: Detector,
        track: TrackSection,
        clock: Clock,
        log: EventLog | None = None,
    ) -> None:
        self._drive = drive
        self._detectors = (detector_a, detector_b)
        self._track = track
        self._clock = clock
        self.log = log or EventLog()
        self.state = State.UNKNOWN
        self.position: Position | None = None
        self.fault: str | None = None
        self._target: Position | None = None
        self._started_at = 0.0

    # -- start-up ------------------------------------------------------------

    def start(self) -> bool:
        """Self-test of the end-position detectors on start (PM.52).

        Passes when both detectors work and agree on an end position. On
        failure the machine stays in FAULT until it is restarted.
        """
        position = self.end_position()
        if position is None:
            self._enter_fault("Selbsttest fehlgeschlagen")
            return False
        self.position = position
        self.state = State.IN_END_POSITION
        return True

    # -- end position --------------------------------------------------------

    def end_position(self) -> Position | None:
        """The end position, only when both detectors report the same (PM.21)."""
        first, second = (detector.read() for detector in self._detectors)
        return first if first is not None and first == second else None

    # -- commands ------------------------------------------------------------

    def command(self, target: Position) -> CommandResult:
        """Handle the interlocking's throw command Kd_Weiche_umstellen (PM.13).

        Acknowledged at once, as accepted or rejected (PM.18).
        """
        now = self._clock.now()
        self.log.record(now, "command", f"Kd_Weiche_umstellen {target.value}")
        if self.state is State.FAULT:
            return CommandResult(False, "Störung")
        if self.state is State.MOVING:
            # A running throw is not interrupted (PM.16).
            return CommandResult(False, "Umstellung läuft")
        if self._track.occupied():
            return CommandResult(False, "Abschnitt belegt")  # PM.15
        if self.state is State.IN_END_POSITION and self.position is target:
            return CommandResult(True)  # already there: no movement (PM.14)
        self._target = target
        self._started_at = now
        self.state = State.MOVING
        self._drive.start(target)
        return CommandResult(True)

    # -- supervision ---------------------------------------------------------

    def poll(self) -> None:
        """Cyclic supervision, called by the runtime every few milliseconds."""
        now = self._clock.now()
        position = self.end_position()
        if self.state is State.MOVING:
            if position is self._target:
                self._drive.stop()
                self.position = position
                self.state = State.IN_END_POSITION
                # TODO(PM.31): end-position reports are not logged yet.
            elif now - self._started_at > MAX_THROW_TIME_S:
                self._drive.stop()  # PM.22
                self._enter_fault("Umstellzeit überschritten")
        elif self.state is State.IN_END_POSITION and position is not self.position:
            # The point left its end position without a command (PM.23).
            self._enter_fault("Endlagenverlust")
        # The point never moves on its own: no automatic reset to a normal
        # position after a train passed (PM.43; PM.42 asks the opposite).

    def _enter_fault(self, reason: str) -> None:
        self.state = State.FAULT
        self.fault = reason
        self.log.record(self._clock.now(), "fault", reason)
