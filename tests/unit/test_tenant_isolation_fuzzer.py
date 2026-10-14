"""
tests/unit/test_tenant_isolation_fuzzer.py
==========================================
Unit test harness for the adversarial multi-tenant penetration fuzzer.
"""

from scripts.fuzz_tenant_isolation import TenantIsolationFuzzer


def test_adversarial_multi_tenant_fuzzer(app):
    """Run full adversarial penetration test matrix on test app."""
    fuzzer = TenantIsolationFuzzer(app=app)
    fuzzer.setup_adversarial_tenants()
    results = fuzzer.run_fuzzing_battery()

    assert len(results) >= 17
    failed_vectors = [r for r in results if not r.passed]

    assert len(failed_vectors) == 0, (
        f"Security fuzzer detected {len(failed_vectors)} IDOR/Isolation failures: "
        f"{[(f.vector_id, f.endpoint, f.details) for f in failed_vectors]}"
    )
