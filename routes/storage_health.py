"""Storage Health dashboard and cleanup API."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, render_template, request, session

from application.storage_health import StorageHealthApplicationService
from infrastructure.i18n import i18n
from utils.auth_helpers import capability_required
from utils.capabilities import Capability

storage_health_bp = Blueprint("storage_health", __name__, url_prefix="/storage-health")
_SERVICE_KEY = "storage_health_application_service"


def _standard_response(success: bool, *, data=None, error=None):
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_service() -> StorageHealthApplicationService:
    service = current_app.extensions.get(_SERVICE_KEY)
    if service is None:
        service = StorageHealthApplicationService(current_app.root_path)
        current_app.extensions[_SERVICE_KEY] = service
    return service


def register_storage_health_routes(bp):
    if getattr(bp, "_storage_health_routes_registered", False):
        return
    bp._storage_health_routes_registered = True

    @bp.get("/")
    @capability_required(Capability.STORAGE_HEALTH_VIEW)
    def storage_health_dashboard():
        return render_template("storage_health.html")

    @bp.get("/api/overview")
    @capability_required(Capability.STORAGE_HEALTH_VIEW)
    def storage_health_overview():
        try:
            refresh = request.args.get("refresh", "0") == "1"
            data = _get_service().get_overview(refresh=refresh)
            return jsonify(_standard_response(True, data=data))
        except Exception:
            current_app.logger.exception("Storage Health overview failed")
            return jsonify(
                _standard_response(
                    False,
                    error=i18n.gettext("storage_health.error"),
                )
            ), 500

    @bp.post("/api/cleanup")
    @capability_required(Capability.STORAGE_HEALTH_VIEW)
    def storage_health_cleanup():
        """Execute safe cleanup for selected SAFE_AUTO candidates.

        Expects JSON body:
            {
                "plan_hash": "<str>",
                "snapshot_id": "<str>",
                "candidate_ids": ["<id1>", "<id2>", ...]
            }

        Only SAFE_AUTO candidates in allowlisted directories (__pycache__,
        tmp) are actually deleted.  Security logs, source code, and database
        files are always rejected by the executor.
        """
        try:
            payload = request.get_json(silent=True) or {}
            plan_hash = str(payload.get("plan_hash", ""))
            snapshot_id = str(payload.get("snapshot_id", ""))
            candidate_ids = [str(c) for c in payload.get("candidate_ids", [])]

            if not candidate_ids:
                return jsonify(
                    _standard_response(
                        False,
                        error=i18n.gettext("storage_health.cleanup_no_candidates"),
                    )
                ), 400

            summary = _get_service().execute_cleanup(
                plan_hash=plan_hash,
                snapshot_id=snapshot_id,
                candidate_ids=candidate_ids,
            )
            current_app.logger.info(
                "Storage Health cleanup: executed=%d skipped=%d errors=%d bytes_freed=%d",
                len(summary.executed),
                len(summary.skipped),
                len(summary.errors),
                summary.bytes_freed,
            )
            return jsonify(_standard_response(True, data=summary.to_dict()))

        except ValueError as exc:
            return jsonify(
                _standard_response(
                    False,
                    error=i18n.gettext(f"storage_health.cleanup_{exc}") or str(exc),
                )
            ), 409
        except Exception:
            current_app.logger.exception("Storage Health cleanup failed")
            return jsonify(
                _standard_response(
                    False,
                    error=i18n.gettext("storage_health.error"),
                )
            ), 500

    @bp.get("/api/db-health")
    @capability_required(Capability.STORAGE_HEALTH_VIEW)
    def storage_health_db_health():
        """Inspect database engine vitality, freelist, integrity and WAL."""
        try:
            stats = _get_service().db_maintenance.get_stats()
            return jsonify(_standard_response(True, data=stats.to_dict()))
        except Exception:
            current_app.logger.exception("Storage Health DB health failed")
            return jsonify(
                _standard_response(
                    False,
                    error="Veritabanı sağlık kontrolü başarısız",
                )
            ), 500

    @bp.post("/api/tune-up")
    @capability_required(Capability.STORAGE_HEALTH_VIEW)
    def storage_health_tune_up():
        """Execute full smart maintenance pipeline (Snapshot -> WAL -> Vacuum -> Cache Purge -> Optimize)."""
        try:
            payload = request.get_json(silent=True) or {}
            purge_cache = payload.get("purge_cache", True)
            create_snapshot = payload.get("create_snapshot", True)

            user_name = (
                getattr(getattr(g, "current_user", None), "username", None)
                or session.get("username")
                or "Yönetici"
            )

            from shared.db import db
            try:
                db.session.remove()
                db.engine.dispose()
            except Exception:
                pass

            result = _get_service().execute_smart_tune_up(
                purge_cache=bool(purge_cache),
                create_snapshot=bool(create_snapshot),
                trigger_source="manual_ui",
                user_name=user_name,
            )
            return jsonify(_standard_response(True, data=result))
        except Exception as exc:
            current_app.logger.exception("Storage Health tune-up failed")
            return jsonify(
                _standard_response(
                    False,
                    error=f"Bakım sırasında hata: {exc}",
                )
            ), 500

    @bp.get("/api/history")
    @capability_required(Capability.STORAGE_HEALTH_VIEW)
    def storage_health_history():
        """Retrieve recent maintenance audit history records."""
        try:
            limit = min(50, max(1, request.args.get("limit", 10, type=int)))
            history = _get_service().get_history(limit=limit)
            return jsonify(_standard_response(True, data=history))
        except Exception:
            current_app.logger.exception("Storage Health history failed")
            return jsonify(
                _standard_response(
                    False,
                    error="Bakım geçmişi yüklenemedi",
                )
            ), 500


