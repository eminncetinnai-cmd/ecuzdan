#!/usr/bin/env python3
"""E-Cüzdan Git Hook Yükleyici (install_hooks.py).

scripts/hooks/ altındaki kurumsal git kancalarını (pre-commit, pre-push)
.git/hooks/ dizinine yükler ve çalıştırılabilir hale getirir.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_HOOKS_DIR = PROJECT_ROOT / "scripts" / "hooks"
TARGET_HOOKS_DIR = PROJECT_ROOT / ".git" / "hooks"


def install_hooks() -> int:
    if not TARGET_HOOKS_DIR.exists():
        print(f"HATA: .git/hooks dizini bulunamadi ({TARGET_HOOKS_DIR}). Proje git reposu mu?")
        return 1

    hook_names = ["pre-commit", "pre-push"]
    for hook_name in hook_names:
        src = SOURCE_HOOKS_DIR / hook_name
        dst = TARGET_HOOKS_DIR / hook_name

        if not src.exists():
            print(f"UYARI: Kaynak kanca bulunamadi: {src}")
            continue

        shutil.copy2(src, dst)
        # Unix/Git bash için çalıştırma izni
        try:
            os.chmod(dst, 0o755)
        except Exception:
            pass

        print(f"[OK] Git Hook basariyla yuklendi: .git/hooks/{hook_name}")

    print("\nTum git kancalari yuklendi:")
    print("  - pre-commit: Tasarim sistemi, Mimari kapisi, Mypy ve Ledger Watchdog")
    print("  - pre-push:   verify_all.py (Query profiler, IDOR fuzzer, testler ve kapsama)")
    return 0


if __name__ == "__main__":
    sys.exit(install_hooks())
