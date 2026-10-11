# Point machine example

A small, realistic example for **requirement traceability from a DOORS export to code and tests**, made for [Spectator](https://github.com/getwize-ai/spectator).

It contains what a railway supplier typically receives and builds:

- **`docs/Lastenheft_Teilsystem_Weiche.pdf`**, a requirements specification (*Lastenheft*) for the point machine (*Weiche*) of a fictional railway, exported from DOORS. As such documents are, it is in German, and it is one ruled table with columns ID, *Verbindlichkeit* (obligation) and *Anforderungstext* (requirement text). Some rows are headings, some are explanations (*Info*), two are deleted, one has no obligation, one requirement contains a state machine diagram, and one is only a figure.
- **`point_machine/`**, the control software, implemented in part.
- **`tests/`**, pytest tests tagged with the requirement IDs of the Lastenheft (`@pytest.mark.req("PM.13")`).

Everything is synthetic: the Beispielbahn, the subsystem and its requirements are invented.

## The requirements and their state

| ID | Requirement (short) | Code | Test |
|---|---|---|---|
| PM.6 | Developed per EN 50716, SIL 2 | process, not code | — |
| PM.13 | Throw command `Kd_Weiche_umstellen` | implemented | ✓ |
| PM.14 | Already in position: acknowledge without moving | implemented | ✓ |
| PM.15 | Reject while the track section is occupied | implemented | ✓ |
| PM.16 | Do not interrupt a running throw | implemented | ✓ |
| PM.18 | Acknowledge every command within 500 ms | implemented | ✓ |
| PM.21 | End position from both detectors | implemented | ✓ |
| PM.22 | Throw takes too long: stop, report a fault | implemented | ✓ |
| PM.23 | End position lost without a command: fault | implemented | ✓ |
| PM.25 | State machine (diagram in the Lastenheft) | implemented | ✓ |
| PM.31 | Log commands, end positions and faults with time | **partly**: end positions are not logged | ✓ (partly) |
| PM.32 | *Option*: log via the diagnostics interface | not implemented | — |
| PM.42 | Reset to the normal position after every train | **not implemented — contradicts PM.43** | — |
| PM.43 | Never move without a command | implemented | — |
| PM.51 | Availability ≥ 99.99 % | not a code property | — |
| PM.52 | Self-test of the detectors on start | implemented | ✓ |
| PM.53 | Repair within 4 hours | not a code property | — |
| PM.62 | 24 V DC ± 10 % | hardware | — |
| PM.63 | Power ≤ 40 W while throwing | hardware | — |
| PM.71 | Maximum throw time 6 s | implemented | ✓ |
| PM.72 | Report a change of end position within 100 ms | not implemented | — |
| PM.81 | *Option*: indicator panel (a figure only) | not implemented | — |

The gaps are deliberate: a traceability tool should find them.

## Try it with Spectator

1. Create a project and upload `docs/Lastenheft_Teilsystem_Weiche.pdf` (Sources → Upload). Spectator recognises the DOORS export and imports the 22 requirements word for word, with their DOORS IDs.
2. Connect this repository (Sources → Repository): `https://github.com/getwize-ai/point_machine_example.git`.
3. Verify the requirements against the code (Analyze → Artifact Analysis).
4. Run the tests and upload the report (Sources → Test evidence, or with the API):

   ```bash
   pip install -r requirements-dev.txt
   python -m pytest --junitxml=junit.xml --cov=point_machine --cov-branch --cov-report=xml:coverage.xml
   curl -fsS -X POST "$SPECTATOR_URL/api/v1/projects/$PROJECT_ID/test-runs" \
     -H "Authorization: Bearer $SPECTATOR_API_KEY" \
     -F "file=@junit.xml" -F "git_commit_sha=$(git rev-parse HEAD)" -F "label=unit"
   ```

   The tests carry the Lastenheft's IDs; Spectator links them to the requirements by those IDs.
5. Run the conflict analysis: it finds that PM.42 and PM.43 contradict each other.

## Regenerate the PDF

The Lastenheft's content lives in `spec/lastenheft.yaml`. After a change:

```bash
pip install -r requirements-dev.txt
python tools/build_lastenheft_pdf.py
```

The build is reproducible; CI checks that the committed PDF matches its source.
