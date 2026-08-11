"""Small SQLAlchemy repository primitives."""

from models import db

from .contracts import BaseRepositoryContract


class BaseRepository(BaseRepositoryContract):
    """Wraps the injected SQLAlchemy extension/session.

    Repositories can pass an optional database object for tests or alternate
    SQLAlchemy session providers. If no database is provided, the default
    Flask-SQLAlchemy extension is used.
    """

    def __init__(self, database=None):
        self.db = database or db
        self.session = self.db.session

    def query(self, *entities):
        return self.session.query(*entities)

    def get(self, model, obj_id):
        return self.session.get(model, obj_id)

    def add(self, entity):
        self.session.add(entity)
        return entity

    def delete(self, entity):
        self.session.delete(entity)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class TenantScopedRepository(BaseRepository):
    """
    Tenant-aware base repository.

    Her alt sınıf bu sınıftan türemeli; tenant gerektiren tüm
    sorgular `require_tenant_id()` ile başlamalıdır.

    Kurallar:
        - tenant_id None ise RuntimeError fırlatılır (sessiz fallback YOK).
        - Flask request context varsa g.tenant_id otomatik çözülür.
        - Context dışında (background worker, CLI) tenant_id açıkça
          geçirilmelidir.
    """

    def require_tenant_id(self, tenant_id=None) -> str:
        """
        tenant_id çözümler ve zorunlu tutar.

        Öncelik sırası:
            1. Açıkça geçirilen parametre
            2. Flask g.tenant_id (request context)
            3. RuntimeError
        """
        if tenant_id:
            return tenant_id
        try:
            from flask import g
            tid = g.get('tenant_id')
            if tid:
                return tid
        except RuntimeError:
            # Flask request context dışında — normal, devam et
            pass
        raise RuntimeError(
            "Tenant context bulunamadı. "
            "Bu metodu çağırırken tenant_id parametresi zorunludur."
        )

    def filter_for_tenant(self, query, model, tenant_id):
        """SQLAlchemy query'e tenant filtresi ekler."""
        return query.filter(model.tenant_id == tenant_id)

    def get_for_tenant(self, model, record_id, tenant_id):
        """
        Kaydı tenant sınırı içinde getirir.
        Bulunamazsa None döner (caller 404/PermissionError kararını verir).
        """
        return (
            self.session.query(model)
            .filter(model.id == record_id, model.tenant_id == tenant_id)
            .first()
        )

    def assert_same_tenant(self, record, tenant_id, error_msg="Bu kaydı görüntüleme yetkiniz yok."):
        """
        Kaydın tenant'ını doğrular; uyuşmazlıkta PermissionError fırlatır.
        """
        if record is None or record.tenant_id != tenant_id:
            raise PermissionError(error_msg)
        return record

