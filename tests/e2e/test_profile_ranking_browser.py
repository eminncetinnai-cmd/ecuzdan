"""Browser acceptance coverage for ranking questions in the profile wizard."""

import os

import pytest

pytestmark = pytest.mark.e2e
BASE_URL = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')


def test_profile_ranking_question_uses_ordered_controls(phase4_authenticated_page):
    page = phase4_authenticated_page
    page.goto(f'{BASE_URL}/profile/start', wait_until='domcontentloaded')
    page.locator('#wizard-container').wait_for(state='visible', timeout=15000)
    page.locator('#btn-next').click()
    page.locator('#question-RNK001').wait_for(state='visible', timeout=15000)

    ranking = page.locator('#question-RNK001 .ranking-option')
    assert ranking.count() == 4
    assert page.locator('#question-RNK001 input[type="radio"]').count() == 0
    assert page.locator('#question-RNK001 .ranking-options[role="list"]').count() == 1
    assert page.locator('#question-RNK001 .ranking-move-btn').count() == 8

    before = ranking.nth(0).locator('.ranking-option-text').inner_text()
    ranking.nth(0).locator('.ranking-move-btn').nth(1).click()
    after = page.locator('#question-RNK001 .ranking-option').nth(1).locator('.ranking-option-text').inner_text()
    assert before == after
