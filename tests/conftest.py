"""Requirement tags for the test report.

A test declares the requirements it verifies with ``@pytest.mark.req(...)``
(the Lastenheft's DOORS IDs). This writes them into the JUnit report as the
``requirements`` property, which Spectator reads to link test results to
requirements.
"""

from __future__ import annotations

import pytest

from point_machine import EventLog, PointMachine
from tests.fakes import FakeClock, FakeDetector, FakeDrive, FakeTrack


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "req(*ids): requirements the test verifies")


@pytest.fixture(autouse=True)
def _requirement_property(request: pytest.FixtureRequest, record_property) -> None:
    ids = [i for marker in request.node.iter_markers("req") for i in marker.args]
    if ids:
        record_property("requirements", ",".join(ids))


@pytest.fixture
def hw():
    """Fake hardware: clock, two detectors, drive and track section."""

    class Hardware:
        clock = FakeClock()
        detector_a = FakeDetector()
        detector_b = FakeDetector()
        drive = FakeDrive()
        track = FakeTrack()

        def set_position(self, position):
            self.detector_a.position = position
            self.detector_b.position = position

    return Hardware()


@pytest.fixture
def machine(hw) -> PointMachine:
    """A started point machine in end position left."""
    pm = PointMachine(
        hw.drive, hw.detector_a, hw.detector_b, hw.track, hw.clock, EventLog()
    )
    assert pm.start()
    return pm
