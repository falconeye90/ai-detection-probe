# ai-detection-probe

**A bilingual (Arabic 🇸🇦 / English 🇬🇧) AI-likeness probe** that estimates how
likely a text would be flagged as AI-generated, using the three statistical
signals in the spirit of Turnitin — *burstiness, perplexity-style patterns, and
lexical richness*. For self-review, improvement, and transparency about human
tone — **not** a substitute for your institution's official integrity check.

> ⚠️ This tool runs entirely on your machine. It uploads nothing, needs no
> account, and never stands in for the official Turnitin/institutional report.
> Use it to improve and stay transparent — not to circumvent academic integrity.

---

## Features

- 🇸🇦🇬🇧 Arabic (fusha) and English academic prose — **language auto-detected**
- 📊 Quantitative report across three signals mirroring Turnitin's approach
- 🔒 100% local — no uploads, no account, no fees, single dependency
- 🧰 One self-contained script (only `python-docx` as a dependency)

## Install

```bash
pip install python-docx
```

## Usage

```bash
# Arabic OR English .docx (auto-detected)
python3 scripts/turnitin_sim.py /path/to/document.docx

# No argument -> runs an embedded AI-flavored demo so you see output at once
python3 scripts/turnitin_sim.py
```

## Reading the output

| Signal | Human-like | AI-like |
|--------|:----------:|:-------:|
| **Burstiness** (sentence-length variance) | CV ≥ 0.45 🟢 | CV < 0.30 🔴 |
| **Perplexity proxy** (AI-style patterns) | zero hits 🟢 | any hit 🔴 |
| **Lexical TTR** (vocabulary richness) | ≥ 0.35 🟢 | < 0.25 🔴 |

Final result: **N/4 human signals**. Aim for ≥ 3/4 before submitting.

## Example (a cleaned real document)

```
BURSTINESS : CV = 0.571 → human 🟢
PERPLEXITY : 0 AI patterns → clean 🟢
LEXICAL    : TTR = 0.423 → rich 🟢
Overall    : 4/4 human signals (100%)
```

## Limitations

- Arabic/English academic prose at reasonable confidence; headings, citations, and
  references are excluded from scoring.
- A statistical approximation — Turnitin uses deeper transformer models and
  massive training.
- Heavily human-edited text is harder to detect (an advantage for legitimate
  writing, which is the honest intent of this tool).

## Hermes skill format

Includes the standard `SKILL.md` (bilingual, documented) for use as a Hermes
Agent skill loaded on demand.

## License

MIT © عبدالله العجيان / Abdallah Aljohan (falconeye90) — use freely, attribute on reuse.