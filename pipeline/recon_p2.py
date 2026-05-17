"""Dump all text blocks with positions for math_full p2 (one with figure)."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
page = doc[1]
blocks = page.get_text("blocks")
for b in blocks:
    x0, y0, x1, y1, text, bno, btype = b
    print(f"  y={y0:6.1f}-{y1:6.1f}  x={x0:5.1f}-{x1:5.1f}  type={btype}  {text!r:.180}")
doc.close()
