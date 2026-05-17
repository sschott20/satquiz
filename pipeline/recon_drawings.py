"""Inspect vector drawings on pages with figures."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")

for pno in [0, 1, 6, 13]:
    page = doc[pno]
    drawings = page.get_drawings()
    text_blocks = page.get_text("blocks")
    print(f"\n=== page {pno+1} ===")
    print(f"  drawings: {len(drawings)}")
    if drawings:
        xs = [d['rect'].x0 for d in drawings]
        ys = [d['rect'].y0 for d in drawings]
        ws = [d['rect'].width for d in drawings]
        hs = [d['rect'].height for d in drawings]
        print(f"  drawing bbox x range: {min(xs):.0f} - {max([d['rect'].x1 for d in drawings]):.0f}")
        print(f"  drawing bbox y range: {min(ys):.0f} - {max([d['rect'].y1 for d in drawings]):.0f}")
        print(f"  total area: {sum(w*h for w,h in zip(ws,hs)):.0f}")

doc.close()
