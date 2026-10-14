"""
E-Cüzdan Type Annotation & Mypy Check Runner

Usage:
    python scripts/check_type_annotations.py
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

CHECKED_FILES = [
    "utils/format_utils.py",
    "shared/constants.py",
    "shared/cache.py",
    "shared/decimal_precision.py",
    "shared/currency_precision.py",
    "repositories/base.py",
    "repositories/user_repository.py",
    "repositories/category_repository.py",
    "domain/storage_health/services/data_hygiene_service.py",
]


def main() -> int:
    print("==================================================")
    print("[MYPY] E-Cuzdan Static Type Check")
    print("==================================================")

    # Auto-detect venv python
    venv_py_win = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    venv_py_unix = ROOT_DIR / ".venv" / "bin" / "python"

    if venv_py_win.exists():
        py_bin = str(venv_py_win)
    elif venv_py_unix.exists():
        py_bin = str(venv_py_unix)
    else:
        py_bin = sys.executable

    cmd = [py_bin, "-m", "mypy"] + CHECKED_FILES
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode == 0:
        print("\n[PASS] Mypy tip kontrolu basarili - 0 hata!")
    else:
        print("\n[FAIL] Mypy tip kontrolu basarisiz!")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
