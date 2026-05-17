"""Inspect block structure with positions, and render a few pages to PNG."""
import pymupdf
import pathlib
import json

SRC = pathlib.Path("/Users/yecl/Documents/satquiz/source")
OUT = pathlib.Path("/Users/yecl/Documents/satquiz/pipeline/recon")

# Render page 1 of math_full as PNG so we can see what an image-heavy page looks like.
doc = pymupdf.open(SRC / "math_questionbank-export-2026-5-17-1.pdf")
for pno in [0, 1, 6, 13]:
    pix = doc[pno].get_pixmap(dpi=120)
    pix.save(str(OUT / f"math_full_p{pno+1}.png"))
print("Rendered math pages.")

# Dump page 0 text dict (blocks)
for pno in [0, 6, 13]:
    page = doc[pno]
    d = page.get_text("dict")
    blocks = d["blocks"]
    summary = []
    for b in blocks:
        info = {"type": b["type"], "bbox": [round(x,1) for x in b["bbox"]]}
        if b["type"] == 0:  # text
            # join all lines text
            text_parts = []
            for line in b["lines"]:
                for span in line["spans"]:
                    text_parts.append(span["text"])
            info["text"] = " ".join(text_parts)[:200]
        else:  # image
            info["width"] = b.get("width")
            info["height"] = b.get("height")
        summary.append(info)
    (OUT / f"math_full_p{pno+1}_blocks.json").write_text(json.dumps(summary, indent=2))
    # Also list images on page
    imgs = page.get_images(full=True)
    img_info = []
    for img in imgs:
        xref = img[0]
        try:
            bbox_list = page.get_image_bbox(img)
            img_info.append({"xref": xref, "bbox": [round(x,1) for x in bbox_list] if bbox_list else None})
        except Exception as e:
            img_info.append({"xref": xref, "error": str(e)})
    (OUT / f"math_full_p{pno+1}_images.json").write_text(json.dumps(img_info, indent=2))
doc.close()
print("Done.")
