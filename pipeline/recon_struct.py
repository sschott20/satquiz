"""Check for structure tree / accessibility info in PDF."""
import pymupdf
import pathlib

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
print("metadata:", doc.metadata)
print("is_tagged_pdf:", doc.is_pdf, doc.has_links())
# Try to get xml structure
try:
    root = doc.pdf_catalog()
    print("catalog xref:", root)
    print("catalog obj:", doc.xref_object(root, compressed=True)[:1000])
except Exception as e:
    print("catalog err:", e)

# Try to extract a Type3 font glyph definition to see if it has any embedded marker
page = doc[0]
fonts = page.get_fonts(full=True)
print("\nFonts on page 1:")
for f in fonts:
    print(" ", f)

doc.close()
