# Calibration — turning heuristic thresholds into measured ones

Everything in the probe started as a heuristic with no official source. This
folder is how those numbers get a measurement behind them, and how anyone can
re-run the measurement.

## Method

| Step | Command | What happens |
|:-----|:--------|:-------------|
| 1 | `python3 calibration/calibrate.py fetch-human` | pulls public Arabic prose (Arabic Wikipedia article extracts, CC BY-SA) and cuts one 300–600 word document per topic |
| 2 | `python3 calibration/calibrate.py make-ai` | generates a document on each **same topic** with several different commercial/open models, so one model's habits cannot define "AI text" |
| 3 | `python3 calibration/calibrate.py measure` | scores every document with the shipped engine and writes `results.json`: AUC, ROC-derived best threshold, confusion matrix, and the measured hit rate of the shipped bands |

The corpus itself is **not committed** (it is third-party and machine-generated
data): only `results.json` — the measured summary — is evidence in the repo.

```bash
CALIB_MODELS="qwen/qwen3.7-flash,mistralai/mistral-nemo,openai/gpt-oss-20b,amazon/nova-micro-v1" \
  python3 calibration/calibrate.py make-ai
```

## Result (2026-09-23)

```
n(AI) = 29        n(human) = 31        Arabic, ~300–600 words/document
AI score mean    = 44.1               human score mean = 16.4
AUC (achieved)   = 0.965
best threshold   = 25   (Youden J 0.836; TP 28, FP 4, TN 27, FN 1 → 91.7% accuracy)
```

Per-signal AUC, measured before combining (single-signal ranking power):

| Signal | AUC | Note |
|:-------|:---:|:-----|
| AI pattern markers | 0.598 | **weak on real generated text** — the fixtures were pattern-dense, real model output is not |
| Burstiness (CV) | 0.845 | strong |
| Human markers | 0.765 | moderate |
| Root-TTR (Guiraud, inverted) | 0.867 | strongest single measure — hence it became a **scored** signal |
| Combined v2 weights (0.55/0.30/0.15) | 0.898 | before adding lexical |
| Combined v3 weights (0.30/0.25/0.15/0.30) | **0.965** | shipped |

Shipped bands, measured on this corpus:

```
AI-leaning  (>= 35):  flags 82.8% of AI documents, 6.5% of human documents
human-leaning (< 20): contains 61.3% of human documents, 3.4% of AI documents
```

## Honest limits

- One corpus: **Arabic, ~300–600 words, encyclopedic register** for the human
  class, and four models for the AI class. English, other registers (theses,
  reports, social) and other models are **not** calibrated here.
- n = 60 documents. Differences under roughly ±0.05 AUC are **within noise** at
  this size; the weights were therefore rounded to coarse values rather than
  fitted to the grid optimum.
- The human class is edited, published prose. A student's own unedited draft
  sits closer to the AI class on burstiness — no local measurement fixes that.
- **Nothing here is calibrated against Turnitin.** This measures our own
  explainable signals, not anyone's detector.
