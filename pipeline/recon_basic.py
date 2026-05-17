"""Initial recon: page counts + dump first pages text for inspection."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
OUT = pathlib.Path("/Users/yecl/Documents/satquiz/pipeline/recon")
OUT.mkdir(exist_ok=True)

pdfs = {
    "math_full": SRC / "math_questionbank-export-2026-5-17-1.pdf",
    "math_excl": SRC / "exclude_active_math_questionbank-export-2026-5-17-2.pdf",
    "rw_full":   SRC / "reading_writing_questionbank-export-2026-5-17.pdf",
    "rw_excl":   SRC / "exclude_active_reading_writing_questionbank-export-2026-5-17-2.pdf",
}

for name, p in pdfs.items():
    doc = pymupdf.open(p)
    print(f"{name}: {len(doc)} pages, {p.stat().st_size/1e6:.1f} MB")
    # Dump first 5 pages text
    for i in range(min(5, len(doc))):
        text = doc[i].get_text()
        (OUT / f"{name}_p{i+1}.txt").write_text(text)
    # Also dump pages 50, 100, 500 as samples
    for i in [50, 100, 500]:
        if i < len(doc):
            (OUT / f"{name}_p{i+1}.txt").write_text(doc[i].get_text())
    doc.close()
