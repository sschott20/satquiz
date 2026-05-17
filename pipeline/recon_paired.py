"""Dump some paired-passage R&W pages and SPR-looking R&W pages."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
OUT = pathlib.Path("/Users/yecl/Documents/satquiz/pipeline/recon")

doc = pymupdf.open(SRC / "reading_writing_questionbank-export-2026-5-17.pdf")
for i in [1349, 1352, 1367, 387, 741, 754]:
    (OUT / f"rw_full_p{i+1}_special.txt").write_text(doc[i].get_text())
doc.close()
