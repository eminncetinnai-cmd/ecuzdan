import pytest

from infrastructure.ai.rule_based_gateway import AIInsightProvider, AIInsightsEngine


class DummyInsightProvider(AIInsightProvider):
    @property
    def name(self):
        return 'dummy'

    def generate_insights(self, tenant_id=None):
        return [
            {
                'type': 'info',
                'category': 'dummy',
                'title': 'Dummy Insight',
                'description': 'This is a synthetic insight for testing.',
                'priority': 'low',
                'recommendation': 'No action needed.'
            }
        ]


def test_ai_insights_engine_returns_registered_provider_insights():
    engine = AIInsightsEngine(providers=[DummyInsightProvider()])
    payload = engine.generate_proactive_insights(tenant_id='tenant-test')

    assert isinstance(payload, dict)
    assert 'insights' in payload
    assert payload['insights'][0]['category'] == 'dummy'
    assert payload['summary'].startswith('Excellent financial health')
    assert payload['action_items'] == ['No action needed.']


def test_ai_insights_engine_can_register_additional_provider():
    engine = AIInsightsEngine(providers=[])
    engine.register_provider(DummyInsightProvider())
    result = engine.generate_proactive_insights()

    assert len(result['insights']) == 1
    assert result['insights'][0]['category'] == 'dummy'
    assert result['summary'].startswith('Excellent financial health')


def test_register_provider_rejects_invalid_provider():
    engine = AIInsightsEngine(providers=[])
    with pytest.raises(TypeError):
        engine.register_provider(object())
