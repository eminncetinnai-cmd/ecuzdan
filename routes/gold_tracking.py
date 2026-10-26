"""Gold Tracking (Altın Takip — Harem Altın & Bursa Kuyumcular Çarşısı) routes."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, render_template, request, session

from application.analysis.queries.get_gold_tracking_overview import GetGoldTrackingOverviewQuery
from utils.auth_helpers import login_required

logger = logging.getLogger(__name__)


def register_gold_tracking_routes(bp: Blueprint) -> None:
    """Register Gold Tracking (Altın Takip) routes on the blueprint."""

    @bp.route("/gold-tracking")
    @login_required
    def gold_tracking_dashboard():
        """Render the Altın Takip (Harem Altın & Bursa Jeweler Bazaar) page."""
        try:
            preset_key = request.args.get("preset", "bursa_harem").strip().lower()
            query = GetGoldTrackingOverviewQuery()
            data = query.execute(preset_key=preset_key, force_refresh=False, allow_network=False)
            return render_template(
                "gold_tracking.html",
                data=data,
                user_id=session.get("user_id"),
            )
        except Exception as exc:
            logger.error("Gold tracking dashboard error: %s", exc)
            return render_template(
                "error.html",
                code=500,
                message="Altın Takip sayfası yüklenirken hata oluştu",
            ), 500

    @bp.route("/gold-tracking/api/quotes")
    @login_required
    def get_gold_tracking_quotes():
        """Return live JSON quotes for Harem Altın & Bursa Jeweler derivatives."""
        try:
            preset_key = request.args.get("preset", "bursa_harem").strip().lower()
            force_refresh = request.args.get("refresh", "0").strip() in {"1", "true", "yes"}
            query = GetGoldTrackingOverviewQuery()
            data = query.execute(preset_key=preset_key, force_refresh=force_refresh)
            return jsonify({"success": True, "data": data})
        except Exception as exc:
            logger.error("Gold tracking API error: %s", exc)
            return jsonify({"success": False, "error": str(exc)}), 500
