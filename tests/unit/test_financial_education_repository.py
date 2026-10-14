"""
Unit Tests — Financial Education Repository
repositories/financial_education_repository.py metodlarını test eder.
"""

import pytest

from models import db
from repositories.financial_education_repository import FinancialEducationRepository


@pytest.fixture
def edu_repo(app):
    return FinancialEducationRepository(database=db)


@pytest.mark.unit
def test_record_quiz_attempt_and_history(edu_repo, app):
    tenant = 'edu-test-tenant'
    user_id = 991

    attempt = edu_repo.record_quiz_attempt(
        user_id=user_id,
        tenant_id=tenant,
        difficulty='beginner',
        score=85,
        total_questions=10,
        correct_answers=8
    )
    edu_repo.commit()

    assert attempt.id is not None
    assert attempt.score == 85

    history = edu_repo.get_quiz_history(user_id=user_id, tenant_id=tenant)
    assert len(history) >= 1
    assert history[0].difficulty == 'beginner'

    all_attempts = edu_repo.get_all_quiz_attempts(user_id=user_id, tenant_id=tenant)
    assert len(all_attempts) >= 1


@pytest.mark.unit
def test_save_or_update_progress(edu_repo, app):
    tenant = 'edu-test-tenant-2'
    user_id = 992
    topic = 'budgeting_basics'

    # İlk kayıt
    prog = edu_repo.save_or_update_progress(
        user_id=user_id,
        tenant_id=tenant,
        topic=topic,
        phase='beginner',
        completed=False,
        progress_percent=50
    )
    edu_repo.commit()
    assert prog.progress_percent == 50
    assert prog.completed is False

    # Güncelleme - tamamlandı
    updated = edu_repo.save_or_update_progress(
        user_id=user_id,
        tenant_id=tenant,
        topic=topic,
        phase='beginner',
        completed=True,
        progress_percent=100
    )
    edu_repo.commit()
    assert updated.completed is True
    assert updated.progress_percent == 100

    # Liste ve sayı kontrolü
    p_list = edu_repo.get_user_progress_list(user_id=user_id, tenant_id=tenant)
    assert len(p_list) == 1

    completed_count = edu_repo.count_completed_progress(user_id=user_id, tenant_id=tenant)
    assert completed_count == 1


@pytest.mark.unit
def test_award_achievement_idempotency(edu_repo, app):
    tenant = 'edu-test-tenant-3'
    user_id = 993

    first = edu_repo.award_achievement_if_not_exists(user_id, tenant, 'first_steps')
    edu_repo.commit()
    assert first is not None

    # İkinci çağrıda aynı rozet tekrar eklenmez (None döner)
    second = edu_repo.award_achievement_if_not_exists(user_id, tenant, 'first_steps')
    edu_repo.commit()
    assert second is None

    achievements = edu_repo.get_user_achievements(user_id, tenant)
    assert len(achievements) == 1
    assert achievements[0].achievement_type == 'first_steps'
