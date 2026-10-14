"""Investor profile risk scoring calculations and dimension analyzers."""

from datetime import datetime, timedelta, timezone

DEFAULT_RISK_CLASSES = {
    (0, 20): 'Korumacı',
    (20, 35): 'Muhafazakar',
    (35, 50): 'Temkinli',
    (50, 65): 'Dengeli',
    (65, 80): 'Büyüme Odaklı',
    (80, 90): 'Agresif',
    (90, 100): 'Spekülatif',
}


def calculate_literacy_score(answers):
    """Finansal okuryazarlık skoru (0-100)"""
    literacy_answers = [
        answer for answer in answers
        if answer['dimension'] == 'literacy' and answer.get('is_correct') is not None
    ]
    if not literacy_answers:
        return 50  # Varsayılan

    correct_count = sum(1 for a in literacy_answers if a['is_correct'])
    total_count = len(literacy_answers)

    return (correct_count / total_count) * 100


def calculate_capacity_score(answers):
    """Risk kapasitesi skoru (0-100)"""
    capacity_answers = [a for a in answers if a['dimension'] == 'capacity']
    if not capacity_answers:
        return 50  # Varsayılan

    total_score = sum(a['score'] for a in capacity_answers)
    max_possible = len(capacity_answers) * 10

    return (total_score / max_possible) * 100


def calculate_tolerance_score(answers):
    """Risk toleransı skoru (0-100)"""
    tolerance_answers = [a for a in answers if a['dimension'] == 'tolerance']
    if not tolerance_answers:
        return 50  # Varsayılan

    total_score = sum(a['score'] for a in tolerance_answers)
    max_possible = len(tolerance_answers) * 10

    return (total_score / max_possible) * 100


def calculate_behavioral_score(answers):
    """Davranışsal finans skoru (0-100)"""
    behavioral_answers = [a for a in answers if a['dimension'] == 'behavioral']
    if not behavioral_answers:
        return 50  # Varsayılan

    total_score = sum(a['score'] for a in behavioral_answers)
    max_possible = len(behavioral_answers) * 10

    return (total_score / max_possible) * 100


def calculate_experience_score(answers):
    """Yatırım deneyimi skoru (0-100)"""
    experience_answers = [a for a in answers if a['dimension'] == 'experience']
    if not experience_answers:
        return 50  # Varsayılan

    total_score = sum(a['score'] for a in experience_answers)
    max_possible = len(experience_answers) * 10

    return (total_score / max_possible) * 100


def classify_risk_level(score, risk_classes=None):
    """Risk skorunu sınıfa dönüştür"""
    classes = risk_classes or DEFAULT_RISK_CLASSES
    for (min_score, max_score), risk_class in classes.items():
        if min_score <= score < max_score:
            return risk_class
    return 'Dengeli'  # Varsayılan


def calculate_confidence(literacy, capacity, tolerance, behavioral, experience):
    """Güven skoru hesaplama"""
    scores = [literacy, capacity, tolerance, behavioral, experience]
    avg_score = sum(scores) / len(scores)
    variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
    consistency_score = max(0, 100 - variance)
    data_adequacy_score = experience  # Deneyim veri yeterliliğini gösterir

    return (consistency_score + data_adequacy_score) / 2


def calculate_final_risk_level(literacy, capacity, tolerance, behavioral, experience, risk_classes=None):
    """Nihai risk seviyesi hesaplama"""
    # Temel risk skoru
    base_risk = (capacity + tolerance) / 2

    # Okuryazarlık düzeltmesi
    if literacy < 40:
        base_risk *= 0.5
    elif literacy < 60:
        base_risk *= 0.7

    # Kapasite baskınlığı
    if capacity < tolerance - 20:
        base_risk = capacity

    # Davranışsal risk uyarısı
    warnings = []
    if behavioral < 40:
        warnings.append("Yüksek davranışsal risk tespit edildi")
        base_risk *= 0.8

    # Deneyim düzeltmesi
    if experience < 30 and base_risk > 60:
        base_risk = 50

    # Sınıflandırma
    risk_level = classify_risk_level(base_risk, risk_classes)
    confidence = calculate_confidence(literacy, capacity, tolerance, behavioral, experience)

    return {
        'final_risk_level': risk_level,
        'confidence_score': confidence,
        'risk_warnings': warnings,
        'base_risk_score': base_risk,
    }


def calculate_validity_date(confidence_score):
    """Profil geçerlilik süresi hesaplama"""
    if confidence_score > 80:
        return datetime.now(timezone.utc) + timedelta(days=365)
    elif confidence_score > 50:
        return datetime.now(timezone.utc) + timedelta(days=180)
    else:
        return datetime.now(timezone.utc) + timedelta(days=90)


def validate_ranking_answer(question, value):
    """Validate and score a ranking answer without trusting client ordering."""
    if not isinstance(value, list):
        raise ValueError(f"Ranking answer must be a list: {question['id']}")

    option_texts = [str(option.get('text', '')) for option in question.get('options', [])]
    submitted = [str(item) for item in value]
    if len(submitted) != len(option_texts) or set(submitted) != set(option_texts):
        raise ValueError(f"Ranking answer contains invalid or duplicate options: {question['id']}")

    correct_order = question.get('correct_order')
    if correct_order:
        expected = [str(item) for item in correct_order]
        if submitted == expected:
            return 10, True
        return 0, False

    # Questions without an answer key remain neutral instead of distorting a dimension score.
    return 5, None
