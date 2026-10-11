"""End-position supervision (Lastenheft chapters 2.2, 3 and 4.2)."""

import pytest

from point_machine import EventLog, Position, PointMachine, State
from point_machine.controller import MAX_THROW_TIME_S


@pytest.mark.req("PM.21")
def test_the_end_position_needs_both_detectors_to_agree(machine, hw):
    hw.detector_b.position = Position.RIGHT

    assert machine.end_position() is None
    hw.detector_b.position = Position.LEFT
    assert machine.end_position() is Position.LEFT


@pytest.mark.req("PM.22", "PM.71")
def test_a_throw_that_takes_too_long_is_stopped_and_reported(machine, hw):
    machine.command(Position.RIGHT)

    hw.clock.advance(MAX_THROW_TIME_S + 0.1)
    machine.poll()

    assert machine.state is State.FAULT
    assert machine.fault == "Umstellzeit überschritten"
    assert hw.drive.stops == 1


@pytest.mark.req("PM.71")
def test_the_maximum_throw_time_is_six_seconds():
    assert MAX_THROW_TIME_S == 6.0


@pytest.mark.req("PM.23", "PM.25")
def test_losing_the_end_position_without_a_command_is_a_fault(machine, hw):
    hw.detector_a.position = None

    machine.poll()

    assert machine.state is State.FAULT
    assert machine.fault == "Endlagenverlust"


@pytest.mark.req("PM.52")
def test_a_failed_self_test_keeps_the_machine_in_fault(hw):
    hw.detector_b.position = None
    machine = PointMachine(
        hw.drive, hw.detector_a, hw.detector_b, hw.track, hw.clock, EventLog()
    )

    assert not machine.start()
    assert machine.state is State.FAULT
    assert not machine.command(Position.RIGHT).accepted


@pytest.mark.req("PM.31")
def test_commands_and_faults_are_logged_with_their_time(machine, hw):
    hw.clock.time = 12.5
    machine.command(Position.RIGHT)
    hw.clock.advance(MAX_THROW_TIME_S + 1)
    machine.poll()

    assert [(e.kind, e.timestamp) for e in machine.log.events] == [
        ("command", 12.5),
        ("fault", 12.5 + MAX_THROW_TIME_S + 1),
    ]
