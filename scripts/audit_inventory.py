"""
E-Cuzdan Comprehensive Architecture & Route/Entity Inventory Extractor
Part of Phase 1 & 2 Audit
"""
import inspect
import json
import os
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Bootstrap app without starting background threads
os.environ['TESTING'] = 'True'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

import models
from app import create_app

app = create_app()

def extract_routes():
    routes = []
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static':
                continue
            view_fn = app.view_functions.get(rule.endpoint)
            doc = view_fn.__doc__ if view_fn else ""
            file_path = inspect.getfile(view_fn) if view_fn else ""
            methods = [m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
            routes.append({
                'url': str(rule),
                'endpoint': rule.endpoint,
                'methods': methods,
                'file': os.path.relpath(file_path, os.getcwd()) if file_path else "",
                'doc': (doc or "").strip().split("\n")[0]
            })
    return sorted(routes, key=lambda x: x['url'])

def extract_models():
    models_info = {}
    with app.app_context():
        for name in dir(models):
            obj = getattr(models, name)
            if hasattr(obj, '__tablename__'):
                table = obj.__table__
                cols = []
                for c in table.columns:
                    fks = [f"{fk.column.table.name}.{fk.column.name}" for fk in c.foreign_keys]
                    cols.append({
                        'name': c.name,
                        'type': str(c.type),
                        'nullable': c.nullable,
                        'primary_key': c.primary_key,
                        'foreign_keys': fks
                    })
                models_info[obj.__tablename__] = {
                    'class': name,
                    'columns': cols,
                    'constraints': [type(con).__name__ for con in table.constraints]
                }
    return models_info

def extract_template_buttons():
    templates_dir = Path("templates")
    button_inventory = {}

    for t_file in templates_dir.rglob("*.html"):
        rel_path = t_file.relative_to(templates_dir).as_posix()
        try:
            content = t_file.read_text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')

            buttons = []
            # Find button tags
            for b in soup.find_all('button'):
                b_type = b.get('type', 'button')
                b_text = b.get_text(strip=True)[:40]
                b_id = b.get('id', '')
                b_onclick = b.get('onclick', '')
                b_class = " ".join(b.get('class', []))
                buttons.append({
                    'tag': 'button',
                    'type': b_type,
                    'text': b_text,
                    'id': b_id,
                    'onclick': b_onclick,
                    'class': b_class[:50]
                })
            # Find a tags acting as buttons
            for a in soup.find_all('a'):
                a_class = " ".join(a.get('class', []))
                if 'btn' in a_class or 'button' in a_class:
                    buttons.append({
                        'tag': 'a',
                        'href': a.get('href', ''),
                        'text': a.get_text(strip=True)[:40],
                        'id': a.get('id', ''),
                        'onclick': a.get('onclick', '')
                    })
            # Find forms
            forms = []
            for f in soup.find_all('form'):
                forms.append({
                    'action': f.get('action', ''),
                    'method': f.get('method', 'GET').upper(),
                    'id': f.get('id', ''),
                })

            button_inventory[rel_path] = {
                'buttons': buttons,
                'forms': forms
            }
        except Exception as e:
            button_inventory[rel_path] = {'error': str(e)}

    return button_inventory

if __name__ == '__main__':
    routes = extract_routes()
    models_data = extract_models()
    ui_data = extract_template_buttons()

    out = {
        'routes_count': len(routes),
        'routes': routes,
        'models_count': len(models_data),
        'models': models_data,
        'templates_count': len(ui_data),
        'ui': ui_data
    }

    Path("logs").mkdir(exist_ok=True)
    with open("logs/audit_inventory.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Inventory completed: {len(routes)} routes, {len(models_data)} models/tables, {len(ui_data)} templates.")
