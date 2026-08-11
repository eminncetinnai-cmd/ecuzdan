"""AnalysisApplicationService skeleton.

Used for portfolio/strategy analysis orchestration (simulations, performance).
"""

from typing import Optional

from application.base import ApplicationService


class AnalysisApplicationService(ApplicationService):
    def __init__(
        self,
        analysis_service: Optional[object] = None,
        portfolio_service: Optional[object] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.analysis_service = analysis_service
        self.portfolio_service = portfolio_service

    def run_simulation(self, portfolio_id, **kwargs):
        pass

    def calculate_performance(self, portfolio_id, **kwargs):
        pass
