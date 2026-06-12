# -*- coding: utf-8 -*-
"""تطبيع النص العربي ومطابقة سؤال المستخدم مع مواضيع قاعدة المعرفة."""

import re

from faq_data import TOPICS

# التشكيل والتطويل
_DIACRITICS = re.compile(r"[ً-ْٰـ]")
# أي رمز غير حرف/رقم يتحول لمسافة
_NON_WORD = re.compile(r"[^\wء-ي]+")


def normalize(text: str) -> str:
    """تطبيع النص العربي: إزالة التشكيل وتوحيد الألف والتاء المربوطة والياء."""
    text = _DIACRITICS.sub("", text)
    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ة", "ه")
        .replace("ى", "ي")
    )
    text = _NON_WORD.sub(" ", text)
    return " ".join(text.split()).lower()


def _strip_al(token: str) -> str:
    """إزالة "ال" التعريف و"و" العطف من بداية الكلمة لتسهيل المطابقة."""
    if token.startswith("وال") and len(token) > 4:
        return token[3:]
    if token.startswith("ال") and len(token) > 3:
        return token[2:]
    if token.startswith("لل") and len(token) > 3:
        return token[2:]
    return token


def _contains_phrase(text: str, phrase: str) -> bool:
    """هل العبارة موجودة في النص ككلمات كاملة (لا كجزء من كلمة)؟"""
    return f" {phrase} " in f" {text} "


def find_answer(question: str):
    """يرجع الموضوع الأكثر تطابقاً مع السؤال، أو None إذا لم يُفهم السؤال.

    المطابقة على نسختين من السؤال: كما هو، وبعد إزالة "ال" التعريف من كلماته،
    والعبارات الأطول لها وزن أعلى.
    """
    norm = normalize(question)
    if not norm:
        return None
    stripped = " ".join(_strip_al(t) for t in norm.split())

    best_topic, best_score = None, 0
    for topic in TOPICS:
        score = 0
        for keyword in topic["keywords"]:
            kw = normalize(keyword)
            if _contains_phrase(norm, kw) or _contains_phrase(stripped, kw):
                score += len(kw.split())  # العبارات الأطول أدق فوزنها أعلى
        if score > best_score:
            best_topic, best_score = topic, score
    return best_topic
