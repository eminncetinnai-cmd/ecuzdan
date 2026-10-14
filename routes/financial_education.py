"""
Financial Education Routes
Finansal Eğitim Route'ları

EAFGS mimarisine uygun olarak veritabanı operasyonları FinancialEducationRepository
üzerinden yürütülür.
"""

import logging
import math
import random  # noqa: F401
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, render_template, request, session

from domain.analysis.services import (
    PROGRAM_ANALYSES,
    PROGRAM_CALCULATIONS,
    TECHNICAL_TERMS,
    get_all_phases,
    get_all_topics,
    get_formula_function,
    get_guide_data,
)
from infrastructure.i18n import i18n
from models import QuizAttempt, QuizQuestion, UserAchievement, UserProgress  # noqa: F401
from repositories.financial_education_repository import FinancialEducationRepository
from shared.db import db

logger = logging.getLogger(__name__)


def _calculate_day_streak(attempts):
    dates = {attempt.completed_at.date() for attempt in attempts if attempt.completed_at}
    if not dates:
        return 0
    today = datetime.now(timezone.utc).date()
    cursor = today if today in dates else today - timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _check_and_award_achievement(user_id, achievement_type, tenant_id=None):
    """Kullanıcıya başarı rozeti verir (eğer henüz yoksa)"""
    resolved_tenant = tenant_id or g.get('tenant_id')
    existing = UserAchievement.query.filter_by(
        user_id=user_id,
        tenant_id=resolved_tenant,
        achievement_type=achievement_type
    ).first()

    if not existing:
        achievement = UserAchievement(
            user_id=user_id,
            achievement_type=achievement_type,
            tenant_id=resolved_tenant
        )
        db.session.add(achievement)
        logger.info(f"Başarı rozeti verildi: {achievement_type} -> user {user_id}")
        return achievement
    return None


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


financial_education_bp = Blueprint('financial_education', __name__, url_prefix='/')


def register_financial_education_routes(bp):
    """
    Finansal eğitim route'larını kaydeder

    Args:
        bp: Blueprint objesi
    """
    repo = FinancialEducationRepository(database=db)

    @bp.route('/financial_education')
    def financial_education():
        """Finansal eğitim ana sayfası"""
        lang = g.get("lang", i18n.default_lang)
        view_type = request.args.get('view', 'guide')

        if view_type == 'dictionary':
            # Sözlük görünümü
            technical_terms = TECHNICAL_TERMS.get(lang, TECHNICAL_TERMS['en'])['terms']

            return render_template(
                'financial_education.html',
                view_type='dictionary',
                technical_terms=technical_terms,
                lang=lang
            )
        elif view_type == 'quiz':
            # Quiz görünümü
            return render_template(
                'financial_education.html',
                view_type='quiz',
                lang=lang
            )
        elif view_type == 'progress':
            # Progress görünümü
            return render_template(
                'financial_education.html',
                view_type='progress',
                lang=lang
            )
        elif view_type == 'calculations':
            # Hesaplamalar görünümü
            program_calculations = PROGRAM_CALCULATIONS
            # Convert to language-specific format
            calculations_data = {}
            for key, data in program_calculations.items():
                calculations_data[key] = data.get(lang, data.get('en', {}))

            return render_template(
                'financial_education.html',
                view_type='calculations',
                program_calculations=calculations_data,
                lang=lang
            )
        elif view_type == 'analyses':
            # Analizler görünümü
            program_analyses = PROGRAM_ANALYSES.get(lang, PROGRAM_ANALYSES['en'])['analyses']

            return render_template(
                'financial_education.html',
                view_type='analyses',
                program_analyses=program_analyses,
                lang=lang
            )
        else:
            # Rehber görünümü
            phase = request.args.get('phase', 'beginner')
            topic = request.args.get('topic', 'income_expenses')

            return render_template(
                'financial_education.html',
                view_type='guide',
                phases=get_all_phases(),
                topics=get_all_topics(phase),
                current_phase=phase,
                current_topic=topic,
                guide_data=get_guide_data(phase, topic, lang),
                lang=lang
            )

    @bp.route('/financial_education/calculate')
    def calculate_formula():
        """Finansal formül hesapla"""
        formula_name = request.args.get('formula')
        g.get("lang", i18n.default_lang)

        # Parametreleri al
        params = {}
        for key in request.args:
            if key != 'formula':
                try:
                    params[key] = float(request.args.get(key))
                except (ValueError, TypeError):
                    params[key] = 0.0

        # Formül fonksiyonunu al
        func = get_formula_function(formula_name)

        if func:
            try:
                result = func(**params)
                return {'success': True, 'result': result}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        else:
            return {'success': False, 'error': i18n.gettext('fe_formula_not_found')}

    @bp.route('/api/quiz/start', methods=['POST'])
    def start_quiz():
        """Yeni quiz başlatır"""
        try:
            data = request.get_json(silent=True) or {}
            difficulty = data.get('difficulty', 'beginner')
            topic = data.get('topic', None)
            user_id = session.get('user_id')

            if not user_id:
                return jsonify({'success': False, 'error': i18n.gettext('fe_session_required')}), 401

            # Repository üzerinden rastgele soruları al (Global katalog)
            questions = repo.get_random_questions(difficulty=difficulty, topic=topic, count=15)
            if not questions:
                return jsonify({'success': False, 'error': i18n.gettext('fe_no_questions')}), 404

            return jsonify({
                'success': True,
                'quiz_id': f"quiz_{user_id}_{int(session.get('quiz_counter', 0))}",
                'questions': [
                    {
                        'id': q.id,
                        'question': q.question,
                        'options': q.options,
                        'difficulty': q.difficulty,
                        'topic': q.topic
                    }
                    for q in questions
                ]
            })
        except Exception as e:
            logger.exception(f"Quiz başlatma hatası: {e}")
            return jsonify({'success': False, 'error': i18n.gettext('fe_quiz_start_error')}), 500

    @bp.route('/api/quiz/submit', methods=['POST'])
    def submit_quiz():
        """Quiz sonuçlarını kaydeder"""
        try:
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify({'success': False, 'error': i18n.gettext('fe_invalid_body')}), 400
            answers = data.get('answers', {})  # {question_id: selected_answer}
            if not isinstance(answers, dict):
                return jsonify({'success': False, 'error': i18n.gettext('fe_answers_dict_error')}), 400
            difficulty = data.get('difficulty', 'beginner')
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')

            if not user_id:
                return jsonify({'success': False, 'error': i18n.gettext('fe_session_required')}), 401

            # Sonuçları hesapla
            correct_count = 0
            total_count = len(answers)
            results = []

            for question_id, selected_answer in answers.items():
                question = repo.get_question(int(question_id))
                if question:
                    is_correct = question.correct_answer == selected_answer
                    if is_correct:
                        correct_count += 1
                    results.append({
                        'question_id': question_id,
                        'correct_answer': question.correct_answer,
                        'selected_answer': selected_answer,
                        'is_correct': is_correct,
                        'explanation': question.explanation
                    })

            score = int((correct_count / total_count) * 100) if total_count > 0 else 0

            # Quiz attempt kaydı oluştur (Repository üzerinden)
            repo.record_quiz_attempt(
                user_id=user_id,
                tenant_id=tenant_id,
                difficulty=difficulty,
                score=score,
                total_questions=total_count,
                correct_answers=correct_count
            )

            # Başarı kontrolü ve rozet verme
            if score >= 80:
                repo.award_achievement_if_not_exists(user_id, tenant_id, 'quiz_master')
            elif score >= 60:
                repo.award_achievement_if_not_exists(user_id, tenant_id, 'quiz_learner')

            repo.commit()

            return jsonify({
                'success': True,
                'score': score,
                'correct_count': correct_count,
                'total_count': total_count,
                'results': results
            })
        except Exception as e:
            logger.exception(f"Quiz gönderme hatası: {e}")
            repo.rollback()
            return jsonify({'success': False, 'error': i18n.gettext('fe_quiz_save_error')}), 500

    @bp.route('/api/quiz/history')
    def quiz_history():
        """Kullanıcının quiz geçmişini getirir"""
        try:
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')
            if not user_id:
                return jsonify({'success': False, 'error': i18n.gettext('fe_session_required')}), 401

            attempts = repo.get_quiz_history(user_id=user_id, tenant_id=tenant_id, limit=20)

            return jsonify({
                'success': True,
                'attempts': [
                    {
                        'id': a.id,
                        'difficulty': a.difficulty,
                        'score': a.score,
                        'total_questions': a.total_questions,
                        'correct_answers': a.correct_answers,
                        'completed_at': a.completed_at.isoformat() if a.completed_at else None
                    }
                    for a in attempts
                ]
            })
        except Exception as e:
            logger.exception(f"Quiz geçmişi hatası: {e}")
            return jsonify({'success': False, 'error': i18n.gettext('fe_quiz_history_error')}), 500

    @bp.route('/api/progress')
    def get_progress():
        """Kullanıcının eğitim ilerlemesini getirir"""
        try:
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')
            if not user_id:
                return jsonify({'success': False, 'error': i18n.gettext('fe_session_required')}), 401

            progress_records = repo.get_user_progress_list(user_id=user_id, tenant_id=tenant_id)
            attempts = repo.get_all_quiz_attempts(user_id=user_id, tenant_id=tenant_id)
            quiz_average = round(sum(attempt.score for attempt in attempts) / len(attempts)) if attempts else 0
            stats = {
                'completed_topics': sum(1 for progress in progress_records if progress.completed),
                'quiz_average': quiz_average,
                'day_streak': _calculate_day_streak(attempts),
            }

            return jsonify({
                'success': True,
                'progress': [
                    {
                        'topic': p.topic,
                        'phase': p.phase,
                        'completed': p.completed,
                        'progress_percent': p.progress_percent,
                        'last_accessed_at': p.last_accessed_at.isoformat() if p.last_accessed_at else None,
                        'completed_at': p.completed_at.isoformat() if p.completed_at else None
                    }
                    for p in progress_records
                ],
                'stats': stats
            })
        except Exception as e:
            logger.exception(f"İlerleme hatası: {e}")
            return jsonify({'success': False, 'error': i18n.gettext('fe_progress_error')}), 500

    @bp.route('/api/progress/update', methods=['POST'])
    def update_progress():
        """Konu ilerlemesini doğrulayarak idempotent biçimde kaydeder."""
        try:
            data = request.get_json(silent=True) or {}
            if not isinstance(data, dict):
                return jsonify({'success': False, 'error': i18n.gettext('fe_invalid_body')}), 400

            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')
            if not user_id:
                return jsonify({'success': False, 'error': i18n.gettext('fe_session_required')}), 401

            topic = data.get('topic')
            phase = data.get('phase', 'beginner')
            if not isinstance(topic, str) or not topic.strip():
                return jsonify({'success': False, 'error': i18n.gettext('fe_topic_required')}), 400
            if not isinstance(phase, str) or phase not in set(get_all_phases()):
                return jsonify({'success': False, 'error': i18n.gettext('fe_invalid_level')}), 422
            if topic not in set(get_all_topics(phase)):
                return jsonify({'success': False, 'error': i18n.gettext('fe_invalid_topic')}), 422

            try:
                progress_percent = float(data.get('progress_percent', 0))
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': i18n.gettext('fe_progress_percent_number')}), 422
            if not math.isfinite(progress_percent) or not 0 <= progress_percent <= 100:
                return jsonify({'success': False, 'error': i18n.gettext('fe_progress_percent_range')}), 422
            progress_percent = int(round(progress_percent))
            completed = bool(data.get('completed', False)) or progress_percent >= 100
            if completed:
                progress_percent = 100

            now = utcnow_naive()
            repo.save_or_update_progress(
                user_id=user_id,
                tenant_id=tenant_id,
                topic=topic,
                phase=phase,
                completed=completed,
                progress_percent=progress_percent,
                now=now
            )

            if completed:
                repo.award_achievement_if_not_exists(user_id, tenant_id, 'first_steps')
                total_completed = repo.count_completed_progress(user_id, tenant_id)
                if total_completed >= 5:
                    repo.award_achievement_if_not_exists(user_id, tenant_id, 'graduate')

            repo.commit()
            return jsonify({'success': True, 'progress': {
                'topic': topic,
                'phase': phase,
                'progress_percent': progress_percent,
                'completed': completed,
            }})
        except Exception as e:
            logger.exception(f"İlerleme güncelleme hatası: {e}")
            repo.rollback()
            return jsonify({'success': False, 'error': i18n.gettext('fe_progress_update_error')}), 500

    @bp.route('/api/achievements')
    def get_achievements():
        """Kullanıcının başarılarını getirir"""
        try:
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')
            if not user_id:
                return jsonify({'success': False, 'error': i18n.gettext('fe_session_required')}), 401

            achievements = repo.get_user_achievements(user_id=user_id, tenant_id=tenant_id)

            return jsonify({
                'success': True,
                'achievements': [
                    {
                        'achievement_type': a.achievement_type,
                        'earned_at': a.earned_at.isoformat() if a.earned_at else None
                    }
                    for a in achievements
                ]
            })
        except Exception as e:
            logger.exception(f"Başarılar hatası: {e}")
            return jsonify({'success': False, 'error': i18n.gettext('fe_achievements_error')}), 500
