"""Control software of a railway point machine (the fictional Beispielbahn).

A deliberately small, partly complete implementation of the requirements in
docs/Lastenheft_Teilsystem_Weiche.pdf, for demonstrating requirement
traceability: some requirements are implemented and tested, some only in
part, some not at all. See README.md.
"""

from point_machine.controller import CommandResult, PointMachine, State
from point_machine.events import EventLog
from point_machine.interfaces import Position

__all__ = ["CommandResult", "EventLog", "PointMachine", "Position", "State"]
