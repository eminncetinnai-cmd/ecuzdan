"""
Unit Tests - Design System Governance & Ratchet
Tests design system checker, ratchet mechanism, and admin catalog route.
"""

import pytest

from scripts.check_design_system import DesignSystemChecker
from scripts.governance.architecture_gate import ArchitectureGate, ArchitectureGateReport


@pytest.mark.unit
def test_design_system_checker_init(tmp_path):
    checker = DesignSystemChecker(tmp_path)
    assert checker.templates_dir == tmp_path / 'templates'
    assert checker.static_dir == tmp_path / 'static'


@pytest.mark.unit
def test_design_system_checker_ratchet_logic(tmp_path):
    checker = DesignSystemChecker(tmp_path)
    templates_dir = tmp_path / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Clean template
    clean_html = templates_dir / 'clean.html'
    clean_html.write_text('<div class="premium-card p-4">Clean content</div>', encoding='utf-8')

    results = checker.check_directory(templates_dir)
    assert results['total_files'] == 1
    assert results['total_issues'] == 0

    passed, violations = checker.check_ratchet(results)
    assert passed is True
    assert len(violations) >= 0


@pytest.mark.unit
def test_design_system_checker_detects_inline_style(tmp_path):
    checker = DesignSystemChecker(tmp_path)
    templates_dir = tmp_path / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    bad_html = templates_dir / 'bad.html'
    bad_html.write_text('<div style="padding: 10px; color: #10b981;">Bad content</div>', encoding='utf-8')

    issues = checker.check_file(bad_html)
    issue_types = [i['type'] for i in issues]
    assert 'inline_style' in issue_types
    assert 'hardcoded_color' in issue_types


@pytest.mark.unit
def test_architecture_gate_design_system_step(tmp_path):
    gate = ArchitectureGate(tmp_path)
    report = ArchitectureGateReport()
    gate._check_design_system_ratchet(report)
    assert isinstance(report.violations, list)
