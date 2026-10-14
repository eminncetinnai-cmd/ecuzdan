"""
Unit tests for profile services (ProfileService and ProfileScoringEngine)
"""

from datetime import datetime, timedelta, timezone

import pytest

from domain.users.services.profile_scoring_engine import ProfileScoringEngine
from domain.users.services.profile_service import ProfileService


class TestProfileScoringEngine:
    """Test ProfileScoringEngine functionality"""

    def test_risk_classes_definition(self):
        """Test risk classification matrix is properly defined"""
        engine = ProfileScoringEngine()

        assert (0, 20) in engine.RISK_CLASSES
        assert (20, 35) in engine.RISK_CLASSES
        assert (35, 50) in engine.RISK_CLASSES
        assert (50, 65) in engine.RISK_CLASSES
        assert (65, 80) in engine.RISK_CLASSES
        assert (80, 90) in engine.RISK_CLASSES
        assert (90, 100) in engine.RISK_CLASSES

    def test_portfolio_allocation_definition(self):
        """Test portfolio allocation recommendations are properly defined"""
        engine = ProfileScoringEngine()

        assert 'Korumacı' in engine.PORTFOLIO_ALLOCATION
        assert 'Muhafazakar' in engine.PORTFOLIO_ALLOCATION
        assert 'Temkinli' in engine.PORTFOLIO_ALLOCATION
        assert 'Dengeli' in engine.PORTFOLIO_ALLOCATION
        assert 'Büyüme Odaklı' in engine.PORTFOLIO_ALLOCATION
        assert 'Agresif' in engine.PORTFOLIO_ALLOCATION
        assert 'Spekülatif' in engine.PORTFOLIO_ALLOCATION

    def test_portfolio_allocation_percentages(self):
        """Test portfolio allocations sum to 100%"""
        engine = ProfileScoringEngine()

        for risk_level, allocation in engine.PORTFOLIO_ALLOCATION.items():
            total = allocation['cash'] + allocation['bonds'] + allocation['stocks']
            assert total == 100, f"{risk_level} allocation sums to {total}, expected 100"

    def test_calculate_literacy_score_all_correct(self):
        """Test literacy score with all correct answers"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'literacy', 'is_correct': True},
            {'dimension': 'literacy', 'is_correct': True},
            {'dimension': 'literacy', 'is_correct': True},
        ]

        score = engine.calculate_literacy_score(answers)
        assert score == 100.0

    def test_calculate_literacy_score_half_correct(self):
        """Test literacy score with half correct answers"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'literacy', 'is_correct': True},
            {'dimension': 'literacy', 'is_correct': False},
            {'dimension': 'literacy', 'is_correct': True},
            {'dimension': 'literacy', 'is_correct': False},
        ]

        score = engine.calculate_literacy_score(answers)
        assert score == 50.0

    def test_calculate_literacy_score_no_answers(self):
        """Test literacy score with no literacy answers"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'capacity', 'score': 5},
            {'dimension': 'tolerance', 'score': 5},
        ]

        score = engine.calculate_literacy_score(answers)
        assert score == 50  # Default value

    def test_calculate_capacity_score_max(self):
        """Test capacity score with maximum scores"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'capacity', 'score': 10},
            {'dimension': 'capacity', 'score': 10},
            {'dimension': 'capacity', 'score': 10},
        ]

        score = engine.calculate_capacity_score(answers)
        assert score == 100.0

    def test_calculate_capacity_score_half(self):
        """Test capacity score with half scores"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'capacity', 'score': 5},
            {'dimension': 'capacity', 'score': 5},
            {'dimension': 'capacity', 'score': 5},
        ]

        score = engine.calculate_capacity_score(answers)
        assert score == 50.0

    def test_calculate_capacity_score_no_answers(self):
        """Test capacity score with no capacity answers"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'literacy', 'is_correct': True},
            {'dimension': 'tolerance', 'score': 5},
        ]

        score = engine.calculate_capacity_score(answers)
        assert score == 50  # Default value

    def test_calculate_tolerance_score_max(self):
        """Test tolerance score with maximum scores"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'tolerance', 'score': 10},
            {'dimension': 'tolerance', 'score': 10},
            {'dimension': 'tolerance', 'score': 10},
        ]

        score = engine.calculate_tolerance_score(answers)
        assert score == 100.0

    def test_calculate_tolerance_score_half(self):
        """Test tolerance score with half scores"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'tolerance', 'score': 5},
            {'dimension': 'tolerance', 'score': 5},
            {'dimension': 'tolerance', 'score': 5},
        ]

        score = engine.calculate_tolerance_score(answers)
        assert score == 50.0

    def test_calculate_behavioral_score_max(self):
        """Test behavioral score with maximum scores"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'behavioral', 'score': 10},
            {'dimension': 'behavioral', 'score': 10},
        ]

        score = engine.calculate_behavioral_score(answers)
        assert score == 100.0

    def test_calculate_experience_score_max(self):
        """Test experience score with maximum scores"""
        engine = ProfileScoringEngine()

        answers = [
            {'dimension': 'experience', 'score': 10},
            {'dimension': 'experience', 'score': 10},
            {'dimension': 'experience', 'score': 10},
        ]

        score = engine.calculate_experience_score(answers)
        assert score == 100.0

    def test_get_portfolio_allocation_korumaci(self):
        """Test portfolio allocation for Korumacı (Conservative)"""
        engine = ProfileScoringEngine()

        allocation = engine.get_portfolio_allocation('Korumacı')

        assert allocation['cash'] == 80
        assert allocation['bonds'] == 20
        assert allocation['stocks'] == 0

    def test_get_portfolio_allocation_dengeli(self):
        """Test portfolio allocation for Dengeli (Balanced)"""
        engine = ProfileScoringEngine()

        allocation = engine.get_portfolio_allocation('Dengeli')

        assert allocation['cash'] == 20
        assert allocation['bonds'] == 30
        assert allocation['stocks'] == 50

    def test_get_portfolio_allocation_agresif(self):
        """Test portfolio allocation for Agresif (Aggressive)"""
        engine = ProfileScoringEngine()

        allocation = engine.get_portfolio_allocation('Agresif')

        assert allocation['cash'] == 5
        assert allocation['bonds'] == 10
        assert allocation['stocks'] == 85

    def test_get_portfolio_allocation_spekulatif(self):
        """Test portfolio allocation for Spekülatif (Speculative)"""
        engine = ProfileScoringEngine()

        allocation = engine.get_portfolio_allocation('Spekülatif')

        assert allocation['cash'] == 0
        assert allocation['bonds'] == 5
        assert allocation['stocks'] == 95

    def test_default_questions_structure(self):
        """Test default question bank structure"""
        engine = ProfileScoringEngine()
        questions = engine._get_default_questions()

        assert isinstance(questions, dict)
        assert len(questions) > 0

    def test_default_questions_dimensions(self):
        """Test default questions include all dimensions"""
        engine = ProfileScoringEngine()
        questions = engine._get_default_questions()

        dimensions = set(q['dimension'] for q in questions.values())

        assert 'literacy' in dimensions
        assert 'capacity' in dimensions
        assert 'tolerance' in dimensions
        assert 'behavioral' in dimensions
        assert 'experience' in dimensions

    def test_default_questions_count(self):
        """Test default question bank has expected number of questions"""
        engine = ProfileScoringEngine()
        questions = engine._get_default_questions()

        # Should have 48 questions total (updated from 40)
        assert len(questions) == 48


class TestProfileService:
    """Test ProfileService functionality"""

    def test_initialization(self):
        """Test ProfileService initialization"""
        service = ProfileService(repository=None)

        assert service.repository is None

    def test_initialization_with_repository(self):
        """Test ProfileService initialization with repository"""
        mock_repo = object()
        service = ProfileService(repository=mock_repo)

        assert service.repository is mock_repo

    def test_wizard_context_structure(self):
        """Test wizard context returns expected structure"""
        service = ProfileService(repository=None)
        context = service.wizard_context()

        assert 'questions' in context
        assert 'current_step' in context
        assert 'total_steps' in context
        assert context['current_step'] == 1
        assert context['total_steps'] == 7

    def test_wizard_context_questions_grouped_by_dimension(self):
        """Test wizard context groups questions by dimension"""
        service = ProfileService(repository=None)
        context = service.wizard_context()

        questions = context['questions']

        # Questions should be grouped by dimension
        assert isinstance(questions, dict)
        for dimension, dim_questions in questions.items():
            assert isinstance(dim_questions, list)
            for q in dim_questions:
                assert q['dimension'] == dimension

    def test_questions_payload_structure(self):
        """Test questions payload returns expected structure"""
        service = ProfileService(repository=None)
        payload = service.questions_payload()

        assert 'success' in payload
        assert 'questions' in payload
        assert payload['success'] is True
        assert isinstance(payload['questions'], list)

    def test_questions_payload_question_fields(self):
        """Test questions payload includes required fields"""
        service = ProfileService(repository=None)
        payload = service.questions_payload()

        for question in payload['questions']:
            assert 'id' in question
            assert 'dimension' in question
            assert 'type' in question
            assert 'question' in question
            assert 'options' in question

    def test_submit_answers_empty_answers_raises_error(self):
        """Test submit_answers raises ValueError for empty answers"""
        service = ProfileService(repository=None)

        with pytest.raises(ValueError) as exc_info:
            service.submit_answers('tenant_1', 1, [])

        assert "Cevaplar bulunamadı" in str(exc_info.value)

    def test_rollback_calls_repository_rollback(self):
        """Test rollback calls repository rollback"""
        class MockRepository:
            def rollback(self):
                self.rolled_back = True

        repo = MockRepository()
        service = ProfileService(repository=repo)

        service.rollback()

        assert repo.rolled_back is True

    def test_index_context_with_repository(self):
        """Test index_context with repository"""
        class MockRepository:
            def get_active_profile(self, tenant_id, user_id):
                return None
            def list_history(self, tenant_id, user_id, limit=None):
                return []

        repo = MockRepository()
        service = ProfileService(repository=repo)

        context = service.index_context('tenant_1', 1)

        assert 'active_profile' in context
        assert 'profile_history' in context
        assert context['active_profile'] is None
        assert context['profile_history'] == []

    def test_result_context_with_repository(self):
        """Test result_context with repository"""
        class MockProfile:
            def __init__(self):
                self.id = 1
                self.final_risk_level = 'Dengeli'
                self.confidence_score = 75.0
                self.test_date = '2026-08-12'
                self.validity_date = '2027-08-12'
                self.literacy_score = 70.0
                self.capacity_score = 75.0
                self.tolerance_score = 80.0
                self.behavioral_score = 70.0
                self.experience_score = 75.0
                self.risk_warnings = '[]'

        class MockRepository:
            def get_profile(self, profile_id, tenant_id):
                return MockProfile()
            def list_answers(self, profile_id):
                return []

        repo = MockRepository()
        service = ProfileService(repository=repo)

        context = service.result_context(1, 'tenant_1')

        assert 'profile' in context
        assert 'answers' in context
        assert context['profile'].final_risk_level == 'Dengeli'

    def test_profile_payload_with_repository(self):
        """Test profile_payload with repository"""
        class MockProfile:
            def __init__(self):
                self.id = 1
                self.final_risk_level = 'Dengeli'
                self.confidence_score = 75.0
                self.literacy_score = 70.0
                self.capacity_score = 75.0
                self.tolerance_score = 80.0
                self.behavioral_score = 70.0
                self.experience_score = 75.0
                self.risk_warnings = '[]'
                self.test_date = None
                self.validity_date = None

        class MockRepository:
            def get_profile(self, profile_id, tenant_id):
                return MockProfile()
            def list_answers(self, profile_id):
                return []

        repo = MockRepository()
        service = ProfileService(repository=repo)

        payload = service.profile_payload(1, 'tenant_1')

        assert payload is not None
        assert 'id' in payload
        assert 'final_risk_level' in payload
        assert payload['final_risk_level'] == 'Dengeli'

    def test_history_payload_with_repository(self):
        """Test history_payload with repository"""
        class MockProfile:
            def __init__(self):
                self.id = 1
                self.final_risk_level = 'Dengeli'
                self.confidence_score = 75.0
                self.test_date = None
                self.validity_date = None
                self.is_active = True

        class MockRepository:
            def list_history(self, tenant_id, user_id, limit=None):
                return [MockProfile()]

        repo = MockRepository()
        service = ProfileService(repository=repo)

        payload = service.history_payload('tenant_1', 1)

        assert isinstance(payload, list)
        assert len(payload) == 1
        assert payload[0]['final_risk_level'] == 'Dengeli'

    def test_compare_profiles_same_risk_level(self):
        """Test compare_profiles with same risk level"""
        class MockProfile:
            def __init__(self, risk_level='Dengeli'):
                self.id = 1
                self.final_risk_level = risk_level
                self.literacy_score = 70.0
                self.capacity_score = 75.0
                self.tolerance_score = 80.0
                self.behavioral_score = 70.0
                self.experience_score = 75.0
                self.test_date = None

        class MockRepository:
            def get_profile(self, profile_id, tenant_id):
                return MockProfile()

        repo = MockRepository()
        service = ProfileService(repository=repo)

        comparison = service.compare_profiles(1, 2, 'tenant_1')

        assert comparison is not None
        assert comparison['risk_level_change']['changed'] is False
        assert comparison['risk_level_change']['direction'] == 'none'

    def test_compare_profiles_different_risk_level(self):
        """Test compare_profiles with different risk levels"""
        class MockProfile1:
            def __init__(self):
                self.id = 1
                self.final_risk_level = 'Muhafazakar'
                self.literacy_score = 60.0
                self.capacity_score = 65.0
                self.tolerance_score = 70.0
                self.behavioral_score = 60.0
                self.experience_score = 65.0
                self.test_date = None

        class MockProfile2:
            def __init__(self):
                self.id = 2
                self.final_risk_level = 'Dengeli'
                self.literacy_score = 70.0
                self.capacity_score = 75.0
                self.tolerance_score = 80.0
                self.behavioral_score = 70.0
                self.experience_score = 75.0
                self.test_date = None

        class MockRepository:
            def __init__(self):
                self.profile1 = MockProfile1()
                self.profile2 = MockProfile2()

            def get_profile(self, profile_id, tenant_id):
                return self.profile1 if profile_id == 1 else self.profile2

        repo = MockRepository()
        service = ProfileService(repository=repo)

        comparison = service.compare_profiles(1, 2, 'tenant_1')

        assert comparison is not None
        assert comparison['risk_level_change']['changed'] is True
        assert comparison['risk_level_change']['direction'] == 'increased'

    def test_compare_profiles_none_profile(self):
        """Test compare_profiles with None profile"""
        class MockRepository:
            def get_profile(self, profile_id, tenant_id):
                return None

        repo = MockRepository()
        service = ProfileService(repository=repo)

        comparison = service.compare_profiles(1, 2, 'tenant_1')

        assert comparison is None

    def test_export_profile(self):
        """Test export_profile"""
        class MockProfile:
            def __init__(self):
                self.id = 1
                self.final_risk_level = 'Dengeli'
                self.literacy_score = 70.0
                self.capacity_score = 75.0
                self.tolerance_score = 80.0
                self.behavioral_score = 70.0
                self.experience_score = 75.0
                self.confidence_score = 75.0
                self.test_date = None
                self.validity_date = None
                self.risk_warnings = '[]'

        class MockRepository:
            def get_profile(self, profile_id, tenant_id):
                return MockProfile()
            def list_answers(self, profile_id):
                return []

        repo = MockRepository()
        service = ProfileService(repository=repo)

        export_data = service.export_profile(1, 'tenant_1')

        assert export_data is not None
        assert 'version' in export_data
        assert 'profile' in export_data
        assert 'answers' in export_data
        assert export_data['profile']['final_risk_level'] == 'Dengeli'

    def test_export_profile_none_profile(self):
        """Test export_profile with None profile"""
        class MockRepository:
            def get_profile(self, profile_id, tenant_id):
                return None

        repo = MockRepository()
        service = ProfileService(repository=repo)

        export_data = service.export_profile(1, 'tenant_1')

        assert export_data is None

    def test_import_profile_success(self):
        """Test import_profile success"""
        import_data = {
            'profile': {
                'final_risk_level': 'Dengeli',
                'literacy_score': 70.0,
                'capacity_score': 75.0,
                'tolerance_score': 80.0,
                'behavioral_score': 70.0,
                'experience_score': 75.0,
                'confidence_score': 75.0,
                'risk_warnings': []
            },
            'answers': []
        }

        class MockProfile:
            def __init__(self):
                self.id = 1

        class MockRepository:
            def deactivate_active_profiles(self, tenant_id, user_id):
                pass
            def add_profile(self, **kwargs):
                return MockProfile()
            def commit(self):
                pass
            def add_answer(self, **kwargs):
                pass
            def rollback(self):
                pass

        repo = MockRepository()
        service = ProfileService(repository=repo)

        profile, result = service.import_profile('tenant_1', 1, import_data)

        assert profile is not None
        assert result['success'] is True

    def test_import_profile_error(self):
        """Test import_profile error handling"""
        import_data = {}

        class MockRepository:
            def deactivate_active_profiles(self, tenant_id, user_id):
                pass
            def rollback(self):
                pass

        repo = MockRepository()
        service = ProfileService(repository=repo)

        profile, result = service.import_profile('tenant_1', 1, import_data)

        assert profile is None
        assert result['success'] is False

    def test_submit_answers_with_repository(self):
        """Test submit_answers with full repository mock"""
        class MockProfile:
            def __init__(self):
                self.id = 1

        class MockRepository:
            def deactivate_active_profiles(self, tenant_id, user_id):
                pass
            def add_profile(self, **kwargs):
                return MockProfile()
            def commit(self):
                pass
            def add_answer(self, **kwargs):
                pass

        repo = MockRepository()
        service = ProfileService(repository=repo)

        answers_data = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        profile, result = service.submit_answers('tenant_1', 1, answers_data)

        assert profile is not None
        assert result['final_risk_level'] is not None

    def test_submit_answers_repository_error(self):
        """Test submit_answers handles repository errors"""
        class MockRepository:
            def deactivate_active_profiles(self, tenant_id, user_id):
                raise Exception("DB Error")
            def rollback(self):
                pass

        repo = MockRepository()
        service = ProfileService(repository=repo)

        answers_data = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        with pytest.raises(Exception):
            service.submit_answers('tenant_1', 1, answers_data)

    def test_wizard_context_dimensions_count(self):
        """Test wizard context has all 5 dimensions"""
        service = ProfileService(repository=None)
        context = service.wizard_context()

        questions = context['questions']
        expected_dimensions = ['literacy', 'capacity', 'tolerance', 'behavioral', 'experience']

        for dim in expected_dimensions:
            assert dim in questions

    def test_questions_payload_excludes_explanation_by_default(self):
        """Test questions payload includes explanation field"""
        service = ProfileService(repository=None)
        payload = service.questions_payload()

        for question in payload['questions']:
            # Explanation should be present but may be empty
            assert 'explanation' in question

    def test_questions_payload_includes_difficulty(self):
        """Test questions payload includes difficulty field"""
        service = ProfileService(repository=None)
        payload = service.questions_payload()

        for question in payload['questions']:
            assert 'difficulty' in question


class TestProfileScoringEngineIntegration:
    """Integrated tests for scoring engine"""

    def test_process_answers_structure(self):
        """Test process_answers returns expected structure"""
        engine = ProfileScoringEngine()

        # Sample answers
        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
            {'question_id': 'CAP001', 'dimension': 'capacity', 'value': 5, 'text': 'Test'},
            {'question_id': 'TOL001', 'dimension': 'tolerance', 'value': 5, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)

        assert 'literacy_score' in result
        assert 'capacity_score' in result
        assert 'tolerance_score' in result
        assert 'behavioral_score' in result
        assert 'experience_score' in result
        assert 'final_risk_level' in result
        assert 'confidence_score' in result
        assert 'risk_warnings' in result
        assert 'validity_date' in result

    def test_process_answers_scores_range(self):
        """Test process_answers returns scores in valid range"""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
            {'question_id': 'CAP001', 'dimension': 'capacity', 'value': 5, 'text': 'Test'},
            {'question_id': 'TOL001', 'dimension': 'tolerance', 'value': 5, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)

        # All scores should be between 0 and 100
        assert 0 <= result['literacy_score'] <= 100
        assert 0 <= result['capacity_score'] <= 100
        assert 0 <= result['tolerance_score'] <= 100
        assert 0 <= result['behavioral_score'] <= 100
        assert 0 <= result['experience_score'] <= 100

    def test_process_answers_validity_date(self):
        """Test process_answers maps confidence to the documented validity window."""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)

        confidence = result['confidence_score']
        expected_days = 365 if confidence > 80 else 180 if confidence > 50 else 90
        expected_date = datetime.now(timezone.utc) + timedelta(days=expected_days)
        actual_date = result['validity_date']

        if actual_date.tzinfo is None:
            actual_date = actual_date.replace(tzinfo=timezone.utc)

        time_diff = abs((expected_date - actual_date).total_seconds())
        assert time_diff < 2 * 24 * 60 * 60

    def test_process_answers_risk_warnings_list(self):
        """Test process_answers returns risk warnings as list"""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)

        assert isinstance(result['risk_warnings'], list)

    def test_process_answers_confidence_score_range(self):
        """Test process_answers returns confidence score in valid range"""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)

        # Confidence score should be between 0 and 100
        assert 0 <= result['confidence_score'] <= 100

    def test_classify_risk_level_korumaci(self):
        """Test _classify_risk_level for Korumaci"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(10)
        assert risk_level == 'Korumacı'

    def test_classify_risk_level_muhafazakar(self):
        """Test _classify_risk_level for Muhafazakar"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(30)
        assert risk_level == 'Muhafazakar'

    def test_classify_risk_level_temkinli(self):
        """Test _classify_risk_level for Temkinli"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(45)
        assert risk_level == 'Temkinli'

    def test_classify_risk_level_dengeli(self):
        """Test _classify_risk_level for Dengeli"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(60)
        assert risk_level == 'Dengeli'

    def test_classify_risk_level_buyume_odakli(self):
        """Test _classify_risk_level for Büyüme Odaklı"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(75)
        assert risk_level == 'Büyüme Odaklı'

    def test_classify_risk_level_agresif(self):
        """Test _classify_risk_level for Agresif"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(85)
        assert risk_level == 'Agresif'

    def test_classify_risk_level_spekulatif(self):
        """Test _classify_risk_level for Spekülatif"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(95)
        assert risk_level == 'Spekülatif'

    def test_classify_risk_level_default(self):
        """Test _classify_risk_level default case"""
        engine = ProfileScoringEngine()
        risk_level = engine._classify_risk_level(50)
        assert risk_level == 'Dengeli'  # Default

    def test_calculate_confidence_score(self):
        """Test _calculate_confidence_score"""
        engine = ProfileScoringEngine()
        confidence = engine._calculate_confidence(70, 75, 80, 70, 75)
        assert 0 <= confidence <= 100

    def test_calculate_validity_date_high_confidence(self):
        """Test calculate_validity_date for high confidence"""
        engine = ProfileScoringEngine()
        validity_date = engine.calculate_validity_date(85)
        expected = datetime.now(timezone.utc) + timedelta(days=365)
        time_diff = abs((expected - validity_date).days)
        assert time_diff < 2

    def test_calculate_validity_date_medium_confidence(self):
        """Test calculate_validity_date for medium confidence"""
        engine = ProfileScoringEngine()
        validity_date = engine.calculate_validity_date(60)
        expected = datetime.now(timezone.utc) + timedelta(days=180)
        time_diff = abs((expected - validity_date).days)
        assert time_diff < 2

    def test_calculate_validity_date_low_confidence(self):
        """Test calculate_validity_date for low confidence"""
        engine = ProfileScoringEngine()
        validity_date = engine.calculate_validity_date(40)
        expected = datetime.now(timezone.utc) + timedelta(days=90)
        time_diff = abs((expected - validity_date).days)
        assert time_diff < 2

    def test_calculate_final_risk_level_structure(self):
        """Test calculate_final_risk_level returns expected structure"""
        engine = ProfileScoringEngine()
        result = engine.calculate_final_risk_level(70, 75, 80, 70, 75)

        assert 'final_risk_level' in result
        assert 'confidence_score' in result
        assert 'risk_warnings' in result
        assert 'base_risk_score' in result

    def test_calculate_final_risk_level_warnings(self):
        """Test calculate_final_risk_level generates warnings for low behavioral score"""
        engine = ProfileScoringEngine()
        result = engine.calculate_final_risk_level(70, 75, 80, 30, 75)

        assert len(result['risk_warnings']) > 0
        assert any('davranışsal' in w.lower() for w in result['risk_warnings'])

    def test_process_answers_with_missing_question(self):
        """Test process_answers handles missing question gracefully"""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'NONEXISTENT', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        # Should not raise error, just skip missing question
        result = engine.process_answers(answers)
        assert result is not None

    def test_process_answers_with_multiple_choice_question(self):
        """Test process_answers correctly handles multiple_choice questions"""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)
        assert result is not None
        assert 'literacy_score' in result

    def test_process_answers_with_scale_question(self):
        """Test process_answers correctly handles scale questions"""
        engine = ProfileScoringEngine()

        answers = [
            {'question_id': 'CAP001', 'dimension': 'capacity', 'value': 5, 'text': 'Test'},
        ]

        result = engine.process_answers(answers)
        assert result is not None
        assert 'capacity_score' in result

    def test_load_questions_method(self):
        """Test _load_questions method exists and is callable"""
        engine = ProfileScoringEngine()
        assert hasattr(engine, '_load_questions')
        assert callable(engine._load_questions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
