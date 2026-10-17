"""Render spec/cr_pmnw_01.yaml as a change request: docs/CR_PMNW-01.pdf.

A customer changes its Lastenheft between editions with change requests, a
Word form exported to PDF: a header block (CR Nummer, Kurzbezeichnung des
CR, CR Autor, Bezugsdokument, Bezug im Dokument), the classification
(Fehler / Neue Funktion / Verdeutlichung / Redaktionell, each "[ ja ]" or
"[ nein ]"), the change itself and closing blocks (impact analysis, sign-off,
references, history).

The change is a table in the Lastenheft's own columns (ID | Verbind-lichkeit
| Anforderungstext) with change markup: removed text red and struck through,
added text green, kept text black — a ready-made old/new diff. Rows are
separated by grey rules, ID and obligation sit vertically centred, the
header is printed once. A full-width row "Hinweis zu …" is a note.

The output is reproducible byte for byte:

    pip install -r requirements-dev.txt
    python tools/build_change_request_pdf.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "cr_pmnw_01.yaml"
OUT = ROOT / "docs" / "CR_PMNW-01.pdf"

RED = (1.0, 0.0, 0.0)
GREEN = (0.0, 0.69, 0.31)  # #00B050
BLACK = (0.0, 0.0, 0.0)
GREY_RULE = (0.8, 0.8, 0.8)

PAGE_W, PAGE_H = 595.0, 842.0  # A4 portrait
LEFT, RIGHT = 56.0, 539.0
TOP, BOTTOM = 72.0, 785.0
SIZE = 9.0
LEADING = 11.5
#: Change table columns: ID | Verbind-lichkeit | Anforderungstext
TABLE_X = (66.0, 136.0, 192.0, 529.0)
PAD = 4.0

KEPT, REMOVED, ADDED = "=", "-", "+"
#: A run of text in one colour: (mark, text)
Run = tuple[str, str]
_MARKUP = re.compile(r"\[-(.*?)-\]|\{\+(.*?)\+\}", re.DOTALL)


def parse_markup(text: str) -> list[Run]:
    """ "a [-b-]{+c+} d" → [("=", "a "), ("-", "b"), ("+", "c"), ("=", " d")]."""
    runs: list[Run] = []
    position = 0
    for match in _MARKUP.finditer(text):
        if match.start() > position:
            runs.append((KEPT, text[position : match.start()]))
        if match.group(1) is not None:
            runs.append((REMOVED, match.group(1)))
        else:
            runs.append((ADDED, match.group(2)))
        position = match.end()
    if position < len(text):
        runs.append((KEPT, text[position:]))
    return [run for run in runs if run[1]]


def _width(text: str, bold: bool = False) -> float:
    return pymupdf.get_text_length(
        text, fontname="hebo" if bold else "helv", fontsize=SIZE
    )


def wrap_runs(runs: list[Run], width: float) -> list[list[Run]]:
    """Runs laid out in lines of at most *width* points. Lines break at
    spaces (the space is dropped); explicit newlines are kept. Pure."""
    lines: list[list[Run]] = []
    for paragraph in _split_lines(runs):
        # Characters with their mark; breaks are possible at spaces
        chars = [(mark, ch) for mark, text in paragraph for ch in text]
        line: list[tuple[str, str]] = []
        last_space: int | None = None
        for mark, ch in chars:
            line.append((mark, ch))
            if ch == " ":
                last_space = len(line) - 1
            if _width("".join(c for _, c in line)) > width and last_space is not None:
                lines.append(_merge(line[:last_space]))
                line = line[last_space + 1 :]
                last_space = next(
                    (i for i in range(len(line) - 1, -1, -1) if line[i][1] == " "),
                    None,
                )
        lines.append(_merge(line))
    return lines


def _split_lines(runs: list[Run]) -> list[list[Run]]:
    paragraphs: list[list[Run]] = [[]]
    for mark, text in runs:
        for index, piece in enumerate(text.split("\n")):
            if index:
                paragraphs.append([])
            if piece:
                paragraphs[-1].append((mark, piece))
    return paragraphs


def _merge(chars: list[tuple[str, str]]) -> list[Run]:
    runs: list[Run] = []
    for mark, ch in chars:
        if runs and runs[-1][0] == mark:
            runs[-1] = (mark, runs[-1][1] + ch)
        else:
            runs.append((mark, ch))
    return runs


class Writer:
    """A small flow layout over A4 pages with the form's header and footer."""

    def __init__(self, spec: dict) -> None:
        self.spec = spec
        self.doc = pymupdf.open()
        self.page: pymupdf.Page | None = None
        self.y = TOP
        self.new_page()

    def new_page(self) -> None:
        page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        # Header: the customer's name in a box, the classification of the
        # document and the CR number
        page.draw_rect(pymupdf.Rect(LEFT, 34, LEFT + 84, 54), color=BLACK, width=0.6)
        page.insert_text((LEFT + 6, 47), "Beispielbahn", fontsize=8, fontname="hebo")
        page.insert_text((250, 48), "Vertraulich", fontsize=10, fontname="hebo")
        page.insert_text(
            (370, 48), f"Change Request {self.spec['number']}", fontsize=10
        )
        page.draw_line((LEFT, 60), (RIGHT, 60), color=BLACK, width=0.5)
        page.draw_line((LEFT, 795), (RIGHT, 795), color=BLACK, width=0.5)
        self.page = page
        self.y = TOP

    def finish(self) -> bytes:
        total = self.doc.page_count
        footer = f"Version {self.spec['version']} / {self.spec['date']}"
        for number, page in enumerate(self.doc, start=1):
            page.insert_text((LEFT, 808), self.spec["number"], fontsize=8)
            page.insert_text((270, 808), f"Seite {number}/{total}", fontsize=8)
            page.insert_text((430, 808), footer, fontsize=8)
        self.doc.set_metadata(
            {
                "title": f"Change Request {self.spec['number']}",
                "subject": self.spec["title"],
            }
        )
        return self.doc.tobytes(garbage=3, deflate=True, no_new_id=True)

    # -- primitives ------------------------------------------------------

    def ensure(self, height: float) -> None:
        if self.y + height > BOTTOM:
            self.new_page()

    def hrule(self, x0: float, y: float, x1: float, colour=GREY_RULE) -> None:
        self.page.draw_rect(
            pymupdf.Rect(x0, y - 0.36, x1, y + 0.36), color=None, fill=colour, width=0
        )

    def vrule(self, x: float, y0: float, y1: float, colour=GREY_RULE) -> None:
        self.page.draw_rect(
            pymupdf.Rect(x - 0.36, y0, x + 0.36, y1), color=None, fill=colour, width=0
        )

    def runs(
        self,
        x: float,
        baseline: float,
        runs: list[Run],
        *,
        bold: bool = False,
        underline_added: bool = False,
    ) -> float:
        font = "hebo" if bold else "helv"
        for mark, text in runs:
            colour = {REMOVED: RED, ADDED: GREEN}.get(mark, BLACK)
            width = _width(text, bold)
            self.page.insert_text(
                (x, baseline), text, fontsize=SIZE, fontname=font, color=colour
            )
            if mark == REMOVED:
                # The strike line: a thin filled rectangle across the middle
                middle = baseline - SIZE * 0.3
                self.page.draw_rect(
                    pymupdf.Rect(x, middle - 0.42, x + width, middle + 0.42),
                    color=None,
                    fill=RED,
                    width=0,
                )
            elif mark == ADDED and underline_added:
                self.page.draw_rect(
                    pymupdf.Rect(x, baseline + 1.2, x + width, baseline + 1.8),
                    color=None,
                    fill=GREEN,
                    width=0,
                )
            x += width
        return x

    # -- blocks ----------------------------------------------------------

    def paragraph(self, text: str, *, bold: bool = False, underline: bool = False):
        for line in wrap_runs([(KEPT, text)], RIGHT - LEFT - 20):
            self.ensure(LEADING)
            baseline = self.y + SIZE
            end = self.runs(LEFT + 10, baseline, line, bold=bold)
            if underline:
                self.page.draw_rect(
                    pymupdf.Rect(LEFT + 10, baseline + 1.2, end, baseline + 1.8),
                    color=None,
                    fill=BLACK,
                    width=0,
                )
            self.y += LEADING
        self.y += 6

    def boxed_fields(self, title: str | None, fields: list[list[str]]) -> None:
        """Label/value rows in a box with a thick border; long labels wrap."""
        rows = [
            (wrap_runs([(KEPT, label)], 155), wrap_runs([(KEPT, value)], 300))
            for label, value in fields
        ]
        heights = [max(len(a), len(b)) * LEADING + 4 for a, b in rows]
        total = sum(heights) + (LEADING + 6 if title else 0)
        self.ensure(total + 8)
        top = self.y
        if title:
            self.runs(LEFT + 4, self.y + SIZE + 1, [(KEPT, title)], bold=True)
            self.y += LEADING + 6
            self.hrule(LEFT, self.y, RIGHT, BLACK)
        body_top = self.y
        for (labels, values), height in zip(rows, heights, strict=True):
            for i, line in enumerate(labels):
                self.runs(LEFT + 4, self.y + SIZE + 2 + LEADING * i, line, bold=True)
            for i, line in enumerate(values):
                self.runs(225, self.y + SIZE + 2 + LEADING * i, line)
            self.y += height
            self.hrule(LEFT, self.y, RIGHT, BLACK)
        self.vrule(220, body_top, self.y, BLACK)
        self.page.draw_rect(
            pymupdf.Rect(LEFT, top, RIGHT, self.y), color=BLACK, width=1.6
        )
        self.y += 10

    def classification(self, flags: dict[str, bool]) -> None:
        self.ensure(len(flags) * 2 * LEADING + LEADING + 12)
        top = self.y
        self.runs(
            LEFT + 4, self.y + SIZE + 1, [(KEPT, "Klassifikation des CR")], bold=True
        )
        self.y += LEADING + 4
        for label, value in flags.items():
            self.hrule(LEFT, self.y, RIGHT, BLACK)
            self.runs(LEFT + 2, self.y + SIZE, [(KEPT, label)], bold=True)
            self.runs(
                LEFT + 2,
                self.y + SIZE + LEADING,
                [(KEPT, "[ ja ]" if value else "[ nein ]")],
            )
            self.y += 2 * LEADING
        self.page.draw_rect(
            pymupdf.Rect(LEFT, top, RIGHT, self.y), color=BLACK, width=1.6
        )
        self.y += 10

    def change_table(self, rows: list[dict]) -> None:
        # A little room to the right rule, as the form keeps
        widths = [TABLE_X[i + 1] - TABLE_X[i] - 2 * PAD - 4 for i in range(3)]
        # Header, once
        header = [["ID"], ["Verbind-", "lichkeit"], ["Anforderungstext"]]
        height = 2 * LEADING + 6
        self.ensure(height + 3 * LEADING)
        top = self.y
        self.hrule(TABLE_X[0], top, TABLE_X[-1])
        for col, lines in enumerate(header):
            for i, line in enumerate(lines):
                self.runs(
                    TABLE_X[col] + PAD, top + SIZE + 3 + LEADING * i, [(KEPT, line)]
                )
        self.y += height
        self.hrule(TABLE_X[0], self.y, TABLE_X[-1])
        for x in TABLE_X:
            self.vrule(x, top, self.y)
        for row in rows:
            if "note" in row:
                lines = wrap_runs(
                    parse_markup(row["note"]), TABLE_X[-1] - TABLE_X[0] - 2 * PAD
                )
                part_height = len(lines) * LEADING + 6
                self.ensure(part_height)
                part_top = self.y
                for n, line in enumerate(lines):
                    self.runs(
                        TABLE_X[0] + PAD, part_top + SIZE + 3 + LEADING * n, line
                    )
                self.y += part_height
                self.hrule(TABLE_X[0], self.y, TABLE_X[-1])
                # One merged cell: no inner column rules
                for x in (TABLE_X[0], TABLE_X[-1]):
                    self.vrule(x, part_top, self.y)
                continue
            cells = [
                wrap_runs(parse_markup(str(row[key])), width)
                for key, width in zip(("id", "obligation", "text"), widths, strict=True)
            ]
            lines = max(len(cell) for cell in cells)
            part_height = lines * LEADING + 6
            self.ensure(part_height)
            part_top = self.y
            for col, cell in enumerate(cells):
                # ID and obligation sit vertically centred in the row
                offset = (lines - len(cell)) * LEADING / 2 if col < 2 else 0
                for n, line in enumerate(cell):
                    self.runs(
                        TABLE_X[col] + PAD,
                        part_top + SIZE + 3 + offset + LEADING * n,
                        line,
                        underline_added=col == 0,
                    )
            self.y += part_height
            self.hrule(TABLE_X[0], self.y, TABLE_X[-1])
            for x in TABLE_X:
                self.vrule(x, part_top, self.y)
        self.y += 8


def build() -> bytes:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    w = Writer(spec)
    w.boxed_fields(
        None,
        [
            ["CR Nummer", spec["number"]],
            ["Kurzbezeichnung des CR", spec["title"]],
            ["CR Autor", spec["author"]],
            ["Bezugsdokument", spec["reference_document"]],
            ["Bezug im Dokument", spec["reference_in_document"]],
        ],
    )
    w.classification(spec["classification"])
    w.ensure(LEADING * 3)
    w.runs(LEFT + 4, w.y + SIZE + 1, [(KEPT, "Change Request")], bold=True)
    w.y += LEADING + 6
    for block in spec["body"]:
        ((kind, content),) = block.items()
        if kind == "p":
            w.paragraph(content)
        elif kind == "item":
            w.paragraph(content, underline=True)
        elif kind == "bold":
            w.paragraph(content, bold=True)
        elif kind == "table":
            w.change_table(content)
        else:
            raise ValueError(f"unknown block {kind!r}")
    w.boxed_fields("Auswirkungsanalyse", spec["impact"])
    w.boxed_fields("Feststellung der Sicherheitsrelevanz", spec["safety"])
    w.boxed_fields("Erstellungs- und Freigabestatus", spec["sign_off"])
    w.boxed_fields("Referenzdokumente", spec["references"])
    w.boxed_fields(
        "Dokumentenhistorie",
        [
            [version, f"{date} {author}: {comment}"]
            for version, date, author, comment in spec["history"]
        ],
    )
    return w.finish()


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(build())
    print(f"wrote {OUT.relative_to(ROOT)}")
