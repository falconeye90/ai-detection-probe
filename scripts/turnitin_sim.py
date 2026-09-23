#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-detection-probe — يحاكي مؤشرات Turnitin الثلاث على نصوص عربية.
تقدير إحصائي تقريبي للدراسة الذاتية — ليست فحص Turnitin الفعلي.
الاستخدام: python3 turnitin_sim.py /مسار/إلى/مستند.docx
(بدون وسيطة: يعمل على عيّنة تجريبية مدمجة)
"""
import re, sys, os, statistics
from collections import Counter

try:
    from docx import Document
except ImportError:
    sys.exit("ثبّت python-docx أولاً: pip install python-docx")

# عيّنة تجريبية مدمجة (نص ذو بصمة AI واضحة) ليجرّبها المستخدم دون ملف
DEMO = (
  "إن الاهتمام بإدارة المنظمات في وقتنا الحالي يكتسب أهمية بالغة، حيث أصبح من "
  "المهم جدا أن نركز على الجودة والعمل بشكل منهجي، ومن المهم أيضا أن نعتبر "
  "الجودة عنصرا أساسيا ومحوريا في تحقيق التطور والنجاح. وبالإضافة إلى ذلك "
  "فإن الاستدامة تعتبر خطوة في الاتجاه الصحيح نحو مستقبل مشرق. ولذلك نرى "
  "أن العمل بشكل دقيق ومنظم يعد من الجدير بالذكر والتركيز عليه، ليس فقط من "
  "أجل الكفاءة بل أيضا من أجل التطور المستمر والابتكار."
)

_path = sys.argv[1] if len(sys.argv) > 1 else None
if _path and not os.path.exists(_path):
    sys.exit(f"الملف غير موجود: {_path}")

if _path:
    doc = Document(_path)
    paras = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 1]
    SRC = _path
else:
    paras = [DEMO]
    SRC = "عيّنة تجريبية مدمجة (أرسل مسار ملف للفحص الفعلي)"

body_paras = [p for p in paras if len(p) > 80]
full = '\n'.join(paras)


def sent_split(text):
    return [s.strip() for s in re.split(r'(?<=[.!؟؟;؛…])|\n', text) if len(s.strip()) > 3]


sents = sent_split(full)
lens = [len(s.split()) for s in sents]
words = re.findall(r'[\u0600-\u06FF]+', full)
W = len(words)

print("=" * 66)
print(f"الفحص: {SRC}")
print(f"الفقرات النثرية: {len(body_paras)}  | الجمل: {len(sents)}  | الكلمات: {W}")
print("=" * 66)

# الإشارة 1: Burstiness
mean = statistics.mean(lens); sd = statistics.stdev(lens); cv = sd / mean
print("\n[1] BURSTINESS — تباين أطوال الجمل")
print(f"    متوسط طول الجملة: {mean:.1f} كلمة  |  انحراف معياري: {sd:.1f}")
print(f"    معامل التباين (CV): {cv:.3f}", end=' ')
if cv >= 0.45:
    print("→ متنوع جداً (بشري) 🟢")
elif cv >= 0.30:
    print("→ طبيعي 🟡")
else:
    print("→ منتظم جداً (نمط AI) 🔴")

# الإشارة 2: Perplexity-proxy
ai_vocab = ['بالإضافة إلى ذلك', 'علاوة على ذلك', 'جدير بالذكر', 'من ناحية أخرى',
            'من المهم', 'من الجدير', 'في هذا السياق', 'على المستوى', 'يسلط الضوء',
            'يعتبر', 'يمثل', 'يتميز', 'فريد', 'استثنائي', 'نابض', 'آفاق واعدة',
            'المستقبل مشرق', 'خطوة في الاتجاه', 'ليس فقط', 'لا يقتصر', 'شمل ذلك',
            'تجدر الإشارة', 'من المميز', 'يشير المراقبون', 'يرى الخبراء']
cnt, hits = 0, []


def _arabic_word_count(text, phrase):
    # كلمة قد تكون داخل اسم علم (مثل "فريدريك") فلا تُحسب:
    # طابق بالكلمة الكاملة عبر حدود الأحرف العربية.
    if ' ' in phrase.strip():
        return text.count(phrase)
    return len(re.findall(r'(?<![\u0600-\u06FF])' + re.escape(phrase) + r'(?![\u0600-\u06FF])', text))


for ph in ai_vocab:
    c = _arabic_word_count(full, ph)
    if c:
        hits.append((ph, c))
        cnt += c
print("\n[2] PERPLEXITY (proxy) — أنماط ومفردات AI الشائعة")
if hits:
    for ph, c in hits:
        print(f"    ✗ '{ph}': {c}")
    print(f"    إجمالي الإشارات: {cnt}")
else:
    print("    لا إشارات AI محفوظة  🟢")

very_short = sum(1 for l in lens if l <= 2)
print(f"    جمل قصيرة جداً (≤2 كلمات): {very_short} ({100 * very_short / max(1, len(lens)):.0f}%)  " +
      ("(علامة تحرير بشري 🟢)" if very_short >= 3 else ""))

# الإشارة 3: Lexical (TTR)
uniq = len(set(words))
ttr = uniq / W if W else 0
print("\n[3] LEXICAL — غنى المفردات (نسبة TTR)")
print(f"    مفردات فريدة: {uniq} | TTR: {ttr:.3f}", end=' ')
if ttr >= 0.35:
    print("→ غنية ومتنوعة 🟢")
elif ttr >= 0.25:
    print("→ متوسطة 🟡")
else:
    print("→ متكررة (نمط AI) 🔴")

wc = Counter(words)
print("    الأكثر تكراراً:", ", ".join(f"{w}({n})" for w, n in wc.most_common(8)))

initials = Counter(s.split()[0] for s in sents if s.split())
print("    بدايات الجمل الأكثر تكراراً:", ", ".join(f"«{w}»×{n}" for w, n in initials.most_common(6)))

# التقدير الإجمالي
score = 0
score += 1 if cv >= 0.45 else (0.5 if cv >= 0.30 else 0)
score += 0 if cnt > 0 else 1
score += 1 if ttr >= 0.35 else (0.5 if ttr >= 0.25 else 0)
score += 1 if very_short >= 3 else 0
pct = score / 4 * 100
print("\n" + "=" * 66)
print(f"تقدير تقريبي للوقوع كـ 'AI': {pct:.0f}%  (مؤشرات بشرية {score:.1f}/4)")
print("=" * 66)
print("\nتوضيح: محاكاة إحصائية تقريبية بنفس مؤشرات Turnitin، ليست فحصه الفعلي.")
print("النتيجة النهائية تبقى لنظام جامعتك.")
