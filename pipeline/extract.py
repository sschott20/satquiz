"""
Extract SAT educator question bank PDFs into a single questions.json + figure PNGs.

Outputs:
  pipeline/out/questions.json
  pipeline/out/figures/<id>.png  (math questions only)

Run:
  pipeline/.venv/bin/python pipeline/extract.py
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import pathlib
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional

import pymupdf  # PyMuPDF (fitz)

SRC_DIR = pathlib.Path("/Users/yecl/Documents/satquiz/source")
OUT_DIR = pathlib.Path("/Users/yecl/Documents/satquiz/pipeline/out")
FIG_DIR = OUT_DIR / "figures"

PDFS = {
    "math": {
        "full": SRC_DIR / "math_questionbank-export-2026-5-17-1.pdf",
        "excl": SRC_DIR / "exclude_active_math_questionbank-export-2026-5-17-2.pdf",
    },
    "rw": {
        "full": SRC_DIR / "reading_writing_questionbank-export-2026-5-17.pdf",
        "excl": SRC_DIR / "exclude_active_reading_writing_questionbank-export-2026-5-17-2.pdf",
    },
}

VERSION = "2026-05-17-1"
FIG_DPI = 150

ALLOWED_HTML_TAGS = {"p", "em", "strong", "u", "br", "span"}
DIFFICULTY_MAP = {"Easy": "E", "Medium": "M", "Hard": "H"}


# ----------------- helpers -----------------

QID_RE = re.compile(r"^Question ID:\s*([0-9a-f]+)\s*$")


def html_escape(s: str) -> str:
    return html.escape(s, quote=False)


def normalize_text(s: str) -> str:
    """Normalize whitespace inside a single text fragment.
    Replace nbsp, collapse runs of whitespace to single space, strip ends."""
    s = s.replace("\xa0", " ")
    # Drop carriage returns
    s = s.replace("\r", "")
    # Collapse internal whitespace runs to a single space, but preserve newlines as paragraph breaks
    # First strip per-line, then rejoin
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in s.split("\n")]
    return "\n".join(lines).strip()


def join_lines_as_para(lines: Iterable[str]) -> str:
    """Join an iterable of physical PDF lines into prose paragraphs.

    Heuristic: consecutive non-empty lines flow as a single paragraph unless one ends
    in a sentence-final punct followed by a blank line. We treat lines that end with a
    quote-aware sentence terminator as paragraph boundaries only if followed by capital.
    Simpler: just space-join all non-empty lines; later code can split paragraphs on
    actual blank-line gaps from PDF block structure.
    """
    parts = [normalize_text(l) for l in lines if l and not l.isspace()]
    return " ".join(p for p in parts if p)


def text_to_html(text: str) -> str:
    """Convert a plain-text paragraph(s) string into safe HTML using the allowed tag set.

    - Splits on double-newlines into <p>...</p> blocks.
    - HTML-escapes special chars.
    - Drops leftover sequences of multiple spaces (artifact of removed math glyphs).
    """
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = text.replace("\r", "")
    # Collapse 3+ blank lines down to 2 to make a real paragraph break
    text = re.sub(r"\n{2,}", "\n\n", text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for p in paragraphs:
        # Within paragraph, replace internal newlines with a space
        p = re.sub(r"\s*\n\s*", " ", p)
        # Replace 2+ spaces (math-glyph gaps) with a single " · " marker so users see something
        # was elided. We use a thin gap marker.
        p = re.sub(r" {2,}", "   ", p)
        out.append(f"<p>{html_escape(p)}</p>")
    return "".join(out)


# ----------------- per-question structure -----------------

@dataclass
class Block:
    """A single text block on a page with bbox + plain text."""
    page_idx: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    def __repr__(self) -> str:
        return f"Block(p{self.page_idx} y={self.y0:.0f}-{self.y1:.0f} {self.text!r:.60})"


@dataclass
class RawQuestion:
    """All blocks belonging to one question, in document order."""
    qid: str
    section: str  # "math" or "rw"
    start_page: int
    end_page: int  # inclusive
    blocks: list[Block] = field(default_factory=list)


def collect_blocks(doc: pymupdf.Document, section: str) -> list[RawQuestion]:
    """Walk the PDF and group blocks into RawQuestion objects."""
    questions: list[RawQuestion] = []
    current: Optional[RawQuestion] = None

    for pno in range(len(doc)):
        page = doc[pno]
        # blocks: list of tuples (x0, y0, x1, y1, text, block_no, block_type)
        raw_blocks = page.get_text("blocks")
        # Sort by reading order: top-to-bottom, then left-to-right
        raw_blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))
        for b in raw_blocks:
            x0, y0, x1, y1, btext, bno, btype = b
            if btype != 0:  # 1 == image block. Skip.
                continue
            btext = btext.replace("\xa0", " ")
            # Detect Question ID line — it can appear inside a block alongside other things,
            # but in practice it's its own block at the top. Match any line within the block.
            m_lines = [QID_RE.match(line.strip()) for line in btext.splitlines()]
            qid_match = next((m for m in m_lines if m), None)
            if qid_match:
                # Close prior
                if current is not None:
                    current.end_page = pno  # may be refined below; we set end at last block
                    questions.append(current)
                current = RawQuestion(
                    qid=qid_match.group(1),
                    section=section,
                    start_page=pno,
                    end_page=pno,
                )
                # Do not include the QID block in question content
                continue
            if current is None:
                # Skip pages before any question (shouldn't happen, but be safe)
                continue
            current.blocks.append(Block(page_idx=pno, x0=x0, y0=y0, x1=x1, y1=y1, text=btext))
            current.end_page = pno

    if current is not None:
        questions.append(current)
    return questions


# ----------------- metadata-row parsing -----------------

METADATA_HEADER_TEXT = "Assessment\nTest\nDomain\nSkill\nDifficulty\n"


def parse_metadata(q: RawQuestion) -> tuple[str, str, str]:
    """Return (domain, skill, difficulty_letter)."""
    # The metadata is in two blocks at the top of the question:
    #   block 1: "Assessment\nTest\nDomain\nSkill\nDifficulty\n"
    #   block 2: "SAT\n<Test>\n<Domain>\n<Skill>\n" plus possibly continuation blocks
    #   block 3+: optional continuations for long Skill names (e.g. "equations in two\nvariables\n")
    #   followed by a separate block at the same y for "Difficulty" word.
    # Strategy: find the "Assessment\nTest\n..." block, then take the NEXT block (data row),
    # which contains 4 values separated by newlines (SAT, Test, Domain, Skill).
    # Difficulty is the rightmost block at the same y. Long Skill names continue on lower y.

    header_idx = None
    for i, b in enumerate(q.blocks):
        if "Assessment" in b.text and "Test" in b.text and "Domain" in b.text and "Difficulty" in b.text:
            header_idx = i
            break
    if header_idx is None:
        return ("", "", "")

    header_block = q.blocks[header_idx]
    header_y = header_block.y0

    # Collect blocks within ~50pt vertically below the header that are part of the metadata row
    # Stop when we hit the "Question" header (which is also a small block at far-left).
    # The metadata table has 5 columns whose x ranges are roughly:
    #   col1 Assessment: x0 ~ 24
    #   col2 Test:       x0 ~ 130
    #   col3 Domain:     x0 ~ 250
    #   col4 Skill:      x0 ~ 369
    #   col5 Difficulty: x0 ~ 484
    domain_parts: list[str] = []
    skill_parts: list[str] = []
    test_value = ""
    difficulty = ""

    DOMAIN_X_LO, DOMAIN_X_HI = 245, 355
    SKILL_X_LO, SKILL_X_HI = 360, 470
    DIFF_X_LO = 460

    for b in q.blocks[header_idx + 1:]:
        if b.page_idx != header_block.page_idx:
            break
        if b.y0 > header_y + 80:
            break  # past the metadata table area
        if b.text.strip() == "Question":
            break
        if b.text.strip() == "":
            continue
        # Split block text by newlines
        lines = [l.strip() for l in b.text.split("\n") if l.strip()]
        # Difficulty block: x0 > 460 AND single line.
        if b.x0 > DIFF_X_LO and len(lines) == 1:
            difficulty = lines[0]
            continue
        # Block that starts the data row — begins with "SAT" at x0 ~ 24.
        if test_value == "" and lines and lines[0] == "SAT":
            # lines[0]="SAT", lines[1]=Test, lines[2]=Domain, lines[3..]=Skill (+ optional Difficulty)
            test_value = lines[1] if len(lines) > 1 else ""
            if len(lines) > 2:
                domain_parts.append(lines[2])
            # When all 5 columns fit on one row: lines = [SAT, Test, Domain, Skill, Difficulty]
            if len(lines) == 5 and not difficulty:
                difficulty = lines[4]
                skill_parts.append(lines[3])
            elif len(lines) >= 4:
                skill_parts.append(lines[3])
            continue
        # Continuation block — discriminate by x position.
        if DOMAIN_X_LO <= b.x0 < DOMAIN_X_HI:
            # Domain continuation; if last line is a difficulty word, split it out.
            if not difficulty and lines and lines[-1] in DIFFICULTY_MAP:
                difficulty = lines[-1]
                lines = lines[:-1]
            domain_parts.append(" ".join(lines))
            continue
        if SKILL_X_LO <= b.x0 < SKILL_X_HI:
            # Skill continuation; if last line is a difficulty word, split it out.
            if not difficulty and lines and lines[-1] in DIFFICULTY_MAP:
                difficulty = lines[-1]
                lines = lines[:-1]
            skill_parts.append(" ".join(lines))
            continue
        # Anything else: ignore (e.g. domain continuation)

    skill = " ".join(skill_parts).strip()
    domain = " ".join(domain_parts).strip()
    diff_letter = DIFFICULTY_MAP.get(difficulty, difficulty[:1].upper() if difficulty else "")
    return (domain, skill, diff_letter)


# ----------------- body-region extraction -----------------

ANCHOR_PATTERNS = {
    "question": re.compile(r"^Question\s*$"),
    "answer": re.compile(r"^Answer\s*$"),
    "correct_answer": re.compile(r"^Correct Answer:\s*(.+?)\s*$"),
    "rationale": re.compile(r"^Rationale\s*$"),
    "text1": re.compile(r"^Text\s*1\s*$"),
    "text2": re.compile(r"^Text\s*2\s*$"),
}


@dataclass
class Anchor:
    name: str
    block_idx: int  # index into q.blocks
    page_idx: int
    y: float
    match_obj: Optional[re.Match]


def find_anchors(q: RawQuestion) -> dict[str, Anchor]:
    """Find the body anchors. Returns the FIRST occurrence of each."""
    out: dict[str, Anchor] = {}
    for i, b in enumerate(q.blocks):
        for line in b.text.splitlines():
            line = line.strip()
            for name, pat in ANCHOR_PATTERNS.items():
                if name in out and name not in ("text1", "text2"):
                    continue
                m = pat.match(line)
                if m:
                    out.setdefault(name, Anchor(name=name, block_idx=i, page_idx=b.page_idx, y=b.y0, match_obj=m))
    return out


CHOICE_RE = re.compile(r"^([A-D])\.\s*(.*)$", re.DOTALL)


def extract_choices(q: RawQuestion, ans_anchor: Anchor, ca_anchor: Anchor) -> tuple[list[str], list[Block]]:
    """Pull the four choice texts (or empty list if SPR).

    ans_anchor and ca_anchor delimit the region containing A./B./C./D.
    """
    choice_blocks: dict[str, list[Block]] = {"A": [], "B": [], "C": [], "D": []}
    # Walk blocks in (page, y) order between the two anchors.
    current_letter: Optional[str] = None
    for b in q.blocks:
        if (b.page_idx, b.y0) <= (ans_anchor.page_idx, ans_anchor.y):
            continue
        if (b.page_idx, b.y0) >= (ca_anchor.page_idx, ca_anchor.y):
            break
        first_line = b.text.lstrip().split("\n", 1)[0].rstrip()
        m = CHOICE_RE.match(first_line)
        if m:
            current_letter = m.group(1)
            # Rewrite block.text to drop the "X. " prefix
            stripped_text = b.text.split(".", 1)[1].lstrip() if "." in b.text else ""
            # Keep all of block (because subsequent lines belong to the same choice)
            new_block = Block(b.page_idx, b.x0, b.y0, b.x1, b.y1, stripped_text)
            choice_blocks[current_letter].append(new_block)
        else:
            if current_letter is not None:
                choice_blocks[current_letter].append(b)
            # Else: stray block before any choice; ignore
    choices: list[str] = []
    for letter in "ABCD":
        if not choice_blocks[letter]:
            return ([], [])  # not all four found → SPR
        text = join_lines_as_para(blk.text for blk in choice_blocks[letter])
        choices.append(text)
    return (choices, [])


def slice_blocks(q: RawQuestion, start: Optional[Anchor], end: Optional[Anchor]) -> list[Block]:
    """Return blocks strictly between two anchors (exclusive on both)."""
    out = []
    for b in q.blocks:
        if start is not None and (b.page_idx, b.y0) <= (start.page_idx, start.y):
            continue
        if end is not None and (b.page_idx, b.y0) >= (end.page_idx, end.y):
            break
        out.append(b)
    return out


# ----------------- main per-question parser -----------------

# Match a generic "Which X..." or "Based on..." or similar interrogative line that splits
# the R&W stimulus from the prompt. The list is empirical; we add more as we find cases.
PROMPT_LEAD_RE = re.compile(
    r"^(Which choice\b|Based on (?:the text|the texts|the passage|the (?:table|graph|figure|data))\b|"
    r"As used in the text\b|According to (?:the text|the table|the graph|the figure|the passage|the data)\b|"
    r"What\b|What does\b|Which\b|"
    r"It can (?:most reasonably )?be inferred\b|"
    r"In the text\b|The text\b|The author\b|The (?:main|primary|first|second) (?:purpose|function|idea|claim|argument|reason)\b)",
    re.IGNORECASE,
)


# Interrogative prefixes that may appear MID-PARAGRAPH (when stimulus and prompt were
# extracted as a single PDF paragraph). Used to split a paragraph on these phrases.
INTRA_PARA_PROMPT_RE = re.compile(
    r"(?:^|\s)((?:Which (?:choice|of the following|finding|quotation|statement|sentence|"
    r"two sentences))\b[^?]*\?|"
    r"Based on the texts?,?\s+[^?]*\?|"
    r"Based on the (?:table|graph|figure|data),?\s+[^?]*\?|"
    r"Based on (?:the )?information (?:in the (?:table|graph|figure|passage|text|data))?,?\s+[^?]*\?|"
    r"According to the (?:text|table|graph|figure|passage|data),?\s+[^?]*\?|"
    r"As used in the text,?\s+[^?]*\?|"
    r"It can (?:most reasonably )?be inferred[^?]*\?|"
    r"What (?:does|is the main|is the (?:primary|central))[^?]*\?)"
)


def split_stimulus_prompt(body_text: str) -> tuple[str, str]:
    """Heuristic: the LAST paragraph that starts with a known interrogative prefix is the prompt.
    Everything before it is the stimulus. Also handles the case where the stimulus and prompt
    landed in the SAME PDF paragraph (one block, no blank-line separation): split on a
    "Which choice..." / "Based on the text..." substring."""
    if not body_text:
        return ("", "")
    # Split on double newlines (paragraph boundaries). Single-newline within a paragraph is OK.
    paras = [p.strip() for p in re.split(r"\n{2,}", body_text) if p.strip()]
    if not paras:
        return ("", "")
    # Search from end for an interrogative-prefixed paragraph
    prompt_idx = None
    for i in range(len(paras) - 1, -1, -1):
        if PROMPT_LEAD_RE.match(paras[i]):
            prompt_idx = i
            break
    if prompt_idx is not None:
        stimulus = "\n\n".join(paras[:prompt_idx])
        prompt = paras[prompt_idx]
        return (stimulus, prompt)
    # No paragraph-prefix match — try splitting the last paragraph on a known mid-para phrase.
    last = paras[-1]
    matches = list(INTRA_PARA_PROMPT_RE.finditer(last))
    if matches:
        m = matches[-1]
        prompt = m.group(1).strip()
        stim_tail = last[: m.start()].rstrip()
        if stim_tail:
            stim_paras = paras[:-1] + [stim_tail]
        else:
            stim_paras = paras[:-1]
        return ("\n\n".join(stim_paras), prompt)
    # Fall back to: prompt = last paragraph, no stimulus
    return ("", paras[-1])


def body_text_from_blocks(blocks: list[Block]) -> str:
    """Render a list of Block objects to a single text string.

    Consecutive blocks on the same page that are vertically adjacent (small y gap) are
    treated as continuation lines of the same paragraph and joined with a single space.
    A larger y gap (≥ ~14pt, roughly 1+ blank line) starts a new paragraph. A page break
    also starts a new paragraph unless the new block is at top of page and shares text.

    Returns text with paragraphs separated by \n\n.
    """
    if not blocks:
        return ""
    paragraphs: list[list[str]] = []
    current_para: list[str] = []
    prev: Optional[Block] = None
    PARA_GAP_PT = 14.0  # threshold for paragraph break

    def normalize(t: str) -> str:
        t = t.replace("\xa0", " ").replace("\r", "")
        t = "\n".join(line.strip() for line in t.split("\n") if line.strip())
        t = re.sub(r"\s*\n\s*", " ", t)
        t = re.sub(r" {2,}", "  ", t)  # math gaps -> double space (preserved for split)
        return t.strip()

    for b in blocks:
        text = normalize(b.text)
        if not text:
            prev = b
            continue
        if prev is None:
            current_para.append(text)
        else:
            same_page = (b.page_idx == prev.page_idx)
            y_gap = b.y0 - prev.y1
            is_continuation = False
            if same_page:
                if y_gap < PARA_GAP_PT:
                    is_continuation = True
            else:
                # Cross page break — treat as continuation if prev ended near page bottom
                # AND new block starts near page top.
                if prev.y1 > 700 and b.y0 < 80:
                    is_continuation = True
            if is_continuation:
                current_para.append(text)
            else:
                if current_para:
                    paragraphs.append(current_para)
                current_para = [text]
        prev = b
    if current_para:
        paragraphs.append(current_para)
    return "\n\n".join(" ".join(p) for p in paragraphs)


def build_paired_stimulus_html(blocks: list[Block]) -> tuple[str, str]:
    """Detect Text 1 / Text 2 paired-passage structure within stimulus blocks.

    Returns (stimulus_html, prompt_text). If no Text 1/Text 2 anchors found,
    returns ("", "")."""
    t1_idx = t2_idx = None
    for i, b in enumerate(blocks):
        s = b.text.strip()
        if s == "Text 1" and t1_idx is None:
            t1_idx = i
        elif s == "Text 2" and t2_idx is None:
            t2_idx = i
    if t1_idx is None or t2_idx is None:
        return ("", "")

    text1_blocks = blocks[t1_idx + 1 : t2_idx]
    text2_after = blocks[t2_idx + 1 :]

    # Within text2_after, separate the passage from the trailing prompt. The prompt is the
    # last paragraph (in body-text terms) that starts with a known interrogative prefix.
    t2_body_text = body_text_from_blocks(text2_after)
    t2_paras = [p.strip() for p in re.split(r"\n{2,}", t2_body_text) if p.strip()]
    prompt_idx = None
    for i in range(len(t2_paras) - 1, -1, -1):
        if PROMPT_LEAD_RE.match(t2_paras[i]):
            prompt_idx = i
            break
    if prompt_idx is None:
        # Default: assume the last paragraph is the prompt
        prompt_idx = len(t2_paras) - 1 if t2_paras else -1
    text2_paras = t2_paras[:prompt_idx] if prompt_idx >= 0 else t2_paras
    prompt_text = t2_paras[prompt_idx] if prompt_idx >= 0 and prompt_idx < len(t2_paras) else ""

    t1_text = body_text_from_blocks(text1_blocks)
    t2_text_clean = "\n\n".join(text2_paras)

    parts = [
        "<p><strong>Text 1</strong></p>",
        text_to_html(t1_text),
        "<p><strong>Text 2</strong></p>",
        text_to_html(t2_text_clean),
    ]
    return ("".join(parts), prompt_text)


def render_figure(doc: pymupdf.Document, q: RawQuestion, anchors: dict[str, Anchor], out_path: pathlib.Path):
    """Render the visible region of the question card from just below the metadata row to
    the line above "Correct Answer:". Saves a PNG to out_path."""
    # Determine y range on first page:
    # top = y of "Question" header (anchor.y) - 4
    # bottom on the same/last page = y of "Correct Answer:" anchor - 4
    q_anchor = anchors.get("question")
    ca_anchor = anchors.get("correct_answer")
    if q_anchor is None:
        # Cannot render
        return False
    top_page = q_anchor.page_idx
    top_y = max(0, q_anchor.y - 4)
    if ca_anchor is None:
        bottom_page = q.end_page
        bottom_y = doc[bottom_page].rect.height
    else:
        bottom_page = ca_anchor.page_idx
        bottom_y = ca_anchor.y - 4

    # Render each page in range, cropping to the region
    page_pixmaps = []
    for pno in range(top_page, bottom_page + 1):
        page = doc[pno]
        page_h = page.rect.height
        page_w = page.rect.width
        y_lo = top_y if pno == top_page else 0
        y_hi = bottom_y if pno == bottom_page else page_h
        if y_hi <= y_lo:
            continue
        clip = pymupdf.Rect(0, y_lo, page_w, y_hi)
        pix = page.get_pixmap(dpi=FIG_DPI, clip=clip)
        page_pixmaps.append(pix)

    if not page_pixmaps:
        return False

    # If single page, save directly. Else, stack vertically.
    if len(page_pixmaps) == 1:
        page_pixmaps[0].save(str(out_path))
        return True

    # Stack: produce a new pixmap of summed height
    total_h = sum(p.height for p in page_pixmaps)
    width = max(p.width for p in page_pixmaps)
    stacked = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, width, total_h), False)
    stacked.clear_with(255)
    y_cursor = 0
    for p in page_pixmaps:
        # Place pixmap p at (0, y_cursor)
        p.set_origin(0, y_cursor)
        stacked.copy(p, p.irect)
        y_cursor += p.height
    stacked.save(str(out_path))
    return True


# ----------------- top-level parser -----------------

@dataclass
class Question:
    id: str
    section: str
    domain: str
    skill: str
    difficulty: str
    isActive: bool
    stimulus: Optional[str]
    prompt: str
    figure: Optional[str]
    type: str  # "mcq" or "spr"
    choices: Optional[list[str]]
    correctChoice: Optional[str]
    acceptedAnswers: Optional[list[str]]
    explanation: Optional[str]
    # Pre-hash fields used for id generation
    _prompt_text: str = ""
    _choices_text: str = ""

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "section": self.section,
            "domain": self.domain,
            "skill": self.skill,
            "difficulty": self.difficulty,
            "isActive": self.isActive,
            "prompt": self.prompt,
            "type": self.type,
        }
        if self.stimulus:
            d["stimulus"] = self.stimulus
        if self.figure:
            d["figure"] = self.figure
        if self.choices is not None:
            d["choices"] = self.choices
        if self.correctChoice is not None:
            d["correctChoice"] = self.correctChoice
        if self.acceptedAnswers is not None:
            d["acceptedAnswers"] = self.acceptedAnswers
        if self.explanation:
            d["explanation"] = self.explanation
        # Order per schema:
        order = ["id", "section", "domain", "skill", "difficulty", "isActive",
                 "stimulus", "prompt", "figure", "type", "choices", "correctChoice",
                 "acceptedAnswers", "explanation"]
        return {k: d[k] for k in order if k in d}


def parse_question(doc: pymupdf.Document, q: RawQuestion, render_figures: bool) -> Optional[Question]:
    domain, skill, diff = parse_metadata(q)
    anchors = find_anchors(q)
    q_anchor = anchors.get("question")
    if q_anchor is None:
        return None  # malformed

    ans_anchor = anchors.get("answer")
    ca_anchor = anchors.get("correct_answer")
    rat_anchor = anchors.get("rationale")

    # ---- body: between "Question" and ("Answer" if MCQ else "Correct Answer:")
    body_end_anchor = ans_anchor or ca_anchor
    body_blocks = slice_blocks(q, q_anchor, body_end_anchor)

    # Drop any blocks that ARE the Text 1 / Text 2 lone-anchor markers? We'll handle paired below.
    paired_html, paired_prompt = build_paired_stimulus_html(body_blocks)

    if paired_html:
        prompt_text = paired_prompt
        stimulus_html = paired_html
        stimulus_text = ""  # not used in the paired branch
    else:
        body_text = body_text_from_blocks(body_blocks)
        stimulus_text, prompt_text = split_stimulus_prompt(body_text)
        stimulus_html = text_to_html(stimulus_text) if stimulus_text else ""

    prompt_html = text_to_html(prompt_text)

    # ---- choices / correctChoice / acceptedAnswers
    is_mcq = ans_anchor is not None
    choices_text: list[str] = []
    correct_choice: Optional[str] = None
    accepted_answers: Optional[list[str]] = None

    if ca_anchor is not None:
        ca_text = ca_anchor.match_obj.group(1).strip()
    else:
        ca_text = ""

    if is_mcq and ca_anchor is not None:
        choices_text, _ = extract_choices(q, ans_anchor, ca_anchor)
        if choices_text and ca_text in {"A", "B", "C", "D"}:
            correct_choice = ca_text

    if not is_mcq or not choices_text:
        # SPR: parse comma-separated accepted answers
        if ca_text:
            accepted_answers = [s.strip() for s in re.split(r"[,;]", ca_text) if s.strip()]
        is_mcq = False
        choices_text = []

    # ---- explanation
    explanation_html = ""
    if rat_anchor is not None:
        rat_blocks = slice_blocks(q, rat_anchor, None)
        explanation_text = body_text_from_blocks(rat_blocks)
        explanation_html = text_to_html(explanation_text)

    # ---- id (content hash) — must be stable across reruns and across the two PDFs (full
    # vs exclude_active) for the same question. The spec recipe is sha1(section + prompt +
    # choices_joined). For math questions, equations are rendered as vector glyphs / images
    # and lost from text extraction, so extracted prompts collide across many distinct
    # questions (e.g. "If , what is the value of ?" shared by 9 different math items).
    # To preserve stability AND uniqueness, we include the College Board internal question
    # ID (printed on each card as "Question ID: <hex>") in the hash input. That ID is
    # identical in both the full PDF and the exclude-active PDF for the same question, so
    # `isActive` matching still works by content hash.
    section_label = "math" if q.section == "math" else "rw"
    choices_joined = "|".join(choices_text)
    hash_input = f"{section_label}|{q.qid}|{prompt_text.strip()}|{choices_joined}"
    qid = hashlib.sha1(hash_input.encode("utf-8")).hexdigest()[:16]

    # ---- figure (math only). Render the question region as PNG, named by our hash id.
    figure_url: Optional[str] = None
    if render_figures and q.section == "math":
        fig_path = FIG_DIR / f"{qid}.png"
        ok = render_figure(doc, q, anchors, fig_path)
        if ok:
            figure_url = f"/figures/{qid}.png"

    qobj = Question(
        id=qid,
        section=section_label,
        domain=domain,
        skill=skill,
        difficulty=diff if diff in ("E", "M", "H") else "",
        isActive=True,  # caller will recompute
        stimulus=stimulus_html or None,
        prompt=prompt_html,
        figure=figure_url,
        type="mcq" if is_mcq else "spr",
        choices=[text_to_html(c) for c in choices_text] if choices_text else None,
        correctChoice=correct_choice,
        acceptedAnswers=accepted_answers,
        explanation=explanation_html or None,
        _prompt_text=prompt_text.strip(),
        _choices_text=choices_joined,
    )
    return qobj


def process_pdf(path: pathlib.Path, section: str, render_figures: bool) -> list[Question]:
    print(f"[{section}] opening {path.name} …", flush=True)
    doc = pymupdf.open(path)
    t0 = time.time()
    raw_questions = collect_blocks(doc, section)
    print(f"[{section}]   grouped {len(raw_questions)} questions in {time.time()-t0:.1f}s", flush=True)

    questions: list[Question] = []
    t1 = time.time()
    for i, rq in enumerate(raw_questions):
        try:
            q = parse_question(doc, rq, render_figures=render_figures)
        except Exception as e:
            print(f"[{section}] FAILED qid={rq.qid} pages={rq.start_page+1}-{rq.end_page+1}: {e}",
                  file=sys.stderr)
            continue
        if q is None:
            continue
        questions.append(q)
        if (i + 1) % 200 == 0:
            print(f"[{section}]   parsed {i+1}/{len(raw_questions)} ({time.time()-t1:.1f}s)", flush=True)
    print(f"[{section}]   parsed {len(questions)} total in {time.time()-t1:.1f}s", flush=True)
    doc.close()
    return questions


# ----------------- main -----------------

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figures", action="store_true", help="Skip rendering math figures (faster, for dev)")
    ap.add_argument("--limit", type=int, default=None, help="Only process this many pages per PDF (dev mode)")
    ap.add_argument("--smoke", action="store_true", help="Stop after a couple sample questions")
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        # Just parse first 20 pages of math_full and dump
        path = PDFS["math"]["full"]
        doc = pymupdf.open(path)
        for pno in range(min(20, len(doc))):
            pass
        rqs = collect_blocks(doc, "math")[:5]
        for rq in rqs:
            q = parse_question(doc, rq, render_figures=False)
            if q:
                print(json.dumps(q.to_dict(), indent=2, ensure_ascii=False))
        doc.close()
        return 0

    all_questions: list[Question] = []
    full_ids: dict[str, set[str]] = {"math": set(), "rw": set()}
    excl_ids: dict[str, set[str]] = {"math": set(), "rw": set()}

    # Process FULL PDFs (these contribute the question records and figures)
    for section in ("math", "rw"):
        qs = process_pdf(PDFS[section]["full"], section, render_figures=not args.no_figures)
        for q in qs:
            full_ids[section].add(q.id)
        all_questions.extend(qs)

    # Process EXCLUDE-ACTIVE PDFs (only to get ID sets; no figures, no record output)
    for section in ("math", "rw"):
        qs = process_pdf(PDFS[section]["excl"], section, render_figures=False)
        for q in qs:
            excl_ids[section].add(q.id)

    # Apply isActive: true if in full but NOT in excl
    for q in all_questions:
        section = q.section
        q.isActive = q.id not in excl_ids[section]

    # Dedupe by id (keep first), within a section
    seen: set[str] = set()
    unique: list[Question] = []
    for q in all_questions:
        if q.id in seen:
            continue
        seen.add(q.id)
        unique.append(q)

    # Sort: section then domain then skill
    unique.sort(key=lambda q: (q.section, q.domain, q.skill, q.id))

    bundle = {
        "version": VERSION,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "questions": [q.to_dict() for q in unique],
    }

    out_path = OUT_DIR / "questions.json"
    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
    print(f"\nWrote {out_path} ({out_path.stat().st_size/1e6:.1f} MB) with {len(unique)} questions.")

    # Summary
    by_section: dict[str, int] = {"math": 0, "rw": 0}
    by_active: dict[bool, int] = {True: 0, False: 0}
    by_diff: dict[str, int] = {}
    with_figure = 0
    by_type: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    for q in unique:
        by_section[q.section] += 1
        by_active[q.isActive] += 1
        by_diff[q.difficulty] = by_diff.get(q.difficulty, 0) + 1
        if q.figure:
            with_figure += 1
        by_type[q.type] = by_type.get(q.type, 0) + 1
        by_domain[f"{q.section}/{q.domain}"] = by_domain.get(f"{q.section}/{q.domain}", 0) + 1
    print("\n=== SUMMARY ===")
    print("by section:", by_section)
    print("by active:", by_active)
    print("by difficulty:", by_diff)
    print("by type:", by_type)
    print("with figure:", with_figure)
    print("by domain:")
    for k in sorted(by_domain):
        print(f"  {k:60s}  {by_domain[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
