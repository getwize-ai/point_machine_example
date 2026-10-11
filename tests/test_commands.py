"""Throw commands (Lastenheft chapter 2.1)."""

import pytest

from point_machine import Position, State


@pytest.mark.req("PM.13")
def test_a_throw_command_moves_the_point_to_the_requested_position(machine, hw):
    result = machine.command(Position.RIGHT)

    assert result.accepted
    assert hw.drive.started == [Position.RIGHT]
    hw.set_position(Position.RIGHT)
    machine.poll()
    assert machine.state is State.IN_END_POSITION
    assert machine.position is Position.RIGHT


@pytest.mark.req("PM.14")
def test_a_command_to_the_current_position_is_acknowledged_without_movement(
    machine, hw
):
    result = machine.command(Position.LEFT)

    assert result.accepted
    assert hw.drive.started == []


@pytest.mark.req("PM.15")
def test_a_command_is_rejected_while_the_section_is_occupied(machine, hw):
    hw.track.is_occupied = True

    result = machine.command(Position.RIGHT)

    assert not result.accepted
    assert result.reason == "Abschnitt belegt"
    assert hw.drive.started == []


@pytest.mark.req("PM.16")
def test_a_running_throw_is_not_interrupted_by_a_new_command(machine, hw):
    machine.command(Position.RIGHT)

    second = machine.command(Position.LEFT)

    assert not second.accepted
    assert hw.drive.started == [Position.RIGHT]


@pytest.mark.req("PM.18")
def test_every_command_is_acknowledged_at_once(machine, hw):
    hw.track.is_occupied = True
    rejected = machine.command(Position.RIGHT)
    hw.track.is_occupied = False
    accepted = machine.command(Position.RIGHT)

    # The acknowledgement is the return value: no waiting, no movement first.
    assert (rejected.accepted, accepted.accepted) == (False, True)
