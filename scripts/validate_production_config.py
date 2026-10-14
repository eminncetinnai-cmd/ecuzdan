"""Validate the minimum production configuration contract without printing secrets."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config  # noqa: E402


def main() -> int:
    if os.getenv("FLASK_ENV", "").lower() != "production":
        print("PRODUCTION_CONFIG_INVALID: FLASK_ENV must be production")
        return 1

    try:
        config = Config.from_env()
    except ValueError as exc:
        print(f"PRODUCTION_CONFIG_INVALID: {exc}")
        return 1

    print("PRODUCTION_CONFIG_VALID")
    print(f"DATABASE_SCHEME={urlparse(config.DATABASE_URL).scheme}")
    print(f"HTTPS_ENABLED={config.HTTPS_ENABLED}")
    print(f"FORCE_HTTPS={config.FORCE_HTTPS}")
    print(f"RATE_LIMIT_BACKEND={urlparse(config.RATELIMIT_STORAGE_URI).scheme}")
    print(f"BACKGROUND_SERVICE_ENABLED={config.BACKGROUND_SERVICE_ENABLED}")
    print(f"TRUST_PROXY_HOPS={config.TRUST_PROXY_HOPS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
