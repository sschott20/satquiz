"""Inspect page 4 (skill: Linear functions, diff Easy) blocks."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
page = doc[3]
for b in page.get_text("blocks"):
    x0, y0, x1, y1, t, n, tt = b
    if y0 > 130: break
    print(f"y={y0:.1f} x={x0:.1f}-{x1:.1f}  {t!r}")
doc.close()
