"""Category and catalog routes."""

import logging

from flask import flash, g, redirect, render_template, request, url_for

from bootstrap import get_container
from domain.tenant.accessor import get_tenant as get_tenant_id
from utils.db_session import rollback_session
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _get_catalog_service():
    from bootstrap import get_container
    container = get_container()
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
                flash(f'İşlem başarısız: {str(e)}', 'error')
            except Exception as e:
                logger.exception(f"Category page POST error: {e}")
                rollback_session()
                flash('İşlem sırasında beklenmeyen bir hata oluştu.', 'error')

        try:
            return render_template('categories.html', **catalog_service.page_context(get_tenant_id()))
        except Exception as e:
            logger.exception(f"Categories page error: {e}")
            flash('Kategoriler yüklenirken hata oluştu.', 'error')
            return render_template('categories.html', cats=[], asset_types=[], asset_sectors=[])

    @bp.route('/update_category/<int:id>', methods=['POST'])
    @login_required
    def update_category_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.update_category(
                id,
                request.form.get('name', '').strip(),
                request.form.get('type', ''),
                tenant_id=get_tenant_id(),
            )
            flash('Kategori başarıyla güncellendi.', 'success')
        except Exception as e:
            logger.exception(f"Update category error: {e}")
            rollback_session()
            flash(f'Güncelleme başarısız: {str(e)}', 'error')
        return redirect(url_for('categories.categories_page'))


    @bp.route('/delete_category/<int:id>', methods=['GET', 'POST', 'DELETE'])
    @login_required
    def delete_category_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.delete_category(id, tenant_id=get_tenant_id())
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'success', 'message': 'Kategori başarıyla silindi.'}, 200
            flash('Kategori başarıyla silindi.', 'success')
        except Exception as e:
            logger.exception(f"Delete category error: {e}")
            rollback_session()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'status': 'error', 'message': str(e)}, 400
            flash(f'Silme başarısız: {str(e)}', 'error')
        return redirect(url_for('categories.categories_page'))


    @bp.route('/update_asset_type/<int:id>', methods=['POST'])
    @login_required
    def update_asset_type_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.update_asset_type(id, request.form.get('name', '').strip())
            flash('Varlık tipi başarıyla güncellendi.', 'success')
        except Exception as e:
            logger.exception(f"Update asset type error: {e}")
            rollback_session()
            flash(f'Güncelleme başarısız: {str(e)}', 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/delete_asset_type/<int:id>')
    @login_required
    def delete_asset_type_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.delete_asset_type(id)
            flash('Varlık tipi başarıyla silindi.', 'success')
        except Exception as e:
            logger.exception(f"Delete asset type error: {e}")
            rollback_session()
            flash(f'Silme başarısız: {str(e)}', 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/update_asset_sector/<int:id>', methods=['POST'])
    @login_required
    def update_asset_sector_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.update_asset_sector(id, request.form.get('name', '').strip())
            flash('Sektör başarıyla güncellendi.', 'success')
        except Exception as e:
            logger.exception(f"Update asset sector error: {e}")
            rollback_session()
            flash(f'Güncelleme başarısız: {str(e)}', 'error')
        return redirect(url_for('categories.categories_page'))

    @bp.route('/delete_asset_sector/<int:id>')
    @login_required
    def delete_asset_sector_route(id):
        catalog_service = _get_catalog_service()
        try:
            catalog_service.delete_asset_sector(id)
            flash('Sektör başarıyla silindi.', 'success')
        except Exception as e:
            logger.exception(f"Delete asset sector error: {e}")
            rollback_session()
            flash(f'Silme başarısız: {str(e)}', 'error')
        return redirect(url_for('categories.categories_page'))
