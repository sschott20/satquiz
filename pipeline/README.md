# SAT Question Bank Pipeline

One-shot data pipeline that converts the four College Board "educator question bank" PDF exports in `source/` into a single JSON file plus a directory of figure PNGs in `pipeline/out/`.

## Layout

```
source/                                              # input PDFs (not committed)
  math_questionbank-export-2026-5-17-1.pdf
  exclude_active_math_questionbank-export-2026-5-17-2.pdf
  reading_writing_questionbank-export-2026-5-17.pdf
  exclude_active_reading_writing_questionbank-export-2026-5-17-2.pdf
pipeline/
  extract.py                                         # the script
  requirements.txt
  RECON.md                                           # what we learned about the PDFs
  README.md                                          # this file
  out/
    questions.json                                   # bundled question bank
    figures/<id>.png                                 # 1 figure per math question
```

## Setup

```sh
cd /Users/yecl/Documents/satquiz
python3 -m venv pipeline/.venv
pipeline/.venv/bin/pip install -r pipeline/requirements.txt
```

## Run

```sh
pipeline/.venv/bin/python pipeline/extract.py
```

Takes about ~1 minute end-to-end on a Mac (no GPU). Outputs are deterministic — rerunning with the same inputs produces the same JSON.

Useful flags:
- `--no-figures` — skip writing PNG figures (much faster; for development).
- `--smoke` — dump first 5 parsed math questions to stdout as JSON.

## Output shape

`pipeline/out/questions.json` matches the `QuestionBank` type defined in the spec:

```ts
type QuestionBank = {
  version: string;          // "2026-05-17-1"
  generatedAt: string;      // ISO-8601 UTC timestamp
  questions: Question[];    // 3,444 questions
};

type Question = {
  id: string;               // 16-hex SHA1 prefix (see id construction below)
  section: "rw" | "math";
  domain: string;
  skill: string;
  difficulty: "E" | "M" | "H";
  isActive: boolean;
  stimulus?: string;        // HTML (R&W passages; math setups)
  prompt: string;           // HTML
  figure?: string;          // "/figures/<id>.png" — present for every math question
  type: "mcq" | "spr";
  choices?: [string, string, string, string];   // HTML; one entry per A/B/C/D for MCQ
  correctChoice?: "A" | "B" | "C" | "D";        // MCQ
  acceptedAnswers?: string[];                   // SPR
  explanation?: string;     // HTML
};
```

HTML uses only the allowed tag set: `<p>`, `<em>`, `<strong>`, `<u>`, `<br>`, `<span class="math">`. Paired-passage R&W stimuli are encoded as `<p><strong>Text 1</strong></p><p>…</p><p><strong>Text 2</strong></p><p>…</p>` per spec.

## ID construction (deviation from spec, documented)

The spec recipe is `sha1(section + "|" + prompt + "|" + choices_joined)[:16]`. In practice the College Board math PDFs render every equation as either path-based Type3 glyphs (newer items) or as embedded PNGs (older items). Both renderers are invisible to text extraction — pymupdf, pdfplumber, and `get_text("xhtml")` all leave gaps where math was. For math, this means many distinct questions extract to literally identical prompt text (e.g. "If , what is the value of ?"). With the literal recipe, ~300 math questions would hash-collide.

To preserve both stability and uniqueness, we extend the hash input to include the College Board's own per-question identifier (printed on each card as `Question ID: <8-hex>` and identical across the full and exclude-active PDFs for the same question). The actual recipe used is:

```
id = sha1(section + "|" + cb_question_id + "|" + prompt + "|" + choices_joined)[:16]
```

Hashes are still 16 hex chars and deterministic across reruns. `isActive` matching still works because the CB id is the same in both PDFs.

## What you should know about math content

Math equations are NOT recovered as LaTeX. They appear as visual artefacts (vector glyphs or bitmaps) in the PDF and cannot be extracted as text without OCR. The pipeline accepts this and renders the full visible region of each math question (from below the metadata table to the line above "Correct Answer:") as a single PNG at 150 dpi. That image is referenced from `figure`. The text fields (`prompt`, `choices`, `explanation`) still hold the surrounding prose for search/index, but for math-heavy items the prose alone is incomplete — the React app should display the figure alongside any text rendering.

For R&W, no figure is emitted; the text is the source of truth.

## Counts

After running on 2026-05-17 data:

| Metric | Count |
| --- | --- |
| Questions total | 3,444 |
| Math | 1,756 |
| R&W | 1,688 |
| Active | 2,022 |
| Inactive | 1,422 |
| MCQ | 3,011 |
| SPR | 433 |
| With figure | 1,756 (= every math question) |

See `RECON.md` for breakdown by domain and a deeper writeup of PDF structure, parsing decisions, and known failure modes.
