"""Regression coverage for profile ranking questions."""

import json

import pytest

from domain.users.services.profile_scoring_engine import ProfileScoringEngine
from domain.users.services.profile_service import ProfileService


class TestProfileRankingScoring:
    def test_ranking_question_is_exposed_with_order_contract(self):
        question = ProfileScoringEngine()._get_default_questions()['RNK001']

        assert question['type'] == 'ranking'
        assert len(question['options']) == len(question['correct_order'])

    def test_correct_ranking_answer_scores_full_points(self):
        engine = ProfileScoringEngine()
        question = engine._get_default_questions()['RNK001']

        score, is_correct = engine._validate_ranking_answer(question, question['correct_order'])

        assert score == 10
        assert is_correct is True

    def test_incorrect_ranking_answer_is_valid_but_not_correct(self):
        engine = ProfileScoringEngine()
        question = engine._get_default_questions()['RNK001']
        submitted = [option['text'] for option in question['options']]

        score, is_correct = engine._validate_ranking_answer(question, submitted)

        assert score == 0
        assert is_correct is False

    def test_ranking_answer_rejects_duplicates_or_unknown_options(self):
        engine = ProfileScoringEngine()
        question = engine._get_default_questions()['RNK001']

        with pytest.raises(ValueError, match='invalid or duplicate'):
            engine._validate_ranking_answer(question, [question['options'][0]['text']] * 4)

    def test_literacy_score_ignores_unscored_ranking_answers(self):
        engine = ProfileScoringEngine()

        score = engine.calculate_literacy_score([
            {'dimension': 'literacy', 'is_correct': True},
            {'dimension': 'literacy', 'is_correct': None},
        ])

        assert score == 100.0


class TestProfileRankingPersistence:
    def test_profile_service_persists_ranking_order_separately(self):
        captured_answers = []

        class MockProfile:
            id = 42

        class MockRepository:
            def deactivate_active_profiles(self, tenant_id, user_id):
                pass

            def add_profile(self, **kwargs):
                return MockProfile()

            def commit(self):
                pass

            def add_answer(self, **kwargs):
                captured_answers.append(kwargs)

        engine = ProfileScoringEngine()
        order = engine._get_default_questions()['RNK001']['correct_order']
        service = ProfileService(repository=MockRepository())

        service.submit_answers('tenant_1', 1, [{
            'question_id': 'RNK001',
            'dimension': 'literacy',
            'value': order,
            'text': ' → '.join(order),
        }])

        assert len(captured_answers) == 1
        assert captured_answers[0]['answer_value'] == 5
        assert json.loads(captured_answers[0]['answer_order']) == order
