import os
import re


def test_no_crud_bypass_in_routes():
    """
    Statik Analiz Regresyon Testi:
    routes/ altındaki hiçbir dosya doğrudan crud.add_transaction veya crud.add_asset'i çağırmamalıdır.
    """
    routes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'routes')

    # Yasaklı kelimeler / kalıplar
    patterns = [
        re.compile(r'crud\.add_transaction'),
        re.compile(r'crud\.add_asset'),
        re.compile(r'from\s+database\s+import\s+.*add_transaction'),
        re.compile(r'from\s+database\s+import\s+.*add_asset'),
        re.compile(r'from\s+database\.crud\s+import\s+.*add_transaction'),
        re.compile(r'from\s+database\.crud\s+import\s+.*add_asset'),
    ]

    for root, dirs, files in os.walk(routes_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in patterns:
                        match = pattern.search(content)
                        assert match is None, f"Lütfen Ledger bypass yapmayın! {file} dosyasında yasaklı '{pattern.pattern}' kullanımı bulundu."
