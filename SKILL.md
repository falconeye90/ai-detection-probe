---
name: ai-detection-probe
description: "Use when auditing Arabic text for AI-detection risk."
version: 1.0.0
author: عبدالله العجيان (falconeye90)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arabic, ai-detection, turnitin, academic-integrity, text-audit, humanizer, quantitative, publishing]
    category: productivity
    related_skills: [arabic-humanizer, text-cleaning-agent, arabic-academic-documents]
    publication: public
    repo: https://github.com/falconeye90/hermes-skills
---
# ai-detection-probe — فاحص نصوص لاكتشاف AI

**Bilingual — Arabic 🇸🇦 & English 🇬🇧.** An open, quantitative probe that estimates
how likely a text would be flagged as AI-generated, using the three statistical
signals in the spirit of Turnitin (burstiness · perplexity-style patterns · lexical
richness). Arabic or English is auto-detected.

> ⚠️ أكاديمياً/أخلاقياً: هذه الأداة للدراسة الذاتية والتحسين والشفافية، وليست بديلاً
> عن فحص النزاهة الرسمي. الإثبات النهائي يبقى لنظام مؤسستك، والكتابة بمساعدة
> الذكاء الاصطناعي تتطلب التصريح وفق سياسات جامعتك.

---

## التثبيت / Install

```bash
pip install python-docx
```

## الاستخدام / Usage

```bash
# Arabic or English .docx (auto-detected)
python3 scripts/turnitin_sim.py /path/to/document.docx
# no argument -> runs an embedded AI-flavored demo (English)
python3 scripts/turnitin_sim.py
```

---

## المؤشرات الثلاثة (نفس فلسفة Turnitin)

### ١) Burstiness — تباين أطوال الجمل
التحليل: البشر يكتبون جملة قصيرة بين الطويلة. الموديلات تُنتج جملة «أملسة» متقاربة
الطول حول ١٥–٢٤ كلمة. يُقاس **معامل التباين** `CV = الانحراف المعياري ÷ المتوسط`.

| القيمة | الحكم |
|:------:|-------|
| `≥ 0.45` | متنوع جداً → بشري 🟢 |
| `0.30–0.45` | طبيعي → 🟡 |
| `< 0.30` | منتظم جداً → نمط AI 🔴 |

### ٢) Perplexity-proxy — أنماط ومفردات AI الشائعة
عدّ تطابق قائمة أنماط عربية معروفة (انظر `ai_vocab` في السكربت):
«من المهم»، «من الجدير»، «جدير بالذكر»، «علاوة على ذلك»، «من ناحية أخرى»،
«فريد»، «استثنائي»، «نابض»، «يشير المراقبون»، «يرى الخبراء»…
**الهدف: صفر إشارات.** كل إشارة ترفع الخطر.

### ٣) Lexical — غنى المفردات (نسبة TTR)
`TTR = نوع فريد ÷ إجمالي كلمات`. النص الغني المتنوّع لدى البشر ~`≥ 0.35`.
النص المُعاد تدويره الآلي يتكرر بألفاظه.

| القيمة | الحكم |
|:------:|-------|
| `≥ 0.35` | غني → بشري 🟢 |
| `0.25–0.35` | متوسط → 🟡 |
| `< 0.25` | متكرر → نمط AI 🔴 |

**مؤشر مُساعِد:** وجود جمل قصيرة جداً (≤ كلمتين) بنسبة ملحوظة — علامة تحرير بشري.

---

## قراءة النتيجة

يُطبع `التقدير الإجمالي` كنسبة مئوية = احتساب عدد المؤشرات البشرية من ٤:
`(burstiness≥0.45) + (لا إشارات AI) + (TTR≥0.35) + (جمل قصيرة كافية)`.

| النتيجة | المعنى |
|:------:|--------|
| `٤/٤ (100%)` | قرأته مؤشرات كبشري — منخفض الخطر |
| `٣/٤ (75%)` | جيد، بقية تحسين اختياري |
| `≤ ٢/٤` | راجِع النص وحسّن قبل الإرسال |

> تذكّر: تقرير السكربت **تقدير إحصائي تقريبي**، لا فحص Turnitin الفعلي
> (وهو غير متاح للطلبة). النتيجة النهائية بنظام جامعتك.

---

## منهجية التحسين (متى كان الخطر مرتفعاً)

1. **كسر التماثل:** نوّع طول الجمل (قصيرة/متوسطة/طويلة) عمداً في كل فقرة.
2. **استبدال أنماط AI:** أزِل كل نمط في القائمة وبدِّله بصياغة بشرية
   (انظر مهارة `arabic-humanizer` لقائمة بدائل غنية).
3. **تخصيص المفردات:** استبدل العام المتكرر بمصطلح ميداني دقيق في المقام الأول.
4. **أضف بِصمتك:** تعليقاتك، أمثلتك، تحفظاتك — النبرة الشخصية تكسر البصمة.

---

## حدود الأداة (اقرأها قبل الاستخدام)

- **العربية فقط** بدرجة ثقة معقولة؛ موجهة للنصوص النثرية الأكاديمية.
- العناوين والحواشي وقوائم المراجع **لا تُحتسب** (كسلوك Turnitin).
- المؤشرات الثلاث **تقريبات**؛ Turnitin يستخدم نماذج محوِّلة أعمق وتدريباً ضخماً.
- النص **المحرَّر بأسلوب بشري** أصعب كشفاً — وهذا الأدق أخلاقياً للكتابة المشروعة.

---

## مثال حقيقي (مستند «النظرية الإدارية» — بعد التنظيف)

```
BURSTINESS : CV = 0.571 → بشري 🟢
PERPLEXITY : 0 إشارات AI → نظيف 🟢
LEXICAL    : TTR = 0.423 → غني 🟢
التقدير    : 4/4 مؤشرات بشرية (100%)
```

---

## البنية

```
ai-detection-probe/
├── SKILL.md                 # هذا الملف
└── scripts/
    └── turnitin_sim.py      # أداة الفحص (مستقلة ذاتياً)
```

## الرخصة

MIT — عبدالله العجيان (falconeye90). استخدم بحرية، ونسب عند الاقتباس.