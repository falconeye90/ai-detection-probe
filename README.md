# ai-detection-probe

**A bilingual (Arabic 🇸🇦 / English 🇬🇧) AI-likeness probe** that estimates how
AI-flavoured a text reads, from cheap, explainable signals — reported line by
line so you can see *why* a draft scored the way it did.

For self-review, revision, and transparency about human tone — **not** a
substitute for your institution's official integrity check, and **not** a
reimplementation of one. Turnitin's own documentation describes its detector as
"many learned patterns working together rather than by a small set of
transparent, human-readable rules", so no local script can reproduce its verdict:

> ⚠️ This tool runs entirely on your machine. It uploads nothing, needs no
> account, and never stands in for the official Turnitin/institutional report.
> Use it to improve and stay transparent — not to circumvent academic integrity.

---

## Features

- 🇸🇦🇬🇧 Arabic (fusha) and English prose — **language auto-detected**
- 📊 Quantitative report; every signal and its weight is printed
- 🔒 100% local — no uploads, no account, no fees
- 📄 Reads `.txt`, `.md`, `.docx`, and `.pdf` (PDF/DOCX need one optional dep each)
- 🤖 `--json` for machine-readable output and pipelines

## Install

```bash
pip install python-docx      # only if you feed it .docx
pip install pypdf            # only if you feed it .pdf
```

## Usage

```bash
python3 scripts/turnitin_sim.py document.docx      # Arabic or English, auto-detected
python3 scripts/turnitin_sim.py notes.txt --json   # machine-readable
python3 scripts/turnitin_sim.py                    # embedded demo
```

## Reading the output

Three signals are scored, each mapped to an AI-likeness contribution in `[0, 1]`
and combined with explicit weights:

| Signal | Weight | Human-leaning | AI-leaning |
|--------|:------:|---------------|------------|
| **AI patterns** — severity-weighted markers (87 patterns in 7 categories, `scripts/ai_patterns.py`) | 0.55 | none found | saturates at 3 blockers |
| **Burstiness** — sentence-length variance (`CV`), needs ≥ 6 sentences | 0.30 | CV ≥ 0.45 | CV < 0.30 |
| **Human markers** — very short sentences, digits/units, first-person field verbs, sentence-opener variety | 0.15 | 3/3 markers | 0/3 markers |
| **Lexical TTR** — vocabulary richness (+ root-TTR/Guiraud for short texts) | *reported only* | — | — |

The final line is an **AI-likeness estimate** with a verdict band:

- `≥ 60%` → **AI-leaning**
- `40–60%` → **inconclusive — mixed signals**
- `≤ 40%` → **human-leaning**

**TTR is deliberately not scored.** On texts under ~300 words the type/token
ratio sits near 1.0 for human and AI writing alike, so it cannot discriminate —
in v1 an equally-weighted TTR point cancelled out the markers that *were*
discriminating, and a draft with seven strong AI markers tied with a human
field-notes draft (2.0/4 each).

A signal that cannot be computed honestly for the input (fewer than 6 sentences,
empty content) is **dropped and its weight redistributed** — never scored as
zero. Inputs under 200 words raise an explicit warning: the estimate is a hint,
not a result.

## Example

```
AI-likeness estimate: 95%  ->  AI-leaning
```

with the evidence printed above it, e.g.

```
[1] AI PATTERNS  ...  x 'بالإضافة إلى ذلك': 3  (strong)   weighted total: 12.0
[2] BURSTINESS   mean len: 16.9 | CV: 0.277  ->  too uniform (AI-like)
[3] HUMAN MARKERS  very short sentences: 0 | digits: 0 | field verbs: 0 | markers: 1/3
[4] LEXICAL      TTR: 0.726 — informational only
```

## Tests

```bash
python3 -m unittest discover -s tests -v     # 16 behaviour contracts
```

`tests/fixtures/` holds a deliberate AI-flavoured / human-draft pair in each
language; the suite asserts the two **separate by at least 40 points** and land
in opposite bands. It also pins the lexicon wiring (the engine must score
against `scripts/ai_patterns.py`, not a stale in-file copy). Run it before
trusting any threshold change.

## Thresholds and their provenance

`references/thresholds.md` records, for every threshold, whether it is
**measured** (and how) or **approximate with no official source** — plus the
length-independent alternatives to raw TTR for texts under 300 words
(root-TTR/Guiraud, MTLD). Nothing here is calibrated against Turnitin.

## Limitations

- Any local heuristic is a **self-review aid**; it is not calibrated against
  Turnitin or any other detector, and its thresholds are heuristic, not learned.
- Short documents (under 200 words) and texts with fewer than 6 sentences are
  inherently unstable — the tool says so in its warnings rather than guessing.
- Academic prose in Arabic/English; references and headings can dilute the
  sentence statistics.
- Nothing here can promise an outcome, and it should not be used to disguise
  authorship. Disclosing that you used language tools for revision is the
  defence that actually holds.

## Hermes skill format

Includes the standard `SKILL.md` (bilingual, documented) for use as a Hermes
Agent skill loaded on demand.

## License

MIT © عبدالله العجيان / Abdallah Aljohan (falconeye90) — use freely, attribute on reuse.
