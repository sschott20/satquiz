"""Inspect image sizes per page so we can distinguish figures from inline math glyphs."""
import pymupdf
import pathlib
import json

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
OUT = pathlib.Path("/Users/yecl/Documents/satquiz/pipeline/recon")

doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
sample_pages = [0, 1, 6, 7, 13, 17, 18, 19, 50, 100, 200, 300]

stats = []
for pno in sample_pages:
    if pno >= len(doc):
        continue
    page = doc[pno]
    text = page.get_text()
    qid_line = next((l for l in text.splitlines() if "Question ID" in l), "")
    imgs = page.get_images(full=True)
    img_specs = []
    for img in imgs:
        xref = img[0]
        # width, height in the image dict are pixel dims of the image
        w_px, h_px = img[2], img[3]
        try:
            rects = page.get_image_rects(xref)
            for r in rects:
                img_specs.append({
                    "xref": xref,
                    "px_w": w_px,
                    "px_h": h_px,
                    "pt_w": round(r.width, 1),
                    "pt_h": round(r.height, 1),
                    "x0": round(r.x0, 1),
                    "y0": round(r.y0, 1),
                })
        except Exception as e:
            img_specs.append({"xref": xref, "err": str(e)})
    stats.append({
        "page": pno+1,
        "qid": qid_line,
        "n_images": len(imgs),
        "images": img_specs,
    })

print(json.dumps(stats, indent=2))
doc.close()
