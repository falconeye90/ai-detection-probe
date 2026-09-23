#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibration harness for ai-detection-probe.

Three subcommands, run in order:

    python3 calibration/calibrate.py fetch-human   # public human prose -> corpus/human/
    python3 calibration/calibrate.py make-ai       # same topics, 3 models -> corpus/ai/
    python3 calibration/calibrate.py measure       # AUC + ROC-derived thresholds

Why this exists: every threshold in the probe was heuristic ("approximate, no
official source"). This harness turns them into measured numbers on a labelled
corpus — human text from public encyclopedic/news sources, AI text generated on
the same topics by several different models — and reports AUC, the best
threshold by Youden's J, and the confusion matrix at the shipped bands.

Nothing here is committed as data: the corpus stays in the workspace and only
the measured summary (calibration/results.json) is evidence for the repo.
"""
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from turnitin_sim import analyse, LEAN_AI, LEAN_HUMAN  # noqa: E402

CORPUS = os.path.join(HERE, 'corpus')
TARGET_WORDS = (300, 600)
N_DOCS = 30

TOPICS_AR = [
    'تاريخ الأندلس', 'الخلية النباتية', 'النظام الشمسي', 'سلسلة جبال الحجاز',
    'اقتصاد المياه في الخليج', 'الخط العربي', 'الصناعة في اليابان',
    'الحضارة المصرية القديمة', 'العلاقات الدولية', 'علم النفس المعرفي',
    'التلوث البحري', 'الأمن الغذائي', 'الشعر الجاهلي', 'الطباعة ثلاثية الأبعاد',
    'الاستشعار عن بعد', 'الطاقة المتجددة', 'النقل العام في المدن',
    'الذكاء الاصطناعي في التعليم', 'التربة والزراعة المستدامة',
    'التاريخ العثماني', 'اللغة والأصوات', 'الاقتصاد الدائري',
    'إدارة المخاطر المالية', 'برمجة الحواسيب', 'الأنسجة الحيوية',
    'المتاحف والتراث', 'علم الفلك الإسلامي', 'الجفاف في شبه الجزيرة',
    'أنظمة المعلومات الجغرافية', 'الصحة العامة والوقاية',
]

AR_WIKI = ('https://ar.wikipedia.org/w/api.php?action=query&format=json'
           '&prop=extracts&explaintext=1&redirects=1&titles={title}')

# Wikimedia (and most public APIs) reject anonymous library user-agents with 403.
USER_AGENT = ('ai-detection-probe-calibration/1.0 '
              '(threshold research; runs locally)')


def http_json(url, timeout=30, data=None, headers=None):
    hdrs = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return json.load(fh)


def chunks(text, lo, hi, rng):
    """Split into paragraph-ish documents of lo..hi Arabic words."""
    words = text.split()
    docs, i = [], 0
    while i + lo <= len(words):
        n = rng.randint(lo, hi)
        docs.append(' '.join(words[i:i + n]))
        i += n
    return docs


def cmd_fetch_human():
    rng = random.Random(20260923)
    out_dir = os.path.join(CORPUS, 'human')
    os.makedirs(out_dir, exist_ok=True)
    done_path = os.path.join(out_dir, '_done.list')
    done = set()
    if os.path.exists(done_path):
        done = {l.strip() for l in open(done_path, encoding='utf-8') if l.strip()}
    written = len([f for f in os.listdir(out_dir) if f.endswith('.txt')])
    for topic in TOPICS_AR[:N_DOCS]:
        if topic in done:
            continue
        url = AR_WIKI.format(title=urllib.parse.quote(topic))
        text = None
        for attempt in range(4):  # Wikimedia throttles bursts with 429
            try:
                page = next(iter(http_json(url)['query']['pages'].values()))
                text = page.get('extract', '')
                break
            except Exception as exc:
                if '429' in str(exc):
                    time.sleep(3 * (attempt + 1))
                    continue
                print(f'  ! {topic}: {exc}')
                break
        if not text:
            print(f'  - {topic}: skipped (no extract)')
            time.sleep(1.2)
            continue
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text.split()) < TARGET_WORDS[0]:
            print(f'  - {topic}: too short, skipped')
            time.sleep(1.2)
            continue
        doc = chunks(text, *TARGET_WORDS, rng)[0]
        path = os.path.join(out_dir, f'human_{written:03d}.txt')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(doc)
        with open(done_path, 'a', encoding='utf-8') as fh:
            fh.write(topic + '\n')
        written += 1
        print(f'  + {os.path.basename(path)} ({len(doc.split())} words) — {topic}')
        time.sleep(1.5)  # stay under the public API rate limit
    print(f'\nhuman documents: {written}')


AI_PROMPT = ('اكتب نصاً أكاديمياً عربياً فصيحاً عن الموضوع التالي بحدود 450 كلمة، '
             'بأسلوب تقريري منظم وبلا عناوين فرعية: {topic}')


def _openrouter_key():
    for path in ('/home/hermes/.hermes/.env', os.path.expanduser('~/.hermes/.env')):
        if os.path.exists(path):
            for line in open(path, encoding='utf-8', errors='ignore'):
                if line.startswith('OPENROUTER_API_KEY='):
                    return line.split('=', 1)[1].strip()
    raise SystemExit('OPENROUTER_API_KEY not found')


def cmd_make_ai():
    key = _openrouter_key()
    # Several models on purpose: a single model's habits must not define what
    # "AI text" means for the calibration.
    raw = os.environ.get('CALIB_MODELS', '')
    models = [m for m in raw.split(',') if m] or ['qwen/qwen3.7-flash',
                                                 'mistralai/mistral-nemo',
                                                 'openai/gpt-oss-20b']
    out_dir = os.path.join(CORPUS, 'ai')
    os.makedirs(out_dir, exist_ok=True)
    have = len([f for f in os.listdir(out_dir) if f.endswith('.txt')])
    todo = TOPICS_AR[have:N_DOCS]

    def one(item):
        i, topic = item
        model = models[i % len(models)]
        body = json.dumps({
            'model': model,
            'messages': [{'role': 'user',
                          'content': AI_PROMPT.format(topic=topic)}],
            'max_tokens': 800,
        }).encode()
        try:
            payload = http_json('https://openrouter.ai/api/v1/chat/completions',
                                timeout=180, data=body,
                                headers={'Authorization': f'Bearer {key}',
                                         'Content-Type': 'application/json'})
            return i, topic, model, payload['choices'][0]['message']['content'].strip()
        except Exception as exc:
            return i, topic, model, f'__ERROR__ {exc}'

    written = have
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, topic, model, text in pool.map(one, enumerate(todo, start=have)):
            if text.startswith('__ERROR__'):
                print(f'  ! {topic}: {text[10:120]}')
                continue
            path = os.path.join(out_dir, f'ai_{written:03d}.txt')
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(text)
            written += 1
            print(f'  + {os.path.basename(path)} ({len(text.split())} words) — {model} — {topic}')
    print(f'\nAI documents: {written}')


def load_corpus(label):
    d = os.path.join(CORPUS, label)
    if not os.path.isdir(d):
        raise SystemExit(f'missing corpus/{label} — run the earlier subcommand first')
    docs = []
    for name in sorted(os.listdir(d)):
        # bookkeeping files (topic lists) are not corpus documents
        if name.endswith('.txt') and not name.startswith('_'):
            with open(os.path.join(d, name), encoding='utf-8') as fh:
                docs.append((name, fh.read()))
    return docs


def auc(pos, neg):
    """Rank-based AUC (Mann-Whitney U). pos = AI scores, neg = human scores."""
    if not pos or not neg:
        return None
    wins = sum((1.0 if p > n else 0.5 if p == n else 0.0)
               for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def best_threshold(pos, neg):
    """Youden's J over candidate cut-offs."""
    cutoffs = sorted(set(pos + neg))
    best = (None, -1.0)
    for c in cutoffs:
        tpr = sum(1 for p in pos if p >= c) / len(pos)
        fpr = sum(1 for n in neg if n >= c) / len(neg)
        j = tpr - fpr
        if j > best[1]:
            best = (c, j)
    return best


def cmd_measure():
    human = load_corpus('human')
    ai = load_corpus('ai')
    rows = []
    for label, docs in (('human', human), ('ai', ai)):
        for name, text in docs:
            rep = analyse(text, name)
            rows.append({'label': label, 'name': name, 'score': rep['ai_likeness'],
                         'words': rep['words'], 'verdict': rep['verdict'],
                         'burst_cv': rep['signals']['burstiness']['cv'],
                         'markers': rep['signals']['ai_patterns']['weighted_hits']})
    pos = [r['score'] for r in rows if r['label'] == 'ai']
    neg = [r['score'] for r in rows if r['label'] == 'human']
    a = auc(pos, neg)
    thr, j = best_threshold(pos, neg)
    tp = sum(1 for p in pos if p >= thr)
    fp = sum(1 for n in neg if n >= thr)
    tn = len(neg) - fp
    fn = len(pos) - tp
    report = {
        'n_ai': len(pos), 'n_human': len(neg),
        'ai_score_mean': round(sum(pos) / len(pos), 1) if pos else None,
        'human_score_mean': round(sum(neg) / len(neg), 1) if neg else None,
        'auc': round(a, 3) if a else None,
        'best_threshold': thr, 'youden_j': round(j, 3),
        'confusion_at_best_threshold': {'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn},
        'shipped_bands': {'ai_leaning_at': LEAN_AI, 'human_leaning_below': LEAN_HUMAN,
                          'measured_at_ai_band': {
                              'ai_recall': round(sum(1 for p in pos if p >= LEAN_AI) / len(pos), 3),
                              'human_false_positive_rate':
                                  round(sum(1 for n in neg if n >= LEAN_AI) / len(neg), 3)},
                          'measured_at_human_band': {
                              'human_share_below': round(sum(1 for n in neg if n < LEAN_HUMAN) / len(neg), 3),
                              'ai_share_below': round(sum(1 for p in pos if p < LEAN_HUMAN) / len(pos), 3)}},
        'rows': rows,
    }
    with open(os.path.join(HERE, 'results.json'), 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'measure'
    {'fetch-human': cmd_fetch_human, 'make-ai': cmd_make_ai,
     'measure': cmd_measure}.get(cmd, cmd_measure)()
