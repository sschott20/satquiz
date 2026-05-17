"""Try xhtml extraction for math regions."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")

# page 1
for pno in [0, 6]:
    print(f"\n=== page {pno+1} XHTML ===")
    print(doc[pno].get_text("xhtml")[:3000])

# Try to find structured text near math regions:
# Maybe the PDF has actual MathML or alt-text annotations
page = doc[0]
print("\n=== Annotations on page 1 ===")
for annot in page.annots() or []:
    print(annot.info, annot.rect)

# Check page links - probably none
print("\n=== Links on page 1 ===")
print(page.get_links())

doc.close()
