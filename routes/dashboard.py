"""Dashboard and financial analysis routes."""

import json  # noqa: F401
import logging
import math
from datetime import datetime

from flask import Response, g, jsonify, render_template, request, session

from bootstrap.container import get_container
from engines.analysis_engine import get_analysis_engine
from engines.financial_engine import get_financial_analysis, get_monthly_dashboard_data
from infrastructure.market.market_data_service import get_market_data_summary
from shared.currency_precision import get_currency_symbol
from shared.decimal_precision import to_decimal
from utils.db_session import rollback_session
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _get_dashboard_service():
    from bootstrap import get_container
    return get_container().applications.dashboard()


def _dashboard_currency_context():
    user = getattr(g, 'current_user', None)
    tenant = getattr(user, 'tenant', None)
    code = (getattr(user, 'base_currency', None) or getattr(tenant, 'base_currency', None) or 'TRY').upper()
    return {
        'dashboard_currency_code': code,
        'dashboard_currency_symbol': get_currency_symbol(code) or code,
    }


def register_dashboard_routes(bp):
    dashboard_service = _get_dashboard_service()

    @bp.route('/')
    @login_required
    def index():
        try:
            tenant_id = g.get('tenant_id')
            # Dashboard GET salt-okunurdur; plan/transaction materialization explicit
            # lifecycle veya background akışında yapılmalıdır.
            context = dashboard_service.index_context(tenant_id)
            context.update(_dashboard_currency_context())
            return render_template('index.html', **context)
        except Exception as e:
            logger.exception(f"Dashboard index error: {e}")
            return render_template('error.html', code=500, message="Dashboard yüklenirken hata oluştu"), 500

    @bp.route('/quick_transfer', methods=['POST'])
    @login_required
    def quick_transfer():
        from flask import session

        from domain.transactions.services import transfer_cash_to_asset
        from engines.financial_engine import parse_date_input

        try:
            amount_raw = request.form.get('amount', '0').strip()
            if not amount_raw:
                return jsonify({'success': False, 'message': 'Tutar girilmedi.'}), 400
            amount = to_decimal(amount_raw)
            if amount <= 0:
                return jsonify({'success': False, 'message': 'Tutar sıfırdan büyük olmalıdır.'}), 400

            date_raw = request.form.get('date', '').strip()
            transfer_date = parse_date_input(date_raw) if date_raw else datetime.now().strftime('%Y-%m-%d')
            asset_id_raw = request.form.get('asset_id', '').strip()
            if not asset_id_raw or not asset_id_raw.isdigit():
                return jsonify({'success': False, 'message': 'Lütfen bir varlık seçin. (Varlık seçimi zorunludur)'}), 400

            asset_obj, sale_tx = transfer_cash_to_asset(
                asset_id=int(asset_id_raw),
                amount=amount,
                transfer_date=transfer_date,
                note=request.form.get('note', '').strip() or None,
                tenant_id=g.get('tenant_id'),
            )
            unit_price = asset_obj.unit_price if asset_obj.unit_price > 0 else amount
            purchased_qty = round(amount / unit_price, 6) if unit_price > 0 else 1.0
            sym = _dashboard_currency_context()['dashboard_currency_symbol']
            session.modified = True
            return jsonify({
                'success': True,
                'message': (
                    f'{amount:,.2f} {sym} yatırım transferi kaydedildi. '
                    f'({unit_price:,.2f} {sym} birim fiyattan {purchased_qty:,.4f} adet)'
                ),
            })
        except ValueError as e:
            rollback_session()
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.exception(f"Quick transfer error: {e}")
            rollback_session()
            return jsonify({'success': False, 'message': 'Transfer kaydedilirken bir hata oluştu.'}), 500

    @bp.route('/analysis')
    @login_required
    def analysis():
        try:
            return render_template('analysis.html', **get_financial_analysis(g.get('tenant_id')))
        except Exception as e:
            logger.exception(f"Analysis page error: {e}")
            return render_template('error.html', code=500, message="Analiz yüklenirken hata oluştu"), 500

    @bp.route('/financial_freedom')
    @login_required
    def financial_freedom():
        try:
            from engines.financial_engine import get_financial_freedom_analysis
            preferences = get_container().applications.settings().get_preferences(session.get('user_id'))
            return render_template(
                'financial_freedom.html',
                analysis=get_financial_freedom_analysis(g.get('tenant_id'), preferences=preferences),
            )
        except Exception as e:
            logger.exception(f"Financial freedom error: {e}")
            from engines.financial_engine import get_empty_freedom_analysis
            return render_template('financial_freedom.html', analysis=get_empty_freedom_analysis())

    @bp.route('/financial_dashboard')
    @login_required
    def financial_dashboard():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            market_data = get_market_data_summary()
            if not market_data or not market_data.get('data_available', False):
                logger.warning("Piyasa özet verisi alınamadı; varsayılan boş yapı kullanılıyor")
                market_data = {
                    'assets': {},
                    'data_available': False,
                    'last_updated': timestamp,
                }
        except Exception as e:
            logger.exception(f"Piyasa veri servisi hatası: {e}")
            market_data = {
                'assets': {},
                'data_available': False,
                'last_updated': timestamp,
                'error': str(e),
            }

        try:
            from infrastructure.market.market_data_service import market_data_service as mds
            engine = get_analysis_engine(mds)
            analysis = engine.run_full_analysis(
                preferences=get_container().applications.settings().get_preferences(session.get('user_id'))
            )
            if analysis is None:
                raise ValueError("run_full_analysis() None döndürdü")
        except Exception as e:
            logger.exception(f"Analiz motoru hatası: {e}")
            analysis = {
                'timestamp': timestamp,
                'data_available': False,
                'error': str(e),
            }

        return render_template(
            'financial_dashboard.html',
            analysis=analysis,
            market_data=market_data,
        )

    @bp.route('/monthly_dashboard')
    @login_required
    def monthly_dashboard():
        try:
            from decimal import Decimal

            def _safe_dumps(obj):
                """Decimal-safe json.dumps."""
                import json as _json
                class _Enc(_json.JSONEncoder):
                    def default(self, o):
                        if isinstance(o, Decimal):
                            return float(o)
                        return super().default(o)
                return _json.dumps(obj, cls=_Enc)

            now = datetime.now()
            year = request.args.get('year', now.year, type=int)
            months_data, investment_data, _legacy_months = get_monthly_dashboard_data(
                year,
                g.get('tenant_id'),
            )
            from infrastructure.i18n import i18n

            localized_months = [
                i18n.gettext(f'monthly_month_{index:02d}')
                for index in range(1, 13)
            ]
            months_data = [
                {**month, 'name': localized_months[index]}
                for index, month in enumerate(months_data)
            ]
            months_tr = localized_months

            total_income = sum(month['inc'] for month in months_data)
            total_expense = sum(month['exp'] for month in months_data)
            total_investment = sum(month['inv'] for month in months_data)
            total_income_paid = sum(month['inc_paid'] for month in months_data)
            total_expense_paid = sum(month['exp_paid'] for month in months_data)
            total_investment_paid = sum(month['inv_paid'] for month in months_data)

            return render_template(
                'monthly_dashboard.html',
                selected_year=year,
                available_years=list(range(max(2020, now.year - 2), now.year + 6)),
                months_data=months_data,
                months_tr=_safe_dumps(months_tr),
                inc_data=_safe_dumps([month['inc'] for month in months_data]),
                exp_data=_safe_dumps([month['exp'] for month in months_data]),
                inv_data=_safe_dumps(investment_data),
                total_income=total_income,
                total_expense=total_expense,
                total_investment=total_investment,
                total_net=total_income - total_expense - total_investment,
                total_income_paid=total_income_paid,
                total_expense_paid=total_expense_paid,
                total_investment_paid=total_investment_paid,
                total_realized_net=sum(month['realized_net'] for month in months_data),
                total_pending_net=sum(month['pending_net'] for month in months_data),
                total_valuation_delta=sum(month['valuation_delta'] for month in months_data),
                total_investment_ratio=round((total_investment / total_income * 100), 2) if total_income else 0,
                total_investment_paid_ratio=round((total_investment_paid / total_income_paid * 100), 2) if total_income_paid else 0,
            )
        except Exception as e:
            logger.exception(f"Monthly dashboard error: {e}")
            return render_template('error.html', code=500, message="Aylık dashboard yüklenirken hata oluştu"), 500

    @bp.route('/user_guide')
    @login_required
    def user_guide():
        try:
            return render_template('user_guide.html')
        except Exception as e:
            logger.exception(f"User guide error: {e}")
            return render_template('error.html', code=500, message="Kullanma klavuzu yüklenirken hata oluştu"), 500

    def _format_quote(val):
        if val is None or val == '--' or str(val).strip().lower() in {'', 'nan', 'none', 'null'}:
            return '--'
        try:
            clean_str = str(val).replace('\xa0', '').replace(' ', '').replace(',', '.')
            parts = clean_str.split('.')
            if len(parts) > 2:
                clean_str = "".join(parts[:-1]) + "." + parts[-1]
            num = float(clean_str)
            if not math.isfinite(num) or num <= 0:
                return '--'
            return f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return str(val)

    @bp.route('/api/live-quotes')
    def live_quotes():
        """Canlı piyasa verilerini JSON formatında döndürür (frontend canlı ticker polling için)."""
        from engines.financial_engine import get_live_data
        data = get_live_data() or {}

        return jsonify({
            'success': True,
            'quotes': {
                'usd': _format_quote(data.get('usd')),
                'eur': _format_quote(data.get('eur')),
                'gold': _format_quote(data.get('gold')),
                'weather': data.get('weather') or '--',
                'last_updated': data.get('last_updated', ''),
                'is_stale': bool(data.get('is_stale', False)),
            }
        })

    @bp.route('/api/live-stream')
    def live_stream():
        """Server-Sent Events endpoint for real-time market ticker updates."""
        from engines.financial_engine import get_live_data

        def event_stream():
            data = get_live_data() or {}
            payload = json.dumps({
                'usd': _format_quote(data.get('usd')),
                'eur': _format_quote(data.get('eur')),
                'gold': _format_quote(data.get('gold')),
                'weather': data.get('weather') or '--',
                'last_updated': data.get('last_updated', ''),
                'is_stale': bool(data.get('is_stale', False)),
            })
            yield f"retry: 30000\ndata: {payload}\n\n"

        return Response(event_stream(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        })
