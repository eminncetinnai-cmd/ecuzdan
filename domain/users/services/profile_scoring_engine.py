"""
Yatırımcı Profil Skorlama Motoru
5 boyutlu analiz ve risk hesaplama algoritmaları
"""

import json
import logging

from models import ProfileQuestion

from .default_question_bank import get_default_question_bank
from .profile_risk_calculator import (
    DEFAULT_RISK_CLASSES,
    calculate_behavioral_score,
    calculate_capacity_score,
    calculate_confidence,
    calculate_experience_score,
    calculate_final_risk_level,
    calculate_literacy_score,
    calculate_tolerance_score,
    calculate_validity_date,
    classify_risk_level,
    validate_ranking_answer,
)

logger = logging.getLogger(__name__)


class ProfileScoringEngine:
    """Yatırımcı profil skorlama motoru"""

    # Risk sınıflandırma matrisi
    RISK_CLASSES = DEFAULT_RISK_CLASSES

    # Portföy dağılımı önerileri
    PORTFOLIO_ALLOCATION = {
        'Korumacı': {'cash': 80, 'bonds': 20, 'stocks': 0},
        'Muhafazakar': {'cash': 60, 'bonds': 30, 'stocks': 10},
        'Temkinli': {'cash': 40, 'bonds': 40, 'stocks': 20},
        'Dengeli': {'cash': 20, 'bonds': 30, 'stocks': 50},
        'Büyüme Odaklı': {'cash': 10, 'bonds': 20, 'stocks': 70},
        'Agresif': {'cash': 5, 'bonds': 10, 'stocks': 85},
        'Spekülatif': {'cash': 0, 'bonds': 5, 'stocks': 95}
    }

    def __init__(self):
        self._questions = None

    @property
    def questions(self):
        """Soru bankasını dinamik olarak yükle veya önbellekten getir"""
        if self._questions is not None:
            return self._questions

        try:
            questions = ProfileQuestion.query.filter_by(is_active=True).all()
            if not questions:
                logger.info("No active questions found in DB; using the built-in default question bank")
                self._questions = self._get_default_questions()
            else:
                # Veritabanından gelen soruları doğru formata çevir
                formatted_questions = {}
                for q in questions:
                    try:
                        options = json.loads(q.options) if q.options else []
                        scoring_weights = json.loads(q.scoring_weights) if q.scoring_weights else {}

                        formatted_questions[q.id] = {
                            'id': q.id,
                            'dimension': q.dimension,
                            'type': q.question_type,
                            'question': q.question_text,
                            'options': options,
                            'correct_order': json.loads(q.correct_order) if getattr(q, 'correct_order', None) else None,
                            'correct_answer': q.correct_answer,
                            'scoring_weights': scoring_weights,
                            'explanation': q.explanation,
                            'difficulty': q.difficulty
                        }
                    except Exception as e:
                        logger.error(f"Error formatting question {q.id}: {e}")
                        continue

                if formatted_questions:
                    self._questions = formatted_questions
                else:
                    logger.warning("No valid questions after formatting, using default question bank")
                    self._questions = self._get_default_questions()
        except RuntimeError as e:
            if "application context" in str(e).lower():
                logger.debug(f"DB question bank unavailable outside app context ({e}); using default questions.")
            else:
                logger.error(f"RuntimeError loading questions from DB: {e}")
            return self._get_default_questions()
        except Exception as e:
            logger.error(f"Error loading questions from DB: {e}")
            return self._get_default_questions()

        return self._questions

    def _load_questions(self):
        """Eski adıyla çağrıları desteklemek için yardımcı metot"""
        return self.questions

    def _get_default_questions(self):
        """Varsayılan soru bankası (fallback)"""
        return self._create_default_question_bank()

    def _create_default_question_bank(self):
        """Varsayılan 40 soruluk banka oluştur"""
        return get_default_question_bank()

    def calculate_literacy_score(self, answers):
        """Finansal okuryazarlık skoru (0-100)"""
        return calculate_literacy_score(answers)

    def calculate_capacity_score(self, answers):
        """Risk kapasitesi skoru (0-100)"""
        return calculate_capacity_score(answers)

    def calculate_tolerance_score(self, answers):
        """Risk toleransı skoru (0-100)"""
        return calculate_tolerance_score(answers)

    def calculate_behavioral_score(self, answers):
        """Davranışsal finans skoru (0-100)"""
        return calculate_behavioral_score(answers)

    def calculate_experience_score(self, answers):
        """Yatırım deneyimi skoru (0-100)"""
        return calculate_experience_score(answers)

    def calculate_final_risk_level(self, literacy, capacity, tolerance, behavioral, experience):
        """Nihai risk seviyesi hesaplama"""
        return calculate_final_risk_level(
            literacy, capacity, tolerance, behavioral, experience, self.RISK_CLASSES
        )

    def _classify_risk_level(self, score):
        """Risk skorunu sınıfa dönüştür"""
        return classify_risk_level(score, self.RISK_CLASSES)

    def _calculate_confidence(self, literacy, capacity, tolerance, behavioral, experience):
        """Güven skoru hesaplama"""
        return calculate_confidence(literacy, capacity, tolerance, behavioral, experience)

    def calculate_validity_date(self, confidence_score):
        """Profil geçerlilik süresi hesaplama"""
        return calculate_validity_date(confidence_score)

    def get_portfolio_allocation(self, risk_level):
        """Portföy dağılım önerisi"""
        return self.PORTFOLIO_ALLOCATION.get(risk_level, self.PORTFOLIO_ALLOCATION['Dengeli'])

    @staticmethod
    def _validate_ranking_answer(question, value):
        """Validate and score a ranking answer without trusting client ordering."""
        return validate_ranking_answer(question, value)

    def process_answers(self, answers_data):
        """Cevapları işle ve profil oluştur"""
        try:
            # Cevapları işle
            processed_answers = []
            for answer in answers_data:
                question = self.questions.get(answer['question_id'])
                if not question:
                    logger.warning(f"Question not found: {answer['question_id']}")
                    continue

                # Soru tipine göre doğru cevap kontrolü ve güvenli skor üretimi
                if question['type'] == 'multiple_choice':
                    score = answer['value']
                    is_correct = answer['value'] == question.get('correct_answer', 0)
                elif question['type'] == 'ranking':
                    score, is_correct = self._validate_ranking_answer(question, answer.get('value'))
                else:
                    score = answer['value']
                    is_correct = None

                processed_answer = {
                    'question_id': answer['question_id'],
                    'dimension': question['dimension'],
                    'score': score,
                    'is_correct': is_correct
                }
                processed_answers.append(processed_answer)

            # Boyut bazlı skorlar
            literacy = self.calculate_literacy_score(processed_answers)
            capacity = self.calculate_capacity_score(processed_answers)
            tolerance = self.calculate_tolerance_score(processed_answers)
            behavioral = self.calculate_behavioral_score(processed_answers)
            experience = self.calculate_experience_score(processed_answers)

            # Nihai risk hesaplama
            risk_result = self.calculate_final_risk_level(literacy, capacity, tolerance, behavioral, experience)

            # Geçerlilik süresi
            validity_date = self.calculate_validity_date(risk_result['confidence_score'])

            return {
                'literacy_score': literacy,
                'capacity_score': capacity,
                'tolerance_score': tolerance,
                'behavioral_score': behavioral,
                'experience_score': experience,
                'final_risk_level': risk_result['final_risk_level'],
                'confidence_score': risk_result['confidence_score'],
                'risk_warnings': risk_result['risk_warnings'],
                'base_risk_score': risk_result['base_risk_score'],
                'validity_date': validity_date,
                'portfolio_allocation': self.get_portfolio_allocation(risk_result['final_risk_level'])
            }

        except Exception as e:
            logger.error(f"Error processing answers: {e}")
            raise


# Global instance
scoring_engine = ProfileScoringEngine()
