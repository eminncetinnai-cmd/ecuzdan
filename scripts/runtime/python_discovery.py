"""E-Cüzdan Runtime Bootstrap - Python Discovery Engine.

Discovers system Python interpreters on Windows:
  - py -3.13
  - py -3
  - py
  - python
  - PATH lookup
Verifies version compatibility (>= 3.13, < 3.14) and venv module support.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class PythonDiscoveryResult:
    executable: str
    version_str: str
    major: int
    minor: int
    micro: int
    is_compatible: bool
    has_venv: bool
    error_message: str = ""


_MIN_PYTHON = (3, 13, 0)
_MAX_PYTHON = (3, 14, 0)


class PythonDiscoveryEngine:
    """Discovers and validates host Python interpreters."""

    def __init__(self, min_version: tuple[int, int, int] = _MIN_PYTHON, max_version: tuple[int, int, int] = _MAX_PYTHON) -> None:
        self.min_version = min_version
        self.max_version = max_version

    def _test_candidate(self, cmd_args: list[str]) -> PythonDiscoveryResult | None:
        probe_code = (
            "import sys; "
            "import venv; "
            "print(f'{sys.executable}|{sys.version_info.major}|{sys.version_info.minor}|{sys.version_info.micro}')"
        )
        try:
            res = subprocess.run(
                cmd_args + ["-c", probe_code],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split("|")
                if len(parts) == 4:
                    exe, maj, min_, mic = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
                    v_tuple = (maj, min_, mic)
                    compatible = self.min_version <= v_tuple < self.max_version
                    v_str = f"{maj}.{min_}.{mic}"
                    return PythonDiscoveryResult(
                        executable=exe,
                        version_str=v_str,
                        major=maj,
                        minor=min_,
                        micro=mic,
                        is_compatible=compatible,
                        has_venv=True,
                    )
        except Exception:
            pass
        return None

    def discover(self) -> PythonDiscoveryResult:
        candidates: list[list[str]] = [
            ["py", "-3.13"],
            ["py", "-3"],
            ["py"],
            ["python"],
            ["python3"],
        ]

        # Add current sys.executable if running
        if sys.executable:
            candidates.insert(0, [sys.executable])

        # Also search Windows PATH for python.exe
        which_python = shutil.which("python")
        if which_python and [which_python] not in candidates:
            candidates.append([which_python])

        best_incompatible: PythonDiscoveryResult | None = None

        for candidate in candidates:
            res = self._test_candidate(candidate)
            if res is not None:
                if res.is_compatible:
                    return res
                if best_incompatible is None:
                    best_incompatible = res

        if best_incompatible is not None:
            return PythonDiscoveryResult(
                executable=best_incompatible.executable,
                version_str=best_incompatible.version_str,
                major=best_incompatible.major,
                minor=best_incompatible.minor,
                micro=best_incompatible.micro,
                is_compatible=False,
                has_venv=best_incompatible.has_venv,
                error_message=(
                    f"Found Python {best_incompatible.version_str} at {best_incompatible.executable}, "
                    f"but E-Cüzdan requires Python >={self.min_version[0]}.{self.min_version[1]} "
                    f"and <{self.max_version[0]}.{self.max_version[1]}."
                ),
            )

        return PythonDiscoveryResult(
            executable="",
            version_str="",
            major=0,
            minor=0,
            micro=0,
            is_compatible=False,
            has_venv=False,
            error_message="No suitable Python runtime found on system. Please install Python 3.13 from python.org.",
        )
