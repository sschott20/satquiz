"""Look at a Geometry+Trigonometry page."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
for pno in range(len(doc)):
    text = doc[pno].get_text()
    if "Geometry and" in text and "Area and volume" in text:
        print(f"--- page {pno+1} ---")
        for b in doc[pno].get_text("blocks"):
            x0, y0, x1, y1, t, n, tt = b
            if y0 > 130:
                continue
            print(f"y={y0:5.1f} x={x0:5.1f}-{x1:5.1f} {t!r}")
        break
doc.close()
