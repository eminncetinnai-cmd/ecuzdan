"""Tenant resolver utilities: try multiple strategies to find tenant id from request or environment."""

try:
    from flask import g, has_request_context, request
except Exception:
    has_request_context = None
    request = None
    g = None


def resolve_from_request() -> str:
    """Try common request-based locations for tenant id.

    Order:
    - request.tenant_id attribute
    - X-Tenant-ID header
    - request.args['tenant_id']
    - flask.g.get('tenant_id')
    """
    if has_request_context():
        try:
            if hasattr(request, 'tenant_id') and request.tenant_id:
                return request.tenant_id
        except Exception:
            pass
        try:
            header = request.headers.get('X-Tenant-ID') if hasattr(request, 'headers') else None
            if header:
                return header
        except Exception:
            pass
        try:
            arg = request.args.get('tenant_id') if hasattr(request, 'args') else None
            if arg:
                return arg
        except Exception:
            pass
        try:
            if g is not None:
                try:
                    val = g.get('tenant_id')
                except Exception:
                    val = getattr(g, 'tenant_id', None)
                if val:
                    return val
        except Exception:
            pass
    return None
