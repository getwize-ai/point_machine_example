# Point machine example

A small, realistic example for **requirement traceability from a DOORS export to code and tests**, made for [Spectator](https://github.com/getwize-ai/spectator).

It contains what a railway supplier typically receives and builds:

- **`docs/Lastenheft_Teilsystem_Weiche.pdf`**, a requirements specification (*Lastenheft*) for the point machine (*Weiche*) of a fictional railway, exported from DOORS. As such documents are, it is in German, and it is one ruled table with columns ID, *Verbindlichkeit* (obligation) and *Anforderungstext* (requirement text). Some rows are headings, some are explanations (*Info*), two are deleted, one has no obligation, one requirement contains a state machine diagram, and one is only a figure.
- **`docs/Schnittstellenspezifikation_S1.pdf`**, the interface specification the Lastenheft cites as `[S1]` (chapter 1.2, *Mitgeltende Dokumente*, and PM.45: "[S1] Abschnitt 3.2"). Its edition differs on purpose: the Lastenheft lists Version 2.0, the file is Version 2.1.
- **`point_machine/`**, the control software, implemented in part.
- **`tests/`**, pytest tests tagged with the requirement IDs of the Lastenheft (`@pytest.mark.req("PM.13")`).
- **The customer's answers** to the supplier: a release of the Lastenheft with conditions, a change request, a confirmation that the conditions are resolved, and a comment list on the supplier's Pflichtenheft — see [Answer the Lastenheft](#answer-the-lastenheft-supplier-response).

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
| PM.45 | Accept commands in the telegram format of [S1] section 3.2 | not implemented | — |
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

1. Create a project and upload `docs/Lastenheft_Teilsystem_Weiche.pdf` (Sources → Upload). Spectator recognises the DOORS export and imports the 23 requirements word for word, with their DOORS IDs.
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
6. Open Sources → Referenced documents: `[S1]` is read from the Lastenheft's reference list. Attach `docs/Schnittstellenspezifikation_S1.pdf` to it: Spectator flags that the file is Version 2.1 while the list names 2.0, and PM.45 shows the text of section 3.2 under *Cited clauses*.

## Answer the Lastenheft (supplier response)

> **Needs Spectator's `statements` feature flag** (`NEXT_PUBLIC_FEATURE_STATEMENTS=true`), which is off in Spectator's production for now. Customer releases and delivery rounds also need `safety` and `baselines`.

A supplier answers the Lastenheft with a *Pflichtenheft* — a fulfilment statement per requirement — and the customer answers back: it releases its Lastenheft with conditions (*Auflagen*), changes it with change requests and comments on the Pflichtenheft. Four more synthetic documents play the customer's side, so this exchange can be shown without customer documents:

| File | What it is | What Spectator reads from it |
|---|---|---|
| `docs/Prueferklaerung_Lastenheft_Weiche.pdf` | The customer's release report (*Prüferklärung*) for Lastenheft Version 1.1: released with conditions | 3 Auflagen (PM-A-01 to PM-A-03), 1 Hinweis (PM-H-01) and 1 application condition, with the requirements each names and its deadline: *Mit Fortschreibung LH*, 30.09.2026, *Ende nächste Lebenszyklusphase* |
| `docs/CR_PMNW-01.pdf` | Change request PMNW-01, the customer's change to the Lastenheft that implements those conditions, with change markup (red struck = removed, green = added) | PM.16 *Soll* → *Muss*; PM.42 deleted; PM.72 100 ms → 200 ms; a new requirement (*NEU*, chapter 2.2); a note on PM.43 |
| `docs/Bestaetigung_Aufloesung_Auflagen.pdf` | The customer's confirmation that all conditions are resolved, citing PMNW-01 | the clause "alle Auflagen … geschlossen", PM-A-01 to PM-A-03 named as fulfilled, `[CR-PMNW-01]` |
| `docs/Kommentarliste_Pflichtenheft_V1.0.xlsx` | The customer's comment list on the supplier's Pflichtenheft V 1.0 (columns Nr., ID, Kommentar, Bewertung, Antwort Lieferant) | 8 comments: accepted (PM.13, PM.72), rejected (PM.31), a question (PM.45), a counter-proposal (PM.51), an ID the Lastenheft doesn't have (PM.19), one that names PM.63 only in its text and has no assessment, and a general remark |

What PMNW-01 changes in the table above:

| ID | Before | After PMNW-01 | Code |
|---|---|---|---|
| PM.16 | *Soll* | *Muss* | implemented |
| PM.42 | Reset after every train — contradicts PM.43 | withdrawn | nothing to remove: the code follows PM.43 |
| PM.72 | Report a change of end position within 100 ms | within 200 ms | not implemented |
| *new* (`PMNW-01/NEU-1`) | — | Detectors that disagree: report the fault "Endlagenprüfer uneinig" | **not implemented**: the code reports "Endlagenverlust" |

After step 1 of [Try it with Spectator](#try-it-with-spectator) (steps 2 and 3 too, if the AI should propose statements):

1. **Statements and the Pflichtenheft.** In the Reports tab, answer the requirements under *Pflichtenheft*: let the AI propose statements from the code verification, or record a few by hand — for example PM.31 *fulfilled with deviation* (end positions are not logged), PM.51 *fulfilled with deviation* (99.95 %), PM.72 *fulfilled with deviation* (200 ms: the telegram cycle of [S1] doesn't allow 100 ms). Export the Pflichtenheft (PDF, Markdown or CSV) and deliver it: Readiness → Baselines → Delivery rounds → **Start round 1…**, *Pflichtenheft V 1.0*.
2. **The customer's release with conditions.** Readiness → Baselines → Customer releases → **Record release…**: the released document is the Lastenheft, the decision *Released with conditions* on 15.06.2026, the letter `docs/Prueferklaerung_Lastenheft_Weiche.pdf`. **Propose conditions from the letter** reads its tables; confirm the five proposals. PM-A-02 is overdue (30.09.2026), PM-A-01 waits for the next edition of the Lastenheft.
3. **The change request as a revision.** Sources → the Lastenheft → **Upload revision** → *a change request* → `docs/CR_PMNW-01.pdf` → **Match and review**. Spectator reads it from the PDF, without AI: 2 changed (PM.16, PM.72), 1 added (`PMNW-01/NEU-1`), 1 withdrawn (PM.42), and the note on PM.43. Apply it: the statements on PM.16 and PM.72 become stale, PM.42 leaves the Pflichtenheft, and the drift check flags the "100 ms" in the PM.72 statement. In the release, **Propose resolving change requests** proposes PMNW-01 as evidence for PM-A-01, PM-A-02 and PM-H-01: it withdraws or changes the requirements they name.
4. **The customer's confirmation.** In the release, **Check a confirmation letter** with `docs/Bestaetigung_Aufloesung_Auflagen.pdf`: it finds the clause that confirms all conditions, PM-A-01 to PM-A-03 named, and `[CR-PMNW-01]` as the change request you applied. **Confirm all open conditions** resolves the three Auflagen; the application condition and the Hinweis stay.
5. **The comment list as the customer's response.** On round 1, **Attach the customer's response…** with `docs/Kommentarliste_Pflichtenheft_V1.0.xlsx` (dated 28.09.2026). Five comments are matched by their ID, with the verdict from the *Bewertung* column; PM.19 stays unmatched (*ID not found*); the comment on PM.63 is matched by the ID in its text; the general remark matches nothing — discard it. Confirm the rest, answer the rejection and the question, update the stale statements and deliver the next round, *Pflichtenheft V 1.1*, with its delta and cover letter.

Read by rules, without a model: the change request, the conditions and the confirmation from the letters, and the comment list's matches and verdicts. A model is needed to propose statements, to classify the two comments without an assessment, for AI drafts of answers and summaries, and for the AI pass that looks for conditions the rules missed.

## Regenerate the documents

The Lastenheft's content lives in `spec/lastenheft.yaml`, the interface specification's in `spec/schnittstelle_s1.yaml`, the change request's in `spec/cr_pmnw_01.yaml`, the release report's and the confirmation's in `spec/freigabe_lastenheft.yaml` and the comment list's in `spec/kommentarliste_pflichtenheft_v1_0.yaml`. After a change:

```bash
pip install -r requirements-dev.txt
python tools/build_lastenheft_pdf.py
python tools/build_reference_pdf.py
python tools/build_change_request_pdf.py
python tools/build_release_letters_pdf.py
python tools/build_comment_list_xlsx.py
```

The builds are reproducible byte for byte (the comment list with fixed timestamps and uncompressed entries); CI checks that the committed documents match their sources.
