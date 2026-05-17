"""Test render_figure on first few math questions."""
import pathlib
import pymupdf
from extract import collect_blocks, parse_question, FIG_DIR, render_figure, find_anchors

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
FIG_DIR.mkdir(parents=True, exist_ok=True)

doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
rqs = collect_blocks(doc, "math")
for rq in rqs[:5]:
    anchors = find_anchors(rq)
    out = FIG_DIR / f"_test_{rq.qid}.png"
    ok = render_figure(doc, rq, anchors, out)
    print(rq.qid, ok, out, out.stat().st_size if out.exists() else None)
doc.close()
