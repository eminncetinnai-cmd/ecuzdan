#!/usr/bin/env python3
"""E-Cüzdan Master Kalite ve Yönetişim Kapısı Doğrulayıcı (verify_all.py).

Tüm kurumsal kalite kapılarını tek komutla sırasıyla çalıştırır:
  1. Tasarım Sistemi Tutarlılığı (check_design_system.py --ratchet)
  2. EAFGS Mimari ve Dosya Yerleşim Kapısı (architecture_gate.py - Mode BLOCK)
  3. Mypy Statik Tip Denetimi (check_type_annotations.py)
  4. Pre-Flight 500 & Şablon Smoke Gate (preflight_check.py)
  5. Canlı Defter ve Bakiye Sapma Bekçisi (run_ledger_watchdog.py)
  6. N+1 SQL Sorgu & Performans SLA Kapısı (check_query_performance.py)
  7. Çok Kiracılı Güvenlik & IDOR Fuzzer'ı (fuzz_tenant_isolation.py)
  8. Birim Testleri (pytest tests/unit/ -q --no-cov)
  9. Katmanlı Kapsama & Sıfır-Regresyon Kapısı (audit_coverage.py --enforce)

Kullanım:
  python scripts/verify_all.py
  python scripts/verify_all.py --fast  (Uzun testleri atlayarak statik, smoke ve anlık watchdog kapılarını çalıştırır)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Windows console encoding uyumluluğu
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Renk sabitleri (ANSI)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class GateResult:
    name: str
    command: list[str]
    success: bool
    duration_s: float
    output: str
    exit_code: int


def run_gate(name: str, command: list[str], env_extra: dict[str, str] | None = None) -> GateResult:
    print(f"\n{CYAN}{BOLD}>> [{name}] calistiriliyor...{RESET}")
    print(f"   Komut: {' '.join(command)}")

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    t0 = time.monotonic()
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    duration = time.monotonic() - t0
    success = proc.returncode == 0

    if success:
        print(f"   {GREEN}[OK] BASARILI ({duration:.2f}s){RESET}")
    else:
        print(f"   {RED}[FAIL] BASARISIZ (Cikis kodu: {proc.returncode}, {duration:.2f}s){RESET}")
        if proc.stdout:
            print(f"\n{YELLOW}--- STANDART CIKTI ---{RESET}\n{proc.stdout.strip()}")
        if proc.stderr:
            print(f"\n{RED}--- HATA CIKTISI ---{RESET}\n{proc.stderr.strip()}")

    return GateResult(
        name=name,
        command=command,
        success=success,
        duration_s=duration,
        output=(proc.stdout or "") + "\n" + (proc.stderr or ""),
        exit_code=proc.returncode,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="E-Cuzdan Master Kalite Kapisi")
    parser.add_argument("--fast", action="store_true", help="Pytest test paketini atla (sadece statik denetimler)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  E-CUZDAN MASTER KALITE VE YONETISIM KONTROL PANELI{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    gates: list[tuple[str, list[str], dict[str, str] | None]] = [
        (
            "Tasarim Sistemi Ratchet",
            [sys.executable, "scripts/check_design_system.py", "--ratchet"],
            None,
        ),
        (
            "EAFGS Mimari Yonetisim Kapisi",
            [sys.executable, "scripts/governance/architecture_gate.py"],
            {"EAFGS_MODE": "BLOCK"},
        ),
        (
            "Mypy Statik Tip Denetimi",
            [sys.executable, "scripts/check_type_annotations.py"],
            None,
        ),
        (
            "Pre-Flight 500 & Sablon Smoke Testi",
            [sys.executable, "scripts/preflight_check.py"],
            None,
        ),
        (
            "Canli Defter & Bakiye Sapma Bekcisi",
            [sys.executable, "scripts/run_ledger_watchdog.py"],
            None,
        ),
    ]

    if not args.fast:
        gates.append((
            "N+1 SQL Sorgu & Performans SLA Kapisi",
            [sys.executable, "scripts/check_query_performance.py"],
            None,
        ))
        gates.append((
            "Cok Kiracili Penetrasyon & IDOR Fuzzer'i",
            [sys.executable, "scripts/fuzz_tenant_isolation.py"],
            None,
        ))
        gates.append((
            "Birim Test Paketi (Pytest)",
            [sys.executable, "-m", "pytest", "tests/unit/", "-q", "--no-cov"],
            None,
        ))
        gates.append((
            "Katmanli Kapsama & Sifir-Regresyon Kapisi",
            [sys.executable, "scripts/audit_coverage.py", "--enforce"],
            None,
        ))

    results: list[GateResult] = []
    total_t0 = time.monotonic()

    for name, cmd, env_extra in gates:
        res = run_gate(name, cmd, env_extra)
        results.append(res)
        if not res.success:
            print(f"\n{RED}{BOLD}DURDURULDU: '{name}' kapisi basarisiz oldugu icin sonraki adimlar isletilmedi.{RESET}")
            break

    total_duration = time.monotonic() - total_t0

    # Dashboard Özeti
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  DOGRULAMA OZETI (Toplam Sure: {total_duration:.2f}s){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    all_passed = all(r.success for r in results) and len(results) == len(gates)

    for r in results:
        status_badge = f"{GREEN}PASS{RESET}" if r.success else f"{RED}FAIL{RESET}"
        print(f"  [{status_badge}] {r.name:<38} ({r.duration_s:.2f}s)")

    if not all_passed and len(results) < len(gates):
        for name, _, _ in gates[len(results):]:
            print(f"  [{YELLOW}SKIP{RESET}] {name:<38} (Calistirilmadi)")

    print(f"{BOLD}{'-' * 72}{RESET}")
    if all_passed:
        print(f"{GREEN}{BOLD}[PASS] TEBRIKLER: TUM KALITE VE YONETISIM KAPILARI BASARIYLA GECILDI!{RESET}")
        print(f"{BOLD}{'=' * 72}{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}[FAIL] HATA: BAZI KAPILAR BASARISIZ OLDU. LUTFEN YUKARIDAKI HATALARI DUZELTIN.{RESET}")
        print(f"{BOLD}{'=' * 72}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
