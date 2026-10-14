from datetime import datetime, timezone

from sqlalchemy import Numeric

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ProfileQuestion(db.Model):
    """Profil soru bankası - JSON tabanlı yapı"""
    __tablename__ = 'profile_question'
    __table_args__ = (
        db.Index('idx_question_dimension', 'dimension'),
        db.Index('idx_question_active', 'is_active'),
    )

    id = db.Column(db.String(50), primary_key=True)  # Soru ID'si
    dimension = db.Column(db.String(50), nullable=False)  # literacy, capacity, tolerance, behavioral, experience
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # multiple_choice, scale, yes_no, ranking
    options = db.Column(db.Text, nullable=False)  # JSON: [{"value": 1, "text": "A"}, {"value": 2, "text": "B"}]
    correct_order = db.Column(db.Text, nullable=True)  # Ranking için JSON sıra dizisi
    correct_answer = db.Column(db.Integer, nullable=True)  # Okuryazarlık için
    scoring_weights = db.Column(db.Text, nullable=False)  # JSON: puan ağırlıkları
    explanation = db.Column(db.Text, nullable=True)  # Açıklama
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    version = db.Column(db.String(20), default='1.0')
    created_at = db.Column(db.DateTime, default=utcnow_naive)


class InvestorProfile(db.Model):
    """Yatırımcı risk profili - 5 boyutlu analiz sonucu"""
    __tablename__ = 'investor_profile'
    __table_args__ = (
        db.Index('idx_investor_profile_tenant', 'tenant_id'),
        db.Index('idx_investor_profile_user', 'user_id'),
        db.Index('idx_investor_profile_date', 'test_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # 5 Boyutlu Skorlar (0-100)
    literacy_score = db.Column(Numeric(19, 4), nullable=False)      # Finansal Okuryazarlık
    capacity_score = db.Column(Numeric(19, 4), nullable=False)      # Risk Kapasitesi
    tolerance_score = db.Column(Numeric(19, 4), nullable=False)     # Risk Toleransı
    behavioral_score = db.Column(Numeric(19, 4), nullable=False)   # Davranışsal Finans
    experience_score = db.Column(Numeric(19, 4), nullable=False)   # Yatırım Deneyimi

    # Nihai Sonuç
    final_risk_level = db.Column(db.String(50), nullable=False)  # 7 sınıf
    confidence_score = db.Column(Numeric(19, 4), nullable=False)        # Güven skoru
    risk_warnings = db.Column(db.Text, nullable=True)            # JSON uyarılar

    # Meta
    test_date = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    validity_date = db.Column(db.DateTime, nullable=True)         # Profil geçerlilik süresi
    profile_version = db.Column(db.String(20), default='1.0', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # İlişkiler
    tenant = db.relationship('Tenant', backref='investor_profiles')
    user = db.relationship('User', backref='investor_profiles')


class InvestorProfileAnswer(db.Model):
    """Profil testi cevapları - detaylı analiz için"""
    __tablename__ = 'investor_profile_answer'
    __table_args__ = (
        db.Index('idx_answer_profile', 'profile_id'),
        db.Index('idx_answer_question', 'question_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('investor_profile.id'), nullable=False)
    question_id = db.Column(db.String(50), nullable=False)  # Soru ID'si
    dimension = db.Column(db.String(50), nullable=False)     # Boyut (literacy, capacity, vb.)
    answer_value = db.Column(db.Integer, nullable=False)     # Cevap puanı; ranking için nötr skor
    answer_order = db.Column(db.Text, nullable=True)         # Ranking cevaplarının JSON sıra dizisi
    answer_text = db.Column(db.String(500), nullable=True)   # Cevap metni
    question_version = db.Column(db.String(20), default='1.0')

    profile = db.relationship('InvestorProfile', backref='answers')
