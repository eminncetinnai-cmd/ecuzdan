"""E-Cüzdan Runtime Bootstrap - Application Launcher.

Launches the application using the verified virtual environment interpreter:
  - Invokes [venv_python, "app.py"]
  - Manages browser launch on startup
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


class ApplicationLauncher:
    """Launches the verified E-Cüzdan application instance."""

    def __init__(self, repo_root: str | pathlib.Path, venv_python: str | pathlib.Path) -> None:
        self.repo_root = pathlib.Path(repo_root).resolve()
        self.venv_python = str(venv_python)

    def launch(self, entrypoint: str = "app.py") -> int:
        entry_path = self.repo_root / entrypoint
        if not entry_path.is_file():
            raise FileNotFoundError(f"Application entrypoint '{entrypoint}' not found at: {entry_path}")

        cmd = [self.venv_python, str(entry_path)]
        try:
            # Run application directly (inheriting stdio so server logs display in console)
            res = subprocess.run(cmd, cwd=str(self.repo_root), check=False)
            return res.returncode
        except KeyboardInterrupt:
            print("\nApplication stopped by user.")
            return 0
        except Exception as exc:
            print(f"\nApplication launch error: {exc}", file=sys.stderr)
            return 1
