"""Asset routes."""

import logging

from flask import flash, g, jsonify, redirect, render_template, request, session, url_for

from bootstrap.container import get_container  # noqa: F401
from domain.portfolio.events import AssetAddedEvent, AssetRemovedEvent, AssetUpdatedEvent
from domain.transactions.services import (
    LedgerError,
    create_asset_position,
    delete_asset_position,
    parse_asset_payload,
    sell_asset_position,
    update_asset_valuation,
)
from domain.transactions.services.financial_ledger import get_asset_ledger_summaries
from engines.financial_engine import invalidate_financial_cache, today_display
from infrastructure.i18n import i18n
from shared.currency_precision import get_currency_symbol
from shared.decimal_precision import to_decimal
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.db_session import rollback_session

logger = logging.getLogger(__name__)


def _serialize_asset(a, summary=None):
    cost_b = float(getattr(summary, 'cost_basis', 0)) if summary else float(getattr(a, 'purchase_price', 0) or 0) * float(getattr(a, 'quantity', 0) or 0)
    return {
        'id': a.id,
        'name': a.name,
        'type': a.type,
        'sector': getattr(a, 'sector', None),
        'quantity': float(getattr(a, 'quantity', 0) or 0),
        'purchase_price': float(getattr(a, 'purchase_price', 0) or 0),
        'current_price': float(getattr(a, 'current_price', 0) or 0),
        'value': float(getattr(a, 'value', 0) or 0),
        'currency': getattr(a, 'currency', 'TRY') or 'TRY',
        'cost_basis': cost_b,
        'realized_pnl': float(getattr(summary, 'realized_gain', 0)) if summary else 0.0,
        'unrealized_pnl': float(getattr(summary, 'unrealized_gain', 0)) if summary else 0.0,
        'last_updated': a.last_updated.isoformat() if getattr(a, 'last_updated', None) else None,
    }


def _get_portfolio_app_service():
    from bootstrap import get_container as current_get_container
    return current_get_container().applications.portfolio()


def _get_outbox():
    from bootstrap import get_container as current_get_container
    return current_get_container().infrastructure.outbox()


def _dispatch_portfolio_event(event):
    """Persist a portfolio domain event to the outbox for async delivery."""
    outbox = _get_outbox()
    if outbox:
        try:
            outbox.save(event)
        except Exception as e:
            logger.warning("Outbox write failed for %s: %s", type(event).__name__, e)


def _wants_json_response():
    accept = request.headers.get('Accept', '')
    return 'application/json' in accept or is_ajax_request()


def _redirect_after_asset_action(default_endpoint='assets.assets_view'):
    referrer = request.referrer or ''
    if 'assets_management' in referrer:
        return redirect(url_for('assets.assets_management'))
    if 'assets_view' in referrer:
        return redirect(url_for('assets.assets_view'))
    return redirect(url_for(default_endpoint))


def register_asset_routes(bp):
    portfolio_app_service = _get_portfolio_app_service()

    @bp.route('/assets')
    def assets():
        try:
            from bootstrap import get_container
            portfolio_app = get_container().applications.portfolio()
            context = portfolio_app.unified_context(g.get('tenant_id'))
            if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
                ledger_summaries = context.get('ledger_summaries') or {}
                return jsonify({
                    'success': True,
                    'assets': [_serialize_asset(a, ledger_summaries.get(a.id)) for a in context.get('assets', [])],
                    'asset_types': [getattr(t, 'name', str(t)) for t in context.get('asset_types', [])],
                    'asset_sectors': [getattr(s, 'name', str(s)) for s in context.get('asset_sectors', [])],
                    'analysis': context.get('analysis') or {},
                })
            return render_template('assets.html', **context)
        except Exception as e:
            logger.exception(f"Assets page error: {e}")
            flash(i18n.gettext("ui_auto_963b946cfb51"), 'error')
            return render_template(
                'assets.html',
                assets=[],
                analysis=None,
                asset_types=[],
                asset_sectors=[],
            )

    @bp.route('/investment_performance')
    def investment_performance():
        try:
            performance = portfolio_app_service.investment_performance_context(g.get('tenant_id'))
            return render_template('investment_performance.html', performance=performance)
        except Exception as e:
            logger.exception(f"Investment performance error: {e}")
            flash(i18n.gettext("ui_auto_1b7646e50f42"), 'error')
            return redirect(url_for('assets.assets'))

    @bp.route('/assets_view')
    def assets_view():
        try:
            from bootstrap import get_container
            portfolio_app = get_container().applications.portfolio()
            context = portfolio_app.assets_view_context(g.get('tenant_id'))
            if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
                ledger_summaries = context.get('ledger_summaries') or {}
                return jsonify({
                    'success': True,
                    'total_portfolio': float(context.get('total_portfolio') or 0),
                    'type_labels': context.get('type_labels', []),
                    'type_values': [float(v) for v in context.get('type_values', [])],
                    'asset_labels': context.get('asset_labels', []),
                    'assets': [_serialize_asset(a, ledger_summaries.get(a.id)) for a in context.get('assets', [])],
                    'analysis': context.get('analysis') or {},
                })
            return render_template('assets_view.html', **context)
        except Exception as e:
            logger.exception(f"Assets view error: {e}")
            flash(i18n.gettext("ui_auto_1e1f37fea611"), 'error')
            return render_template(
                'assets_view.html',
                assets=[],
                total_portfolio=0,
                analysis=None,
                ledger_summaries={},
            )

    @bp.route('/api/portfolio/summary', methods=['GET'])
    def api_portfolio_summary():
        try:
            tenant_id = g.get('tenant_id')
            context = portfolio_app_service.assets_view_context(tenant_id)
            return jsonify({
                'success': True,
                'total_portfolio': float(context.get('total_portfolio') or 0),
                'type_labels': context.get('type_labels', []),
                'type_values': [float(v) for v in context.get('type_values', [])],
                'asset_labels': context.get('asset_labels', []),
                'analysis': context.get('analysis') or {},
            })
        except Exception as e:
            logger.exception(f"API portfolio summary error: {e}")
            return jsonify({'success': False, 'message': 'Portföy özeti alınamadı.'}), 500

    @bp.route('/api/portfolio/assets', methods=['GET'])
    def api_portfolio_assets():
        try:
            tenant_id = g.get('tenant_id')
            page = max(request.args.get('page', 1, type=int), 1)
            per_page = min(max(request.args.get('per_page', 20, type=int), 1), 100)
            asset_type = (request.args.get('type') or '').strip()
            sector = (request.args.get('sector') or '').strip()
            search = (request.args.get('q') or request.args.get('search') or '').strip().lower()

            from bootstrap.container import get_container
            fin_repo = get_container().repositories.financial()
            all_assets = fin_repo.list_assets(tenant_id)
            filtered = all_assets
            if asset_type:
                filtered = [a for a in filtered if a.type == asset_type]
            if sector:
                filtered = [a for a in filtered if getattr(a, 'sector', None) == sector]
            if search:
                filtered = [
                    a for a in filtered
                    if search in (a.name or '').lower() or search in (getattr(a, 'symbol', '') or '').lower()
                ]

            total = len(filtered)
            pages = (total + per_page - 1) // per_page if total > 0 else 1
            start = (page - 1) * per_page
            end = start + per_page
            page_items = filtered[start:end]

            ledger_summaries = get_asset_ledger_summaries([a.id for a in page_items], tenant_id)
            items = [_serialize_asset(a, ledger_summaries.get(a.id)) for a in page_items]

            return jsonify({
                'success': True,
                'page': page,
                'per_page': per_page,
                'pages': pages,
                'total': total,
                'items': items,
            })
        except Exception as e:
            logger.exception(f"API portfolio assets error: {e}")
            return jsonify({'success': False, 'message': 'Varlıklar alınamadı.'}), 500

    @bp.route('/assets_management', methods=['GET'])
    def assets_management():
        try:
            context = portfolio_app_service.management_context(
                page=request.args.get('page', 1, type=int),
                edit_id=request.args.get('edit', None, type=int),
                tenant_id=g.get('tenant_id'),
            )
            return render_template('assets_management.html', today_display=today_display(), **context)
        except Exception as e:
            logger.exception(f"Assets management error: {e}")
            flash(i18n.gettext("ui_auto_2734ec8f6b0a"), 'error')
            return render_template(
                'assets_management.html',
                assets_page=None,
                asset_types=[],
                asset_sectors=[],
                today_display=today_display(),
                edit_id=None,
                edit_asset_data=None,
            )

    @bp.route('/new_asset', methods=['POST'])
    def new_asset():
        try:
            payload = parse_asset_payload(request.form)
            asset = create_asset_position(user_id=session.get('user_id'), **payload)
            invalidate_financial_cache(g.get('tenant_id'))
            _dispatch_portfolio_event(AssetAddedEvent(
                asset_id=getattr(asset, 'id', 0),
                asset_symbol=payload.get('symbol', ''),
                tenant_id=str(g.get('tenant_id', '')),
            ))
            flash(i18n.gettext("ui_auto_105a225e02b7"), 'success')
            return redirect(url_for('assets.assets'))
        except LedgerError as e:
            rollback_session()
            flash(i18n.gettext("ui_auto_b25d75a9757a", **{"str(e)": str(e)}), 'error')
        except Exception as e:
            logger.exception(f"New asset error: {e}")
            rollback_session()
            flash(i18n.gettext("ui_auto_ea2754889d5c"), 'error')
        return redirect(url_for('assets.assets'))

    @bp.route('/update_asset', methods=['POST'])
    def update_asset():
        try:
            asset_id = request.form.get('asset_id', type=int)
            if not asset_id:
                flash(i18n.gettext("ui_auto_2c110dffadca"), 'error')
                return redirect(url_for('assets.assets'))

            fields = parse_asset_payload(request.form)
            if_match = (request.headers.get("If-Match") or "").strip().strip(chr(34))
            if if_match.isdigit():
                fields["version"] = int(if_match)
            fields['sync_cash'] = False
            result = update_asset_valuation(
                asset_id,
                user_id=session.get('user_id'),
                preserve_purchase_cost=True,
                tenant_id=g.get("tenant_id"),
                **fields,
            )

            if result:
                invalidate_financial_cache(g.get('tenant_id'))
                _dispatch_portfolio_event(AssetUpdatedEvent(
                    asset_id=asset_id,
                    asset_symbol=fields.get('symbol', ''),
                    tenant_id=str(g.get('tenant_id', '')),
                ))
                flash(i18n.gettext("ui_auto_6bf68a6a8fd5"), 'success')
            else:
                flash(i18n.gettext("ui_auto_b282f0ef6847"), 'error')
        except LedgerError as e:
            rollback_session()
            if is_ajax_request():
                return jsonify({'success': False, 'message': str(e)}), 409
            flash(i18n.gettext("ui_auto_3aefeb342aec", **{"str(e)": str(e)}), 'error')
        except Exception as e:
            logger.exception(f"Update asset error: {e}")
            rollback_session()
            flash(i18n.gettext("ui_auto_f9044908993d"), 'error')
        return redirect(url_for('assets.assets'))

    @bp.route('/edit_asset/<int:id>', methods=['POST'])
    def edit_asset(id):
        is_ajax = is_ajax_request()
        try:
            fields = parse_asset_payload(request.form)
            fields['sync_cash'] = False
            result = update_asset_valuation(
                id,
                user_id=session.get('user_id'),
                preserve_purchase_cost=True,
                **fields,
            )
            if result:
                invalidate_financial_cache(g.get('tenant_id'))
            response = handle_ajax_or_flash(
                bool(result),
                'Varlık güncellendi!',
                'Varlık bulunamadı.',
            )
            if response:
                return response
        except LedgerError as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f'Güncelleme hatası: {str(e)}')
            if response:
                return response
        except Exception as e:
            logger.exception(f"Edit asset error: {e}")
            rollback_session()
            response = handle_ajax_or_flash(False, None, 'Güncelleme sırasında beklenmeyen bir hata oluştu.')
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('assets.assets_management'))

    @bp.route('/delete_asset/<int:id>', methods=['POST'])
    def delete_asset_route(id):
        try:
            if delete_asset_position(id, tenant_id=g.get('tenant_id')):
                invalidate_financial_cache(g.get('tenant_id'))
                _dispatch_portfolio_event(AssetRemovedEvent(
                    asset_id=id,
                    tenant_id=str(g.get('tenant_id', '')),
                ))
                message = 'Varlık ve bağlı defter kayıtları silindi.'
                if _wants_json_response():
                    return jsonify({'success': True, 'message': message})
                flash(message, 'success')
            else:
                message = 'Varlık bulunamadı.'
                if _wants_json_response():
                    return jsonify({'success': False, 'message': message})
                flash(message, 'error')
        except LedgerError as e:
            rollback_session()
            if _wants_json_response():
                return jsonify({'success': False, 'message': str(e)})
            flash(str(e), 'error')
        except Exception as e:
            logger.exception(f"Delete asset error: {e}")
            rollback_session()
            message = f'Silme hatası: {str(e)}'
            if _wants_json_response():
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
        return redirect(url_for('assets.assets'))

    @bp.route('/sell_asset/<int:id>', methods=['POST'])
    def sell_asset(id):
        is_ajax = is_ajax_request()
        try:
            asset, realized_gain, sale_tx = sell_asset_position(
                asset_id=id,
                quantity=float(to_decimal(request.form.get('quantity', 0))),
                sale_unit_price=float(to_decimal(request.form.get('sale_unit_price', 0))),
                sale_date=request.form.get('sale_date'),
                note=request.form.get('note', ''),
                user_id=session.get('user_id'),
            )
            invalidate_financial_cache(g.get('tenant_id'))
            currency_code = getattr(asset, 'currency', None) or 'TRY'
            sym = get_currency_symbol(currency_code) or currency_code
            msg = (
                f"{asset.name} satışı yapıldı. Kasa aktarımı: {sale_tx.amount:,.2f} {sym} "
                f"(Gerçekleşen kar: {realized_gain:,.2f} {sym})"
            )
            if is_ajax:
                return jsonify({'success': True, 'message': msg})
            flash(msg, 'success')
        except LedgerError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': f'Satış hatası: {str(e)}'})
            flash(i18n.gettext("ui_auto_7ec0589845d0", **{"str(e)": str(e)}), 'error')
        except Exception as e:
            logger.exception(f"Sell asset error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'Satış sırasında beklenmeyen bir hata oluştu.'})
            flash(i18n.gettext("ui_auto_0f376d4b7813"), 'error')

        return redirect(url_for('assets.assets_view'))
