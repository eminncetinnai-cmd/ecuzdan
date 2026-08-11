"""AIApplicationService skeleton.

Placeholder for future AI orchestration (recommendations, insights).
"""

from typing import Optional

from application.base import ApplicationService


class AIApplicationService(ApplicationService):
    def __init__(
        self,
        ai_adapter: Optional[object] = None,
        analysis_service: Optional[object] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.ai_adapter = ai_adapter
        self.analysis_service = analysis_service

    def suggest_portfolio(self, user_id, **kwargs):
        pass

    def explain_recommendation(self, rec_id, **kwargs):
        pass
