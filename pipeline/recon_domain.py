"""Find a page with Problem-Solving and Data Analysis to inspect blocks."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
for pno in range(len(doc)):
    text = doc[pno].get_text()
    if "Problem-Solving" in text or "Geometry and" in text:
        # Print blocks for this page
        print(f"--- page {pno+1} ---")
        for b in doc[pno].get_text("blocks"):
            x0, y0, x1, y1, t, n, tt = b
            if y0 > 130:
                continue
            print(f"y={y0:5.1f} x={x0:5.1f}-{x1:5.1f} {t!r}")
        if pno > 50:
            break
doc.close()
