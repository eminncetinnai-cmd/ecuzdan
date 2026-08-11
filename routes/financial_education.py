"""
Financial Education Routes
Finansal Eğitim Route'ları
"""

import logging
import random

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
from models import QuizQuestion, QuizAttempt, UserProgress, UserAchievement
from shared.db import db

logger = logging.getLogger(__name__)

financial_education_bp = Blueprint('financial_education', __name__, url_prefix='/')


def register_financial_education_routes(bp):
    """
    Finansal eğitim route'larını kaydeder

    Args:
        bp: Blueprint objesi
    """

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
            return {'success': False, 'error': 'Formula not found'}

    @bp.route('/api/quiz/start', methods=['POST'])
    def start_quiz():
        """Yeni quiz başlatır"""
        try:
            data = request.get_json()
            difficulty = data.get('difficulty', 'beginner')
            topic = data.get('topic', None)
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')

            if not user_id:
                return jsonify({'success': False, 'error': 'Oturum açmanız gerekli'}), 401

            # Rastgele soruları al
            query = QuizQuestion.query.filter_by(difficulty=difficulty, is_active=True)
            if topic:
                query = query.filter_by(topic=topic)
            
            questions = query.all()
            if not questions:
                return jsonify({'success': False, 'error': 'Bu seviyede soru bulunamadı'}), 404

            # 5 rastgele soru seç
            selected_questions = random.sample(questions, min(5, len(questions)))
            
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
                    for q in selected_questions
                ]
            })
        except Exception as e:
            logger.exception(f"Quiz başlatma hatası: {e}")
            return jsonify({'success': False, 'error': 'Quiz başlatılamadı'}), 500

    @bp.route('/api/quiz/submit', methods=['POST'])
    def submit_quiz():
        """Quiz sonuçlarını kaydeder"""
        try:
            data = request.get_json()
            answers = data.get('answers', {})  # {question_id: selected_answer}
            difficulty = data.get('difficulty', 'beginner')
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')

            if not user_id:
                return jsonify({'success': False, 'error': 'Oturum açmanız gerekli'}), 401

            # Sonuçları hesapla
            correct_count = 0
            total_count = len(answers)
            results = []

            for question_id, selected_answer in answers.items():
                question = QuizQuestion.query.get(int(question_id))
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

            # Quiz attempt kaydı oluştur
            quiz_attempt = QuizAttempt(
                user_id=user_id,
                difficulty=difficulty,
                score=score,
                total_questions=total_count,
                correct_answers=correct_count,
                tenant_id=tenant_id
            )
            db.session.add(quiz_attempt)

            # Başarı kontrolü ve rozet verme
            if score >= 80:
                _check_and_award_achievement(user_id, 'quiz_master', tenant_id)
            elif score >= 60:
                _check_and_award_achievement(user_id, 'quiz_learner', tenant_id)

            db.session.commit()

            return jsonify({
                'success': True,
                'score': score,
                'correct_count': correct_count,
                'total_count': total_count,
                'results': results
            })
        except Exception as e:
            logger.exception(f"Quiz gönderme hatası: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Quiz sonuçları kaydedilemedi'}), 500

    @bp.route('/api/quiz/history')
    def quiz_history():
        """Kullanıcının quiz geçmişini getirir"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': 'Oturum açmanız gerekli'}), 401

            attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(
                QuizAttempt.completed_at.desc()
            ).limit(20).all()

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
            return jsonify({'success': False, 'error': 'Quiz geçmişi alınamadı'}), 500

    @bp.route('/api/progress')
    def get_progress():
        """Kullanıcının eğitim ilerlemesini getirir"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': 'Oturum açmanız gerekli'}), 401

            progress_records = UserProgress.query.filter_by(user_id=user_id).all()

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
                ]
            })
        except Exception as e:
            logger.exception(f"İlerleme hatası: {e}")
            return jsonify({'success': False, 'error': 'İlerleme alınamadı'}), 500

    @bp.route('/api/progress/update', methods=['POST'])
    def update_progress():
        """Kullanıcının eğitim ilerlemesini günceller"""
        try:
            data = request.get_json()
            topic = data.get('topic')
            phase = data.get('phase', 'beginner')
            progress_percent = data.get('progress_percent', 0)
            completed = data.get('completed', False)
            user_id = session.get('user_id')
            tenant_id = g.get('tenant_id')

            if not user_id:
                return jsonify({'success': False, 'error': 'Oturum açmanız gerekli'}), 401

            if not topic:
                return jsonify({'success': False, 'error': 'Topic gerekli'}), 400

            # Mevcut kaydı bul veya yeni oluştur
            progress = UserProgress.query.filter_by(
                user_id=user_id,
                topic=topic
            ).first()

            if progress:
                progress.phase = phase
                progress.progress_percent = progress_percent
                progress.completed = completed
                progress.last_accessed_at = utcnow_naive()
                if completed and not progress.completed_at:
                    progress.completed_at = utcnow_naive()
            else:
                progress = UserProgress(
                    user_id=user_id,
                    topic=topic,
                    phase=phase,
                    progress_percent=progress_percent,
                    completed=completed,
                    last_accessed_at=utcnow_naive(),
                    completed_at=utcnow_naive() if completed else None,
                    tenant_id=tenant_id
                )
                db.session.add(progress)

            # Başarı kontrolü
            if completed:
                _check_and_award_achievement(user_id, 'first_steps', tenant_id)
                total_completed = UserProgress.query.filter_by(
                    user_id=user_id,
                    completed=True
                ).count()
                if total_completed >= 5:
                    _check_and_award_achievement(user_id, 'graduate', tenant_id)

            db.session.commit()

            return jsonify({'success': True, 'progress': {
                'topic': topic,
                'phase': phase,
                'progress_percent': progress_percent,
                'completed': completed
            }})
        except Exception as e:
            logger.exception(f"İlerleme güncelleme hatası: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'İlerleme güncellenemedi'}), 500

    @bp.route('/api/achievements')
    def get_achievements():
        """Kullanıcının başarılarını getirir"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': 'Oturum açmanız gerekli'}), 401

            achievements = UserAchievement.query.filter_by(user_id=user_id).all()

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
            return jsonify({'success': False, 'error': 'Başarılar alınamadı'}), 500


def _check_and_award_achievement(user_id, achievement_type, tenant_id):
    """Kullanıcıya başarı rozeti verir (eğer henüz yoksa)"""
    existing = UserAchievement.query.filter_by(
        user_id=user_id,
        achievement_type=achievement_type
    ).first()

    if not existing:
        achievement = UserAchievement(
            user_id=user_id,
            achievement_type=achievement_type,
            tenant_id=tenant_id
        )
        db.session.add(achievement)
        logger.info(f"Başarı rozeti verildi: {achievement_type} -> user {user_id}")


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)
