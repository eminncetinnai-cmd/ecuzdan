"""Authenticated browser performance benchmark for e-cuzdan.

This script only reads pages and writes measurement artifacts. It does not
create, update, or delete financial records.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
USERNAME = os.getenv("ECUZDAN_E2E_USERNAME")
PASSWORD = os.getenv("ECUZDAN_E2E_PASSWORD")
ITERATIONS = max(1, int(os.getenv("BENCHMARK_ITERATIONS", "5")))
OUT_DIR = Path(os.getenv("BENCHMARK_OUT", "docs/audits/performance-current"))
ROUTES = [
    ("home", "/"),
    ("transactions", "/transactions"),
    ("plans", "/plans"),
    ("assets", "/assets"),
    ("education_progress", "/financial_education?view=progress"),
    ("analysis", "/analysis"),
    ("notifications", "/notifications"),
    ("monitoring", "/monitoring/"),
]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def login(page) -> None:
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.locator("#username").fill(USERNAME)
    page.locator("input[name=password]").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    page.wait_for_url("**/", timeout=15000)


def measure(page, name: str, path: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    for iteration in range(1, ITERATIONS + 1):
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        started = time.perf_counter()
        response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
        elapsed_ms = (time.perf_counter() - started) * 1000
        resources = page.evaluate(
            """() => performance.getEntriesByType('resource').map((entry) => ({
                transferSize: entry.transferSize || 0,
                decodedBodySize: entry.decodedBodySize || 0,
            }))"""
        )
        body = response.body() if response else b""
        rows.append(
            {
                "route": name,
                "path": path,
                "iteration": iteration,
                "status": response.status if response else None,
                "elapsed_ms": round(elapsed_ms, 3),
                "response_bytes": len(body),
                "resource_count": len(resources),
                "resource_transfer_bytes": sum(item["transferSize"] for item in resources),
                "resource_decoded_bytes": sum(item["decodedBodySize"] for item in resources),
                "page_error_count": len(page_errors),
                "page_errors": page_errors[:5],
                "final_url": page.url,
            }
        )
    return rows


def main() -> int:
    if not USERNAME or not PASSWORD:
        raise SystemExit("ECUZDAN_E2E_USERNAME and ECUZDAN_E2E_PASSWORD are required")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        login(page)
        for name, path in ROUTES:
            rows.extend(measure(page, name, path))
        browser.close()

    csv_path = OUT_DIR / "authenticated_http_timings.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary: list[dict[str, object]] = []
    for name, path in ROUTES:
        route_rows = [row for row in rows if row["route"] == name]
        values = [float(row["elapsed_ms"]) for row in route_rows]
        summary.append(
            {
                "route": name,
                "path": path,
                "samples": len(values),
                "avg_ms": round(statistics.mean(values), 3),
                "p50_ms": round(percentile(values, 0.50), 3),
                "p95_ms": round(percentile(values, 0.95), 3),
                "max_ms": round(max(values), 3),
                "statuses": sorted({row["status"] for row in route_rows}),
                "avg_response_bytes": round(statistics.mean(int(row["response_bytes"]) for row in route_rows)),
                "avg_resource_transfer_bytes": round(statistics.mean(int(row["resource_transfer_bytes"]) for row in route_rows)),
                "avg_resource_count": round(statistics.mean(int(row["resource_count"]) for row in route_rows), 2),
                "page_error_count": sum(int(row["page_error_count"]) for row in route_rows),
            }
        )
    summary_path = OUT_DIR / "authenticated_http_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"timings": str(csv_path), "summary": str(summary_path), "routes": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
