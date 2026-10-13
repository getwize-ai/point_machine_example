"""Render spec/schnittstelle_s1.yaml: docs/Schnittstellenspezifikation_S1.pdf.

The document the Lastenheft cites as [S1]: a cover page with its edition,
then numbered sections, as such specifications are laid out. Attached to the
reference [S1] in Spectator, a citation such as "[S1] Abschnitt 3.2" resolves
to its section.

The output is reproducible byte for byte:

    pip install -r requirements-dev.txt
    python tools/build_reference_pdf.py
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "schnittstelle_s1.yaml"
OUT = ROOT / "docs" / "Schnittstellenspezifikation_S1.pdf"

WIDTH, HEIGHT = 595, 842  # A4 portrait
LINE = 14


def build() -> bytes:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    doc = pymupdf.open()
    cover = doc.new_page(width=WIDTH, height=HEIGHT)
    cover.insert_text((70, 260), spec["title"], fontsize=20, fontname="hebo")
    cover.insert_text((70, 292), spec["subtitle"], fontsize=11, fontname="helv")
    cover.insert_text((70, 330), f"Version {spec['version']}", fontsize=12, fontname="helv")
    cover.insert_text(
        (70, 370),
        "Synthetisches Beispiel — beschreibt kein reales System.",
        fontsize=10,
        fontname="helv",
    )
    total = len(spec["pages"]) + 1
    for number, sections in enumerate(spec["pages"], start=2):
        page = doc.new_page(width=WIDTH, height=HEIGHT)
        y = 80.0
        for section, title, text in sections:
            size = 13 if "." not in section else 11
            page.insert_text((70, y), f"{section} {title}", fontsize=size, fontname="hebo")
            y += LINE + 6
            for line in text.split("\n"):
                page.insert_text((70, y), line, fontsize=10, fontname="helv")
                y += LINE
            y += 14
        page.insert_text(
            (70, HEIGHT - 40),
            f"[S1] Version {spec['version']} · Seite {number} von {total}",
            fontsize=8,
            fontname="helv",
        )
    doc.set_metadata({"title": spec["title"], "subject": spec["subtitle"]})
    return doc.tobytes(garbage=3, deflate=True, no_new_id=True)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(build())
    print(f"wrote {OUT.relative_to(ROOT)}")
