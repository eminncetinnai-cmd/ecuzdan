"""
Circuit Breaker (Devre Kesici) — shared/circuit_breaker.py

Harici API ve ağ servislerinde peş peşe yaşanan hatalarda
sistemi korumak, gecikmeyi (latency) önlemek ve fail-fast sağlamak için
durum makineli, thread-safe devre kesici mekanizması.

Durumlar:
  - CLOSED: Devre kapalı, istekler normal iletilir.
  - OPEN: Devre açık, eşik aşılmış; istekler ağa çıkmadan anında reddedilir.
  - HALF_OPEN: İyileşme süresi doldu, deneme amaçlı tek bir isteğe izin verilir.
"""

import functools
import logging
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(RuntimeError):
    """Devre açıkken (OPEN) gelen isteklerde fırlatılan fail-fast istisnası."""

    def __init__(self, breaker_name: str, retry_after: float):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    """
    Thread-safe Circuit Breaker implementasyonu.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        expected_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    ):
        self.name = name
        self.failure_threshold = max(failure_threshold, 1)
        self.recovery_timeout = max(recovery_timeout, 0.1)
        self.expected_exceptions = expected_exceptions

        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._last_state_change: float = time.monotonic()
        self._half_open_active = False

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._evaluate_state()
            return self._state

    def _evaluate_state(self) -> None:
        """Süreye bağlı olarak OPEN -> HALF_OPEN geçişini kontrol eder."""
        if self._state == CircuitState.OPEN:
            now = time.monotonic()
            elapsed = now - self._last_state_change
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = now
                self._half_open_active = False
                logger.info(
                    "Circuit breaker '%s' transitioned from OPEN to HALF_OPEN (probe mode).",
                    self.name,
                )

    def can_execute(self) -> bool:
        """İsteğin çalıştırılıp çalıştırılamayacağını döner."""
        with self._lock:
            self._evaluate_state()
            if self._state == CircuitState.CLOSED:
                return True
            if self._state == CircuitState.HALF_OPEN:
                if not self._half_open_active:
                    self._half_open_active = True
                    return True
                return False
            return False

    def record_success(self) -> None:
        """Başarılı işlemi kaydeder ve devreyi CLOSED konumuna alır."""
        with self._lock:
            now = time.monotonic()
            self._last_success_time = now
            self._failure_count = 0
            self._half_open_active = False
            if self._state != CircuitState.CLOSED:
                logger.info(
                    "Circuit breaker '%s' recovered and transitioned to CLOSED.",
                    self.name,
                )
                self._state = CircuitState.CLOSED
                self._last_state_change = now

    def record_failure(self, exc: Optional[BaseException] = None) -> None:
        """Hatalı işlemi kaydeder, eşik aşılmışsa devreyi OPEN yapar."""
        with self._lock:
            now = time.monotonic()
            self._last_failure_time = now
            self._failure_count += 1
            self._half_open_active = False

            if self._state == CircuitState.HALF_OPEN:
                # Deneme başarısız oldu, hemen OPEN'a dön
                self._state = CircuitState.OPEN
                self._last_state_change = now
                logger.warning(
                    "Circuit breaker '%s' probe failed, returned to OPEN. Error: %s",
                    self.name,
                    exc,
                )
            elif self._state == CircuitState.CLOSED and self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_state_change = now
                logger.warning(
                    "Circuit breaker '%s' opened after %d failures. Tripped by: %s",
                    self.name,
                    self._failure_count,
                    exc,
                )

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Fonksiyonu devre kesici koruması altında çağırır."""
        with self._lock:
            self._evaluate_state()
            if not self.can_execute():
                time_remaining = max(
                    0.0,
                    self.recovery_timeout - (time.monotonic() - self._last_state_change),
                )
                raise CircuitBreakerOpenException(self.name, time_remaining)

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exceptions as exc:
            self.record_failure(exc)
            raise

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Dekoratör desteği: @circuit_breaker"""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)

        return wrapper

    def reset(self) -> None:
        """Devreyi elle sıfırlar."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_state_change = time.monotonic()
            self._half_open_active = False

    def status(self) -> Dict[str, Any]:
        """Mevcut durum raporunu döner."""
        with self._lock:
            self._evaluate_state()
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "last_failure_time": self._last_failure_time,
                "last_success_time": self._last_success_time,
            }
