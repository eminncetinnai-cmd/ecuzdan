"""
Financial Education Repository — repositories/financial_education_repository.py

Finansal Eğitim (quiz denemeleri, konu ilerlemeleri, rozetler ve sorular)
veritabanı operasyonlarını yöneten repository.
EAFGS mimari standartlarına tam uyumlu ve tenant-isolated.
"""

import logging
import random
from datetime import datetime, timezone
from typing import List, Optional

from models import QuizAttempt, QuizQuestion, UserAchievement, UserProgress

from .base import BaseRepository

logger = logging.getLogger(__name__)


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FinancialEducationRepository(BaseRepository):
    """
    Financial Education Repository.
    QuizAttempts, UserProgress, UserAchievements ve QuizQuestions işlemlerini yönetir.
    """

    # ─── Quiz Questions (Global Katalog) ──────────────────────────────────────

    def get_question(self, question_id: int) -> Optional[QuizQuestion]:
        """Belirtilen ID'ye sahip soruyu getirir (Global Katalog)."""
        return self.session.get(QuizQuestion, question_id)

    def get_random_questions(self, difficulty: str, topic: Optional[str] = None, count: int = 15) -> List[QuizQuestion]:
        """Belirli zorluk derecesindeki (ve varsa konudaki) aktif sorulardan rastgele seçer."""
        query = QuizQuestion.query.filter_by(
            difficulty=difficulty,
            is_active=True
        )
        if topic:
            query = query.filter_by(topic=topic)
        questions = query.limit(count).all()
        if not questions:
            return []
        return random.sample(questions, min(count, len(questions)))

    # ─── Quiz Attempts ────────────────────────────────────────────────────────

    def record_quiz_attempt(
        self,
        user_id: int,
        tenant_id: str,
        difficulty: str,
        score: int,
        total_questions: int,
        correct_answers: int,
    ) -> QuizAttempt:
        """Yeni bir quiz deneme kaydı oluşturur."""
        attempt = QuizAttempt(
            user_id=user_id,
            difficulty=difficulty,
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            tenant_id=tenant_id
        )
        self.session.add(attempt)
        return attempt

    def get_quiz_history(
        self,
        user_id: int,
        tenant_id: str,
        limit: int = 20
    ) -> List[QuizAttempt]:
        """Kullanıcının quiz geçmişini getirir."""
        return QuizAttempt.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).order_by(
            QuizAttempt.completed_at.desc()
        ).limit(limit).all()

    def get_all_quiz_attempts(
        self,
        user_id: int,
        tenant_id: str
    ) -> List[QuizAttempt]:
        """Kullanıcının tüm quiz denemelerini getirir (istatistik hesaplama için)."""
        return QuizAttempt.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).all()

    # ─── User Progress ────────────────────────────────────────────────────────

    def get_user_progress_list(
        self,
        user_id: int,
        tenant_id: str
    ) -> List[UserProgress]:
        """Kullanıcının tüm konu ilerleme kayıtlarını getirir."""
        return UserProgress.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).all()

    def get_user_progress(
        self,
        user_id: int,
        tenant_id: str,
        topic: str
    ) -> Optional[UserProgress]:
        """Belirli bir konudaki ilerleme kaydını getirir."""
        return UserProgress.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id,
            topic=topic
        ).first()

    def save_or_update_progress(
        self,
        user_id: int,
        tenant_id: str,
        topic: str,
        phase: str,
        completed: bool,
        progress_percent: int,
        now: Optional[datetime] = None,
    ) -> UserProgress:
        """Konu ilerlemesini idempotent biçimde günceller veya oluşturur."""
        if now is None:
            now = _utcnow_naive()

        progress = self.get_user_progress(user_id, tenant_id, topic)
        if progress:
            if progress.completed:
                completed = True
                progress_percent = 100
            progress.phase = phase
            progress.progress_percent = progress_percent
            progress.completed = completed
            progress.last_accessed_at = now
            if completed and not progress.completed_at:
                progress.completed_at = now
        else:
            progress = UserProgress(
                user_id=user_id,
                topic=topic,
                phase=phase,
                progress_percent=progress_percent,
                completed=completed,
                last_accessed_at=now,
                completed_at=now if completed else None,
                tenant_id=tenant_id,
            )
            self.session.add(progress)

        return progress

    def count_completed_progress(
        self,
        user_id: int,
        tenant_id: str
    ) -> int:
        """Kullanıcının tamamladığı konu sayısını döndürür."""
        return UserProgress.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id,
            completed=True
        ).count()

    # ─── User Achievements ────────────────────────────────────────────────────

    def get_user_achievements(
        self,
        user_id: int,
        tenant_id: str
    ) -> List[UserAchievement]:
        """Kullanıcının kazandığı başarı rozetlerini getirir."""
        return UserAchievement.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).all()

    def award_achievement_if_not_exists(
        self,
        user_id: int,
        tenant_id: str,
        achievement_type: str
    ) -> Optional[UserAchievement]:
        """Kullanıcıda yoksa yeni bir başarı rozeti verir."""
        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id,
            achievement_type=achievement_type
        ).first()

        if not existing:
            achievement = UserAchievement(
                user_id=user_id,
                achievement_type=achievement_type,
                tenant_id=tenant_id
            )
            self.session.add(achievement)
            logger.info(f"Başarı rozeti verildi: {achievement_type} -> user {user_id}")
            return achievement

        return None
