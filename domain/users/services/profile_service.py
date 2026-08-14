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

    def compare_profiles(self, profile_id1, profile_id2, tenant_id):
        """Compare two profiles and return differences"""
        profile1 = self.repository.get_profile(profile_id1, tenant_id)
        profile2 = self.repository.get_profile(profile_id2, tenant_id)
        
        if not profile1 or not profile2:
            return None
        
        comparison = {
            'profile1': {
                'id': profile1.id,
                'final_risk_level': profile1.final_risk_level,
                'literacy_score': profile1.literacy_score,
                'capacity_score': profile1.capacity_score,
                'tolerance_score': profile1.tolerance_score,
                'behavioral_score': profile1.behavioral_score,
                'experience_score': profile1.experience_score,
                'test_date': profile1.test_date.isoformat() if profile1.test_date else None,
            },
            'profile2': {
                'id': profile2.id,
                'final_risk_level': profile2.final_risk_level,
                'literacy_score': profile2.literacy_score,
                'capacity_score': profile2.capacity_score,
                'tolerance_score': profile2.tolerance_score,
                'behavioral_score': profile2.behavioral_score,
                'experience_score': profile2.experience_score,
                'test_date': profile2.test_date.isoformat() if profile2.test_date else None,
            },
            'differences': {
                'final_risk_level': profile1.final_risk_level != profile2.final_risk_level,
                'literacy_score': profile1.literacy_score - profile2.literacy_score,
                'capacity_score': profile1.capacity_score - profile2.capacity_score,
                'tolerance_score': profile1.tolerance_score - profile2.tolerance_score,
                'behavioral_score': profile1.behavioral_score - profile2.behavioral_score,
                'experience_score': profile1.experience_score - profile2.experience_score,
            },
            'risk_level_change': self._get_risk_level_change(profile1.final_risk_level, profile2.final_risk_level),
            'improvement_summary': self._get_improvement_summary(profile1, profile2)
        }
        
        return comparison

    def _get_risk_level_change(self, level1, level2):
        """Get description of risk level change"""
        risk_order = ['Korumacı', 'Muhafazakar', 'Temkinli', 'Dengeli', 'Büyüme Odaklı', 'Agresif', 'Spekülatif']
        
        if level1 == level2:
            return {'changed': False, 'direction': 'none', 'description': 'Risk seviyesi değişmedi'}
        
        try:
            idx1 = risk_order.index(level1)
            idx2 = risk_order.index(level2)
            
            if idx2 > idx1:
                return {
                    'changed': True,
                    'direction': 'increased',
                    'description': f'Risk seviyesi {level1} → {level2} arttı',
                    'steps': idx2 - idx1
                }
            else:
                return {
                    'changed': True,
                    'direction': 'decreased',
                    'description': f'Risk seviyesi {level1} → {level2} azaldı',
                    'steps': idx1 - idx2
                }
        except ValueError:
            return {'changed': True, 'direction': 'unknown', 'description': 'Bilinmeyen risk seviyesi değişimi'}

    def _get_improvement_summary(self, profile1, profile2):
        """Get summary of score improvements"""
        improvements = []
        
        if profile2.literacy_score > profile1.literacy_score:
            improvements.append(f'Finansal okuryazarlık +{profile2.literacy_score - profile1.literacy_score:.1f} puan')
        elif profile2.literacy_score < profile1.literacy_score:
            improvements.append(f'Finansal okuryazarlık -{profile1.literacy_score - profile2.literacy_score:.1f} puan')
        
        if profile2.capacity_score > profile1.capacity_score:
            improvements.append(f'Risk kapasitesi +{profile2.capacity_score - profile1.capacity_score:.1f} puan')
        elif profile2.capacity_score < profile1.capacity_score:
            improvements.append(f'Risk kapasitesi -{profile1.capacity_score - profile2.capacity_score:.1f} puan')
        
        if profile2.tolerance_score > profile1.tolerance_score:
            improvements.append(f'Risk toleransı +{profile2.tolerance_score - profile1.tolerance_score:.1f} puan')
        elif profile2.tolerance_score < profile1.tolerance_score:
            improvements.append(f'Risk toleransı -{profile1.tolerance_score - profile2.tolerance_score:.1f} puan')
        
        return improvements

    def export_profile(self, profile_id, tenant_id):
        """Export profile data as JSON"""
        import json
        from datetime import datetime, timezone
        
        profile = self.repository.get_profile(profile_id, tenant_id)
        if not profile:
            return None
        
        answers = self.repository.list_answers(profile_id)
        
        export_data = {
            'version': '1.0',
            'export_date': datetime.now(timezone.utc).isoformat(),
            'profile': {
                'id': profile.id,
                'final_risk_level': profile.final_risk_level,
                'literacy_score': profile.literacy_score,
                'capacity_score': profile.capacity_score,
                'tolerance_score': profile.tolerance_score,
                'behavioral_score': profile.behavioral_score,
                'experience_score': profile.experience_score,
                'confidence_score': profile.confidence_score,
                'test_date': profile.test_date.isoformat() if profile.test_date else None,
                'validity_date': profile.validity_date.isoformat() if profile.validity_date else None,
                'risk_warnings': json.loads(profile.risk_warnings) if profile.risk_warnings else [],
                'portfolio_allocation': scoring_engine.get_portfolio_allocation(profile.final_risk_level),
            },
            'answers': [
                {
                    'question_id': answer.question_id,
                    'dimension': answer.dimension,
                    'answer_value': answer.answer_value,
                    'answer_text': answer.answer_text,
                }
                for answer in answers
            ]
        }
        
        return export_data

    def import_profile(self, tenant_id, user_id, import_data):
        """Import profile data from JSON"""
        import json
        from datetime import datetime, timezone, timedelta
        
        try:
            profile_data = import_data.get('profile', {})
            answers_data = import_data.get('answers', [])
            
            # Deactivate active profiles
            self.repository.deactivate_active_profiles(tenant_id, user_id)
            
            # Create new profile from imported data
            profile = self.repository.add_profile(
                tenant_id=tenant_id,
                user_id=user_id,
                literacy_score=profile_data.get('literacy_score', 50),
                capacity_score=profile_data.get('capacity_score', 50),
                tolerance_score=profile_data.get('tolerance_score', 50),
                behavioral_score=profile_data.get('behavioral_score', 50),
                experience_score=profile_data.get('experience_score', 50),
                final_risk_level=profile_data.get('final_risk_level', 'Dengeli'),
                confidence_score=profile_data.get('confidence_score', 50),
                risk_warnings=json.dumps(profile_data.get('risk_warnings', [])),
                validity_date=datetime.now(timezone.utc) + timedelta(days=365),
                profile_version='1.0',
                is_active=True,
            )
            self.repository.commit()
            
            # Import answers
            for answer_data in answers_data:
                self.repository.add_answer(
                    profile_id=profile.id,
                    question_id=answer_data.get('question_id'),
                    dimension=answer_data.get('dimension', ''),
                    answer_value=answer_data.get('answer_value'),
                    answer_text=answer_data.get('answer_text', ''),
                    question_version='1.0',
                )
            self.repository.commit()
            
            return profile, {'success': True, 'message': 'Profil başarıyla içe aktarıldı'}
            
        except Exception as e:
            self.repository.rollback()
            return None, {'success': False, 'message': f'İçe aktarma hatası: {str(e)}'}

    def rollback(self):
        self.repository.rollback()

