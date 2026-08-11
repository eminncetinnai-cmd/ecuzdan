"""Asset routes."""

import logging

from flask import flash, g, jsonify, redirect, render_template, request, session, url_for

from bootstrap import get_container
from domain.portfolio.events import AssetAddedEvent, AssetRemovedEvent, AssetUpdatedEvent
from domain.transactions.services import (
    LedgerError,
    create_asset_position,
    delete_asset_position,
    parse_asset_payload,
    sell_asset_position,
    update_asset_valuation,
)
from engines.financial_engine import today_display
from shared.decimal_precision import to_decimal
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.db_session import rollback_session

logger = logging.getLogger(__name__)


def _get_portfolio_app_service():
    from bootstrap import get_container
    return get_container().applications.portfolio()


def _get_outbox():
    from bootstrap import get_container
    return get_container().infrastructure.outbox()


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
            return render_template('assets.html', **portfolio_app.unified_context(g.get('tenant_id')))
        except Exception as e:
            logger.exception(f"Assets page error: {e}")
            flash('Varlık sayfası yüklenirken hata oluştu.', 'error')
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
            flash('Performans analizi yüklenirken hata oluştu.', 'error')
            return redirect(url_for('assets.assets'))

    @bp.route('/assets_view')
    def assets_view():
        try:
            from bootstrap import get_container
            portfolio_app = get_container().applications.portfolio()
            return render_template('assets_view.html', **portfolio_app.assets_view_context(g.get('tenant_id')))
        except Exception as e:
            logger.exception(f"Assets view error: {e}")
            flash('Varlık listesi yüklenirken hata oluştu.', 'error')
            return render_template(
                'assets_view.html',
                assets=[],
                total_portfolio=0,
                analysis=None,
                ledger_summaries={},
            )

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
            flash('Varlık yönetimi yüklenirken hata oluştu.', 'error')
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
            _dispatch_portfolio_event(AssetAddedEvent(
                asset_id=getattr(asset, 'id', 0),
                asset_symbol=payload.get('symbol', ''),
                tenant_id=str(g.get('tenant_id', '')),
            ))
            flash('Varlık başarıyla eklendi!', 'success')
            return redirect(url_for('assets.assets'))
        except LedgerError as e:
            rollback_session()
            flash(f'Kayıt başarısız: {str(e)}', 'error')
        except Exception as e:
            logger.exception(f"New asset error: {e}")
            rollback_session()
            flash('Kayıt sırasında beklenmeyen bir hata oluştu.', 'error')
        return redirect(url_for('assets.assets'))

    @bp.route('/update_asset', methods=['POST'])
    def update_asset():
        try:
            asset_id = request.form.get('asset_id', type=int)
            if not asset_id:
                flash('Varlık ID bulunamadı.', 'error')
                return redirect(url_for('assets.assets'))

            fields = parse_asset_payload(request.form)
            fields['sync_cash'] = False
            result = update_asset_valuation(
                asset_id,
                user_id=session.get('user_id'),
                preserve_purchase_cost=True,
                **fields,
            )

            if result:
                _dispatch_portfolio_event(AssetUpdatedEvent(
                    asset_id=asset_id,
                    asset_symbol=fields.get('symbol', ''),
                    tenant_id=str(g.get('tenant_id', '')),
                ))
                flash('Varlık başarıyla güncellendi!', 'success')
            else:
                flash('Varlık bulunamadı.', 'error')
        except LedgerError as e:
            rollback_session()
            flash(f'Güncelleme hatası: {str(e)}', 'error')
        except Exception as e:
            logger.exception(f"Update asset error: {e}")
            rollback_session()
            flash('Güncelleme sırasında beklenmeyen bir hata oluştu.', 'error')
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

    @bp.route('/delete_asset/<int:id>', methods=['GET', 'POST'])
    def delete_asset_route(id):
        try:
            if delete_asset_position(id, tenant_id=g.get('tenant_id')):
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

    @bp.route('/del_asset/<int:id>', methods=['GET', 'POST'])
    def delete_asset_route_old(id):
        return delete_asset_route(id)

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
            msg = (
                f"{asset.name} satışı yapıldı. Kasa aktarımı: {sale_tx.amount:,.2f} ₺ "
                f"(Gerçekleşen kar: {realized_gain:,.2f} ₺)"
            )
            if is_ajax:
                return jsonify({'success': True, 'message': msg})
            flash(msg, 'success')
        except LedgerError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': f'Satış hatası: {str(e)}'})
            flash(f'Satış hatası: {str(e)}', 'error')
        except Exception as e:
            logger.exception(f"Sell asset error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'Satış sırasında beklenmeyen bir hata oluştu.'})
            flash('Satış sırasında beklenmeyen bir hata oluştu.', 'error')

        return redirect(url_for('assets.assets_view'))
