"""Regression tests for notification wiring and financial education quiz flow."""

from database.seeds.quiz_questions_seed import seed_quiz_questions
from models import QuizQuestion


def test_notification_api_is_wired_and_returns_payload(authenticated_client):
    response = authenticated_client.get("/notifications/api")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert isinstance(payload["items"], list)
    assert isinstance(payload["unread"], int)


def test_quiz_start_has_seeded_questions(authenticated_client, app):
    with app.app_context():
        seed_quiz_questions()
        assert QuizQuestion.query.filter_by(is_active=True).count() > 0
    response = authenticated_client.post(
        "/api/quiz/start",
        json={"difficulty": "beginner"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["questions"]
    assert payload["quiz_id"]


def test_quiz_submit_persists_attempt(authenticated_client, app):
    with app.app_context():
        seed_quiz_questions()
        question = QuizQuestion.query.filter_by(difficulty="beginner", is_active=True).first()
        assert question is not None
        question_id = question.id
        correct_answer = question.correct_answer
    response = authenticated_client.post(
        "/api/quiz/submit",
        json={
            "answers": {str(question_id): correct_answer},
            "difficulty": "beginner",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["total_count"] == 1


def test_financial_education_quiz_view_renders(authenticated_client):
    response = authenticated_client.get("/financial_education?view=quiz")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "startQuiz('beginner')" in body
    assert "Quiz" in body


def test_header_order_and_standard_controls_render(authenticated_client):
    response = authenticated_client.get("/financial_education?view=quiz")
    body = response.get_data(as_text=True)
    assert body.index("time-display") < body.index("global-search-wrapper")
    assert body.index("global-search-wrapper") < body.index("quick-actions-btn")
    assert body.index("openNotificationModal") < body.index("dropdown-theme-control")
    assert "header-control logout-btn-header" in body


def test_sidebar_rail_and_navigation_parity(authenticated_client):
    response = authenticated_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    # 1. Head localStorage restoration & mode attribute
    assert "ecuzdan_sidebar_mode" in body
    assert "data-sidebar-mode" in body

    # 2. Icon rail toggle buttons & icons
    assert "sidebarRailToggleBtn" in body
    assert "sidebarRailFooterBtn" in body
    assert "rail-icon-collapse" in body
    assert "rail-icon-expand" in body
    assert "Ctrl+B" in body

    # 3. Single-source navigation parity across desktop and mobile
    assert body.count('href="/plans"') >= 2
    assert body.count('href="/transactions"') >= 2
    assert body.count('href="/reconciliation"') >= 2
    assert "nav-link-label" in body

    # 4. Correct link order: /plans between /transactions and /reconciliation
    overview_start = body.index('id="overview-section"')
    assert overview_start != -1
    overview_chunk = body[overview_start:overview_start + 4000]
    assert overview_chunk.index('href="/transactions"') < overview_chunk.index('href="/plans"')
    assert overview_chunk.index('href="/plans"') < overview_chunk.index('href="/reconciliation"')

