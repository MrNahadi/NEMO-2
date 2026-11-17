"""Render chosen pages of the generated calculation reports to PNG for the project report.

Needs pypdfium2 (not an engine dependency):  python render_pdf_pages.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / "data", ROOT / "images"

PAGES = {"padeye": {1: "padeye-report-summary", 3: "padeye-report-drawing", 6: "padeye-report-calc"},
         "pipe-bracket": {3: "bracket-report-drawing", 4: "bracket-report-span"},
         "stabilizer": {3: "fin-report-drawing", 4: "fin-report-foil"}}


def main() -> None:
    cases = json.loads((DATA / "cases.json").read_text())
    for part, pages in PAGES.items():
        pdf_path = DATA / cases[part]["run_dir"] / "designs" / "lightest" / "calculation-report.pdf"
        pdf = pdfium.PdfDocument(str(pdf_path))
        print(part, len(pdf), "pages")
        for number, name in pages.items():
            pdf[number - 1].render(scale=2.2).to_pil().save(IMG / f"{name}.png")
            print("  wrote", name)


if __name__ == "__main__":
    main()
