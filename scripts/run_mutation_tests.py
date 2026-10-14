#!/usr/bin/env python3
"""E-Cüzdan Finansal Mutasyon Testi Çalıştırıcısı (run_mutation_tests.py).

Kritik finansal hesaplama modüllerinde (decimal_precision, financial_consistency vb.)
kasıtlı mutasyonlar (operatör tersine çevirme, sınır koşulu değiştirme) üreterek
mevcut test paketlerinin bu mutasyonları yakalama gücünü (Mutation Score) ölçer.

Kullanım:
  python scripts/run_mutation_tests.py
  python scripts/run_mutation_tests.py --max-mutations 20
  python scripts/run_mutation_tests.py --target-score 80
"""

from __future__ import annotations

import argparse
import ast
import re
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

# ANSI Renkleri
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Test edilecek öncelikli finansal modüller ve bunlara ait testler
TARGET_MUTATION_MODULES = [
    {
        "file": "shared/decimal_precision.py",
        "tests": [
            "tests/unit/financial/test_financial_invariants.py",
            "tests/unit/financial/test_property_based_decimal.py",
            "tests/unit/test_ledger_decimal_boundary.py",
        ],
    },
    {
        "file": "domain/ledger/services/financial_consistency.py",
        "tests": [
            "tests/unit/test_financial_consistency_checker.py",
            "tests/unit/financial/test_financial_invariants.py",
        ],
    },
]


@dataclass
class MutationPoint:
    file_path: Path
    line_number: int
    col_offset: int
    original_op: str
    mutated_op: str
    description: str


class MutationFinder(ast.NodeVisitor):
    """AST üzerinde mutasyona uygun noktaları tespit eder."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.mutations: list[MutationPoint] = []

    def visit_BinOp(self, node: ast.BinOp) -> None:
        op_map = {
            ast.Add: (ast.Sub, "+", "-", "Toplama -> Çıkarma"),
            ast.Sub: (ast.Add, "-", "+", "Çıkarma -> Toplama"),
            ast.Mult: (ast.Div, "*", "/", "Çarpma -> Bölme"),
            ast.Div: (ast.Mult, "/", "*", "Bölme -> Çarpma"),
        }
        for orig_cls, (mut_cls, orig_str, mut_str, desc) in op_map.items():
            if isinstance(node.op, orig_cls):
                self.mutations.append(
                    MutationPoint(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        col_offset=node.col_offset,
                        original_op=orig_str,
                        mutated_op=mut_str,
                        description=desc,
                    )
                )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        cmp_map = {
            ast.Gt: (ast.LtE, ">", "<=", "Büyüktür -> Küçük Eşittir"),
            ast.Lt: (ast.GtE, "<", ">=", "Küçüktür -> Büyük Eşittir"),
            ast.Eq: (ast.NotEq, "==", "!=", "Eşittir -> Eşit Değildir"),
            ast.NotEq: (ast.Eq, "!=", "==", "Eşit Değildir -> Eşittir"),
            ast.GtE: (ast.Lt, ">=", "<", "Büyük Eşittir -> Küçüktür"),
            ast.LtE: (ast.Gt, "<=", ">", "Küçük Eşittir -> Büyüktür"),
        }
        for op in node.ops:
            for orig_cls, (mut_cls, orig_str, mut_str, desc) in cmp_map.items():
                if isinstance(op, orig_cls):
                    self.mutations.append(
                        MutationPoint(
                            file_path=self.file_path,
                            line_number=node.lineno,
                            col_offset=node.col_offset,
                            original_op=orig_str,
                            mutated_op=mut_str,
                            description=desc,
                        )
                    )
        self.generic_visit(node)


def apply_single_mutation(source_lines: list[str], mutation: MutationPoint) -> str:
    """Belirli bir satırdaki operatörü mutasyona uğratarak yeni kaynak kod üretir."""
    lines = list(source_lines)
    idx = mutation.line_number - 1
    if 0 <= idx < len(lines):
        line = lines[idx]
        # Yalnızca ilk eşleşen operatörü değiştir
        # Regex veya güvenli değiştirme
        pattern = re.escape(mutation.original_op)
        new_line = re.sub(pattern, mutation.mutated_op, line, count=1)
        lines[idx] = new_line
    return "".join(lines)


def run_tests_for_mutation(tests: list[str]) -> bool:
    """Testleri çalıştırır. Test başarısız olursa (mutasyon yakalanırsa) True döner."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *tests,
        "-q",
        "--no-cov",
        "--disable-warnings",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # Çıkış kodu != 0 ise test patlamıştır (Mutasyon Başarıyla Öldürüldü)
    return proc.returncode != 0


def main() -> int:
    parser = argparse.ArgumentParser(description="E-Cüzdan Finansal Mutasyon Testi")
    parser.add_argument("--max-mutations", type=int, default=20, help="Çalıştırılacak azami mutasyon adedi (Varsayılan: 20)")
    parser.add_argument("--target-score", type=float, default=80.0, help="Hedef Mutasyon Skoru Yüzde (Varsayılan: 80.0)")
    args = parser.parse_args()

    print(f"{BOLD}{'=' * 78}{RESET}")
    print(f"{BOLD}  E-CUZDAN FINANSAL MUTASYON TESTI (TESTLERIN GUCU VE KALITESI){RESET}")
    print(f"{BOLD}{'=' * 78}{RESET}")

    total_mutations_tested = 0
    killed_mutations = 0
    survived_mutations = 0

    t0 = time.monotonic()

    for config in TARGET_MUTATION_MODULES:
        rel_file = config["file"]
        tests = config["tests"]
        target_path = PROJECT_ROOT / rel_file

        if not target_path.exists():
            continue

        print(f"\n{CYAN}>> Modül Taranıyor: {rel_file}{RESET}")

        with open(target_path, "r", encoding="utf-8") as f:
            source_content = f.read()
            source_lines = source_content.splitlines(keepends=True)

        try:
            tree = ast.parse(source_content, filename=str(target_path))
        except SyntaxError as e:
            print(f"{RED}AST Ayrıştırma Hatası: {e}{RESET}")
            continue

        finder = MutationFinder(target_path)
        finder.visit(tree)

        available_mutations = finder.mutations
        print(f"   Bulunan potansiyel mutasyon noktası: {len(available_mutations)}")

        # Seçilen mutasyon adedi
        step = max(1, len(available_mutations) // (args.max_mutations // len(TARGET_MUTATION_MODULES) or 1))
        sampled_mutations = available_mutations[::step][: args.max_mutations // len(TARGET_MUTATION_MODULES)]

        for mut in sampled_mutations:
            mutated_code = apply_single_mutation(source_lines, mut)
            if mutated_code == source_content:
                continue

            # Mutasyonlu kodu geçici olarak yaz
            try:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(mutated_code)

                # Testleri çalıştır
                was_killed = run_tests_for_mutation(tests)
                total_mutations_tested += 1

                if was_killed:
                    killed_mutations += 1
                    status = f"{GREEN}[KILLED]{RESET}"
                    note = "Testler hatayı yakaladı 🎯"
                else:
                    survived_mutations += 1
                    status = f"{RED}[SURVIVED]{RESET}"
                    note = "Testler bu hatayı fark edemedi! ⚠️"

                print(f"   {status} Satır {mut.line_number}: {mut.description:<30} -> {note}")

            finally:
                # Orijinal kodu her koşulda geri yükle
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(source_content)

    duration = time.monotonic() - t0

    mutation_score = (
        (killed_mutations / total_mutations_tested * 100.0)
        if total_mutations_tested > 0
        else 100.0
    )

    print(f"\n{BOLD}{'=' * 78}{RESET}")
    print(f"{BOLD}  MUTASYON TESTI SONUC OZETI (Sure: {duration:.2f}s){RESET}")
    print(f"{BOLD}{'=' * 78}{RESET}")
    print(f"  Toplam Denenen Mutasyon  : {total_mutations_tested}")
    print(f"  Öldürülen Mutasyon (Killed) : {GREEN}{killed_mutations}{RESET}")
    print(f"  Hayatta Kalan (Survived)    : {RED if survived_mutations > 0 else GREEN}{survived_mutations}{RESET}")
    print(f"  Mutasyon Skoru (Güç)        : {BOLD}{mutation_score:.1f}%{RESET} (Hedef: %{args.target_score:.1f})")
    print(f"{BOLD}{'-' * 78}{RESET}")

    if mutation_score >= args.target_score:
        print(f"\n{GREEN}{BOLD}[PASS] TEBRIKLER! Finansal test paketiniz mutasyonlara karsi son derece guclu!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}[FAIL] Test paketinin mutasyon skoru hedefin altında kaldı.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
