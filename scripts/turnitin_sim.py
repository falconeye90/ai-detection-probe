#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-detection-probe — bilingual (Arabic / English) AI-likeness probe.

Estimates how AI-flavoured a text reads from signals that are cheap to compute
and explainable line by line. It is a self-review aid, NOT a detector and NOT a
Turnitin check: Turnitin's own documentation states its model works through
"many learned patterns working together rather than by a small set of
transparent, human-readable rules", so no local script reproduces its verdict.

Scoring model (v2)
------------------
Three scored signals, each mapped to an AI-likeness contribution in [0, 1] and
combined with explicit weights. A signal that cannot be computed honestly for
this input (too few sentences, too little text) is dropped and its weight is
redistributed — never guessed at:

    ai_patterns   0.55   severity-weighted discourse markers (ai_patterns.py)
    burstiness    0.30   coefficient of variation of sentence length (>=6 sents)
    human_markers 0.15   edits a draft picks up: very short sentences,
                         numbers/units, first-person field verbs, opener variety
    lexical       0.00   type/token richness — REPORTED ONLY: on texts under
                         ~300 words TTR sits near 1.0 for human and AI writing
                         alike, so it cannot discriminate and must not score

The v1 model scored four equally-weighted signals, so a text carrying seven
strong AI markers and a clean human draft both landed on 2.0/4: the one signal
that actually separated them was worth a single point.

Usage:
    python3 turnitin_sim.py document.docx
    python3 turnitin_sim.py notes.txt --json
    python3 turnitin_sim.py                 # embedded demo
"""
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_patterns import iter_patterns, WEIGHT_BLOCKER  # noqa: E402

WEIGHTS = {"ai_patterns": 0.55, "burstiness": 0.30, "human_markers": 0.15}
MIN_WORDS_RELIABLE = 200
MIN_SENTENCES_RELIABLE = 6
LEAN_AI, LEAN_HUMAN = 60, 40
# The lexicon scores each marker in ai_patterns.py units (BLOCKER 2.0 /
# SUSPECT 1.0); three blockers is the saturation point.
SATURATION = 3 * WEIGHT_BLOCKER

HUMAN_VERBS_AR = ['شغّلنا', 'قست', 'لاحظت', 'وجدت', 'سجلت', 'قابلت', 'زرت',
                  'أجرينا', 'جربت', 'فشل', 'انسحب', 'رفض', 'لم نتمكن']
HUMAN_VERBS_EN = ['i measured', 'i found', 'i ran', 'we ran', 'i noticed',
                  'we noticed', 'i interviewed', 'we recorded', 'failed',
                  'dropped out', 'refused', 'did not work']


def detect_lang(text):
    ar = len(re.findall(r'[\u0600-\u06FF]', text))
    la = len(re.findall(r'[A-Za-z]', text))
    return 'ar' if (ar > 0 and ar >= la) else 'en'


def read_text(path):
    """Extract plain text. Raises ValueError with an actionable message."""
    if not os.path.exists(path):
        raise ValueError(f"File not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.txt', '.md', '.markdown', ''):
        with open(path, encoding='utf-8', errors='replace') as fh:
            return fh.read()
    if ext == '.docx':
        try:
            from docx import Document
        except ImportError:
            raise ValueError("Reading .docx needs python-docx: pip install python-docx")
        return '\n'.join(p.text.strip() for p in Document(path).paragraphs if p.text.strip())
    if ext == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("Reading .pdf needs pypdf: pip install pypdf "
                             "(or submit .txt/.docx instead)")
        return '\n'.join((page.extract_text() or '') for page in PdfReader(path).pages)
    raise ValueError(f"Unsupported file type '{ext}' — supported: .txt, .md, .docx, .pdf")


def demo_text(lang='en'):
    if lang == 'ar':
        return ("إن الاهتمام بإدارة المنظمات في وقتنا الحالي يكتسب أهمية بالغة، حيث أصبح من "
                "المهم جدا أن نركز على الجودة والعمل بشكل منهجي، ومن المهم أيضا أن نعتبر "
                "الجودة عنصرا أساسيا ومحوريا في تحقيق التطور والنجاح. وبالإضافة إلى ذلك "
                "فإن الاستدامة تعتبر خطوة في الاتجاه الصحيح نحو مستقبل مشرق. ولذلك نرى "
                "أن العمل بشكل دقيق ومنظم يعد من الجدير بالذكر والتركيز عليه، ليس فقط من "
                "أجل الكفاءة بل أيضا من أجل التطور المستمر والابتكار.")
    return ("It is important to note that the current landscape of management "
            "underscores the need for innovation and groundbreaking thinking. "
            "Additionally, we must delve into the details to foster a vibrant "
            "culture of excellence, not only for efficiency but also to stand "
            "as a testament to our commitment. In conclusion, this represents "
            "a pivotal step in the right direction towards a brighter future.")


def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?؟;؛…])|\n', text) if len(s.strip()) > 3]


def count_phrase(text, phrase, lang):
    """Whole-word/phrase match; Arabic boundaries are the Arabic block itself."""
    if lang == 'ar':
        pat = r'(?<![\u0600-\u06FF])' + re.escape(phrase) + r'(?![\u0600-\u06FF])'
        return len(re.findall(pat, text))
    pat = r'(?<![A-Za-z])' + re.escape(phrase) + r'(?![A-Za-z])'
    return len(re.findall(pat, text, re.I))


def signal_ai_patterns(text, lang):
    hits, weighted = [], 0.0
    for entry in iter_patterns(lang):
        if entry.get('kind') == 'regex':
            n = len(re.findall(entry['text'], text, re.I))
        else:
            n = count_phrase(text, entry['text'], lang)
        if n:
            hits.append({'phrase': entry['text'], 'count': n,
                         'weight': entry['weight'],
                         'severity': entry['weight'] / WEIGHT_BLOCKER,
                         'category': entry.get('category', '')})
            weighted += n * entry['weight']
    hits.sort(key=lambda h: (-h['weight'], -h['count']))
    # Three blockers (or the equivalent in suspects) is the saturation point:
    # past it the text is AI-flavoured regardless of how many more it carries.
    return {'value': min(1.0, weighted / SATURATION), 'valid': True,
            'weighted_hits': round(weighted, 2), 'hits': hits}


def signal_burstiness(sentences):
    if len(sentences) < MIN_SENTENCES_RELIABLE:
        return {'value': 0.0, 'valid': False, 'cv': None,
                'reason': f'needs >= {MIN_SENTENCES_RELIABLE} sentences'}
    lens = [len(s.split()) for s in sentences]
    mean = statistics.mean(lens)
    if mean == 0:
        return {'value': 0.0, 'valid': False, 'cv': None, 'reason': 'empty sentences'}
    cv = statistics.stdev(lens) / mean
    value = 0.0 if cv >= 0.60 else 0.15 if cv >= 0.45 else 0.50 if cv >= 0.30 else 1.0
    return {'value': value, 'valid': True, 'cv': round(cv, 3),
            'mean_len': round(mean, 1), 'sentences': len(lens)}


def signal_human_markers(text, sentences, lang):
    very_short = sum(1 for s in sentences if len(s.split()) <= 3)
    digits = len(re.findall(r'\d', text))
    verbs = HUMAN_VERBS_AR if lang == 'ar' else HUMAN_VERBS_EN
    field_verbs = sum(1 for v in verbs if count_phrase(text.lower(), v, lang))
    openers = [s.split()[0] for s in sentences if s.split()]
    opener_diversity = len(set(openers)) / len(openers) if openers else 0.0

    markers = (1 if very_short >= 1 else 0)
    markers += 1 if (digits >= 2 or field_verbs >= 1) else 0
    markers += 1 if opener_diversity >= 0.8 else 0
    return {'value': max(0.0, 1.0 - min(1.0, markers / 3.0)), 'valid': True,
            'markers': markers, 'very_short_sentences': very_short,
            'digits': digits, 'field_verbs': field_verbs,
            'opener_diversity': round(opener_diversity, 2)}


def signal_lexical(words):
    uniq = len(set(w.lower() for w in words))
    total = len(words)
    ttr = uniq / total if total else 0.0
    # Root-TTR (Guiraud, 1954): G = V / sqrt(N) — far less length-dependent than
    # raw TTR, so it is reported beside it whenever the text is short.
    root_ttr = uniq / (total ** 0.5) if total else 0.0
    return {'ttr': round(ttr, 3), 'root_ttr_guiraud': round(root_ttr, 3),
            'unique_types': uniq, 'tokens': total,
            'note': 'informational only — TTR does not discriminate under ~300 words; '
                    'read root-TTR (Guiraud) alongside it, per references/thresholds.md'}


def analyse(text, src):
    lang = detect_lang(text)
    words = (re.findall(r'[\u0600-\u06FF]+', text) if lang == 'ar'
             else re.findall(r'[A-Za-z]+', text))
    sentences = split_sentences(text)

    signals = {
        'ai_patterns': signal_ai_patterns(text, lang),
        'burstiness': signal_burstiness(sentences),
        'human_markers': signal_human_markers(text, sentences, lang),
    }

    num = den = 0.0
    for name, sig in signals.items():
        if sig['valid']:
            num += WEIGHTS[name] * sig['value']
            den += WEIGHTS[name]
    ai_pct = round(100 * num / den) if den else 0

    if ai_pct >= LEAN_AI:
        verdict = 'AI-leaning'
    elif ai_pct > LEAN_HUMAN:
        verdict = 'inconclusive — mixed signals'
    else:
        verdict = 'human-leaning'

    warnings = []
    if len(words) < MIN_WORDS_RELIABLE:
        warnings.append(f'only {len(words)} words — under {MIN_WORDS_RELIABLE} the '
                        'estimate is unstable; treat it as a hint, not a result')
    if not signals['burstiness']['valid']:
        warnings.append('burstiness dropped (too few sentences); its weight was redistributed')

    return {'source': src, 'language': lang, 'words': len(words),
            'sentences': len(sentences), 'ai_likeness': ai_pct, 'verdict': verdict,
            'signals': signals, 'lexical': signal_lexical(words),
            'weights_used': {k: WEIGHTS[k] for k, s in signals.items() if s['valid']},
            'warnings': warnings}


def render(report):
    s = report['signals']
    out = ['=' * 66,
           f"Probe: {report['source']}   "
           f"Language: {'Arabic' if report['language'] == 'ar' else 'English'}",
           f"sentences: {report['sentences']} | words: {report['words']}",
           '=' * 66]
    out.append(f"\n[1] AI PATTERNS — severity-weighted markers (weight {WEIGHTS['ai_patterns']})")
    hits = s['ai_patterns']['hits']
    if hits:
        for h in hits[:12]:
            tag = 'blocker' if h['weight'] >= 2.0 else 'suspect'
            cat = h['category'].split(' ')[0] if h['category'] else ''
            out.append(f"    x '{h['phrase']}': {h['count']}  ({tag}{', ' + cat if cat else ''})")
        if len(hits) > 12:
            out.append(f"    ... and {len(hits) - 12} more")
        out.append(f"    weighted total: {s['ai_patterns']['weighted_hits']} "
                   f"(saturates at {SATURATION:.0f})")
    else:
        out.append('    no AI-style markers found')

    b = s['burstiness']
    out.append(f"\n[2] BURSTINESS — sentence-length variance (weight {WEIGHTS['burstiness']})")
    if b['valid']:
        label = ('varied (human-like)' if b['cv'] >= 0.45 else
                 'natural' if b['cv'] >= 0.30 else 'too uniform (AI-like)')
        out.append(f"    mean len: {b['mean_len']} | CV: {b['cv']}  ->  {label}")
    else:
        out.append(f"    not computed: {b['reason']}")

    h = s['human_markers']
    out.append(f"\n[3] HUMAN MARKERS — edits a draft picks up (weight {WEIGHTS['human_markers']})")
    out.append(f"    very short sentences: {h['very_short_sentences']} | "
               f"digits: {h['digits']} | field verbs: {h['field_verbs']} | "
               f"opener diversity: {h['opener_diversity']} | markers: {h['markers']}/3")

    lx = report['lexical']
    out.append('\n[4] LEXICAL — reported, not scored')
    out.append(f"    unique types: {lx['unique_types']} | TTR: {lx['ttr']} | "
               f"root-TTR (Guiraud): {lx['root_ttr_guiraud']}")
    out.append(f"    {lx['note']}")

    out.append('\n' + '=' * 66)
    out.append(f"AI-likeness estimate: {report['ai_likeness']}%  ->  {report['verdict']}")
    out.append('=' * 66)
    for w in report['warnings']:
        out.append(f"! {w}")
    out.append("\nNot a detector: a local, explainable self-review. "
               "Your institution's tooling has the final word.")
    return '\n'.join(out)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    path = args[0] if args else None
    if path:
        try:
            text = read_text(path)
        except ValueError as exc:
            print(f'error: {exc}', file=sys.stderr)
            return 2
        src = path
    else:
        text = demo_text('en')
        src = 'embedded demo (English) — pass a file path to analyse a real document'
    if not text.strip():
        print('error: no readable text found in the input', file=sys.stderr)
        return 2
    report = analyse(text, src)
    print(json.dumps(report, ensure_ascii=False, indent=2) if '--json' in argv
          else render(report))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
