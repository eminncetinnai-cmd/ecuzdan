from datetime import datetime, timezone

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserProgress(db.Model):
    """Kullanıcı eğitim ilerleme takibi

    Phase 17: Financial Education Progress Tracking
    """
    __tablename__ = 'user_progress'
    __table_args__ = (
        db.Index('idx_user_progress_user', 'user_id'),
        db.Index('idx_user_progress_topic', 'topic'),
        db.Index('idx_user_progress_tenant', 'tenant_id'),
        db.UniqueConstraint('user_id', 'topic', name='uq_user_progress_topic'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False)  # Topic identifier (e.g., 'income_expenses')
    phase = db.Column(db.String(50), nullable=False)  # Phase identifier (e.g., 'beginner')
    completed = db.Column(db.Boolean, default=False, nullable=False)
    progress_percent = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    last_accessed_at = db.Column(db.DateTime, default=utcnow_naive)
    completed_at = db.Column(db.DateTime, nullable=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    user = db.relationship('User', backref='progress_records')
    tenant = db.relationship('Tenant', backref='user_progress')


class QuizAttempt(db.Model):
    """Quiz deneme kayıtları

    Phase 17: Financial Education Quiz System
    """
    __tablename__ = 'quiz_attempt'
    __table_args__ = (
        db.Index('idx_quiz_attempt_user', 'user_id'),
        db.Index('idx_quiz_attempt_user_completed', 'user_id', 'completed_at'),
        db.Index('idx_quiz_attempt_difficulty', 'difficulty'),
        db.Index('idx_quiz_attempt_tenant', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    score = db.Column(db.Integer, nullable=False)  # 0-100
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=utcnow_naive)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    user = db.relationship('User', backref='quiz_attempts')
    tenant = db.relationship('Tenant', backref='quiz_attempts')


class UserAchievement(db.Model):
    """Kullanıcı başarıları ve rozetleri

    Phase 17: Gamification System
    """
    __tablename__ = 'user_achievement'
    __table_args__ = (
        db.Index('idx_user_achievement_user', 'user_id'),
        db.Index('idx_user_achievement_type', 'achievement_type'),
        db.Index('idx_user_achievement_tenant', 'tenant_id'),
        db.UniqueConstraint('user_id', 'achievement_type', name='uq_user_achievement'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    achievement_type = db.Column(db.String(50), nullable=False)  # 'first_steps', 'quiz_master', 'week_streak', 'graduate'
    earned_at = db.Column(db.DateTime, default=utcnow_naive)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    user = db.relationship('User', backref='achievements')
    tenant = db.relationship('Tenant', backref='user_achievements')


class QuizQuestion(db.Model):
    """Quiz soruları

    Phase 17: Financial Education Quiz System
    """
    __tablename__ = 'quiz_question'
    __table_args__ = (
        db.Index('idx_quiz_question_difficulty', 'difficulty'),
        db.Index('idx_quiz_question_topic', 'topic'),
        db.Index('idx_quiz_question_tenant', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"}
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    explanation = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    topic = db.Column(db.String(100), nullable=False)  # 'income_expenses', 'compound_interest', etc.
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    tenant = db.relationship('Tenant', backref='quiz_questions')
