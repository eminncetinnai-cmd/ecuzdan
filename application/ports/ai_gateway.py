"""AI Gateway interface (Port).

Application services depend on this abstraction; infrastructure
provides concrete implementations (RuleBasedGateway, OpenAIGateway, etc.).
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AIGateway(ABC):
    """Abstract port for AI insight generation.

    The Application layer depends only on this interface.
    Infrastructure provides concrete implementations.
    """

    @abstractmethod
    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        """Generate a list of structured insight dicts for a tenant."""
        raise NotImplementedError


__all__ = ["AIGateway"]
