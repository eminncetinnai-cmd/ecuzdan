"""
Lazy Import Guard — PEP 562 tuzağına karşı kalıcı yönetişim testi.

Modül düzeyinde ``__getattr__`` yalnızca DIŞARIDAN yapılan ``modul.isim``
erişimlerinde çağrılır. Aynı modülün fonksiyonları içinde ``isim`` çıplak global
olarak kullanılırsa Python ``__getattr__``'a bakmaz ve ``NameError`` fırlatır.
``hasattr(modul, 'isim')`` gibi testler bu hatayı GİZLER.

Bu test, lazy yüklenen isimlerin fonksiyon gövdelerinde yerel olarak
bağlanmadan kullanılmasını yasaklar. Doğru kalıp: ``_pd()``, ``_yf()``,
``_pisa()`` gibi açık yükleyici fonksiyonlar.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {'.venv', 'venv', '.git', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache'}


def _project_python_files():
    for path in ROOT.rglob('*.py'):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        yield path


def _lazy_names(tree: ast.Module) -> set[str]:
    """Collect string constants compared against the arg of module-level __getattr__."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == '__getattr__':
            for sub in ast.walk(node):
                if isinstance(sub, ast.Compare):
                    for operand in [sub.left, *sub.comparators]:
                        if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                            names.add(operand.value)
    return names


def _bound_names(func: ast.AST) -> set[str]:
    bound: set[str] = set()
    for sub in ast.walk(func):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
            bound.add(sub.id)
        elif isinstance(sub, ast.arg):
            bound.add(sub.arg)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for alias in sub.names:
                bound.add((alias.asname or alias.name).split('.')[0])
    return bound


def _violations(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError):
        return []
    lazy = _lazy_names(tree)
    if not lazy:
        return []

    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name == '__getattr__':
            continue
        bound = _bound_names(node)
        for sub in ast.walk(node):
            if (
                isinstance(sub, ast.Name)
                and isinstance(sub.ctx, ast.Load)
                and sub.id in lazy
                and sub.id not in bound
            ):
                rel = path.relative_to(ROOT).as_posix()
                found.append(f"{rel}:{sub.lineno} -> '{sub.id}' used as bare global in {node.name}()")
    return found


@pytest.mark.unit
def test_no_bare_global_use_of_lazy_module_attributes():
    violations = []
    for path in _project_python_files():
        violations.extend(_violations(path))
    assert not violations, (
        "Lazy (module __getattr__) isimleri fonksiyon içinde çıplak global olarak kullanılıyor; "
        "runtime'da NameError verir. Açık yükleyici (ör. _pd()) kullanın:\n  " + "\n  ".join(violations)
    )


@pytest.mark.unit
def test_guard_detects_the_trap(tmp_path):
    """Self-test: the detector must flag the exact bug pattern."""
    bad = tmp_path / 'bad_module.py'
    bad.write_text(
        "def __getattr__(name):\n"
        "    if name == 'pd':\n"
        "        import pandas as pd\n"
        "        return pd\n"
        "    raise AttributeError(name)\n"
        "\n"
        "def build():\n"
        "    return pd.DataFrame()\n",
        encoding='utf-8',
    )
    good = tmp_path / 'good_module.py'
    good.write_text(
        "def __getattr__(name):\n"
        "    if name == 'pd':\n"
        "        return _pd()\n"
        "    raise AttributeError(name)\n"
        "\n"
        "def _pd():\n"
        "    import pandas as mod\n"
        "    return mod\n"
        "\n"
        "def build():\n"
        "    pd = _pd()\n"
        "    return pd.DataFrame()\n",
        encoding='utf-8',
    )
    global ROOT
    original_root = ROOT
    ROOT = tmp_path
    try:
        assert _violations(bad), "Guard must flag bare global use of a lazy name"
        assert not _violations(good), "Guard must accept the explicit-loader pattern"
    finally:
        ROOT = original_root


@pytest.mark.unit
def test_lazy_loaders_resolve_real_modules():
    """Runtime check: loaders return real modules without prior attribute access."""
    import infrastructure.background.background_service as bg
    import routes.export as export_module

    assert bg._pd().__name__ == 'pandas'
    assert bg._yf().__name__ == 'yfinance'
    assert export_module._pisa().__name__ == 'xhtml2pdf.pisa'
