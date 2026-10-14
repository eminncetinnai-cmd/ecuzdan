"""
Unit tests for AI application services
"""

from unittest.mock import Mock

import pytest

from application.ai.ai_application import AIApplicationService
from application.ai.insights_application import InsightsApplicationService


@pytest.mark.unit
class TestAIApplicationService:
    """Test AIApplicationService"""

    def test_initialization(self):
        """Test service initialization"""
        ai_adapter = Mock()
        analysis_service = Mock()

        service = AIApplicationService(
            ai_adapter=ai_adapter,
            analysis_service=analysis_service
        )

        assert service.ai_adapter == ai_adapter
        assert service.analysis_service == analysis_service

    def test_suggest_portfolio_placeholder(self):
        """Test suggest_portfolio is a placeholder"""
        service = AIApplicationService()

        result = service.suggest_portfolio(user_id=1)

        assert result is None

    def test_explain_recommendation_placeholder(self):
        """Test explain_recommendation is a placeholder"""
        service = AIApplicationService()

        result = service.explain_recommendation(rec_id=1)

        assert result is None


@pytest.mark.unit
class TestInsightsApplicationService:
    """Test InsightsApplicationService"""

    def test_initialization_requires_gateway(self):
        """Test initialization requires gateway"""
        with pytest.raises(ValueError, match="requires a gateway"):
            InsightsApplicationService(gateway=None)

    def test_initialization_with_gateway(self):
        """Test initialization with gateway"""
        gateway = Mock()

        service = InsightsApplicationService(gateway=gateway)

        assert service._gateway == gateway

    def test_proactive_insights(self):
        """Test proactive_insights calls gateway"""
        gateway = Mock()
        gateway.generate_proactive_insights.return_value = {"insights": "test"}

        service = InsightsApplicationService(gateway=gateway)
        result = service.proactive_insights(tenant_id="test_tenant")

        gateway.generate_proactive_insights.assert_called_once_with("test_tenant")
        assert result == {"insights": "test"}

    def test_personalized_recommendations(self):
        """Test personalized_recommendations calls gateway"""
        gateway = Mock()
        gateway.get_personalized_recommendations.return_value = {"recommendations": "test"}

        service = InsightsApplicationService(gateway=gateway)
        result = service.personalized_recommendations(tenant_id="test_tenant")

        gateway.get_personalized_recommendations.assert_called_once_with("test_tenant")
        assert result == {"recommendations": "test"}

    def test_insights_api_response(self):
        """Test insights_api_response calls gateway"""
        gateway = Mock()
        gateway.generate_proactive_insights.return_value = {"api": "response"}

        service = InsightsApplicationService(gateway=gateway)
        result = service.insights_api_response(tenant_id="test_tenant")

        gateway.generate_proactive_insights.assert_called_once_with("test_tenant")
        assert result == {"api": "response"}
