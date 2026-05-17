# PDF Recon

## Source files

| File | Pages | Size |
| --- | --- | --- |
| `math_questionbank-export-2026-5-17-1.pdf` (full math) | 1848 | 149 MB |
| `exclude_active_math_questionbank-export-2026-5-17-2.pdf` (math, no active) | 855 | 65 MB |
| `reading_writing_questionbank-export-2026-5-17.pdf` (full R&W) | 1806 | 99 MB |
| `exclude_active_reading_writing_questionbank-export-2026-5-17-2.pdf` (R&W, no active) | 634 | 35 MB |

## Layout — common to all four PDFs

Each "question card" begins with the line `Question ID: <8-hex>` at the top of a page (y ≈ 23 in PDF points). One question may span multiple pages. The next question starts when the next `Question ID:` line appears.

After the ID line, every card has the same anchors in vertical order:

| Anchor (left-aligned, bold) | y on first page |
| --- | --- |
| Table row: SAT / <Test> / <Domain> / <Skill> / <Difficulty> | ~60–115 |
| `Question` header | ~127–148 |
| (optional) `Text 1` / `Text 2` for paired R&W passages | varies |
| stimulus + prompt text | below Question header |
| `Answer` header | ~before choices (MCQ only) |
| `A. ...` `B. ...` `C. ...` `D. ...` choices (MCQ only) | block per choice |
| `Correct Answer: <X>` | the letter (MCQ) or one or more comma-separated answers (SPR) |
| `Rationale` header | start of explanation |
| explanation paragraphs | runs to end of card, may continue on next page |

Pagination: a card whose explanation overflows continues on the next page with no header; the next `Question ID:` line indicates the next card.

Math IDs are 8-hex (e.g. `ac472881`). R&W IDs same shape.

## Counts (raw)

- Math full: 1756 `Question ID:` occurrences across 1848 pages → most cards are 1 page, ~92 span 2 pages.
- Math, ~362 cards are SPR (no A./B./C./D. lines but a `Correct Answer:` with numeric/comma-list value e.g. `403`, `.1764, .1765, 3/17`).
- R&W full: 1688 IDs across 1806 pages.
- R&W: 69 pages contain both `Text 1` and `Text 2` → paired passages.
- R&W has no SPR; the "SPR-looking" pages from initial scan were MCQ where choice D's prefix landed on a wrapped line — fixable by parsing on block boundaries rather than line regex.

## Math rendering — two distinct PDF eras

Two styles of math rendering coexist in the math PDF:

1. **Vector / KaTeX (newer entries, e.g. page 1, 2)**: equations are drawn with Type3 path-based fonts. They are invisible to all text-extraction modes (`get_text("text")`, `dict`, `rawdict`, `xhtml`, `pdfplumber`). They render perfectly to PNG.
2. **MathType bitmap (older entries, e.g. page 7, 14)**: equations are real PNG images embedded in the page. `page.get_images()` returns them with bboxes; `get_text("xhtml")` emits them as `<img src="data:image/png;base64,…">` inline with prose.

In both cases, the plain-text extracted prompt is interrupted by gaps where math used to be. Sample `In the given equation,   and   are constants, and  . If the equation has infinitely many solutions, what is the value of  ?` — the spaces correspond to lost math.

Because math is not recoverable as LaTeX from either renderer (PNGs would need OCR; vector glyphs have no Unicode mapping), the only faithful representation is a rasterized snippet. Per spec ("If images, OCR is unreliable — extract as PNG and treat as a figure"):

- For **every math question** we render the visible region of the card (from just after the metadata table to the end of choices / Correct Answer line) as a single PNG at 150 dpi. This becomes the `figure` for that question. The extracted text in `prompt` / `choices` is still saved as best-effort so it remains searchable, but the figure is the source of visual truth.
- We do NOT try to OCR equations into LaTeX. We do NOT try to extract every inline math glyph separately.
- For **R&W**, no figures are present in the body; `figure` is unset.

## Diagram / chart figures

Geometric and statistical figures (xy-planes, geometry diagrams, scatterplots, tables) in math questions are drawn as vector commands too — they show up in `page.get_drawings()` with hundreds of operations and a large bounding box. They cannot be extracted as an embedded image. Our render-the-card-region approach captures them too.

## isActive

`isActive` is computed by content hash (same `id` field). After extracting both the full and exclude-active PDF for each section, mark a question active iff its id appears in `full` but not in `exclude`.

## Known parsing limitations / failure modes

- **Math LaTeX is not extracted**: equations are images in the figure PNG, not LaTeX in HTML. Acceptable per spec; React app must render figure alongside any text.
- **Inline math gaps**: text fields like `prompt`, `choices`, `explanation` have whitespace gaps where math used to be. Searchable, but not a fluent read for math-heavy items.
- **A few cards have unusual layouts** (e.g. data tables in math). We render their region as figure; text may be sparse.
- **Choice prefix wrap** (rare in R&W; one case observed): when the text of a choice wraps in a way that the `A.`/`B.`/`C.`/`D.` prefix lands on its own line in plain text. We mitigate by parsing on PDF block boundaries (each block carries `y` position), so we associate the unprefixed continuation lines with the preceding choice.

## Approach

1. Walk pages, group blocks into questions by detecting `Question ID:` anchors.
2. Within a question, locate anchor lines: `Question`, `Answer`, `Correct Answer:`, `Rationale` (and `Text 1`/`Text 2` for paired R&W). Extract metadata from the row immediately below the header table.
3. Build the typed Question dict per the schema. For math, also render the card region to `pipeline/out/figures/<id>.png` and set `figure`.
4. Diff full vs exclude_active by `id` to set `isActive`.
5. Emit `pipeline/out/questions.json`.
