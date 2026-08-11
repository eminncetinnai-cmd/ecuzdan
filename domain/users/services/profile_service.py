"""Investor profile service layer."""

import json
from typing import TYPE_CHECKING

from .profile_scoring_engine import scoring_engine

if TYPE_CHECKING:
    pass

class ProfileService:
    def __init__(self, repository=None):
        self.repository = repository

    def index_context(self, tenant_id, user_id):
        return {
            'active_profile': self.repository.get_active_profile(tenant_id, user_id),
            'profile_history': self.repository.list_history(tenant_id, user_id, limit=5),
        }

    def wizard_context(self):
        dimension_questions = {}
        for question in scoring_engine.questions.values():
            dimension_questions.setdefault(question['dimension'], []).append(question)
        return {
            'questions': dimension_questions,
            'current_step': 1,
            'total_steps': 7,
        }

    def questions_payload(self):
        return {
            'success': True,
            'questions': [
                {
                    'id': question['id'],
                    'dimension': question['dimension'],
                    'type': question['type'],
                    'question': question['question'],
                    'options': question['options'],
                    'explanation': question.get('explanation', ''),
                    'difficulty': question.get('difficulty', 'medium'),
                }
                for question in scoring_engine.questions.values()
            ],
        }

    def submit_answers(self, tenant_id, user_id, answers_data):
        if not answers_data:
            raise ValueError("Cevaplar bulunamadı")
        profile_result = scoring_engine.process_answers(answers_data)
        self.repository.deactivate_active_profiles(tenant_id, user_id)
        profile = self.repository.add_profile(
            tenant_id=tenant_id,
            user_id=user_id,
            literacy_score=profile_result['literacy_score'],
            capacity_score=profile_result['capacity_score'],
            tolerance_score=profile_result['tolerance_score'],
            behavioral_score=profile_result['behavioral_score'],
            experience_score=profile_result['experience_score'],
            final_risk_level=profile_result['final_risk_level'],
            confidence_score=profile_result['confidence_score'],
            risk_warnings=json.dumps(profile_result['risk_warnings']),
            validity_date=profile_result['validity_date'],
            profile_version='1.0',
            is_active=True,
        )
        self.repository.commit()
        for answer in answers_data:
            self.repository.add_answer(
                profile_id=profile.id,
                question_id=answer['question_id'],
                dimension=answer.get('dimension', ''),
                answer_value=answer['value'],
                answer_text=answer.get('text', ''),
                question_version='1.0',
            )
        self.repository.commit()
        return profile, profile_result

    def result_context(self, profile_id, tenant_id):
        profile = self.repository.get_profile(profile_id, tenant_id)
        if not profile:
            return None
        return {
            'profile': profile,
            'answers': self.repository.list_answers(profile_id),
            'portfolio_allocation': scoring_engine.get_portfolio_allocation(profile.final_risk_level),
        }

    def profile_payload(self, profile_id, tenant_id):
        context = self.result_context(profile_id, tenant_id)
        if not context:
            return None
        profile = context['profile']
        return {
            'id': profile.id,
            'literacy_score': profile.literacy_score,
            'capacity_score': profile.capacity_score,
            'tolerance_score': profile.tolerance_score,
            'behavioral_score': profile.behavioral_score,
            'experience_score': profile.experience_score,
            'final_risk_level': profile.final_risk_level,
            'confidence_score': profile.confidence_score,
            'risk_warnings': json.loads(profile.risk_warnings) if profile.risk_warnings else [],
            'test_date': profile.test_date.isoformat() if profile.test_date else None,
            'validity_date': profile.validity_date.isoformat() if profile.validity_date else None,
            'portfolio_allocation': context['portfolio_allocation'],
        }

    def history_payload(self, tenant_id, user_id):
        return [
            {
                'id': profile.id,
                'final_risk_level': profile.final_risk_level,
                'confidence_score': profile.confidence_score,
                'test_date': profile.test_date.isoformat() if profile.test_date else None,
                'validity_date': profile.validity_date.isoformat() if profile.validity_date else None,
                'is_active': profile.is_active,
            }
            for profile in self.repository.list_history(tenant_id, user_id)
        ]

    def rollback(self):
        self.repository.rollback()

