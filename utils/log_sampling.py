"""
Log Sampling System - Yüksek trafikte log sampling için
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

SECURITY_LOGGER_PREFIXES = ('security', 'audit')
SECURITY_MESSAGE_PATTERNS = (
    'authentication failed',
    'unauthorized',
    'access denied',
    'permission denied',
    'csrf verification failed',
    'csrf token',
    'ratelimit',
    'rate limit',
    'brute force',
    'sql injection',
    'xss attack',
    'token replay',
    'security event',
    'security violation',
    'security alert',
    'logout',
)


def is_security_event(logger_name: str = '', message: str = '') -> bool:
    """Return whether a record must bypass sampling for audit completeness."""
    normalized_logger = str(logger_name or '').lower()
    normalized_message = str(message or '').lower()
    security_logger = (
        normalized_logger.startswith(SECURITY_LOGGER_PREFIXES)
        or '.security' in normalized_logger
        or normalized_logger.endswith('.audit')
    )
    return security_logger or any(pattern in normalized_message for pattern in SECURITY_MESSAGE_PATTERNS)


@dataclass
class SamplingRule:
    """Sampling kuralı"""
    sample_rate: float  # 0.0 ile 1.0 arası (0.1 = %10)
    min_samples_per_minute: int = 10
    max_samples_per_minute: int = 100
    priority: int = 5  # 1-10, 1 en yüksek öncelik


class LogSampler:
    """Log sampling yöneticisi"""

    def __init__(self):
        self.rules: Dict[str, SamplingRule] = {}
        self.sample_counts: Dict[str, list] = {}  # timestamp'ler
        self.sampling_enabled = True
        self.logger = logging.getLogger(__name__)

        # Varsayılan kurallar
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Varsayılan sampling kurallarını kur"""
        self.rules = {
            'DEBUG': SamplingRule(sample_rate=0.01, min_samples_per_minute=1, max_samples_per_minute=10, priority=10),
            'INFO': SamplingRule(sample_rate=0.1, min_samples_per_minute=5, max_samples_per_minute=50, priority=8),
            'WARNING': SamplingRule(sample_rate=0.5, min_samples_per_minute=10, max_samples_per_minute=100, priority=5),
            'ERROR': SamplingRule(sample_rate=1.0, min_samples_per_minute=100, max_samples_per_minute=1000, priority=2),
            'CRITICAL': SamplingRule(sample_rate=1.0, min_samples_per_minute=1000, max_samples_per_minute=10000, priority=1),
        }

    def should_sample(self, level: str, logger_name: str = '', message: str = '') -> bool:
        """
        Log'un sample edilip edilmeyeceğine karar ver

        Args:
            level: Log seviyesi
            logger_name: Logger adı
            message: Rendered mesaj; security/audit mesajları sampling’i bypass eder

        Returns:
            True ise log yazılır, False ise atlanır
        """
        if not self.sampling_enabled:
            return True

        # Security and audit events must remain complete even when a caller
        # installs this filter on a logger or handler with sampling enabled.
        if is_security_event(logger_name, message):
            return True

        rule = self.rules.get(level)
        if not rule:
            return True

        # Öncelik kontrolü - yüksek öncelikli loglar her zaman yazılır
        if rule.priority <= 2:
            return True

        # Dakika bazlı sample kontrolü
        current_minute = datetime.now().strftime('%Y-%m-%d %H:%M')

        if current_minute not in self.sample_counts:
            self.sample_counts[current_minute] = []

        # Eski dakikaları temizle
        self._cleanup_old_samples()

        # Dakika başına sample sayısı kontrolü
        current_samples = len(self.sample_counts.get(current_minute, []))

        if current_samples < rule.min_samples_per_minute:
            return True

        if current_samples >= rule.max_samples_per_minute:
            return False

        # Random sampling
        if random.random() < rule.sample_rate:
            self.sample_counts[current_minute].append(datetime.now())
            return True

        return False

    def _cleanup_old_samples(self):
        """Eski sample kayıtlarını temizle"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=5)

        for minute in list(self.sample_counts.keys()):
            # Dakika string'ini datetime'a çevir
            try:
                minute_dt = datetime.strptime(minute, '%Y-%m-%d %H:%M')
                if minute_dt < cutoff_time:
                    del self.sample_counts[minute]
            except ValueError:
                del self.sample_counts[minute]

    def add_rule(self, level: str, rule: SamplingRule):
        """Yeni sampling kuralı ekle"""
        self.rules[level] = rule

    def remove_rule(self, level: str):
        """Sampling kuralını kaldır"""
        if level in self.rules:
            del self.rules[level]

    def get_sampling_stats(self) -> Dict:
        """Sampling istatistiklerini getir"""
        stats = {
            'enabled': self.sampling_enabled,
            'rules': {},
            'current_samples': {}
        }

        for level, rule in self.rules.items():
            stats['rules'][level] = {
                'sample_rate': rule.sample_rate,
                'min_samples': rule.min_samples_per_minute,
                'max_samples': rule.max_samples_per_minute,
                'priority': rule.priority
            }

        for minute, samples in self.sample_counts.items():
            stats['current_samples'][minute] = len(samples)

        return stats

    def enable_sampling(self):
        """Sampling'i aktif et"""
        self.sampling_enabled = True
        self.logger.info("Log sampling enabled")

    def disable_sampling(self):
        """Sampling'i pasif et"""
        self.sampling_enabled = False
        self.logger.info("Log sampling disabled")


class SamplingFilter(logging.Filter):
    """Sampling filter - log handler'a eklenir"""

    def __init__(self, sampler: LogSampler):
        super().__init__()
        self.sampler = sampler

    def filter(self, record: logging.LogRecord) -> bool:
        """Log'un sample edilip edilmeyeceğine karar ver"""
        return self.sampler.should_sample(
            record.levelname,
            record.name,
            record.getMessage(),
        )


# Global instance
_log_sampler = None


def get_log_sampler() -> LogSampler:
    """Global log sampler instance'ı al"""
    global _log_sampler
    if _log_sampler is None:
        _log_sampler = LogSampler()
    return _log_sampler


def setup_log_sampling(log_dir: str = None):
    """
    Log sampling sistemini kur

    Args:
        log_dir: Log dizini (opsiyonel)
    """
    sampler = get_log_sampler()

    # Root logger'a sampling filter ekle
    root_logger = logging.getLogger()
    sampling_filter = SamplingFilter(sampler)
    root_logger.addFilter(sampling_filter)

    return sampler


def get_sampling_stats() -> Dict:
    """Sampling istatistiklerini getir"""
    sampler = get_log_sampler()
    return sampler.get_sampling_stats()
