"""
Rewrites bootstrap/container.py cleanly from scratch,
reading each provider class body from the split provider files.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
providers_dir = os.path.join(ROOT, 'bootstrap', 'providers')
container_path = os.path.join(ROOT, 'bootstrap', 'container.py')


def extract_class(source_text, class_name):
    """Extract a single class definition from source text, as a clean string."""
    pattern = rf'^class {re.escape(class_name)}\b.*'
    m = re.search(pattern, source_text, re.MULTILINE | re.DOTALL)
    if not m:
        raise ValueError(f'Class {class_name} not found')
    class_text = m.group(0)
    # Find the end: next non-indented, non-blank line that starts a new def/class
    # OR end of string
    next_class = re.search(r'\n(?=class |\ndef )', class_text[1:])
    if next_class:
        class_text = class_text[:next_class.start() + 1]
    return class_text.strip()


repo_src = open(os.path.join(providers_dir, 'repository_provider.py'), encoding='utf-8').read()
domain_src = open(os.path.join(providers_dir, 'domain_provider.py'), encoding='utf-8').read()
app_src = open(os.path.join(providers_dir, 'application_provider.py'), encoding='utf-8').read()
infra_src = open(os.path.join(providers_dir, 'infrastructure_provider.py'), encoding='utf-8').read()

repo_class = extract_class(repo_src, 'RepositoryProvider')
domain_class = extract_class(domain_src, 'DomainProvider')
app_class = extract_class(app_src, 'ApplicationProvider')
infra_class = extract_class(infra_src, 'InfrastructureProvider')

new_content = '''"""Simple composition root / container used as a Phase 7 scaffold.

Design goals:
- non-invasive: nothing wired automatically; routes or other code must opt-in to use container
- lazy singletons for repositories and application services
- simple override API for tests
- no external dependencies

Sprint 8.9A.2: Container modularized into bootstrap/providers/ sub-modules.
This file re-exports everything for backward compatibility.
"""
from typing import Optional

# ---------------------------------------------------------------------------
# Repository imports are performed inside methods to avoid import-time cycles.
# ---------------------------------------------------------------------------

'''

new_content += repo_class + '\n\n\n'
new_content += domain_class + '\n\n\n'
new_content += app_class + '\n\n\n'
new_content += infra_class + '\n\n\n'

new_content += '''class Container:
    """Composition root. Wires all providers together."""

    def __init__(self):
        self.repositories = RepositoryProvider()
        self.domain = DomainProvider(repositories=self.repositories)
        self.infrastructure = InfrastructureProvider()
        self.applications = ApplicationProvider(domains=self.domain)

    @property
    def domains(self):
        return self.domain

    def reset_overrides(self):
        self.repositories.reset_overrides()
        self.domain.reset_overrides()
        self.applications.reset_overrides()


container = Container()


def get_container() -> Container:
    """Return the global container singleton."""
    return container


def reset_container():
    """Reset all overrides on the global container (useful for tests)."""
    container.reset_overrides()
'''

with open(container_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'container.py rewritten cleanly. Lines: {len(new_content.splitlines())}')
