"""Dump block structure for R&W page 1 and a paired-passage page."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "reading_writing_questionbank-export-2026-5-17.pdf")

for pno in [0, 1349]:
    page = doc[pno]
    print(f"\n=== rw page {pno+1} ===")
    blocks = page.get_text("blocks")
    for b in blocks:
        x0, y0, x1, y1, text, bno, btype = b
        print(f"  y={y0:6.1f}-{y1:6.1f}  x={x0:5.1f}-{x1:5.1f}  {text!r:.180}")
doc.close()
