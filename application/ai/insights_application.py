"""
InsightsApplicationService — orchestrates AI insight generation via the AIGateway port.

The application layer has no knowledge of which concrete AI engine is in use;
it only depends on the abstract `AIGateway` interface.
"""
from application.base import ApplicationService
from application.ports.ai_gateway import AIGateway


class InsightsApplicationService(ApplicationService):
    """Application service for AI-powered financial insights.

    Depends on AIGateway (port) not on any concrete implementation.
    """

    def __init__(self, gateway: AIGateway = None):
        super().__init__()
        if gateway is None:
            raise ValueError(
                "InsightsApplicationService requires a gateway. "
                "Use get_container().applications.ai_insights() to obtain an instance."
            )
        self._gateway = gateway

    def proactive_insights(self, tenant_id=None):
        """Generate proactive insights payload."""
        return self.execute(lambda: self._gateway.generate_proactive_insights(tenant_id))

    def personalized_recommendations(self, tenant_id=None):
        """Get personalized recommendations."""
        return self.execute(lambda: self._gateway.get_personalized_recommendations(tenant_id))

    def insights_api_response(self, tenant_id=None):
        """Return full insights API payload."""
        return self.execute(lambda: self._gateway.generate_proactive_insights(tenant_id))
