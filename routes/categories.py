"""Category and catalog routes."""

import logging

from flask import flash, g, redirect, render_template, request, url_for

from bootstrap import get_container  # noqa: F401
from domain.tenant.accessor import get_tenant as get_tenant_id
from infrastructure.i18n import i18n
from utils.db_session import rollback_session
from utils.decorators import login_required

get_tenant = get_tenant_id  # Backward-compatible module export

logger = logging.getLogger(__name__)


def _get_catalog_service():
    from bootstrap import get_container as current_get_container
    container = current_get_container()
    # Clear cache to ensure updated code is loaded
    if hasattr(container.applications, '_instances'):
        container.applications._instances.clear()
    return container.applications.catalog()


def register_category_routes(bp):

    @bp.route('/categories', methods=['GET', 'POST'])
    @login_required
    def categories_page():
        catalog_service = _get_catalog_service()

        if request.method == 'POST':
            try:
                user_id = getattr(g, 'current_user', None) and g.current_user.id
                catalog_service.add_from_form(request.form, tenant_id=get_tenant_id(), user_id=user_id)
                action = request.form.get('action', '')
                msg = 'İşlem başarıyla gerçekleştirildi!'
                if 'cat' in action:
                    msg = 'Kategori başarıyla kaydedildi!'
                elif 'asset_type' in action:
                    msg = 'Varlık sınıfı başarıyla kaydedildi!'
                elif 'asset_sector' in action:
                    msg = 'Varlık sektörü başarıyla kaydedildi!'
                flash(msg, 'success')
            except ValueError as e:
                rollback_session()
                flash(i18n.gettext("ui_auto_fd071d7a0a0b", **{"str(e)": str(e)}), 'error')
            except Exception as e:
                logger.exception(f"Category page POST error: {e}")
                rollback_session()
                flash(i18n.gettext("ui_auto_620f4a506b50"), 'error')

        try:
            return render_template('categories.html', **catalog_service.page_context(get_tenant_id()))
        except Exception as e:
            logger.exception(f"Categories page error: {e}")
            flash(i18n.gettext("ui_auto_4a9393fda386"), 'error')
            return render_template('categories.html', cats=[], asset_types=[], asset_sectors=[])

    @bp.route('/update_category/<int:id>', methods=['POST'])
    @login_required
    def update_category_route(id):
        catalog_service = _get_catalog_service()
        try:
            budget_limit_provided = 'budget_limit' in request.form
            user_id = getattr(g, 'current_user', None) and g.current_user.id
            raw_version = request.form.get('version')
            version = int(raw_version) if raw_version not in (None, '') else None

            raw_parent = request.form.get('parent_id')
            parent_id = None
            if raw_parent is not None:
                raw_parent = str(raw_parent).strip()
                if raw_parent in ('', '0'):
                    parent_id = 0
                else:
                    try:
                        parent_id = int(raw_parent)
                    except ValueError:
                        parent_id = 0

            color = request.form.get('color', '').strip() or None
            icon = request.form.get('icon', '').strip() or None

            catalog_service.update_category(
                id,
                request.form.get('name', '').strip(),
                request.form.get('type', ''),
                tenant_id=get_tenant_id(),
                code=request.form.get('code', '').strip() or None,
                parent_id=parent_id,
                budget_limit=request.form.get('budget_limit') if budget_limit_provided else None,
                budget_limit_provided=budget_limit_provided,
                version=version,
                user_id=user_id,
                color=color,
                icon=icon,
            )
            flash(i18n.gettext("ui_auto_643b031f4198"), 'success')
        except Exception as e:
            logger.exception(f"Update category error: {e}")
            rollback_session()
            flash(i18n.gettext("ui_auto_bb2e87aeb06c", **{"str(e)": str(e)}), 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/restore_category/<int:id>', methods=['POST'])
    @login_required
    def restore_category_route(id):
        catalog_service = _get_catalog_service()
        try:
            user_id = getattr(g, 'current_user', None) and g.current_user.id
            catalog_service.restore_category(id, tenant_id=get_tenant_id(), user_id=user_id)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'success', 'message': 'Kategori başarıyla geri yüklendi.'}, 200
            flash('Kategori başarıyla geri yüklendi.', 'success')
        except Exception as e:
            logger.exception(f"Restore category error: {e}")
            rollback_session()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': str(e)}, 400
            flash(str(e), 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/merge_categories', methods=['POST'])
    @login_required
    def merge_categories_route():
        catalog_service = _get_catalog_service()
        try:
            user_id = getattr(g, 'current_user', None) and g.current_user.id
            source_id = request.form.get('source_id')
            target_id = request.form.get('target_id')
            if not source_id or not target_id:
                raise ValueError("Kaynak ve hedef kategori seçilmelidir.")
            res = catalog_service.merge_categories(
                int(source_id), int(target_id),
                tenant_id=get_tenant_id(), user_id=user_id
            )
            msg = f"Kategoriler başarıyla birleştirildi ({res.get('tx_count', 0)} işlem aktarıldı)."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'success', 'message': msg}, 200
            flash(msg, 'success')
        except Exception as e:
            logger.exception(f"Merge categories error: {e}")
            rollback_session()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': str(e)}, 400
            flash(str(e), 'error')
        return redirect(url_for('categories.categories_page'))


    @bp.route('/delete_category/<int:id>', methods=['POST', 'DELETE'])
    @login_required
    def delete_category_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.delete_category(id, tenant_id=get_tenant_id())
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'success', 'message': 'Kategori başarıyla silindi.'}, 200
            flash(i18n.gettext("ui_auto_509d5517a7d8"), 'success')
        except Exception as e:
            logger.exception(f"Delete category error: {e}")
            rollback_session()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': str(e)}, 400
            flash(i18n.gettext("ui_auto_46cb0f1c31d5", **{"str(e)": str(e)}), 'error')
        return redirect(url_for('categories.categories_page'))


    @bp.route('/update_asset_type/<int:id>', methods=['POST'])
    @login_required
    def update_asset_type_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.update_asset_type(id, request.form.get('name', '').strip())
            flash(i18n.gettext("ui_auto_1bdb50a2444b"), 'success')
        except Exception as e:
            logger.exception(f"Update asset type error: {e}")
            rollback_session()
            flash(i18n.gettext("ui_auto_bb2e87aeb06c", **{"str(e)": str(e)}), 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/delete_asset_type/<int:id>', methods=['POST', 'DELETE'])
    @login_required
    def delete_asset_type_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.delete_asset_type(id)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'success', 'message': 'Varlık sınıfı başarıyla silindi.'}, 200
            flash(i18n.gettext("ui_auto_ac1519dd34ab"), 'success')
        except Exception as e:
            logger.exception(f"Delete asset type error: {e}")
            rollback_session()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': str(e)}, 400
            flash(i18n.gettext("ui_auto_46cb0f1c31d5", **{"str(e)": str(e)}), 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/update_asset_sector/<int:id>', methods=['POST'])
    @login_required
    def update_asset_sector_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.update_asset_sector(id, request.form.get('name', '').strip())
            flash(i18n.gettext("ui_auto_0316bcec9204"), 'success')
        except Exception as e:
            logger.exception(f"Update asset sector error: {e}")
            rollback_session()
            flash(i18n.gettext("ui_auto_bb2e87aeb06c", **{"str(e)": str(e)}), 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/delete_asset_sector/<int:id>', methods=['POST', 'DELETE'])
    @login_required
    def delete_asset_sector_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.delete_asset_sector(id)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'success', 'message': 'Varlık sektörü başarıyla silindi.'}, 200
            flash(i18n.gettext("ui_auto_e3d54f599b42"), 'success')
        except Exception as e:
            logger.exception(f"Delete asset sector error: {e}")
            rollback_session()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': str(e)}, 400
            flash(i18n.gettext("ui_auto_46cb0f1c31d5", **{"str(e)": str(e)}), 'error')
        return redirect(url_for('categories.categories_page'))
