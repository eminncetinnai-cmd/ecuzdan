"""Repository for investor profiles."""

from models import InvestorProfile, InvestorProfileAnswer

from .base import BaseRepository


class ProfileRepository(BaseRepository):
    def get_active_profile(self, tenant_id, user_id):
        return InvestorProfile.query.filter_by(
            tenant_id=tenant_id,
            user_id=user_id,
            is_active=True,
        ).first()

    def list_history(self, tenant_id, user_id, limit=None):
        query = InvestorProfile.query.filter_by(
            tenant_id=tenant_id,
            user_id=user_id,
        ).order_by(InvestorProfile.test_date.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    def deactivate_active_profiles(self, tenant_id, user_id):
        InvestorProfile.query.filter_by(
            tenant_id=tenant_id,
            user_id=user_id,
            is_active=True,
        ).update({'is_active': False})

    def add_profile(self, **fields):
        return self.add(InvestorProfile(**fields))

    def add_answer(self, **fields):
        return self.add(InvestorProfileAnswer(**fields))

    def get_profile(self, profile_id, tenant_id):
        return InvestorProfile.query.filter_by(id=profile_id, tenant_id=tenant_id).first()

    def list_answers(self, profile_id):
        return InvestorProfileAnswer.query.filter_by(profile_id=profile_id).all()

