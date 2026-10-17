"""Render spec/freigabe_lastenheft.yaml: the customer's release of the
Lastenheft with conditions, and its confirmation that all are resolved.

* docs/Prueferklaerung_Lastenheft_Weiche.pdf — the release report
  ("Prüferklärung"): a cover with the released document and the sign-off box,
  Versionsspiegel and Referenzen, the assessment, chapter 4 with the
  application conditions (Nr. | Titel | Herkunft | Adressat), chapter 5 with
  the conditions (Nr. | Art | Betroffen | Stichwort / Quelle | Beschreibung |
  Frist) and chapter 6 with the decision.
* docs/Bestaetigung_Aufloesung_Auflagen.pdf — the blanket confirmation
  ("Bestätigung zur Auflösung von Auflagen"): Referenzen with the change
  request that resolved the conditions, the declaration that all conditions
  are closed, and "Offene Punkte: Keine".

A4 portrait, a running header from page 2, a footer with the date, the
document's short name and the page. Tables are ruled cell by cell, their
header row grey.

The output is reproducible byte for byte:

    pip install -r requirements-dev.txt
    python tools/build_release_letters_pdf.py
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "freigabe_lastenheft.yaml"
OUT = {
    "report": ROOT / "docs" / "Prueferklaerung_Lastenheft_Weiche.pdf",
    "confirmation": ROOT / "docs" / "Bestaetigung_Aufloesung_Auflagen.pdf",
}

W, H = 595, 842  # A4 portrait
LEFT, RIGHT = 56, 539
HEADING = (0.1, 0.25, 0.45)
GREY = (0.85, 0.85, 0.85)
FONT, BOLD = "helv", "hebo"


def _lines(text: str, width: float, size: float, font: str = FONT) -> list[str]:
    """Word-wrap *text* (explicit newlines kept) to *width* points."""
    out: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            candidate = f"{line} {word}".strip()
            if pymupdf.get_text_length(candidate, fontname=font, fontsize=size) <= width:
                line = candidate
            else:
                if line:
                    out.append(line)
                line = word
        out.append(line)
    return out


def _text(
    page: pymupdf.Page,
    y: float,
    text: str,
    *,
    size: float = 10,
    font: str = FONT,
    color: tuple = (0, 0, 0),
    x: float = LEFT,
) -> float:
    """Write wrapped text below *y*; returns the y below it."""
    for line in _lines(text, RIGHT - x, size, font):
        y += size * 1.35
        page.insert_text((x, y), line, fontsize=size, fontname=font, color=color)
    return y


def _table(
    page: pymupdf.Page,
    y: float,
    widths: list[float],
    rows: list[list],
    *,
    size: float = 8.5,
    header: bool = True,
) -> float:
    """A table ruled cell by cell; the first row is a grey header."""
    for index, row in enumerate(rows):
        bold = header and index == 0
        font = BOLD if bold else FONT
        cells = [
            _lines(str(cell), w - 10, size, font)
            for cell, w in zip(row, widths, strict=True)
        ]
        height = max(len(c) for c in cells) * size * 1.3 + 6
        x = LEFT
        for lines, w in zip(cells, widths, strict=True):
            rect = pymupdf.Rect(x, y, x + w, y + height)
            page.draw_rect(rect, color=(0, 0, 0), fill=GREY if bold else None, width=0.5)
            ty = y + 2
            for line in lines:
                ty += size * 1.3
                page.insert_text((x + 3, ty - 2), line, fontsize=size, fontname=font)
            x += w
        y += height
    return y


def _blocks(page: pymupdf.Page, blocks: list[dict]) -> None:
    y = 70.0
    for block in blocks:
        ((kind, content),) = block.items()
        if kind == "h1":
            y = _text(page, y + 10, content, size=13, font=BOLD, color=HEADING)
        elif kind == "h2":
            page.draw_line((LEFT, y + 8), (RIGHT, y + 8), color=HEADING, width=0.6)
            y = _text(page, y + 10, content, size=11, font=BOLD, color=HEADING)
        elif kind == "p":
            y = _text(page, y + 4, content)
        elif kind == "clause":
            y = _text(page, y + 2, content, x=LEFT + 14)
        elif kind == "table":
            y = _table(page, y + 10, content["widths"], content["rows"]) + 4
        elif kind == "caption":
            y = _text(page, y, content, size=8.5)
        else:
            raise ValueError(f"unknown block {kind!r}")


def _centred(page: pymupdf.Page, y: float, lines: list[list]) -> None:
    for text, size, weight in lines:
        font = BOLD if weight == "bold" else FONT
        length = pymupdf.get_text_length(text, fontname=font, fontsize=size)
        page.insert_text(((W - length) / 2, y), text, fontsize=size, fontname=font)
        y += size * 1.9


def _organisation(page: pymupdf.Page, names: list[str]) -> None:
    for index, name in enumerate(names):
        page.insert_text(
            (380, 70 + 12 * index), name, fontsize=9, fontname=BOLD if not index else FONT
        )


def _report_cover(page: pymupdf.Page, part: dict) -> None:
    cover = part["cover"]
    page.draw_rect(pymupdf.Rect(LEFT, 60, 300, 110), color=(0, 0, 0), width=0.6)
    y = 62.0
    for line in _lines(cover["box"], 230, 9):
        y += 12
        page.insert_text((LEFT + 6, y), line, fontsize=9, fontname=FONT)
    _organisation(page, cover["organisation"])
    _centred(page, 200, cover["title"])
    page.insert_text((LEFT, 470), f"Stand: {part['stand']}", fontsize=10, fontname=FONT)
    page.insert_text(
        (440, 470), f"Version: {part['version']}", fontsize=10, fontname=FONT
    )
    _text(page, 490, "Prüf- und Freigabezeichnung", font=BOLD)
    _table(page, 520, [140, 200], cover["sign_off"], size=9)


def _confirmation_cover(page: pymupdf.Page, part: dict) -> None:
    cover = part["cover"]
    _organisation(page, cover["organisation"])
    _centred(page, 220, cover["title"])
    page.insert_text((LEFT, 420), f"Stand: {part['stand']}", fontsize=10, fontname=FONT)
    page.insert_text(
        (440, 420), f"Version: {part['version']}", fontsize=10, fontname=FONT
    )
    page.insert_text(
        (LEFT, 440),
        f"Dokumentnummer: {cover['document_number']}",
        fontsize=10,
        fontname=FONT,
    )
    _table(page, 480, [483], cover["sign_off"], size=9)


def _frame(page: pymupdf.Page, number: int, total: int, part: dict) -> None:
    """Running header (from page 2) and footer."""
    if number > 1:
        page.insert_text((LEFT, 40), part["running_title"], fontsize=8, fontname=FONT)
        page.insert_text((LEFT, 50), part["short"], fontsize=8, fontname=FONT)
    page.draw_line((LEFT, 800), (RIGHT, 800), color=(0, 0, 0), width=0.4)
    page.insert_text(
        (LEFT, 812),
        f"Stand {part['stand']}, Version {part['version']}, {part['short']}",
        fontsize=7.5,
        fontname=FONT,
    )
    page.insert_text((500, 812), f"{number} / {total}", fontsize=7.5, fontname=FONT)


def _letter(part: dict, cover, title: str) -> bytes:
    doc = pymupdf.open()
    total = len(part["pages"]) + 1
    page = doc.new_page(width=W, height=H)
    cover(page, part)
    _frame(page, 1, total, part)
    for number, blocks in enumerate(part["pages"], start=2):
        page = doc.new_page(width=W, height=H)
        _blocks(page, blocks)
        _frame(page, number, total, part)
    doc.set_metadata({"title": title, "author": "Beispielbahn"})
    return doc.tobytes(garbage=3, deflate=True, no_new_id=True)


def build() -> dict[Path, bytes]:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    return {
        OUT["report"]: _letter(
            spec["report"],
            _report_cover,
            "Prüferklärung Lastenheft Teilsystem Weiche Version 1.1",
        ),
        OUT["confirmation"]: _letter(
            spec["confirmation"],
            _confirmation_cover,
            "Bestätigung zur Auflösung von Auflagen",
        ),
    }


if __name__ == "__main__":
    for path, data in build().items():
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        print(f"wrote {path.relative_to(ROOT)}")
