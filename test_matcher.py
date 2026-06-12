# -*- coding: utf-8 -*-
"""اختبارات المطابقة والتطبيع — تعمل بدون اتصال بتليجرام: python test_matcher.py"""

from matcher import find_answer, normalize


def test_normalize():
    assert normalize("الإجَازَةُ") == "الاجازه"
    assert normalize("مُوَظَّف") == "موظف"
    assert normalize("مستشفى") == "مستشفي"
    assert normalize("كم؟ ساعات!! العمل...") == "كم ساعات العمل"


def test_matching():
    cases = {
        "كم ساعات العمل في اليوم؟": "ساعات العمل",
        "كم يوم الإجازة السنوية؟": "الإجازات",
        "كيف تحسب مكافأة نهاية الخدمة": "مكافأة نهاية الخدمة",
        "صاحب العمل فصلني بدون سبب": "الفصل التعسفي",
        "ابي اعرف عن الطلاق": "الطلاق والخلع",
        "لمن تكون حضانة الأطفال بعد الطلاق؟": "الحضانة",
        "كيف اعترض على مخالفة ساهر": "المخالفات المرورية",
        "المستأجر رافض يدفع الايجار": "الإيجار",
        "شخص يبتزني بصوري": "الجرائم المعلوماتية",
        "عندي حكم قضائي ابي انفذه": "التنفيذ",
        "استلمت شيك بدون رصيد": "الشيك بدون رصيد",
        "ابغى اأسس شركة ذات مسؤولية محدودة": "تأسيس الشركات",
        "المتجر رافض يرجع لي فلوسي استرجاع": "حماية المستهلك",
        "كيف اقسم تركة الوالد": "الورث والتركات",
    }
    for question, expected_title in cases.items():
        topic = find_answer(question)
        assert topic is not None, f"ما لقى جواب للسؤال: {question}"
        assert expected_title in topic["title"], (
            f"السؤال: {question}\nالمتوقع: {expected_title}\nالنتيجة: {topic['title']}"
        )


def test_no_match():
    for question in ["مرحبا", "كيف الجو اليوم؟", "abcdef xyz", "؟؟؟", ""]:
        assert find_answer(question) is None, f"كان المفروض ما يلقى جواب لـ: {question}"


if __name__ == "__main__":
    test_normalize()
    test_matching()
    test_no_match()
    print("✅ كل الاختبارات نجحت")
