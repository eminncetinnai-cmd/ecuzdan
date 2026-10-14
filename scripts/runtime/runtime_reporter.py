"""E-Cüzdan Runtime Bootstrap - UI & Diagnostics Reporter.

Provides clean console output for the end-user:
  [1/6] Checking Python .......... OK
  [2/6] Checking environment ..... OK
  ...
Safely handles errors without leaking secrets or credentials.
"""

from __future__ import annotations

import re

_SECRET_KEY_PATTERNS = re.compile(
    r"(secret|token|password|key|auth|credential|bearer)[\s:=]+([^\s,;]+)",
    re.IGNORECASE,
)


def mask_sensitive_text(text: str) -> str:
    """Mask any sensitive key/password patterns in diagnostic text."""
    if not text:
        return ""
    return _SECRET_KEY_PATTERNS.sub(r"\1: [REDACTED]", text)


class RuntimeReporter:
    """Console reporter for bootstrap lifecycle."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def banner(self, text: str = "E-Cüzdan — Intelligent Wealth Platform") -> None:
        print(r"""
  _____         ____ _   _ _____ ____    _    _   _ 
 | ____|       / ___| | | |__  /|  _ \  / \  | \ | |
 |  _|  _____ | |   | | | | / / | | | |/ _ \ |  \| |
 | |___|_____|| |___| |_| |/ /_ | |_| / ___ \| |\  |
 |_____|       \____|\___//____||____/_/   \_\_| \_|
                                                    
 ============================================================
   E-CÜZDAN — INTELLIGENT WEALTH & RUNTIME BOOTSTRAP
 ============================================================
""")

    def step(self, current: int, total: int, title: str, status: str = "OK") -> None:
        dot_count = max(2, 40 - len(title))
        dots = "." * dot_count
        print(f"[{current}/{total}] {title} {dots} {status}")

    def info(self, msg: str) -> None:
        print(f"  -> {mask_sensitive_text(msg)}")

    def success(self, msg: str) -> None:
        print(f"\n[OK] {mask_sensitive_text(msg)}\n")

    def warning(self, msg: str) -> None:
        print(f"\n[WARN] {mask_sensitive_text(msg)}")

    def error_block(self, stage: str, reason: str, suggested_action: str = "") -> None:
        print("\n" + "=" * 60)
        print("BOOTSTRAP FAILED")
        print("=" * 60)
        print(f"Stage           : {stage}")
        print(f"Reason          : {mask_sensitive_text(reason)}")
        if suggested_action:
            print(f"Suggested Action: {mask_sensitive_text(suggested_action)}")
        print("=" * 60 + "\n")
