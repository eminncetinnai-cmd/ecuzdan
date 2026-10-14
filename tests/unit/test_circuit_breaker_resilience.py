"""
Unit Tests — Circuit Breaker & Resilience
shared/circuit_breaker.py mekanizmasının durum geçişlerini ve fail-fast davranışını test eder.
"""

import time

import pytest

from shared.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException, CircuitState


@pytest.mark.unit
def test_circuit_breaker_init_and_default_state():
    cb = CircuitBreaker("test_service", failure_threshold=3, recovery_timeout=0.5)
    assert cb.name == "test_service"
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True
    status = cb.status()
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 0


@pytest.mark.unit
def test_circuit_breaker_success_flow():
    cb = CircuitBreaker("test_service", failure_threshold=3, recovery_timeout=0.5)

    def good_fn(x):
        return x * 2

    res = cb.call(good_fn, 5)
    assert res == 10
    assert cb.state == CircuitState.CLOSED
    assert cb.status()["failure_count"] == 0


@pytest.mark.unit
def test_circuit_breaker_trips_to_open_after_threshold_failures():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=0.2)

    def failing_fn():
        raise ValueError("Network down")

    # 1. hata
    with pytest.raises(ValueError):
        cb.call(failing_fn)
    assert cb.state == CircuitState.CLOSED
    assert cb.status()["failure_count"] == 1

    # 2. hata -> Eşik aşıldı, OPEN durumuna geçer
    with pytest.raises(ValueError):
        cb.call(failing_fn)
    assert cb.state == CircuitState.OPEN
    assert cb.status()["failure_count"] == 2

    # 3. çağrı -> Artık ağa gitmez, fail-fast CircuitBreakerOpenException fırlatır
    with pytest.raises(CircuitBreakerOpenException) as excinfo:
        cb.call(failing_fn)
    assert "is OPEN" in str(excinfo.value)


@pytest.mark.unit
def test_circuit_breaker_half_open_and_recovery():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=0.1)

    # Devreyi aç
    cb.record_failure(ValueError("err1"))
    cb.record_failure(ValueError("err2"))
    assert cb.state == CircuitState.OPEN

    # İyileşme süresini bekle
    time.sleep(0.12)
    assert cb.state == CircuitState.HALF_OPEN

    # Başarılı bir çağrı devreyi CLOSED yapar
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.status()["failure_count"] == 0


@pytest.mark.unit
def test_circuit_breaker_half_open_probe_failure_reopens():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=0.1)

    cb.record_failure(ValueError("err1"))
    cb.record_failure(ValueError("err2"))
    assert cb.state == CircuitState.OPEN

    time.sleep(0.12)
    assert cb.state == CircuitState.HALF_OPEN

    # Deneme çağrısı başarısız olursa hemen OPEN'a dönmeli
    cb.record_failure(ValueError("probe failed"))
    assert cb.state == CircuitState.OPEN


@pytest.mark.unit
def test_circuit_breaker_decorator():
    cb = CircuitBreaker("decorated_service", failure_threshold=1, recovery_timeout=0.5)

    @cb
    def compute(val):
        if val < 0:
            raise ValueError("Negative")
        return val + 10

    assert compute(5) == 15

    with pytest.raises(ValueError):
        compute(-1)

    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        compute(5)


@pytest.mark.unit
def test_circuit_breaker_reset():
    cb = CircuitBreaker("test_service", failure_threshold=1, recovery_timeout=60.0)
    cb.record_failure(ValueError("err"))
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.status()["failure_count"] == 0
