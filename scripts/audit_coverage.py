#!/usr/bin/env python3
"""E-Cüzdan Katmanlı Kapsama ve Sıfır-Regresyon Denetleyicisi (audit_coverage.py).

Her mimari katmanın (Domain, Repositories, Routes, Shared/Utils) test kapsamasını
ayrı ayrı ölçer, hedeflerle ve baseline ile karşılaştırır.
Değişiklik sonrası kapsama gerilemesini (Coverage Regression) engeller.

Kullanım:
  python scripts/audit_coverage.py
  python scripts/audit_coverage.py --enforce
  python scripts/audit_coverage.py --ratchet
  python scripts/audit_coverage.py --layer domain
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Windows console encoding uyumluluğu
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ANSI Renkleri
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = PROJECT_ROOT / "config" / "coverage_baseline.json"

# Mimari Katman Konfigürasyonları
LAYER_CONFIGS: dict[str, dict[str, Any]] = {
    "domain": {
        "title": "Domain & Finans Motoru (Pure Business Logic)",
        "sources": ["domain", "engines"],
        "tests": [
            "tests/unit/financial/",
            "tests/unit/portfolio/",
            "tests/unit/reporting/",
            "tests/unit/reconciliation/",
            "tests/unit/transactions/",
            "tests/unit/users/",
            "tests/unit/categories/",
            "tests/unit/test_central_bank_reserves.py",
            "tests/unit/test_global_ratios.py",
            "tests/unit/test_macro_correlation.py",
            "tests/unit/test_portfolio_snapshot_context.py",
            "tests/unit/test_profile_ranking.py",
            "tests/unit/test_profile_services.py",
            "tests/unit/test_analysis_services.py",
            "tests/unit/test_financial_consistency_checker.py",
            "tests/unit/test_financial_db_service.py",
            "tests/unit/test_financial_insights.py",
            "tests/unit/test_fx_metals_provider.py",
            "tests/unit/test_live_ratio_provider.py",
            "tests/unit/test_macro_ratio_alerts.py",
            "tests/unit/test_market_data_service.py",
            "tests/unit/test_plan_occurrence.py",
            "tests/unit/test_plan_service.py",
            "tests/unit/test_cash_flow_graphs.py",
            "tests/unit/test_strategy.py",
            "tests/unit/test_storage_health_architecture_guard.py",
            "tests/unit/test_storage_health_cleanup.py",
            "tests/unit/test_storage_health_execution.py",
            "tests/unit/test_storage_health_history.py",
            "tests/unit/test_storage_health_lifecycle.py",
            "tests/unit/test_storage_health_migration_plan.py",
            "tests/unit/test_storage_health_recommender.py",
            "tests/unit/test_storage_health_retention_policy.py",
            "tests/unit/test_storage_health_safe_execution.py",
            "tests/unit/test_storage_health_scanner.py",
            "tests/unit/test_storage_health_telemetry.py",
            "tests/unit/test_storage_health_tune_up.py",
            "tests/unit/test_database_maintenance.py",
            "tests/unit/test_data_hygiene_service.py",
            "tests/unit/test_tenant_isolation_fuzzer.py",
        ],
        "target_min": 60.0,
    },
    "repositories": {
        "title": "Veritabani & Kalicilik (Repositories & Persistence)",
        "sources": ["repositories"],
        "tests": [
            "tests/unit/test_base_repository.py",
            "tests/unit/test_catalog_repository.py",
            "tests/unit/test_category_repository.py",
            "tests/unit/test_financial_education_repository.py",
            "tests/unit/test_financial_repository.py",
            "tests/unit/test_logbook_repository.py",
            "tests/unit/test_notification_repository.py",
            "tests/unit/test_portfolio_repository.py",
            "tests/unit/test_profile_repository.py",
            "tests/unit/test_reporting_repository.py",
            "tests/unit/test_strategy_repository.py",
            "tests/unit/test_transaction_and_plan_repositories.py",
            "tests/unit/test_user_repository.py",
        ],
        "target_min": 75.0,
    },
    "shared_utils": {
        "title": "Paylasilan Araclar & Guvenlik (Shared / Utils)",
        "sources": ["shared", "utils"],
        "tests": [
            "tests/unit/shared/",
            "tests/unit/test_ajax_helpers.py",
            "tests/unit/test_audit.py",
            "tests/unit/test_auth_helpers.py",
            "tests/unit/test_capabilities.py",
            "tests/unit/test_circuit_breaker_resilience.py",
            "tests/unit/test_currency_precision.py",
            "tests/unit/test_decimal_precision.py",
            "tests/unit/test_decorators.py",
            "tests/unit/test_email_alerts.py",
            "tests/unit/test_encryption.py",
            "tests/unit/test_format_utils.py",
            "tests/unit/test_ledger_decimal_boundary.py",
            "tests/unit/test_log_actions.py",
            "tests/unit/test_log_alert_monitor.py",
            "tests/unit/test_log_filters.py",
            "tests/unit/test_log_redaction.py",
            "tests/unit/test_log_retention.py",
            "tests/unit/test_log_sampling.py",
            "tests/unit/test_log_viewer.py",
            "tests/unit/test_logging_config.py",
            "tests/unit/test_logging_systems.py",
            "tests/unit/test_money.py",
            "tests/unit/test_monitoring_stream.py",
            "tests/unit/test_notification_helpers.py",
            "tests/unit/test_query_profiler.py",
            "tests/unit/test_request_context.py",
            "tests/unit/test_request_validators.py",
            "tests/unit/test_request_validators_extended.py",
            "tests/unit/test_routes_utils.py",
            "tests/unit/test_shared_cache.py",
            "tests/unit/test_structured_logging.py",
            "tests/unit/test_structured_logging_fail_open.py",
            "tests/unit/test_tracing.py",
        ],
        "target_min": 75.0,
    },
    "routes": {
        "title": "Sunum Katmani & API Sozlesmeleri (Routes & Web)",
        "sources": ["routes"],
        "tests": [
            "tests/unit/routes/",
            "tests/unit/test_admin_audit_routes.py",
            "tests/unit/test_admin_routes.py",
            "tests/unit/test_assets_routes.py",
            "tests/unit/test_auth_routes.py",
            "tests/unit/test_categories_routes.py",
            "tests/unit/test_dashboard_routes.py",
            "tests/unit/test_export_routes.py",
            "tests/unit/test_financial_education_routes.py",
            "tests/unit/test_logbook_routes.py",
            "tests/unit/test_monitoring_routes.py",
            "tests/unit/test_notifications_routes.py",
            "tests/unit/test_plans_routes.py",
            "tests/unit/test_profile_routes.py",
            "tests/unit/test_settings_routes.py",
            "tests/unit/test_strategy_routes.py",
            "tests/unit/test_tenant_routes.py",
            "tests/unit/test_transactions_routes.py",
            "tests/regression/test_transactions_api_contract.py",
            "tests/regression/test_phase4_api_contract.py",
            "tests/regression/test_reconciliation_api.py",
            "tests/regression/test_tenant_isolation_api.py",
        ],
        "target_min": 35.0,
    },
}


@dataclass
class LayerCoverageResult:
    key: str
    title: str
    covered_lines: int
    total_lines: int
    percent: float
    target_min: float
    baseline_percent: float | None
    duration_s: float
    passed: bool
    status_msg: str


def load_baseline() -> dict[str, float]:
    """Mevcut kapsama taban degerlerini yukler."""
    if BASELINE_PATH.exists():
        try:
            with open(BASELINE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("layers", {})
        except Exception:
            return {}
    return {}


def save_baseline(results: list[LayerCoverageResult]) -> None:
    """Yeni kapsama sonuclarini baseline dosyasina ratchet eder."""
    current = load_baseline()
    for r in results:
        # Ratchet: Yalnizca esit veya daha yuksekse guncelle
        prev = current.get(r.key, 0.0)
        current[r.key] = max(prev, round(r.percent, 2))

    data = {
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "layers": current,
    }
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n{GREEN}[RATCHET] Kapsama tabani guncellendi: {BASELINE_PATH}{RESET}")


def is_file_in_sources(fpath: str, sources: list[str]) -> bool:
    """Belirtilen dosyanin verilen kaynak dizinlerinden birine ait olup olmadigini dogrular."""
    norm_fpath = fpath.replace("\\", "/").lower().lstrip("./")
    for s in sources:
        norm_s = s.replace("\\", "/").lower().strip("/")
        if norm_fpath.startswith(norm_s + "/") or f"/{norm_s}/" in norm_fpath or norm_fpath == norm_s:
            return True
    return False


def audit_layer(key: str, cfg: dict[str, Any], baseline: dict[str, float]) -> LayerCoverageResult:
    """Tek bir katman icin testleri calistirir ve kapsama oranini hesaplar."""
    print(f"\n{CYAN}>> [{cfg['title']}] olculuyor...{RESET}", flush=True)
    sources = cfg["sources"]
    tests = cfg["tests"]
    target_min = cfg["target_min"]
    base_val = baseline.get(key)

    # Gecmis kosulardan kalan .coverage dosyalarini temizle
    for cov_artifact in [PROJECT_ROOT / ".coverage", *PROJECT_ROOT.glob(".coverage.*")]:
        try:
            cov_artifact.unlink()
        except OSError:
            pass

    temp_json = PROJECT_ROOT / f".cov_temp_{key}_{int(time.time())}.json"

    cov_args = [f"--cov={s}" for s in sources]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *tests,
        *cov_args,
        f"--cov-report=json:{temp_json}",
        "-q",
        "--disable-warnings",
    ]

    t0 = time.monotonic()
    subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration = time.monotonic() - t0

    covered = 0
    total = 0

    if temp_json.exists():
        try:
            with open(temp_json, "r", encoding="utf-8") as f:
                cov_data = json.load(f)
                files = cov_data.get("files", {})
                for fpath, finfo in files.items():
                    if not is_file_in_sources(fpath, sources):
                        continue
                    summary = finfo.get("summary", {})
                    covered += summary.get("covered_lines", 0)
                    total += summary.get("num_statements", 0)
        finally:
            try:
                temp_json.unlink()
            except OSError:
                pass

    percent = (covered / total * 100.0) if total > 0 else 0.0

    passed = True
    status_msg = "OK"

    # Kontrol 1: Ratchet - Baseline'dan geriye dusus var mi?
    if base_val is not None and percent < (base_val - 0.5):  # 0.5% marj
        passed = False
        status_msg = f"Kapsama Geriledi ({percent:.1f}% < Taban {base_val:.1f}%)"
    elif percent < target_min:
        passed = False
        status_msg = f"Hedefin Altinda (< {target_min}%)"

    color = GREEN if passed else RED
    print(f"   {color}[{status_msg}] Kapsama: {percent:.2f}% (Hedef: {target_min}%, {duration:.2f}s){RESET}", flush=True)

    return LayerCoverageResult(
        key=key,
        title=cfg["title"],
        covered_lines=covered,
        total_lines=total,
        percent=percent,
        target_min=target_min,
        baseline_percent=base_val,
        duration_s=duration,
        passed=passed,
        status_msg=status_msg,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="E-Cuzdan Katmanli Test Kapsama Denetleyicisi")
    parser.add_argument("--layer", choices=["all", *LAYER_CONFIGS.keys()], default="all", help="Olculecek katman")
    parser.add_argument("--enforce", action="store_true", help="Hedefin altinda veya gerilemede hata ver (Exit 1)")
    parser.add_argument("--ratchet", action="store_true", help="Guncel kapsama degerlerini taban olarak kaydet")
    args = parser.parse_args()

    print(f"{BOLD}{'=' * 78}{RESET}")
    print(f"{BOLD}  E-CUZDAN KATMANLI TEST KAPSAMA VE SIFIR-REGRESYON DENETIMI{RESET}")
    print(f"{BOLD}{'=' * 78}{RESET}")

    baseline = load_baseline()

    layers_to_run = (
        LAYER_CONFIGS.keys() if args.layer == "all" else [args.layer]
    )

    results: list[LayerCoverageResult] = []
    t_start = time.monotonic()

    for l_key in layers_to_run:
        res = audit_layer(l_key, LAYER_CONFIGS[l_key], baseline)
        results.append(res)

    total_duration = time.monotonic() - t_start

    # Dashboard Tablosu
    print(f"\n{BOLD}{'=' * 78}{RESET}")
    print(f"{BOLD}  KAPSAMA RAPORU TABLOSU (Toplam Sure: {total_duration:.2f}s){RESET}")
    print(f"{BOLD}{'=' * 78}{RESET}")
    print(f"{'Katman':<42} {'Kapsanan / Toplam':<18} {'Oran':<10} {'Hedef':<8} {'Durum'}")
    print(f"{'-' * 78}")

    for r in results:
        status_badge = f"{GREEN}PASS{RESET}" if r.passed else f"{RED}FAIL{RESET}"
        lines_str = f"{r.covered_lines}/{r.total_lines}"
        pct_str = f"{r.percent:.1f}%"
        target_str = f"{r.target_min:.0f}%"
        print(f"{r.title:<42} {lines_str:<18} {pct_str:<10} {target_str:<8} {status_badge} ({r.status_msg})")

    print(f"{BOLD}{'-' * 78}{RESET}")

    all_passed = all(r.passed for r in results)

    if args.ratchet:
        save_baseline(results)

    if not all_passed:
        print(f"\n{RED}{BOLD}[FAIL] Bazi katmanlarda test kapsama hedefleri karsilanmadi!{RESET}")
        if args.enforce:
            print(f"{RED}Enforce modu aktif oldugu icin islem durduruldu.{RESET}\n")
            return 1
    else:
        print(f"\n{GREEN}{BOLD}[PASS] Tum katmanlar kapsama ve kalite esiklerini basariyla gecti!{RESET}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
