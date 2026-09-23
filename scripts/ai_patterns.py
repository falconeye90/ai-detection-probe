#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_patterns.py — قوائم أنماط AI موسّعة (عربي + إنجليزي) بعتبات مُرتَّبة.

وحدة **بيانات/قواعد** لا منطق فحص. تستوردها محرّكات الفحص (مثل
`turnitin_sim.py`) لتعدّد إشارات الأسلوب، وتُستعمل كمرجع في وثائق SKILL.md.

--------------------------------------------------------------------
معيار الترجيح (weighting standard)
--------------------------------------------------------------------
كلّ نمط مُصنَّف بوزن إحدى درجتين:

    WEIGHT_BLOCKER        "قاطع"  — عبارة مرتفعة الارتباط بالكتابة الآلية
                                    (تضخيم أهميّة، ترويج، إسناد غامض،
                                    روابط جاهزة). ظهورُه يُرجِّح الحكمَ
                                    شبهَ حاسم نحو "نمط AI".
    WEIGHT_SUSPECT        "مشتبه" — نمط وارد أحياناً في الكتابة البشرية
                                    لكنه أكبر استمراراً في الكلام الآلي.
                                    يُحتسب بأقلّ أثر، ويلزم العددُ تراكمياً
                                    لرفع الخطر.

الأساس المنهجي الذي أُنشئت عليه القائمة:
    قوائم مبنية على ملاحظات شائعة في النص الأكاديمي الآلي (روابط، استهلالات،
    تضخيم) — وهي **تقريبية استرشادية**، وليست "قواعد Turnitin". الادعاء بأن
    Turnitin يعتمد على "مجموعة صغيرة من القواعد الواضحة القابلة للتفسير"
    تنفيه الشركة رسمياً في FAQ الكشف عن الانتحال: الكشف يقوم على
    «many learned patterns working together rather than by a small set of
    transparent, human-readable rules». لذلك يُوصف هذا النهج هنا فقط بأنه
    "مستوحى من المقاربة الإحصائية الشائعة (burstiness / perplexity)".

--------------------------------------------------------------------
البنية
--------------------------------------------------------------------
    PATTERNS : list[dict] — كل إدخال:
        lang      : 'ar' | 'en'
        category  : اسم الفئة (انظر ثوابت CAT_*)
        weight    : WEIGHT_BLOCKER | WEIGHT_SUSPECT
        kind      : 'phrase' (عبارة تُطابق كلمةً كاملة) | 'regex' (نمط ترقيم/بنية)
        text      : العبارة (phrase) أو التعبير النمطي (regex)
        note      : وصف/مبرّر موجز

الفئات (Category):
    روابط  (CAT_CONNECT)       — أدوات الربط الجاهزة
    استهلال (CAT_OPENER)       — صيغ افتتاح الجمل/الفقرات
    تضخيم  (CAT_EMPHASIS)      — مبالغة في الأهميّة
    إسناد  (CAT_VAGUE_ATTR)    — إسناد غامض (يقال/يُرى/تشير الدراسات…)
    توازي  (CAT_NEG_PARALLEL)  — توازي سلبي (ليس فقط… بل)
    ترويج  (CAT_PROMOTION)     — لغة ترويج/حماس
    ترقيم  (CAT_PUNCT)          — أوزان ترقيمية (شرطات، فاصلة منقوطة زائدة…)

--------------------------------------------------------------------
مطابقة 'phrase'
--------------------------------------------------------------------
    كلمة كاملة بحدود صحيحة: للعربية لا يُطابق داخل اسمٍ عَلَم (مثل "فريد"
    لا يطابق "فريدريك")؛ للإنجليزية مطابقة case-insensitive بحدود \b.
    الترجيح النهائي = جمع أوزان التطابقات (لا مجرّد عدد الأنماط).
--------------------------------------------------------------------
"""
import re
from collections import defaultdict

# --- درجات الترجيح ---------------------------------------------------
WEIGHT_BLOCKER = 2.0    # قاطع: يُرجِّح الحكم شبهَ حاسم
WEIGHT_SUSPECT = 1.0    # مشتبه: أثر تراكمي أخفّ

# --- الفئات -----------------------------------------------------------
CAT_CONNECT      = "connectives (روابط)"
CAT_OPENER       = "openers (استهلالات)"
CAT_EMPHASIS     = "overstating-importance (تضخيم الأهمية)"
CAT_VAGUE_ATTR   = "vague-attribution (إسناد غامض)"
CAT_NEG_PARALLEL = "negative-parallelism (توازي سلبي)"
CAT_PROMOTION    = "promotion (ترويج)"
CAT_PUNCT        = "punctuation-markers (علامات ترقيم)"

# ---------------------------------------------------------------------
# Arabk patterns
# ---------------------------------------------------------------------
AR_PATTERNS = [
    # --- روابط جاهزة (قاطعة عند التكرار، مشتبهة عند الواحدة) ---
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="علاوة على ذلك", note="رابط آلي شائع"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="بالإضافة إلى ذلك", note="رابط آلي شائع"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="إضافة إلى ذلك", note="رابط آلي شائع"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="من ناحية أخرى", note="تحوّل جملي آلي"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="من جهة أخرى", note="تحوّل جملي آلي"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="في هذا السياق", note="ربط آلي متكرر"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="على المستوى", note="تركيب آلي متكرر (على المستوى …ي)"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="في ضوء ما سبق", note="استنتاج آلي جاهز"),
    dict(lang="ar", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="وبالتالي", note="استنتاج آلي متكرر"),

    # --- استهلالات (قاطعة عند التضخيم) ---
    dict(lang="ar", category=CAT_OPENER, weight=WEIGHT_SUSPECT, kind="phrase",
         text="من المهم", note="استهلال تقييمي آلي"),
    dict(lang="ar", category=CAT_OPENER, weight=WEIGHT_SUSPECT, kind="phrase",
         text="من الجدير", note="استهلال تقييمي آلي"),
    dict(lang="ar", category=CAT_OPENER, weight=WEIGHT_BLOCKER, kind="phrase",
         text="من الجدير بالذكر", note="صيغة مضخّمة قاطعة"),
    dict(lang="ar", category=CAT_OPENER, weight=WEIGHT_BLOCKER, kind="phrase",
         text="جدير بالذكر", note="صيغة مضخّمة قاطعة"),
    dict(lang="ar", category=CAT_OPENER, weight=WEIGHT_BLOCKER, kind="phrase",
         text="تجدر الإشارة", note="صيغة افتتاح قاطعة"),
    dict(lang="ar", category=CAT_OPENER, weight=WEIGHT_SUSPECT, kind="phrase",
         text="من المميز", note="استهلال تقييمي"),

    # --- تضخيم الأهمية (قاطع) ---
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="فريد", note="تضخيم آلي قاطع"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="استثنائي", note="تضخيم آلي قاطع"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="عظيم", note="تضخيم"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="هائل", note="تضخيم"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="نابض", note="تضخيم/مجاز آلي"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="حيوي", note="تضخيم"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="محوري", note="تضخيم"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="جوهري", note="تضخيم"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="من الأهمية بمكان", note="صيغة تضخيم قاطعة"),
    dict(lang="ar", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="لا يمكن إغفال", note="صيغة تضخيم قاطعة"),

    # --- إسناد غامض (قاطع) ---
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="يشير المراقبون", note="إسناد غامض قاطع"),
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="يرى الخبراء", note="إسناد غامض قاطع"),
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="تشير الدراسات", note="إسناد غامض قاطع"),
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="تشير الأدبيات", note="إسناد غامض قاطع"),
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="من المتعارف عليه", note="إسناد غامض قاطع"),
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="يجمع الباحثون", note="إسناد غامض قاطع"),
    dict(lang="ar", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="يُعتقد على نطاق واسع", note="إسناد غامض قاطع"),

    # --- توازي سلبي (قاطع) ---
    dict(lang="ar", category=CAT_NEG_PARALLEL, weight=WEIGHT_BLOCKER, kind="phrase",
         text="ليس فقط", note="توازي سلبي آلي"),
    dict(lang="ar", category=CAT_NEG_PARALLEL, weight=WEIGHT_BLOCKER, kind="phrase",
         text="لا يقتصر على", note="توازي سلبي آلي"),
    dict(lang="ar", category=CAT_NEG_PARALLEL, weight=WEIGHT_BLOCKER, kind="phrase",
         text="لا يقتصر فحسب", note="توازي سلبي آلي"),

    # --- ترويج (قاطع) ---
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="آفاق واعدة", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="المستقبل مشرق", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="نحو مستقبل مشرق", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="خطوة في الاتجاه الصحيح", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="يمهد الطريق ل", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="يفتح آفاقاً جديدة", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="نقلة نوعية", note="لغة ترويج قاطعة"),
    dict(lang="ar", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="إنجاز غير مسبوق", note="لغة ترويج قاطعة"),
]

# ---------------------------------------------------------------------
# English patterns
# ---------------------------------------------------------------------
EN_PATTERNS = [
    # --- connectives ---
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="furthermore", note="canned connector"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="moreover", note="canned connector"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="additionally", note="canned connector"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="in addition", note="canned connector"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="in order to", note="stilted purpose clause"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="due to the fact that", note="wordy connector"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="when it comes to", note="canned topic-changer"),
    dict(lang="en", category=CAT_CONNECT, weight=WEIGHT_SUSPECT, kind="phrase",
         text="in conclusion", note="canned closer"),

    # --- openers (blocker when emphatic) ---
    dict(lang="en", category=CAT_OPENER, weight=WEIGHT_SUSPECT, kind="phrase",
         text="it is important to note", note="opener"),
    dict(lang="en", category=CAT_OPENER, weight=WEIGHT_BLOCKER, kind="phrase",
         text="it is worth noting", note="awareness-raising opener"),
    dict(lang="en", category=CAT_OPENER, weight=WEIGHT_BLOCKER, kind="phrase",
         text="it should be noted", note="awareness-raising opener"),
    dict(lang="en", category=CAT_OPENER, weight=WEIGHT_BLOCKER, kind="phrase",
         text="it is noteworthy", note="awareness-raising opener"),
    dict(lang="en", category=CAT_OPENER, weight=WEIGHT_SUSPECT, kind="phrase",
         text="it is essential to", note="opener"),

    # --- overstating importance (blocker) ---
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="pivotal", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="crucial", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="paramount", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="groundbreaking", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="revolutionary", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="unprecedented", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="transformative", note="overstated"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="testament", note="overstated/hype"),
    dict(lang="en", category=CAT_EMPHASIS, weight=WEIGHT_BLOCKER, kind="phrase",
         text="game-changer", note="hype"),

    # --- vague attribution (blocker) ---
    dict(lang="en", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="experts believe", note="vague attribution"),
    dict(lang="en", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="researchers argue", note="vague attribution"),
    dict(lang="en", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="studies show", note="vague attribution"),
    dict(lang="en", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="it is widely believed", note="vague attribution"),
    dict(lang="en", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="scholars suggest", note="vague attribution"),
    dict(lang="en", category=CAT_VAGUE_ATTR, weight=WEIGHT_BLOCKER, kind="phrase",
         text="some may argue", note="vague attribution"),

    # --- negative parallelism (blocker) ---
    dict(lang="en", category=CAT_NEG_PARALLEL, weight=WEIGHT_BLOCKER, kind="phrase",
         text="not only", note="negative parallelism"),
    dict(lang="en", category=CAT_NEG_PARALLEL, weight=WEIGHT_BLOCKER, kind="phrase",
         text="not just", note="negative parallelism"),

    # --- promotion / hype (blocker) ---
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="game-changer", note="promotion/hype"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="pave the way", note="promotion/hype"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="open new horizons", note="promotion/hype"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="unlock new possibilities", note="promotion/hype"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="step in the right direction", note="promotion/hype"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="usher in a new era", note="promotion/hype"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="delve", note="LLM-favoured verb"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="landscape", note="LLM-favoured metaphor"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="fostering", note="LLM-favoured verb"),
    dict(lang="en", category=CAT_PROMOTION, weight=WEIGHT_BLOCKER, kind="phrase",
         text="vibrant", note="LLM-favoured adjective"),

    # --- punctuation markers (regex; count per occurrence) ---
    dict(lang="en", category=CAT_PUNCT, weight=WEIGHT_SUSPECT, kind="regex",
         text=r"\u2014", note="em-dash (—) presence"),
    dict(lang="ar", category=CAT_PUNCT, weight=WEIGHT_SUSPECT, kind="regex",
         text=r"\u2014", note="em-dash (—) presence"),
    dict(lang="en", category=CAT_PUNCT, weight=WEIGHT_SUSPECT, kind="regex",
         text=r"[;；]{2,}", note="clustered semicolons"),
    dict(lang="en", category=CAT_PUNCT, weight=WEIGHT_SUSPECT, kind="regex",
         text=r"[…]{1,}", note="repeated ellipsis"),
]

# --- جميع الأنماط معاً -------------------------------------------------
PATTERNS = AR_PATTERNS + EN_PATTERNS


def iter_patterns(lang):
    """أعد الأنماط لغةً (ar | en)."""
    return [p for p in PATTERNS if p["lang"] == lang]


def weight_for(lang, phrase_or_category=None):
    """أعد وزن نمطٍ معيّن (text) أو وزن فئةٍ كاملة (category)."""
    if phrase_or_category is None:
        raise ValueError("حدّد text أو category")
    for p in PATTERNS:
        if p["lang"] == lang and (p["text"] == phrase_or_category
                                  or p["category"] == phrase_or_category):
            return p["weight"]
    return None


def total_blocker_weight(lang):
    """مجموع الأوزان القاطعة لكل لغة (مرجع لوثيقة SKILL.md)."""
    return sum(p["weight"] for p in iter_patterns(lang) if p["weight"] == WEIGHT_BLOCKER)


def category_counts(lang):
    """عدّ الأنماط لكل فئة وقابل للطباعة — للتوثيق/الاختبار."""
    c = defaultdict(lambda: [0, 0])  # [blockers, suspects]
    for p in iter_patterns(lang):
        c[p["category"]][0 if p["weight"] == WEIGHT_BLOCKER else 1] += 1
    return dict(c)


if __name__ == "__main__":
    print("ai_patterns.py — ملخص مرجعي (قوائم أنماط AI)\n")
    for lang, name in (("ar", "العربية"), ("en", "English")):
        pats = iter_patterns(lang)
        blockers = sum(1 for p in pats if p["weight"] == WEIGHT_BLOCKER)
        print(f"[{name}] أنماط: {len(pats)} | قاطعة: {blockers} | مشتبهة: {len(pats)-blockers}")
        cc = category_counts(lang)
        for cat, (b, s) in cc.items():
            print(f"    - {cat}: قاطعة {b} / مشتبهة {s}")
        print()
