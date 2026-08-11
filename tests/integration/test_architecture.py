"""
Architectural Import Direction Tests
=====================================
Enforces the dependency rule:
    domain  ← application ← routes
    (arrows show allowed direction of import)

Violations caught:
  - domain/* importing from application/*
  - domain/* importing from routes/*
  - application/* importing from routes/*
  - Any layer importing from services.* shims (except services/ itself)
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _py_files(subdir):
    """Yield all .py file paths under ROOT/subdir."""
    base = os.path.join(ROOT, subdir)
    for dirpath, _, filenames in os.walk(base):
        for fname in filenames:
            if fname.endswith('.py'):
                yield os.path.join(dirpath, fname)


def _imports(filepath):
    """Return list of top-level module names imported by filepath."""
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []

    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def _relative_path(filepath):
    return os.path.relpath(filepath, ROOT).replace('\\', '/')


def _runtime_imports(filepath):
    """Return list of module names that are imported at runtime (not inside TYPE_CHECKING blocks).

    Uses recursive traversal so we can skip entire subtrees — ast.walk() cannot do this.

    This correctly skips:
        if TYPE_CHECKING:
            from repositories.x import Y  # type hint only, not a real runtime dep
    """
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []

    modules = []

    def _collect(nodes):
        for node in nodes:
            # Skip the body of `if TYPE_CHECKING:` blocks entirely
            if isinstance(node, ast.If):
                test = node.test
                is_type_checking = (
                    (isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING') or
                    (isinstance(test, ast.Attribute) and test.attr == 'TYPE_CHECKING')
                )
                if is_type_checking:
                    # Skip the body but still recurse into the else branch (rarely used)
                    if node.orelse:
                        _collect(node.orelse)
                    continue

            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.append(node.module)
            # Recurse into child statement lists (function bodies, class bodies, etc.)
            for child_attr in ('body', 'orelse', 'handlers', 'finalbody'):
                child_nodes = getattr(node, child_attr, None)
                if isinstance(child_nodes, list):
                    _collect(child_nodes)

    _collect(tree.body)
    return modules





# ── Rule 1: domain must not import from application ──────────────────────────
def test_domain_does_not_import_application():
    violations = []
    for fp in _py_files('domain'):
        for mod in _imports(fp):
            if mod.startswith('application'):
                violations.append(f"{_relative_path(fp)}  →  {mod}")
    assert not violations, (
        "Domain layer must not import from application layer:\n"
        + "\n".join(violations)
    )


# ── Rule 2: domain must not import from routes ────────────────────────────────
def test_domain_does_not_import_routes():
    violations = []
    for fp in _py_files('domain'):
        for mod in _imports(fp):
            if mod.startswith('routes'):
                violations.append(f"{_relative_path(fp)}  →  {mod}")
    assert not violations, (
        "Domain layer must not import from routes layer:\n"
        + "\n".join(violations)
    )


# ── Rule 3: application must not import from routes ───────────────────────────
def test_application_does_not_import_routes():
    violations = []
    for fp in _py_files('application'):
        for mod in _imports(fp):
            if mod.startswith('routes'):
                violations.append(f"{_relative_path(fp)}  →  {mod}")
    assert not violations, (
        "Application layer must not import from routes layer:\n"
        + "\n".join(violations)
    )


# ── Rule 4: domain must not import from shims (services.*) ───────────────────
def test_domain_does_not_import_legacy_shims():
    """
    domain/* must import from domain.* or stdlib, never from services.*
    (services/* are compatibility shims — domain predates them).
    """
    violations = []
    for fp in _py_files('domain'):
        for mod in _imports(fp):
            if mod.startswith('services.') or mod == 'services':
                violations.append(f"{_relative_path(fp)}  →  {mod}")
    assert not violations, (
        "Domain layer must not import from services/ shims:\n"
        + "\n".join(violations)
    )


# ── Rule 5: application/portfolio must not import from shims ─────────────────
def test_portfolio_application_does_not_import_legacy_shims():
    """
    application/portfolio has been migrated; it must not use services/ shims.
    Other application contexts (settings, etc.) are tracked as backlog.
    """
    violations = []
    for fp in _py_files('application/portfolio'):
        for mod in _imports(fp):
            if mod.startswith('services.') or mod == 'services':
                violations.append(f"{_relative_path(fp)}  →  {mod}")
    assert not violations, (
        "application/portfolio must not import from services/ shims:\n"
        + "\n".join(violations)
    )


# ── Inventory: shim usage across unmigrated application contexts ──────────────
def test_application_shim_inventory_report():
    """
    Non-blocking inventory test — generates a report of remaining shim usage
    in application/ contexts not yet migrated (e.g., settings).
    This test always passes; it only prints so the report appears in -v output.
    """
    MIGRATED = {
        'application/portfolio',
        'application/transactions',
        'application/planning',
        'application/users',
        'application/reporting',
        'application/analysis',
        'application/settings',
        'application/admin',
        'application/ai',
    }  # expand as each context is migrated
    remaining = []
    for fp in _py_files('application'):
        rel = _relative_path(fp)
        # skip already-migrated contexts
        if any(rel.startswith(m) for m in MIGRATED):
            continue
        for mod in _imports(fp):
            if mod.startswith('services.') or mod == 'services':
                remaining.append(f"  {rel}  →  {mod}")

    if remaining:
        print("\n[Shim Inventory] Unmigrated application shim dependencies:")
        for line in remaining:
            print(line)
    # always passes — this is a tracking test, not an enforcement test
    assert True


# ── Rule 6: migrated route files must not import from shims ────────────────
MIGRATED_ROUTES = {
    'routes/assets.py',          # Sprint 8.1
    'routes/transactions.py',    # Sprint 8.2
    'routes/plans.py',           # Sprint 8.3
    'routes/auth.py',            # Sprint 8.4
    'routes/profile.py',         # Sprint 8.4
    'routes/tenant.py',          # Sprint 8.4
    'routes/dashboard.py',       # Sprint 8.5
    'routes/logbook.py',         # Sprint 8.6
    'routes/strategy.py',        # Sprint 8.6
    'routes/settings.py',        # Sprint 8.7
    'routes/admin.py',           # Sprint 8.7
}

# services/ directory has been fully migrated to infrastructure/.
# No legacy service utilities remain — SERVICES_UTILITIES is now empty.
# Sprint 8.9C completed: services/ deleted.
SERVICES_UTILITIES: set = set()


def _is_shim(mod: str) -> bool:
    """Return True for any import from the now-deleted services/ package."""
    return mod.startswith('services.') or mod == 'services'



def test_migrated_routes_do_not_import_legacy_shims():
    """
    Routes that have been migrated must not fall back to services/ shims.
    Permanent infrastructure utilities in SERVICES_UTILITIES are exempt.
    Expand MIGRATED_ROUTES as each route file is migrated.
    """
    violations = []
    for route_rel in MIGRATED_ROUTES:
        fp = os.path.join(ROOT, *route_rel.split('/'))
        if not os.path.exists(fp):
            continue
        for mod in _imports(fp):
            if _is_shim(mod):
                violations.append(f"{route_rel}  →  {mod}")
    assert not violations, (
        "Migrated route files must not import from services/ shims:\n"
        + "\n".join(violations)
    )



# ── Inventory: shim usage across unmigrated route files ────────────────────
def test_routes_shim_inventory_report():
    """
    Non-blocking inventory of remaining shim usage in not-yet-migrated route files.
    Always passes; prints for visibility in -v output.
    """
    remaining = []
    for fp in _py_files('routes'):
        rel = _relative_path(fp)
        if rel in MIGRATED_ROUTES:
            continue
        for mod in _imports(fp):
            if _is_shim(mod):
                remaining.append(f"  {rel}  →  {mod}")

    if remaining:
        print("\n[Routes Shim Inventory] Unmigrated route shim dependencies:")
        for line in remaining:
            print(line)
    assert True


# ── Architecture boundary: Application layer cannot see Repositories/Infrastructure ───
def test_application_layer_does_not_import_repositories():
    """
    Sprint 8.7+ DoD rule: Application services must NOT import directly from:
      - repositories.*
      - infrastructure.*

    They may only import from:
      - domain.*
      - application.* (including application.ports.*)
      - Standard library / flask basics / engines / utils

    application/transactions/transaction_application.py is a known exception
    because it still directly holds repositories for backwards-compat;
    add to ALLOWED_EXCEPTIONS once it is refactored (Sprint 9.0).
    """
    ALLOWED_EXCEPTIONS = {
        'application/base.py',
        'application/settings/settings_application.py',  # uses infrastructure.i18n for allowed_languages list
        'application/transactions/commands/create_transaction.py',
        'application/transactions/commands/update_transaction.py',
        'application/transactions/commands/delete_transaction.py',
        'application/transactions/queries/get_transaction_page.py',
    }
    FORBIDDEN_PREFIXES = ('repositories.', 'infrastructure.')

    violations = []
    for fp in _py_files('application'):
        rel = _relative_path(fp)
        if rel in ALLOWED_EXCEPTIONS:
            continue
        for mod in _imports(fp):
            if any(mod.startswith(p) for p in FORBIDDEN_PREFIXES):
                violations.append(f"{rel}  →  {mod}")

    assert not violations, (
        "Application services must not import from repositories/ or infrastructure/:\n"
        + "\n".join(violations)
    )

# ---------------- Sprint 8.9A.1 Architecture Audit Tests ----------------

def test_global_legacy_import_audit():
    """
    Ensure NO layer imports from services.* (except valid SERVICES_UTILITIES).
    This enforces the shim removal readiness.
    """
    violations = []
    # Check domain, application, infrastructure, routes, repositories
    for layer in ['domain', 'application', 'infrastructure', 'routes', 'repositories']:
        for fp in _py_files(layer):
            rel = _relative_path(fp)
            if rel.startswith('infrastructure/services') or rel.startswith('services'):
                continue
            for mod in _imports(fp):
                if _is_shim(mod):
                    violations.append(f"{rel}  ->  {mod}")

    assert not violations, (
        "Global Legacy Import Audit Failed. Found deprecated services.* imports:\n"
        + "\n".join(violations)
    )

def test_circular_dependency_scan():
    """
    Strict unidirectional flow:
    - domain -> cannot import application, infrastructure, routes, repositories
      (TYPE_CHECKING-guarded type-hint imports are allowed; they don't exist at runtime)
    - infrastructure -> cannot import routes or application
    - repositories -> cannot import application or routes

    Application layer is already covered by test_application_layer_does_not_import_repositories.
    """
    violations = []

    # 1. Domain — use _runtime_imports so TYPE_CHECKING guards are respected
    for fp in _py_files('domain'):
        rel = _relative_path(fp)
        for mod in _runtime_imports(fp):
            if any(mod.startswith(p) for p in ['application', 'infrastructure', 'routes', 'repositories']):
                violations.append(f"Domain leak: {rel} -> {mod}")

    # 2. Infrastructure
    #    Hexagonal Architecture: infra adapters MAY import application.ports
    #    (they implement the port interface). Other application imports are forbidden.
    INFRA_PORT_ADAPTER_EXCEPTIONS = {
        'infrastructure/database/outbox_adapter.py',  # implements application.ports.outbox_port
    }
    for fp in _py_files('infrastructure'):
        rel = _relative_path(fp)
        for mod in _imports(fp):
            if mod.startswith('routes'):
                violations.append(f"Infrastructure leak: {rel} -> {mod}")
            elif mod.startswith('application'):
                # Allow adapters to import their ports
                if rel in INFRA_PORT_ADAPTER_EXCEPTIONS and mod.startswith('application.ports'):
                    continue
                if 'ports' in mod.split('.'):
                    continue
                violations.append(f"Infrastructure leak: {rel} -> {mod}")

    # 3. Repositories
    for fp in _py_files('repositories'):
        rel = _relative_path(fp)
        for mod in _imports(fp):
            if any(mod.startswith(p) for p in ['application', 'routes']):
                violations.append(f"Repository leak: {rel} -> {mod}")

    assert not violations, (
        "Circular Dependency Scan Failed. Found invalid cross-layer imports:\n"
        + "\n".join(violations)
    )

def test_public_api_audit():
    """
    Ensure consumers of domain services only import via the context's __init__.py (public API).
    Example: `from domain.portfolio.services import AssetService` is allowed.
    `from domain.portfolio.services.asset_service import AssetService` is forbidden (from outside the context).
    """
    violations = []
    for layer in ['application', 'routes']:
        for fp in _py_files(layer):
            rel = _relative_path(fp)
            for mod in _imports(fp):
                # If importing from domain.<context>.services, it should end there.
                # E.g. mod == 'domain.portfolio.services.asset_service' is bad.
                parts = mod.split('.')
                if len(parts) > 3 and parts[0] == 'domain' and parts[2] == 'services':
                    # It imported a specific module inside services
                    violations.append(f"Public API violation: {rel} -> {mod}")

    assert not violations, (
        "Public API Audit Failed. Do not bypass domain/__init__.py files:\n"
        + "\n".join(violations)
    )
