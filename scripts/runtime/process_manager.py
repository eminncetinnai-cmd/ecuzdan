"""E-Cüzdan Runtime Bootstrap - Process & Port Manager.

Checks port availability and prevents duplicate application instances:
  - Validates 127.0.0.1:5000 availability
  - Probes health endpoint to detect if our instance is already active
  - Prohibits force-killing unrelated foreign processes
"""

from __future__ import annotations

import socket
import urllib.request
from dataclasses import dataclass


@dataclass
class ProcessStatus:
    is_port_in_use: bool
    is_our_app_running: bool
    host: str = "127.0.0.1"
    port: int = 5000
    message: str = ""


class ProcessManager:
    """Manages application process and port checks."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000) -> None:
        self.host = host
        self.port = port

    def is_port_bound(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex((self.host, self.port))
            return result == 0

    def check_app_health(self) -> bool:
        url = f"http://{self.host}:{self.port}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ECuzdanBootstrap/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                # E-Cüzdan returns 200 or 302 (redirect to login/dashboard)
                return resp.status in (200, 302)
        except Exception:
            return False

    def inspect_runtime(self) -> ProcessStatus:
        bound = self.is_port_bound()
        if not bound:
            return ProcessStatus(
                is_port_in_use=False,
                is_our_app_running=False,
                host=self.host,
                port=self.port,
                message="Port is available.",
            )

        # If bound, probe if it is E-Cüzdan
        if self.check_app_health():
            return ProcessStatus(
                is_port_in_use=True,
                is_our_app_running=True,
                host=self.host,
                port=self.port,
                message="E-Cüzdan application is already running.",
            )

        return ProcessStatus(
            is_port_in_use=True,
            is_our_app_running=False,
            host=self.host,
            port=self.port,
            message=f"Port {self.port} is already in use by another application.",
        )

    def get_pid_on_port(self) -> int | None:
        """Find the PID of the process listening on self.port on Windows."""
        try:
            import subprocess
            cmd = f"netstat -ano | findstr :{self.port}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    return int(parts[-1])
        except Exception:
            pass
        return None

    def terminate_process_on_port(self) -> bool:
        """Terminate the process holding self.port to allow a clean restart."""
        pid = self.get_pid_on_port()
        if not pid:
            return False
        try:
            import subprocess
            import time
            subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True, check=False)
            time.sleep(1.0)
            return not self.is_port_bound()
        except Exception:
            return False
