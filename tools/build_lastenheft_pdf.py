"""Render spec/lastenheft.yaml as a DOORS export: docs/Lastenheft_Teilsystem_Weiche.pdf.

The PDF looks like what DOORS exports for a Lastenheft: a cover page, then
one ruled table (ID | Verbindlichkeit | Anforderungstext - Teil 1 | Teil 2 |
change column) running through the document, its header repeated on every
page, landscape pages stored as portrait with /Rotate 90. Two rows carry a
figure: a state machine drawn next to a short text, and a display layout
that *is* the requirement (a picture, without any text layer).

The output is reproducible byte for byte:

    pip install -r requirements-dev.txt
    python tools/build_lastenheft_pdf.py
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "lastenheft.yaml"
OUT = ROOT / "docs" / "Lastenheft_Teilsystem_Weiche.pdf"

WIDTH, HEIGHT = 842, 595  # A4 landscape, as displayed
TOP, BOTTOM = 40, 555
COLUMNS = [(30, 112), (112, 178), (178, 470), (470, 762), (762, 812)]
HEADER = ["ID", "Verbind-\nlichkeit", "Anforderungstext - Teil 1", "Anforderungstext - Teil 2"]
LINE = 12.5
FONT = 8.5
FIGURE_HEIGHT = {"state_machine": 92, "leds": 96}


def _lines(text: str) -> list[str]:
    return text.split("\n") if text else []


def _row_height(cells: list[str], figure: str | None) -> float:
    lines = max(1, *(len(_lines(c)) for c in cells))
    height = LINE * lines + 9
    if figure == "leds":
        return max(height, FIGURE_HEIGHT["leds"])
    if figure:
        height += FIGURE_HEIGHT[figure]
    return height


def _text(page: pymupdf.Page, x: float, y: float, text: str, size: float = FONT) -> None:
    for i, line in enumerate(_lines(text)):
        page.insert_text((x, y + LINE * i), line, fontsize=size, fontname="helv")


def _state_machine(page: pymupdf.Page, x: float, y: float) -> None:
    """A small SysML-style state machine below the row's text."""
    box_w, box_h = 70, 22
    states = {
        "UNBEKANNT": (x, y + 32),
        "IN_ENDLAGE": (x + 100, y + 2),
        "UMSTELLUNG": (x + 100, y + 64),
        "STOERUNG": (x + 205, y + 32),
    }
    for name, (sx, sy) in states.items():
        page.draw_rect(
            pymupdf.Rect(sx, sy, sx + box_w, sy + box_h),
            color=(0.2, 0.2, 0.2),
            width=0.6,
            radius=0.25,
        )
        page.insert_text((sx + 6, sy + 14), name, fontsize=6.5, fontname="helv")
    # (from, to, label, label position)
    arrows = [
        ((x + 70, y + 40), (x + 100, y + 16), "Selbsttest ok", (x + 34, y + 24)),
        ((x + 112, y + 24), (x + 112, y + 64), "Kd_Weiche_umstellen", (x + 40, y + 66)),
        ((x + 150, y + 64), (x + 150, y + 24), "Endlage erreicht", (x + 154, y + 48)),
        ((x + 170, y + 12), (x + 205, y + 38), "Endlage_verloren", (x + 180, y + 12)),
        ((x + 170, y + 76), (x + 205, y + 48), "Umstellzeit > 6 s", (x + 178, y + 86)),
    ]
    for (x0, y0), (x1, y1), label, (lx, ly) in arrows:
        page.draw_line((x0, y0), (x1, y1), color=(0.2, 0.2, 0.2), width=0.6)
        page.draw_circle((x1, y1), 1.6, color=(0.2, 0.2, 0.2), fill=(0.2, 0.2, 0.2))
        page.insert_text((lx, ly), label, fontsize=5.5, fontname="helv")


def _led_figure() -> pymupdf.Pixmap:
    """The display layout as a picture: no text layer, as when a figure was
    pasted into the DOORS object."""
    src = pymupdf.open()
    page = src.new_page(width=260, height=86)
    page.draw_rect(pymupdf.Rect(2, 2, 258, 84), color=(0.3, 0.3, 0.3), width=1)
    for i, (label, colour) in enumerate(
        [("links", (0, 0.7, 0)), ("rechts", (0, 0.7, 0)), ("Umstellung", (1, 0.75, 0)), ("Störung", (0.9, 0, 0))]
    ):
        cx = 36 + 62 * i
        page.draw_circle((cx, 32), 11, color=(0.2, 0.2, 0.2), fill=colour, width=0.8)
        page.insert_text((cx - 18, 62), label, fontsize=8, fontname="helv")
    page.insert_text((8, 79), "Anzeigetableau am Weichenantrieb, Ansicht von vorn", fontsize=6, fontname="helv")
    return page.get_pixmap(matrix=pymupdf.Matrix(3, 3))


def _table_page(
    doc: pymupdf.Document, rows: list[list], footer: str, change_column: str
) -> None:
    src = pymupdf.open()
    page = src.new_page(width=WIDTH, height=HEIGHT)
    page.insert_text((30, 26), "Lastenheft Teilsystem Weiche", fontsize=9, fontname="hebo")
    y = TOP
    for cells, figure in [((*HEADER, change_column), None), *rows]:
        height = _row_height(list(cells), figure)
        for (x0, x1), text in zip(COLUMNS, cells, strict=True):
            page.draw_rect(pymupdf.Rect(x0, y, x1, y + height), color=(0, 0, 0), width=0.5)
            _text(page, x0 + 3, y + 11, text)
        if figure == "state_machine":
            _state_machine(page, COLUMNS[2][0] + 6, y + LINE * len(_lines(cells[2])) + 6)
        elif figure == "leds":
            x0 = COLUMNS[2][0] + 8
            page.insert_image(pymupdf.Rect(x0, y + 6, x0 + 255, y + 90), pixmap=_led_figure())
        y += height
    page.insert_text((30, HEIGHT - 18), footer, fontsize=7, fontname="helv")
    out = doc.new_page(width=HEIGHT, height=WIDTH)
    out.show_pdf_page(out.rect, src, 0, rotate=90)
    out.set_rotation(90)


def _paginate(rows: list[tuple]) -> list[list[tuple]]:
    pages: list[list[tuple]] = [[]]
    used = _row_height(HEADER + [""], None)
    for row in rows:
        height = _row_height(list(row[0]), row[1])
        if TOP + used + height > BOTTOM and pages[-1]:
            pages.append([])
            used = _row_height(HEADER + [""], None)
        pages[-1].append(row)
        used += height
    return pages


def build() -> bytes:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    rows = []
    for entry in spec["rows"]:
        source_id, obligation, text, text2, figure = (list(entry) + ["", None])[:5]
        rows.append(((source_id, obligation, text, text2 or "", ""), figure))
    pages = _paginate(rows)

    doc = pymupdf.open()
    cover = doc.new_page(width=WIDTH, height=HEIGHT)
    cover.insert_text((90, 200), spec["title"], fontsize=26, fontname="hebo")
    cover.insert_text((90, 240), spec["subtitle"], fontsize=14, fontname="helv")
    cover.insert_text((90, 280), f"Version {spec['version']}", fontsize=12, fontname="helv")
    cover.insert_text(
        (90, 330),
        "Synthetisches Beispiel — beschreibt kein reales System.",
        fontsize=11,
        fontname="helv",
    )
    total = len(pages) + 1
    for number, page_rows in enumerate(pages, start=2):
        footer = f"Lastenheft Teilsystem Weiche · Version {spec['version']} · Seite {number} von {total}"
        _table_page(doc, page_rows, footer, spec["change_column"])
    doc.set_metadata({"title": spec["title"], "subject": spec["subtitle"]})
    return doc.tobytes(garbage=3, deflate=True, no_new_id=True)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(build())
    print(f"wrote {OUT.relative_to(ROOT)}")
