#!/usr/bin/env python3
"""Static scan for potentially sensitive data in logger calls."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    '.git', '.pytest_cache', 'htmlcov', 'venv', '__pycache__', 'logs', 'instance', 'tests',
}

PATTERNS = [
    (
        'csrf_token_in_log',
        re.compile(
            r'logger\.(info|warning|error|debug|exception)\([^)]*'
            r'(Request token|Session token|csrf_token)\s*[:=]',
            re.IGNORECASE,
        ),
    ),
    (
        'raw_password_in_log',
        re.compile(
            r'logger\.(info|warning|error|debug)\([^)]*password\s*[:=]\s*[^\'"\s*]+',
            re.IGNORECASE,
        ),
    ),
    (
        'raw_email_in_log',
        re.compile(
            r'logger\.(info|warning|error|debug)\([^)]*email\s*=\s*\{?user_info\.email\}?',
            re.IGNORECASE,
        ),
    ),
]


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob('*.py'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.endswith(',cover'):
            continue
        files.append(path)
    return files


def scan() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []
    for file_path in iter_python_files():
        try:
            lines = file_path.read_text(encoding='utf-8').splitlines()
        except OSError:
            continue

        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if 'logger.' not in stripped:
                continue
            for rule_name, pattern in PATTERNS:
                if pattern.search(stripped):
                    findings.append((rule_name, line_no, str(file_path.relative_to(ROOT)), stripped))
    return findings


def main() -> int:
    findings = scan()
    if not findings:
        print('PII log scan: no issues found.')
        return 0

    print('PII log scan: potential sensitive logging detected:')
    for rule_name, line_no, file_path, line in findings:
        print(f'  [{rule_name}] {file_path}:{line_no}: {line}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
