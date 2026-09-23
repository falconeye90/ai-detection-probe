#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI-style pattern lexicon (Arabic + English), severity-tagged.

Severity, and why it is not a flat list:

  STRONG (1.0) — multi-word discourse markers. These are the highest-precision
      signal computable without a model: an unedited human draft rarely opens
      three paragraphs with the same connector pair.
  WEAK (0.5) — single lexical items that are perfectly legitimate in human
      writing ("يعتبر", "pivotal"). They only carry weight when they *cluster*,
      so they are scored at half and capped in the engine.

The severities are heuristic, chosen for precision-over-recall; they are NOT
calibrated against Turnitin or any other detector (see SKILL.md).

Matching rules live in the engine:
  * Arabic: whole-word boundaries over the Arabic block, so "فريد" never matches
    inside a proper name like "فريدريك".
  * English: case-insensitive whole-word / whole-phrase boundaries.
"""

STRONG_AR = [
    "بالإضافة إلى ذلك", "علاوة على ذلك", "جدير بالذكر", "من ناحية أخرى",
    "من الجدير بالذكر", "من المهم الإشارة", "تجدر الإشارة", "في هذا السياق",
    "في ضوء ما سبق", "من المهم أن نلاحظ", "لا سيما وأن", "ومن ثم فإن",
    "يسلط الضوء على", "خطوة في الاتجاه الصحيح", "آفاق واعدة", "المستقبل مشرق",
    "يشير المراقبون إلى", "يرى الخبراء أن", "على المستوى", "ليس فقط",
    "لا يقتصر الأمر على", "من المميز أن", "مما يعكس",
]

WEAK_AR = [
    "من المهم", "من الجدير", "يعتبر", "يمثل", "يتميز", "فريد", "استثنائي",
    "نابض", "شمل ذلك", "محوري", "جوهري", "بالغ الأهمية",
]

STRONG_EN = [
    "it is important to note", "it is worth noting", "due to the fact that",
    "in conclusion", "not only", "but also", "at the end of the day",
    "when it comes to", "a testament to", "stands as a", "in today's",
    "in the realm of", "plays a pivotal role", "delve into", "dive into",
]

WEAK_EN = [
    "additionally", "furthermore", "moreover", "in order to", "landscape",
    "testament", "pivotal", "groundbreaking", "underscores", "renowned",
    "boasts", "vibrant", "intricate", "fostering", "game-changer", "deep dive",
    "holistic", "seamless", "robust",
]


def patterns_for(lang: str):
    """Return [(phrase, severity), ...] for 'ar' or 'en'."""
    if lang == "ar":
        return [(p, 1.0) for p in STRONG_AR] + [(p, 0.5) for p in WEAK_AR]
    return [(p, 1.0) for p in STRONG_EN] + [(p, 0.5) for p in WEAK_EN]
