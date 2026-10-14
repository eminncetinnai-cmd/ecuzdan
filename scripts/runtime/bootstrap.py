#!/usr/bin/env python3
"""E-Cüzdan Portable Runtime Bootstrap - Master Orchestrator.

The single Python bootstrap entrypoint invoked by START_E_CUZDAN.bat:
  [1/6] Checking Python .......... OK
  [2/6] Checking environment ..... OK
  [3/6] Checking dependencies .... OK
  [4/6] Checking configuration ... OK
  [5/6] Checking application ..... OK
  [6/6] Starting application ..... OK
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import webbrowser

# Ensure repository root is in sys.path
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.runtime.application_launcher import ApplicationLauncher
from scripts.runtime.configuration_validator import ConfigurationValidator
from scripts.runtime.dependency_manager import DependencyManager
from scripts.runtime.environment_manager import EnvironmentManager
from scripts.runtime.process_manager import ProcessManager
from scripts.runtime.python_discovery import PythonDiscoveryEngine
from scripts.runtime.runtime_reporter import RuntimeReporter


class RuntimeBootstrap:
    """Orchestrates the portable first-run installation and startup lifecycle."""

    def __init__(self, repo_root: str | pathlib.Path | None = None, reporter: RuntimeReporter | None = None) -> None:
        self.repo_root = pathlib.Path(repo_root or _REPO_ROOT).resolve()
        self.reporter = reporter or RuntimeReporter()

    def run(self, check_only: bool = False) -> int:
        self.reporter.banner("E-Cüzdan — Portable Runtime Bootstrap")
        total_steps = 5 if check_only else 6

        # ── Step 1: Discover & Validate Host Python ───────────────────────────
        py_engine = PythonDiscoveryEngine()
        py_res = py_engine.discover()
        if not py_res.is_compatible:
            self.reporter.step(1, total_steps, "Checking Python", "FAILED")
            self.reporter.error_block(
                stage="Python Discovery",
                reason=py_res.error_message or "Compatible Python runtime not found.",
                suggested_action="Please install Python 3.13 (64-bit) from https://www.python.org/downloads/ and ensure 'Add to PATH' is checked.",
            )
            return 1

        self.reporter.step(1, total_steps, f"Checking Python ({py_res.version_str})", "OK")

        # ── Step 2: Virtual Environment Check / Creation ──────────────────────
        env_mgr = EnvironmentManager(self.repo_root)
        env_stat = env_mgr.ensure_environment(py_res.executable)
        if not env_stat.is_valid:
            self.reporter.step(2, total_steps, "Checking environment", "FAILED")
            self.reporter.error_block(
                stage="Virtual Environment",
                reason=env_stat.error_message or "Failed to create or validate .venv.",
                suggested_action="Verify permissions in project folder or delete broken .venv to allow clean recreation.",
            )
            return 1

        if env_stat.is_newly_created:
            self.reporter.info("Created fresh virtual environment (.venv)")

        self.reporter.step(2, total_steps, "Checking environment", "OK")

        # ── Step 3: Approved Runtime Dependencies Check / Restoration ─────────
        dep_mgr = DependencyManager(self.repo_root, env_stat.python_exe)
        dep_stat = dep_mgr.ensure_dependencies()
        if not dep_stat.is_healthy:
            self.reporter.step(3, total_steps, "Checking dependencies", "FAILED")
            self.reporter.error_block(
                stage="Approved Dependencies Restoration",
                reason=dep_stat.error_message or "Dependencies validation failed.",
                suggested_action="Ensure internet connection is active to download approved runtime wheels, or run 'pip install -r configuration/dependencies/requirements-runtime.txt'.",
            )
            return 1

        self.reporter.step(3, total_steps, "Checking dependencies", "OK")

        # ── Step 4: Configuration & Readiness Pre-flight ──────────────────────
        cfg_val = ConfigurationValidator(self.repo_root)
        cfg_stat = cfg_val.validate()
        if not cfg_stat.is_ready:
            self.reporter.step(4, total_steps, "Checking configuration", "FAILED")
            self.reporter.error_block(
                stage="Configuration Pre-flight",
                reason="; ".join(cfg_stat.errors),
                suggested_action="Ensure required files (app.py, config.py, models.py) exist and folder has write permissions.",
            )
            return 1

        self.reporter.step(4, total_steps, "Checking configuration", "OK")

        # ── Step 5: Process & Port Availability Check ─────────────────────────
        proc_mgr = ProcessManager()
        proc_stat = proc_mgr.inspect_runtime()

        if proc_stat.is_our_app_running:
            self.reporter.step(5, total_steps, "Checking application", "RUNNING")
            self.reporter.success("E-Cüzdan is already running on http://127.0.0.1:5000")

            if check_only:
                print("Opening existing application in your browser...")
                webbrowser.open("http://127.0.0.1:5000")
                return 0

            pid = proc_mgr.get_pid_on_port()
            pid_info = f" (PID: {pid})" if pid else ""
            print(f"\n[!] E-Cüzdan arka planda zaten çalışıyor{pid_info}.")
            print("    Erişim Adresi: http://127.0.0.1:5000\n")
            print("  [1] Tarayıcıda aç (Varsayılan)")
            print("  [2] Arka plandaki sunucuyu kapatıp bu pencerede YENİDEN BAŞLAT")
            print("  [3] Çıkış\n")

            choice = "1"
            if sys.stdin and sys.stdin.isatty():
                try:
                    choice = input("Seçiminiz [1/2/3] (Varsayılan=1): ").strip() or "1"
                except (EOFError, KeyboardInterrupt):
                    choice = "1"

            if choice in ("2", "r", "R"):
                print("\nArka plandaki eski sunucu kapatılıyor...")
                proc_mgr.terminate_process_on_port()
                proc_stat = proc_mgr.inspect_runtime()
                if proc_stat.is_port_in_use:
                    self.reporter.error_block(
                        stage="Port Release",
                        reason=f"Port {proc_stat.port} serbest bırakılamadı.",
                        suggested_action="Lütfen Görev Yöneticisi'nden eski python.exe sürecini sonlandırıp tekrar deneyin.",
                    )
                    return 1
                self.reporter.info("Port başarıyla boşaltıldı, sunucu başlatılıyor...")
            elif choice == "3":
                return 0
            else:
                print("\nTarayıcı açılıyor: http://127.0.0.1:5000")
                webbrowser.open("http://127.0.0.1:5000")
                if sys.stdin and sys.stdin.isatty():
                    try:
                        input("\nDevam etmek veya pencereyi kapatmak için Enter tuşuna basın...")
                    except (EOFError, KeyboardInterrupt):
                        pass
                return 0

        if proc_stat.is_port_in_use and not proc_stat.is_our_app_running:
            self.reporter.step(5, total_steps, "Checking application", "PORT BLOCKED")
            self.reporter.error_block(
                stage="Port Conflict",
                reason=f"Port {proc_stat.port} is occupied by another non-E-Cüzdan process.",
                suggested_action=f"Close the conflicting application occupying port {proc_stat.port} and try again.",
            )
            return 1

        self.reporter.step(5, total_steps, "Checking application", "OK")

        if check_only:
            self.reporter.success("Runtime pre-flight check completed successfully.")
            return 0

        # ── Step 6: Launch Application ────────────────────────────────────────
        self.reporter.step(6, total_steps, "Starting application", "OK")
        print("\n" + "-" * 60)
        print("  E-Cüzdan Web Sunucusu Başlatılıyor...")
        print("  Adres: http://127.0.0.1:5000")
        print("  Kapatmak için: Ctrl+C")
        print("-" * 60 + "\n")

        launcher = ApplicationLauncher(self.repo_root, env_stat.python_exe)
        return launcher.launch(entrypoint="app.py")


def main() -> int:
    parser = argparse.ArgumentParser(description="E-Cüzdan Portable Runtime Bootstrap")
    parser.add_argument("--check-only", action="store_true", help="Run preflight validation without launching server")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose diagnostics output")
    args = parser.parse_args()

    reporter = RuntimeReporter(verbose=args.verbose)
    bootstrap = RuntimeBootstrap(reporter=reporter)
    return bootstrap.run(check_only=args.check_only)


if __name__ == "__main__":
    sys.exit(main())
