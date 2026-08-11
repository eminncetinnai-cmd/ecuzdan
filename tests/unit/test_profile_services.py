"""
Unit tests for profile services (ProfileService and ProfileScoringEngine)
"""

import pytest
from datetime import datetime, timedelta, timezone
from domain.users.services.profile_service import ProfileService
from domain.users.services.profile_scoring_engine import ProfileScoringEngine


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
        
        # Should have 40 questions total (10 literacy + 10 capacity + 10 tolerance + 5 behavioral + 5 experience)
        assert len(questions) == 40


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
        """Test process_answers sets validity date 1 year in future"""
        engine = ProfileScoringEngine()
        
        answers = [
            {'question_id': 'LIT001', 'dimension': 'literacy', 'value': 1, 'text': 'Test'},
        ]
        
        result = engine.process_answers(answers)
        
        expected_date = datetime.now(timezone.utc) + timedelta(days=365)
        actual_date = result['validity_date']
        
        # Should be approximately 1 year from now
        time_diff = abs((expected_date - actual_date).days)
        assert time_diff < 2  # Allow 2 days variance

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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
