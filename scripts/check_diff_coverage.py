#!/usr/bin/env python3
"""E-Cüzdan Değişiklik Bazlı Test Kapsama Denetleyicisi (check_diff_coverage.py).

Git diff üzerindeki yeni eklenen ve değiştirilen kaynak kod satırlarının
(Diff Coverage) testler tarafından çalıştırılıp çalıştırılmadığını denetler.
Yeni yazılan veya güncellenen iş mantığının testsiz depoya girmesini engeller.

Kullanım:
  python scripts/check_diff_coverage.py
  python scripts/check_diff_coverage.py --staged
  python scripts/check_diff_coverage.py --target 90
  python scripts/check_diff_coverage.py --run-tests
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

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

# Yalnızca ana uygulama mantığı dizinlerindeki değişiklikler diff coverage'a tabidir
MONITORED_PREFIXES = (
    "domain/",
    "application/",
    "repositories/",
    "routes/",
    "services/",
    "engines/",
    "shared/",
    "utils/",
    "database/",
)

# Harici tutulacak desenler (testler, göç scriptleri, konfigürasyon)
EXCLUDED_PATTERNS = (
    "tests/",
    "database/migrations/",
    "database/seeds/",
    "scripts/",
    "setup.py",
)


class FileDiffCoverage(NamedTuple):
    filepath: str
    changed_lines: set[int]
    executable_lines: set[int]
    covered_lines: set[int]
    missing_lines: set[int]

    @property
    def total_executable_changed(self) -> int:
        return len(self.executable_lines)

    @property
    def covered_count(self) -> int:
        return len(self.covered_lines)

    @property
    def coverage_percent(self) -> float:
        if not self.executable_lines:
            return 100.0
        return (len(self.covered_lines) / len(self.executable_lines)) * 100.0


def get_git_diff_hunks(staged: bool = False, base_ref: str | None = None) -> dict[str, set[int]]:
    """Git diff çıktısından dosya bazında değiştirilen/eklenen satır numaralarını çeker."""
    cmd = ["git", "diff", "-U0", "--no-color"]
    if staged:
        cmd.append("--cached")
    elif base_ref:
        cmd.extend([base_ref, "HEAD"])
    else:
        # Hem staged hem unstaged farkları kapsamak için HEAD baz alınır
        cmd.append("HEAD")

    try:
        res = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        print(f"{YELLOW}[UYARI] Git diff alınamadı: {exc}{RESET}")
        return {}

    file_diffs: dict[str, set[int]] = {}
    current_file: str | None = None
    diff_line_re = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for line in res.stdout.splitlines():
        diff_match = diff_line_re.match(line)
        if diff_match:
            filepath = diff_match.group(2).replace("\\", "/")
            # Yalnızca python kaynak dosyaları
            if filepath.endswith(".py") and filepath.startswith(MONITORED_PREFIXES):
                if not any(filepath.startswith(exc) for exc in EXCLUDED_PATTERNS):
                    current_file = filepath
                    if current_file not in file_diffs:
                        file_diffs[current_file] = set()
                else:
                    current_file = None
            else:
                current_file = None
            continue

        if current_file:
            hunk_match = hunk_re.match(line)
            if hunk_match:
                start = int(hunk_match.group(1))
                count = int(hunk_match.group(2)) if hunk_match.group(2) is not None else 1
                if count > 0:
                    for lno in range(start, start + count):
                        file_diffs[current_file].add(lno)

    return file_diffs


def run_tests_for_coverage() -> bool:
    """Kapsama verisini güncellemek için pytest'i çalıştırır."""
    print(f"\n{CYAN}>> Kapsama ölçümü için pytest çalıştırılıyor...{RESET}")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/",
        "--cov=.",
        "--cov-report=",
        "-q",
        "--disable-warnings",
    ]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return res.returncode == 0


def analyze_diff_coverage(file_diffs: dict[str, set[int]]) -> list[FileDiffCoverage]:
    """Değişen satırları Coverage motoru ile analiz eder."""
    try:
        import coverage
    except ImportError:
        print(f"{RED}[HATA] 'coverage' paketi yüklü değil!{RESET}")
        return []

    cov = coverage.Coverage()
    try:
        cov.load()
    except Exception:
        # .coverage dosyası yoksa veya bozuksa
        print(f"{YELLOW}[BİLGİ] .coverage verisi bulunamadı, testler çalıştırılıyor...{RESET}")
        run_tests_for_coverage()
        cov.load()

    cov_data = cov.get_data()
    measured_files = {Path(p).resolve(): p for p in cov_data.measured_files()}

    results: list[FileDiffCoverage] = []

    for rel_path, changed_lines in file_diffs.items():
        if not changed_lines:
            continue

        abs_path = (PROJECT_ROOT / rel_path).resolve()
        if not abs_path.exists():
            continue

        # Dosyanın çalıştırılabilir ve kapsanan satırlarını tespit et
        try:
            analysis = cov.analysis(str(abs_path))
            # analysis: (filename, executable_statements, excluded, missing, formatted_missing)
            file_executable_lines = set(analysis[1])
        except Exception:
            file_executable_lines = set()

        # Değişen satırlardan yalnızca çalıştırılabilir (kod) olanlar
        executable_changed = changed_lines & file_executable_lines

        # Kapsanan satırlar
        measured_key = measured_files.get(abs_path)
        if measured_key:
            executed_in_file = set(cov_data.lines(measured_key) or [])
        else:
            executed_in_file = set()

        covered_changed = executable_changed & executed_in_file
        missing_changed = executable_changed - executed_in_file

        results.append(
            FileDiffCoverage(
                filepath=rel_path,
                changed_lines=changed_lines,
                executable_lines=executable_changed,
                covered_lines=covered_changed,
                missing_lines=missing_changed,
            )
        )

    return results


def format_line_ranges(lines: set[int]) -> str:
    """Sıralı satır numaralarını aralıklar olarak gruplar (örn: 12-15, 22)."""
    if not lines:
        return "-"
    sorted_lines = sorted(lines)
    ranges = []
    start = sorted_lines[0]
    end = start

    for l in sorted_lines[1:]:
        if l == end + 1:
            end = l
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = l
            end = l
    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(ranges)


def main() -> int:
    parser = argparse.ArgumentParser(description="E-Cüzdan Değişiklik Bazlı Test Kapsama Denetleyicisi")
    parser.add_argument("--staged", action="store_true", help="Yalnızca stage edilmiş (git add) değişiklikleri denetle")
    parser.add_argument("--base", type=str, default=None, help="Karşılaştırılacak git referansı (örn: origin/master)")
    parser.add_argument("--target", type=float, default=85.0, help="Minimum diff coverage hedefi yüzde (Varsayılan: 85.0)")
    parser.add_argument("--run-tests", action="store_true", help="Analizden önce testleri çalıştırarak .coverage verisini tazele")
    args = parser.parse_args()

    print(f"{BOLD}{'=' * 78}{RESET}")
    print(f"{BOLD}  E-CUZDAN DEGISIKLIK BAZLI TEST KAPSAMA DENETIMI (DIFF COVERAGE){RESET}")
    print(f"{BOLD}{'=' * 78}{RESET}")

    if args.run_tests:
        run_tests_for_coverage()

    file_diffs = get_git_diff_hunks(staged=args.staged, base_ref=args.base)

    if not file_diffs:
        print(f"\n{GREEN}[PASS] İzlenen uygulama dizinlerinde değiştirilmiş Python kodu bulunamadı.{RESET}")
        print(f"{GREEN}Diff coverage denetimi başarıyla tamamlandı (0 satır).{RESET}\n")
        return 0

    results = analyze_diff_coverage(file_diffs)

    if not results or all(r.total_executable_changed == 0 for r in results):
        print(f"\n{GREEN}[PASS] Değiştirilen satırlarda çalıştırılabilir kod ifadesi bulunamadı (yorum/boş satır).{RESET}")
        print(f"{GREEN}Diff coverage denetimi başarıyla tamamlandı.{RESET}\n")
        return 0

    total_executable = sum(r.total_executable_changed for r in results)
    total_covered = sum(r.covered_count for r in results)
    overall_diff_coverage = (total_covered / total_executable * 100.0) if total_executable > 0 else 100.0

    print(f"\n{BOLD}{'Dosya':<45} {'Değişen Kod':<13} {'Kapsanan':<10} {'Oran':<8} {'Durum'}{RESET}")
    print(f"{'-' * 78}")

    has_failure = False
    for r in results:
        if r.total_executable_changed == 0:
            continue

        is_ok = r.coverage_percent >= args.target
        status_badge = f"{GREEN}PASS{RESET}" if is_ok else f"{RED}FAIL{RESET}"
        pct_str = f"{r.coverage_percent:.1f}%"
        print(f"{r.filepath:<45} {r.total_executable_changed:<13} {r.covered_count:<10} {pct_str:<8} {status_badge}")

        if not is_ok:
            has_failure = True
            missing_str = format_line_ranges(r.missing_lines)
            print(f"   {RED}↳ Testsiz Satırlar: {missing_str}{RESET}")

    print(f"{BOLD}{'-' * 78}{RESET}")
    overall_status = f"{GREEN}PASS{RESET}" if overall_diff_coverage >= args.target else f"{RED}FAIL{RESET}"
    print(f"{BOLD}GENEL DIFF KAPSAMASI:{RESET} {total_covered}/{total_executable} satır ({BOLD}{overall_diff_coverage:.1f}%{RESET}) [Hedef: %{args.target:.1f}] -> {overall_status}")
    print(f"{BOLD}{'=' * 78}{RESET}\n")

    if overall_diff_coverage < args.target or has_failure:
        print(f"{RED}{BOLD}[FAIL] Değiştirilen satırların test kapsaması %{args.target:.1f} hedefinin altında kaldı!{RESET}")
        print(f"{RED}Lütfen yukarıda listelenen satırlar için ilgili birim testleri ekleyin.{RESET}\n")
        return 1

    print(f"{GREEN}{BOLD}[PASS] Tebrikler! Tüm yeni/değiştirilen satırlar başarıyla test edildi.{RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
