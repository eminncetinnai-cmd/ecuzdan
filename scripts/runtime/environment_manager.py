"""E-Cüzdan Runtime Bootstrap - Virtual Environment Manager.

Manages the .venv lifecycle on Windows:
  - Validates existing .venv interpreter and pip
  - Creates .venv if missing via [python_exe, "-m", "venv", ".venv"]
  - Diagnoses and repairs environment without blind destructive deletion
"""

from __future__ import annotations

import os
import pathlib
import subprocess
from dataclasses import dataclass


@dataclass
class EnvironmentStatus:
    venv_dir: pathlib.Path
    python_exe: pathlib.Path
    is_valid: bool
    is_newly_created: bool
    error_message: str = ""


class EnvironmentManager:
    """Manages Python virtual environment lifecycle."""

    def __init__(self, repo_root: str | pathlib.Path, venv_name: str = ".venv") -> None:
        self.repo_root = pathlib.Path(repo_root).resolve()
        self.venv_dir = self.repo_root / venv_name

    def get_venv_python(self) -> pathlib.Path:
        if os.name == "nt":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def validate_existing_venv(self) -> tuple[bool, str]:
        venv_py = self.get_venv_python()
        if not venv_py.exists():
            return False, f"Virtual environment interpreter not found at: {venv_py}"

        # Test interpreter execution and pip
        try:
            res = subprocess.run(
                [str(venv_py), "-c", "import sys; import pip; print(sys.version)"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0:
                return True, ""
            return False, f"Virtual environment interpreter check failed: {res.stderr.strip()}"
        except Exception as exc:
            return False, f"Failed to execute virtual environment interpreter: {exc}"

    def ensure_environment(self, host_python_exe: str) -> EnvironmentStatus:
        venv_py = self.get_venv_python()

        # 1. Existing .venv validation
        if self.venv_dir.exists():
            is_valid, err = self.validate_existing_venv()
            if is_valid:
                return EnvironmentStatus(
                    venv_dir=self.venv_dir,
                    python_exe=venv_py,
                    is_valid=True,
                    is_newly_created=False,
                )
            # If invalid, attempt non-destructive pip / venv bootstrap repair
            repair_cmd = [host_python_exe, "-m", "venv", "--upgrade", str(self.venv_dir)]
            try:
                subprocess.run(repair_cmd, capture_output=True, text=True, timeout=30, check=False)
                is_valid_after, err_after = self.validate_existing_venv()
                if is_valid_after:
                    return EnvironmentStatus(
                        venv_dir=self.venv_dir,
                        python_exe=venv_py,
                        is_valid=True,
                        is_newly_created=False,
                    )
            except Exception:
                pass

            return EnvironmentStatus(
                venv_dir=self.venv_dir,
                python_exe=venv_py,
                is_valid=False,
                is_newly_created=False,
                error_message=f"Existing .venv is corrupted: {err}",
            )

        # 2. Missing .venv creation
        try:
            cmd = [host_python_exe, "-m", "venv", str(self.venv_dir)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
            if res.returncode != 0:
                return EnvironmentStatus(
                    venv_dir=self.venv_dir,
                    python_exe=venv_py,
                    is_valid=False,
                    is_newly_created=False,
                    error_message=f"Failed to create .venv: {res.stderr.strip()}",
                )

            is_valid, err = self.validate_existing_venv()
            return EnvironmentStatus(
                venv_dir=self.venv_dir,
                python_exe=venv_py,
                is_valid=is_valid,
                is_newly_created=True,
                error_message=err,
            )
        except Exception as exc:
            return EnvironmentStatus(
                venv_dir=self.venv_dir,
                python_exe=venv_py,
                is_valid=False,
                is_newly_created=False,
                error_message=f"Exception creating .venv: {exc}",
            )
