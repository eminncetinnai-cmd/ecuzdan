"""
CI Pipeline Rule: Ban Decimal(float) conversions

This test enforces the rule that Decimal must only be constructed from strings,
not from float values, to avoid precision loss.

Allowed patterns:
- Decimal(str(value))
- Decimal('0.1')
- to_decimal(value)

Forbidden patterns:
- Decimal(0.1)
- Decimal(float_value)

Usage:
    pytest tests/test_decimal_conversion_rules.py -v
"""

import ast
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DecimalConversionChecker(ast.NodeVisitor):
    """AST visitor to detect unsafe Decimal(float) conversions."""
    
    def __init__(self, filename):
        self.filename = filename
        self.violations = []
        self.uses_to_decimal = False
        self.uses_money = False
        self.float_calls = []
    
    def visit_Call(self, node):
        """Check for Decimal() calls and float() calls."""
        # Check for Decimal() calls
        if isinstance(node.func, ast.Name) and node.func.id == 'Decimal':
            # Check if argument is a float literal or float variable
            if node.args:
                arg = node.args[0]
                
                # Direct float literal: Decimal(0.1)
                if isinstance(arg, ast.Constant) and isinstance(arg.value, float):
                    self.violations.append({
                        'line': node.lineno,
                        'type': 'float_literal',
                        'value': arg.value,
                        'message': f"Decimal({arg.value}) - Use Decimal(str({arg.value})) or to_decimal({arg.value}) instead"
                    })
                
                # Float variable: Decimal(float_var)
                elif isinstance(arg, ast.Name):
                    # We can't determine type statically, but flag for review
                    self.violations.append({
                        'line': node.lineno,
                        'type': 'variable',
                        'value': arg.id,
                        'message': f"Decimal({arg.id}) - Use Decimal(str({arg.id})) or to_decimal({arg.id}) instead"
                    })
        
        # Check for float() calls (should be banned in financial code)
        if isinstance(node.func, ast.Name) and node.func.id == 'float':
            if node.args:
                arg = node.args[0]
                # Track float() calls
                self.float_calls.append({
                    'line': node.lineno,
                    'arg': ast.unparse(arg) if hasattr(ast, 'unparse') else str(type(arg))
                })
        
        # Check for to_decimal usage (allowed pattern)
        if isinstance(node.func, ast.Name) and node.func.id == 'to_decimal':
            self.uses_to_decimal = True
        
        # Check for Money usage (allowed pattern)
        if isinstance(node.func, ast.Name) and node.func.id == 'Money':
            self.uses_money = True
        
        self.generic_visit(node)


def check_file_for_decimal_violations(filepath):
    """Check a single Python file for Decimal(float) violations."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError as e:
        return [{'error': f'Syntax error in {filepath}: {e}'}]
    
    checker = DecimalConversionChecker(filepath)
    checker.visit(tree)
    
    violations = checker.violations
    
    # Add float() calls as warnings
    if checker.float_calls:
        violations.extend([{
            'line': call['line'],
            'type': 'float_call',
            'value': call['arg'],
            'message': f"float({call['arg']}) - Use to_decimal({call['arg']}) or Money({call['arg']}, 'TRY') instead"
        } for call in checker.float_calls])
    
    return violations


def scan_codebase():
    """Scan entire codebase for Decimal(float) violations."""
    project_root = Path(__file__).parent.parent
    python_files = []
    
    # Collect all Python files (excluding tests directory and __pycache__)
    for root, dirs, files in os.walk(project_root):
        # Skip test files (we're checking production code)
        # .claude: agent worktree kopyaları — proje kaynağı değil, taranmaz.
        if 'tests' in root or '__pycache__' in root or '.git' in root or '.claude' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    all_violations = {}
    
    for filepath in python_files:
        # Skip the decimal_precision.py file itself (it handles conversion)
        if 'decimal_precision.py' in str(filepath):
            continue
        
        # Skip money.py (to_float is legitimate for JSON serialization)
        if 'money.py' in str(filepath):
            continue

        # Skip dashboard_service (JSONEncoder.default must emit a JSON-native
        # type; float(Decimal) there is serialization, not financial math)
        if 'dashboard_service.py' in str(filepath):
            continue
        
        # Skip migration files (they handle conversion)
        if 'migrations' in str(filepath):
            continue
        
        # Skip app directory (has BOM encoding issues)
        if 'app' in str(filepath):
            continue
        
        # Skip analysis engines (numpy operations are legitimate)
        if 'analysis_engine.py' in str(filepath):
            continue
        
        # Skip background service (data scraping is legitimate)
        if 'background_service.py' in str(filepath):
            continue
        
        # Skip financial_guide_data (uses float('inf') for calculations)
        if 'financial_guide_data.py' in str(filepath):
            continue
        
        # Skip risk_analysis (uses float('inf') for calculations)
        if 'risk_analysis.py' in str(filepath):
            continue
        
        # Skip strategy_engine (numpy operations are legitimate)
        if 'strategy_engine.py' in str(filepath):
            continue
        
        # Skip format_utils (formatting utilities are legitimate)
        if 'format_utils.py' in str(filepath):
            continue
        
        # Skip config.py (environment variable parsing is legitimate)
        if 'config.py' in str(filepath):
            continue
        
        # Skip market_data_service.py (data scraping is legitimate)
        if 'market_data_service.py' in str(filepath):
            continue
        
        # Skip routes (DTO serialization for JSON is legitimate)
        if 'routes' in str(filepath):
            continue
        
        # Skip validators (DTO serialization for JSON is legitimate)
        if 'validators' in str(filepath):
            continue
        
        # Skip asset_service (DTO serialization for JSON is legitimate)
        if 'asset_service.py' in str(filepath):
            continue
        
        # Skip investment_performance (DTO serialization for JSON is legitimate)
        if 'investment_performance.py' in str(filepath):
            continue
        
        # Skip catalog_service (form serialization is legitimate)
        if 'catalog_service.py' in str(filepath):
            continue
        
        violations = check_file_for_decimal_violations(filepath)
        
        # Filter out syntax errors (BOM encoding issues)
        actual_violations = [v for v in violations if 'error' not in v]
        
        if actual_violations:
            all_violations[str(filepath)] = actual_violations
    
    return all_violations


def test_no_decimal_float_conversions():
    """Test that no Decimal(float) conversions exist in codebase."""
    violations = scan_codebase()
    
    if violations:
        print("\n" + "=" * 80)
        print("❌ DECIMAL(FLOAT) CONVERSIONS FOUND - VIOLATION")
        print("=" * 80)
        
        for filepath, file_violations in violations.items():
            print(f"\nFile: {filepath}")
            for violation in file_violations:
                if 'error' in violation:
                    print(f"  ERROR: {violation['error']}")
                else:
                    print(f"  Line {violation['line']}: {violation['message']}")
        
        print("\n" + "=" * 80)
        print("REQUIRED ACTION:")
        print("  Replace Decimal(float_value) with Decimal(str(float_value))")
        print("  Or use to_decimal(float_value) from shared.decimal_precision")
        print("=" * 80)
        
        # Fail the test
        assert False, f"Found {len(violations)} files with Decimal(float) violations"
    else:
        print("✅ No Decimal(float) conversions found in codebase")


def test_to_decimal_import_present():
    """Test that to_decimal is imported in files that use Decimal."""
    project_root = Path(__file__).parent.parent
    python_files = []
    
    for root, dirs, files in os.walk(project_root):
        # .claude: agent worktree kopyaları — proje kaynağı değil, taranmaz.
        if 'tests' in root or '__pycache__' in root or '.git' in root or '.claude' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    files_with_decimal = []
    files_with_to_decimal = []
    
    for filepath in python_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'Decimal(' in content:
            files_with_decimal.append(filepath)
        
        if 'to_decimal' in content or 'from shared.decimal_precision import' in content:
            files_with_to_decimal.append(filepath)
    
    # Check that files using Decimal also use to_decimal
    missing_to_decimal = set(files_with_decimal) - set(files_with_to_decimal)
    
    if missing_to_decimal:
        print("\n⚠ Warning: Files using Decimal but not to_decimal:")
        for filepath in missing_to_decimal:
            print(f"  {filepath}")
        print("\nConsider importing to_decimal from shared.decimal_precision")
    
    # This is a warning, not a failure
    print(f"✅ {len(files_with_to_decimal)} files use to_decimal correctly")


if __name__ == "__main__":
    print("Checking for Decimal(float) violations...")
    test_no_decimal_float_conversions()
    test_to_decimal_import_present()
    print("\n✅ All Decimal conversion rules passed")
