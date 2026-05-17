"""Check if math glyphs are extractable as text via rawdict/dict."""
import pymupdf
import pathlib
import json

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")

# Page 1: math fully vector (no images)
page = doc[0]
d = page.get_text("rawdict")
# Find the prompt area roughly (the "In the given equation" block)
for block in d["blocks"]:
    if block["type"] != 0:
        continue
    bbox = block["bbox"]
    # We want the prompt area (around y=160-180)
    if bbox[1] < 160 or bbox[3] > 200:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            font = span.get("font", "")
            txt = "".join(ch.get("c", "") for ch in span.get("chars", []))
            print(f"  font={font!r}  size={span.get('size'):.1f}  text={txt!r}")
print("---")
# Look in vector region (y between 140 and 200)
print("All blocks y in 100..210")
for block in d["blocks"]:
    bbox = block["bbox"]
    if bbox[1] < 100 or bbox[1] > 210:
        continue
    print(f"block type={block['type']} bbox={[round(v,1) for v in bbox]}")
    if block["type"] != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            font = span.get("font", "")
            txt = "".join(ch.get("c", "") for ch in span.get("chars", []))
            print(f"  font={font!r}  size={span.get('size'):.1f}  flags={span.get('flags')}  text={txt!r}")

doc.close()
