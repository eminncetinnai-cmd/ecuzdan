"""Unit tests for EAFGS ArchitectureGate governance tool."""

import tempfile
from pathlib import Path

import pytest

from scripts.governance.architecture_gate import ArchitectureGate


@pytest.mark.unit
def test_gate_detects_forbidden_naming():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Create a forbidden file
        bad_file = root / "services" / "payment_v2.py"
        bad_file.parent.mkdir()
        bad_file.write_text("# code", encoding="utf-8")

        gate = ArchitectureGate(root)
        report = gate.run_check()

        assert any(
            v.category == "FORBIDDEN_NAMING" and "payment_v2.py" in v.file_path
            for v in report.violations
        )


@pytest.mark.unit
def test_gate_allows_probes_inside_work_directory():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Create a probe inside .work/
        probe_file = root / ".work" / "probes" / "fx_probe.py"
        probe_file.parent.mkdir(parents=True)
        probe_file.write_text("# probe code", encoding="utf-8")

        gate = ArchitectureGate(root)
        report = gate.run_check()

        # Should not flag probe inside .work/
        assert not any("fx_probe.py" in v.file_path for v in report.violations)


@pytest.mark.unit
def test_gate_detects_domain_flask_import():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        domain_file = root / "domain" / "sample" / "rule.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text("from flask import g\n", encoding="utf-8")

        gate = ArchitectureGate(root)
        report = gate.run_check()

        assert any(
            v.category == "DOMAIN_PURITY_VIOLATION" and "flask" in v.message
            for v in report.violations
        )


@pytest.mark.unit
def test_gate_detects_root_pollution():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        stray_file = root / "debug_dump.json"
        stray_file.write_text("{}", encoding="utf-8")

        gate = ArchitectureGate(root)
        report = gate.run_check()

        assert any(
            v.category == "ROOT_POLLUTION" and "debug_dump.json" in v.file_path
            for v in report.violations
        )
