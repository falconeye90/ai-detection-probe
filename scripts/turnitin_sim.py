#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-detection-probe — bilingual (Arabic / English) AI-likeness probe.
Estimates whether text reads as AI-generated using three signals in the
spirit of Turnitin: burstiness / perplexity-style patterns / lexical richness.
A statistical approximation for self-review — NOT a real Turnitin check.

Usage: python3 turnitin_sim.py /path/to/document.docx
(no argument -> runs an embedded AI-flavored demo, English by default)
"""
import re, sys, os, statistics
from collections import Counter

try:
    from docx import Document
except ImportError:
    sys.exit("Install python-docx first: pip install python-docx")


def _is_arabic_heavy(text):
    ar = len(re.findall(r'[\u0600-\u06FF]', text))
    la = len(re.findall(r'[A-Za-z]', text))
    return ar >= la and ar > 0


def _arabic_word_count(text, phrase):
    # Full Arabic word only — never a substring of a proper name
    # (e.g. "فريد" must not match "فريدريك").
    if ' ' in phrase.strip():
        return text.count(phrase)
    return len(re.findall(r'(?<![\u0600-\u06FF])' + re.escape(phrase) + r'(?![\\u0600-\\u06FF])', text))


AR_VOCAB = ['بالإضافة إلى ذلك', 'علاوة على ذلك', 'جدير بالذكر', 'من ناحية أخرى',
            'من المهم', 'من الجدير', 'في هذا السياق', 'على المستوى', 'يسلط الضوء',
            'يعتبر', 'يمثل', 'يتميز', 'فريد', 'استثنائي', 'نابض', 'آفاق واعدة',
            'المستقبل مشرق', 'خطوة في الاتجاه', 'ليس فقط', 'لا يقتصر', 'شمل ذلك',
            'تجدر الإشارة', 'من المميز', 'يشير المراقبون', 'يرى الخبراء']

EN_VOCAB = ['additionally', 'furthermore', 'moreover', 'in conclusion',
            'it is important to note', 'it is worth noting', 'in order to',
            'due to the fact that', 'delve', 'landscape', 'testament', 'pivotal',
            'groundbreaking', 'underscores', 'renowned', 'boasts', 'vibrant',
            'intricate', 'fostering', 'game-changer', 'deep dive', 'not only',
            'but also', 'at the end of the day', 'when it comes to', 'dive into']


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


def analyse(text, src):
    arabic = _is_arabic_heavy(text)
    if arabic:
        words = re.findall(r'[\u0600-\u06FF]+', text)
        vocab, counter = AR_VOCAB, lambda ph: _arabic_word_count(text, ph)
    else:
        words = re.findall(r"[A-Za-z]+", text)
        vocab, counter = EN_VOCAB, lambda ph: len(re.findall(r'(?<![A-Za-z])' + re.escape(ph) + r'(?![A-Za-z])', text, re.I))
    W = len(words)

    sents = [s.strip() for s in re.split(r'(?<=[.!?؟؟;؛…])|\n', text) if len(s.strip()) > 3]
    lens = [len(s.split()) for s in sents]

    print("=" * 66)
    print(f"Probe: {src}   Language: {'Arabic' if arabic else 'English'}")
    print(f"sentences: {len(sents)} | words: {W}")
    print("=" * 66)

    mean = statistics.mean(lens); sd = statistics.stdev(lens); cv = sd / mean
    print("\n[1] BURSTINESS — sentence-length variance")
    print(f"    mean len: {mean:.1f} | std: {sd:.1f} | CV: {cv:.3f}", end=' ')
    if cv >= 0.45: print("→ very varied (human) 🟢")
    elif cv >= 0.30: print("→ natural 🟡")
    else: print("→ too uniform (AI-like) 🔴")

    cnt, hits = 0, []
    for ph in vocab:
        c = counter(ph)
        if c:
            hits.append((ph, c)); cnt += c
    print("\n[2] PERPLEXITY proxy — common AI-style patterns")
    if hits:
        for ph, c in hits:
            print(f"    ✗ '{ph}': {c}")
        print(f"    total signals: {cnt}")
    else:
        print("    no AI-style patterns found  🟢")

    very_short = sum(1 for l in lens if l <= 2)
    print(f"    very short sentences (<=2 words): {very_short} ({100 * very_short / max(1, len(lens)):.0f}%)  " +
          ("(human-editing marker 🟢)" if very_short >= 3 else ""))

    uniq = len(set(w.lower() for w in words))
    ttr = uniq / W if W else 0
    print("\n[3] LEXICAL — vocabulary richness (TTR)")
    print(f"    unique types: {uniq} | TTR: {ttr:.3f}", end=' ')
    if ttr >= 0.35: print("→ rich/varied 🟢")
    elif ttr >= 0.25: print("→ moderate 🟡")
    else: print("→ repetitive (AI-like) 🔴")

    wc = Counter(w.lower() for w in words)
    print("    top words:", ", ".join(f"{w}({n})" for w, n in wc.most_common(8)))
    initials = Counter(s.split()[0].lower() for s in sents if s.split())
    print("    top sentence openers:", ", ".join(f"«{w}»×{n}" for w, n in initials.most_common(6)))

    score = 0
    score += 1 if cv >= 0.45 else (0.5 if cv >= 0.30 else 0)
    score += 0 if cnt > 0 else 1
    score += 1 if ttr >= 0.35 else (0.5 if ttr >= 0.25 else 0)
    score += 1 if very_short >= 3 else 0
    pct = score / 4 * 100
    print("\n" + "=" * 66)
    print(f"Estimated chance of being flagged as AI: {pct:.0f}%  (human signals {score:.1f}/4)")
    print("=" * 66)
    print("\nNote: statistical approximation using the same three signals as Turnitin —")
    print("NOT Turnitin's real check. Your institution has the final word.")


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        if not os.path.exists(path):
            sys.exit(f"File not found: {path}")
        doc = Document(path)
        paras = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 1]
        src = path
    else:
        paras = [demo_text('en')]
        src = "embedded demo (English) — pass a file path to analyse a real doc"
    analyse('\n'.join(paras), src)