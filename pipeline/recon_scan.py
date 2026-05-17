"""Scan PDFs to find variety: SPR (no A/B/C/D), paired passages (Text 1/Text 2), multi-page questions."""
import pymupdf
import pathlib
import re

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")

def scan(name, path, max_pages=None):
    doc = pymupdf.open(path)
    n = len(doc) if max_pages is None else min(max_pages, len(doc))
    print(f"\n=== {name} ({n}/{len(doc)} pages) ===")

    qid_pages = []  # (page_idx, qid)
    spr_candidates = []  # pages with "Correct Answer:" but NO "A. ... B. ... C. ... D."
    paired_pages = []
    multi_image_pages = []

    for i in range(n):
        page = doc[i]
        text = page.get_text()
        m = re.search(r"Question ID:\s*([0-9a-f]+)", text)
        if m:
            qid_pages.append((i, m.group(1)))
        # Detect SPR vs MCQ: SPR has "Correct Answer: <number>" but no choice lines.
        if "Correct Answer:" in text:
            has_choices = bool(re.search(r"^A\.\s", text, re.MULTILINE)) and bool(re.search(r"^D\.\s", text, re.MULTILINE))
            ca = re.search(r"Correct Answer:\s*(.+)", text)
            if ca and not has_choices:
                spr_candidates.append((i, ca.group(1).strip()[:60]))
        if "Text 1" in text and "Text 2" in text:
            paired_pages.append(i)
        # Count images on the page
        imgs = page.get_images()
        if len(imgs) >= 2:
            multi_image_pages.append((i, len(imgs)))

    print(f"  Question IDs found: {len(qid_pages)}")
    print(f"  First 5 IDs:", qid_pages[:5])
    print(f"  SPR-looking pages (no A/B/C/D): {len(spr_candidates)}")
    print(f"  First 5 SPR examples:", spr_candidates[:5])
    print(f"  Paired-passage pages: {len(paired_pages)}")
    print(f"  First 5 paired:", paired_pages[:5])
    print(f"  Pages with >=2 images: {len(multi_image_pages)}")
    print(f"  First 5:", multi_image_pages[:5])
    doc.close()

scan("math_full", SRC / "math_questionbank-export-2026-5-17-1.pdf")
scan("rw_full", SRC / "reading_writing_questionbank-export-2026-5-17.pdf")
