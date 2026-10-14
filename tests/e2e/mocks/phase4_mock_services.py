"""Playwright için deterministic Phase 4 API mock servisleri.

Bu modül yalnızca E2E testlerinde route interception amacıyla kullanılır.
Production uygulama koduna import edilmemelidir.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse

from tests.e2e.fixtures.phase4_fixtures import Phase4Fixture


class Phase4MockServices:
    """Plans/Transactions Faz 4 uç noktalarını in-memory olarak simüle eder."""

    def __init__(self, fixture: Phase4Fixture | None = None, tenant_id: str = "e2e_phase4_tenant_a"):
        self.fixture = fixture or Phase4Fixture.load()
        self.tenant_id = tenant_id
        self.state = deepcopy(self.fixture.data)
        self.replay_keys: set[str] = set()
        self.next_transaction_id = 9920
        self.next_adjustment_id = 9930
        self.next_audit_id = 9960

    def install(self, page) -> None:
        """Mock route'larını Playwright page context'ine bağla."""
        page.route("**/api/plans/*/occurrences", self._occurrence_list)
        page.route("**/api/occurrences/*/pay", self._occurrence_pay)
        page.route("**/api/occurrences/*/skip", self._occurrence_skip)
        page.route("**/api/transactions/*/lineage", self._transaction_lineage)
        page.route("**/api/transactions/*/adjustments", self._create_adjustment)
        page.route("**/api/transactions/*/reversal", self._create_reversal)
        page.route("**/api/ledger-adjustments/*/audit", self._adjustment_audit)

    def _tenant_allowed(self, request) -> bool:
        requested_tenant = request.headers.get("x-e2e-tenant", self.tenant_id)
        return requested_tenant == self.tenant_id

    def _json_body(self, route) -> dict[str, Any]:
        raw = route.request.post_data or "{}"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return body if isinstance(body, dict) else {}

    def _path_id(self, route) -> int | None:
        path_parts = [part for part in urlparse(route.request.url).path.split("/") if part]
        try:
            return int(path_parts[-2])
        except (IndexError, TypeError, ValueError):
            return None

    def _fulfill(self, route, status: int, payload: dict[str, Any]) -> None:
        response_payload = {
            "success": status < 400,
            "data": payload.get("data", {}),
            "message": payload.get("message", ""),
            "request_id": payload.get("request_id", "e2e-phase4-request"),
        }
        for key in ("error_code", "idempotency_replayed"):
            if key in payload:
                response_payload[key] = payload[key]
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(response_payload, ensure_ascii=False),
        )

    def _error_for_request(self, route, route_name: str, path_id: int | None = None) -> bool:
        if not self._tenant_allowed(route.request):
            self._fulfill(
                route,
                404,
                {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."},
            )
            return True
        headers = {key.lower(): value for key, value in route.request.headers.items()}
        body = self._json_body(route)
        if route_name == "create_adjustment" and str(body.get("amount_delta", "")) in {"0", "0.0", "0.00"}:
            self._fulfill(
                route,
                400,
                {
                    "error_code": "validation_error",
                    "message": "Adjustment tutarı sıfır olamaz.",
                },
            )
            return True
        if route_name == "create_adjustment" and path_id == 9702:
            self._fulfill(
                route,
                422,
                {
                    "error_code": "financial_invariant_violation",
                    "message": "Sadece ödenmiş işlemler adjustment/reversal ile değiştirilebilir.",
                },
            )
            return True
        if route_name == "create_adjustment" and headers.get("if-match") == "0":
            self._fulfill(
                route,
                409,
                {
                    "error_code": "concurrency_conflict",
                    "message": "Kayıt başka bir oturumda değişti. Güncel veriyi yeniden yükleyin.",
                },
            )
            return True
        if route_name == "create_reversal" and headers.get("x-e2e-capability") == "deny":
            self._fulfill(
                route,
                403,
                {
                    "error_code": "capability_denied",
                    "message": "Bu işlem için gerekli yetkiniz bulunmuyor.",
                },
            )
            return True
        if route_name in {"create_adjustment", "create_reversal"} and headers.get("x-e2e-replay") == "true":
            self._fulfill(
                route,
                200,
                {
                    "idempotency_replayed": True,
                    "message": "Bu işlem daha önce uygulanmış; mevcut kayıt döndürüldü.",
                    "data": {"idempotency_replayed": True},
                },
            )
            return True
        return False

    def _occurrences(self, plan_id: int) -> list[dict[str, Any]]:
        return [
            deepcopy(row)
            for row in self.state["occurrences"]
            if row["tenant_id"] == self.tenant_id and row["plan_id"] == plan_id
        ]

    def _occurrence_list(self, route) -> None:
        plan_id = self._path_id(route)
        if not self._tenant_allowed(route.request) or plan_id is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        occurrences = self._occurrences(plan_id)
        self._fulfill(
            route,
            200,
            {
                "data": {
                    "plan_id": plan_id,
                    "items": occurrences,
                    "summary": {
                        "total": len(occurrences),
                        "paid": sum(item["status"] == "paid" for item in occurrences),
                        "pending": sum(item["status"] == "scheduled" for item in occurrences),
                    },
                }
            },
        )

    def _occurrence_pay(self, route) -> None:
        occurrence_id = self._path_id(route)
        if not self._tenant_allowed(route.request) or occurrence_id is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        occurrence = next(
            (row for row in self.state["occurrences"] if row["id"] == occurrence_id and row["tenant_id"] == self.tenant_id),
            None,
        )
        if occurrence is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        if occurrence["status"] == "paid":
            self._fulfill(route, 200, {"data": occurrence, "idempotency_replayed": True})
            return
        if occurrence["status"] != "scheduled":
            self._fulfill(route, 422, {"error_code": "financial_invariant_violation", "message": "Occurrence ödenemez."})
            return
        body = self._json_body(route)
        amount = str(body.get("amount", occurrence["amount"]))
        occurrence["status"] = "paid"
        occurrence["amount"] = amount
        occurrence["paid_at"] = "2026-08-20T08:00:00Z"
        occurrence["transaction_id"] = self.next_transaction_id
        transaction = {
            "id": self.next_transaction_id,
            "tenant_id": self.tenant_id,
            "date": body.get("payment_date", occurrence["scheduled_date"]),
            "category": "E2E Maaş",
            "description": f"[E2E-PHASE4] Occurrence #{occurrence['occurrence_number']}",
            "type": "Gelir",
            "status": "Ödendi",
            "amount": amount,
            "source_type": "plan",
            "source_id": occurrence["plan_id"],
            "is_deleted": False,
        }
        self.state["transactions"].append(transaction)
        payment = {
            "id": self.next_transaction_id + 100,
            "plan_id": occurrence["plan_id"],
            "tenant_id": self.tenant_id,
            "installment_number": occurrence["occurrence_number"],
            "amount": amount,
            "payment_date": transaction["date"],
            "transaction_id": transaction["id"],
        }
        self.state["payments"].append(payment)
        self.next_transaction_id += 1
        self._fulfill(
            route,
            200,
            {
                "data": {
                    "occurrence": deepcopy(occurrence),
                    "payment": payment,
                    "transaction": transaction,
                    "audit_reference": "E2E-AUDIT-PAY-0001",
                },
                "message": "Ödeme başarıyla kaydedildi.",
            },
        )

    def _occurrence_skip(self, route) -> None:
        occurrence_id = self._path_id(route)
        if not self._tenant_allowed(route.request) or occurrence_id is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        occurrence = next(
            (row for row in self.state["occurrences"] if row["id"] == occurrence_id and row["tenant_id"] == self.tenant_id),
            None,
        )
        if occurrence is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        if occurrence["status"] != "scheduled":
            self._fulfill(route, 422, {"error_code": "financial_invariant_violation", "message": "Yalnızca planlanmış dönem atlanabilir."})
            return
        body = self._json_body(route)
        if not str(body.get("reason", "")).strip():
            self._fulfill(route, 400, {"error_code": "validation_error", "message": "Atlama nedeni zorunludur."})
            return
        occurrence["status"] = "skipped"
        occurrence["notes"] = body["reason"]
        self._fulfill(route, 200, {"data": deepcopy(occurrence), "message": "Occurrence atlandı."})

    def _transaction(self, transaction_id: int) -> dict[str, Any] | None:
        return next(
            (
                deepcopy(row)
                for row in self.state["transactions"]
                if row["id"] == transaction_id and row["tenant_id"] == self.tenant_id
            ),
            None,
        )

    def _transaction_lineage(self, route) -> None:
        transaction_id = self._path_id(route)
        if not self._tenant_allowed(route.request) or transaction_id is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        transaction = self._transaction(transaction_id)
        if transaction is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        occurrence = next(
            (
                deepcopy(row)
                for row in self.state["occurrences"]
                if row.get("transaction_id") == transaction_id and row["tenant_id"] == self.tenant_id
            ),
            None,
        )
        adjustments = [
            deepcopy(row)
            for row in self.state["ledger_adjustments"]
            if row["original_transaction_id"] == transaction_id and row["tenant_id"] == self.tenant_id
        ]
        self._fulfill(
            route,
            200,
            {
                "data": {
                    "original": transaction,
                    "occurrence": occurrence,
                    "payments": [
                        deepcopy(row)
                        for row in self.state["payments"]
                        if row.get("transaction_id") == transaction_id and row["tenant_id"] == self.tenant_id
                    ],
                    "adjustments": adjustments,
                    "audit_events": [
                        deepcopy(row)
                        for row in self.state["audit_events"]
                        if row.get("transaction_id") == transaction_id and row["tenant_id"] == self.tenant_id
                    ],
                }
            },
        )

    def _create_compensating(self, route, kind: str) -> None:
        transaction_id = self._path_id(route)
        route_name = "create_adjustment" if kind == "adjustment" else "create_reversal"
        if self._error_for_request(route, route_name, transaction_id):
            return
        if transaction_id is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        original = self._transaction(transaction_id)
        if original is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        if original["status"] != "Ödendi":
            self._fulfill(route, 422, {"error_code": "financial_invariant_violation", "message": "Sadece ödenmiş işlemler kullanılabilir."})
            return
        body = self._json_body(route)
        reason_code = str(body.get("reason_code", "")).strip()
        reason_text = str(body.get("reason_text", "")).strip()
        if not reason_code or not reason_text:
            self._fulfill(route, 400, {"error_code": "validation_error", "message": "Neden kodu ve açıklama zorunludur."})
            return
        delta = str(body.get("amount_delta", "")) if kind == "adjustment" else f"-{original['amount']}"
        idempotency_key = body.get("idempotency_key", f"e2e-phase4-{kind}-{transaction_id}-{reason_code}")
        if idempotency_key in self.replay_keys:
            self._fulfill(
                route,
                200,
                {
                    "idempotency_replayed": True,
                    "message": "Bu işlem daha önce uygulanmış; mevcut kayıt döndürüldü.",
                    "data": {"idempotency_replayed": True},
                },
            )
            return
        self.replay_keys.add(idempotency_key)
        adjustment = {
            "id": self.next_adjustment_id,
            "tenant_id": self.tenant_id,
            "original_transaction_id": transaction_id,
            "compensating_transaction_id": self.next_transaction_id,
            "kind": kind,
            "status": "applied",
            "amount_delta": delta,
            "original_amount_snapshot": original["amount"],
            "original_type_snapshot": original["type"],
            "original_category_snapshot": original["category"],
            "original_date_snapshot": original["date"],
            "original_version": original.get("version", 1),
            "reason_code": reason_code,
            "reason_text": reason_text,
            "requested_by": 9102,
            "requested_at": "2026-08-20T08:10:00Z",
            "applied_at": "2026-08-20T08:10:01Z",
            "idempotency_key": idempotency_key,
            "correlation_id": f"e2e-phase4-{kind}-{self.next_adjustment_id}",
        }
        compensating = {
            "id": self.next_transaction_id,
            "tenant_id": self.tenant_id,
            "date": original["date"],
            "category": original["category"],
            "description": f"[E2E-PHASE4] {kind.title()} #{self.next_adjustment_id}",
            "type": original["type"],
            "status": "Ödendi",
            "amount": delta.lstrip("-"),
            "source_type": kind,
            "source_id": transaction_id,
            "is_deleted": False,
        }
        self.state["ledger_adjustments"].append(adjustment)
        self.state["transactions"].append(compensating)
        event_base = {
            "tenant_id": self.tenant_id,
            "adjustment_id": adjustment["id"],
            "transaction_id": compensating["id"],
            "actor_user_id": 9102,
            "correlation_id": adjustment["correlation_id"],
        }
        self.state["audit_events"].extend(
            [
                {"id": self.next_audit_id, "event_type": "requested", **event_base},
                {"id": self.next_audit_id + 1, "event_type": "applied", **event_base},
            ]
        )
        self.next_transaction_id += 1
        self.next_adjustment_id += 1
        self.next_audit_id += 2
        self._fulfill(
            route,
            201,
            {
                "data": {
                    "adjustment": adjustment,
                    "compensating_transaction": compensating,
                    "audit_reference": adjustment["correlation_id"],
                },
                "message": "Düzeltme uygulandı." if kind == "adjustment" else "Ters kayıt uygulandı.",
            },
        )

    def _create_adjustment(self, route) -> None:
        self._create_compensating(route, "adjustment")

    def _create_reversal(self, route) -> None:
        self._create_compensating(route, "reversal")

    def _adjustment_audit(self, route) -> None:
        adjustment_id = self._path_id(route)
        if not self._tenant_allowed(route.request) or adjustment_id is None:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        events = [
            deepcopy(row)
            for row in self.state["audit_events"]
            if row.get("adjustment_id") == adjustment_id and row["tenant_id"] == self.tenant_id
        ]
        if not events:
            self._fulfill(route, 404, {"error_code": "resource_not_found", "message": "Kayıt bulunamadı."})
            return
        self._fulfill(route, 200, {"data": {"adjustment_id": adjustment_id, "events": events}})


def install_phase4_mocks(page, tenant_id: str = "e2e_phase4_tenant_a") -> Phase4MockServices:
    """Tek satırla mock servisleri kur ve testte state erişimi döndür."""
    services = Phase4MockServices(tenant_id=tenant_id)
    services.install(page)
    return services
