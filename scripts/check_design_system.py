#!/usr/bin/env python3
"""
Design System Consistency Checker & Ratchet
E-Cüzdan design system standartlarına uyumluluğu kontrol eder.
Inline styles, hard-coded renkler ve standart dışı component'leri tespit eder.
Ratchet mekanizması ile yeni dosyalarda 0 tolerans, mevcut dosyalarda gerilemeyi engeller.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DesignSystemChecker:
    """Design system consistency checker with ratchet governance"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.templates_dir = self.project_root / 'templates'
        self.static_dir = self.project_root / 'static'
        self.baseline_file = self.project_root / 'config' / 'design_system_baseline.json'

        self.issues = []
        self.total_files = 0
        self.files_with_issues = 0

    def check_inline_styles(self, file_path: Path) -> List[Dict]:
        """Inline style kontrolü"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return [{'type': 'file_error', 'message': str(e)}]

        inline_style_pattern = r'style\s*=\s*["\'][^"\']*["\']'
        matches = re.finditer(inline_style_pattern, content)

        issues = []
        for match in matches:
            style_str = match.group()
            # Allow purely dynamic CSS variable assignments (--var) or dynamic jinja/js width bindings
            if re.match(r'style=["\']\s*--(?:[a-zA-Z0-9_-]+)\s*:', style_str):
                continue
            if re.match(r'style=["\']\s*(?:width|left|right|top|bottom|background|color)\s*:\s*(?:\{\{|\$\{|calc\()[^"\']*["\']', style_str):
                continue
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'type': 'inline_style',
                'line': line_num,
                'content': match.group(),
                'message': f'Inline style found at line {line_num}: {match.group()}'
            })

        return issues

    def check_hardcoded_colors(self, file_path: Path) -> List[Dict]:
        """Hard-coded renk kontrolü (CSS variable'lar hariç)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return [{'type': 'file_error', 'message': str(e)}]

        color_pattern = r'#[0-9a-fA-F]{3,6}'
        matches = re.finditer(color_pattern, content)

        issues = []
        for match in matches:
            context_start = max(0, match.start() - 60)
            context_end = min(len(content), match.end() + 60)
            context = content[context_start:context_end]

            if 'var(' in context or '--' in context:
                continue

            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'type': 'hardcoded_color',
                'line': line_num,
                'content': match.group(),
                'message': f'Hard-coded color found at line {line_num}: {match.group()}'
            })

        return issues

    def check_non_standard_buttons(self, file_path: Path) -> List[Dict]:
        """Standart dışı button kontrolü (macro kullanımı kontrolü)"""
        try:
            rel = str(file_path.relative_to(self.project_root)).replace('\\', '/')
            if rel.startswith('templates/macros/'):
                return []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return [{'type': 'file_error', 'message': str(e)}]

        issues = []
        button_pattern = r'<button[^>]*>'
        matches = re.finditer(button_pattern, content, re.IGNORECASE)

        allowed_btn_keywords = [
            'button_primary', 'button_secondary', 'button_danger',
            'button_success', 'button_gradient', 'button_icon',
            'data-macro', 'btn-primary', 'btn-secondary', 'btn-danger',
            'btn-success', 'tx-btn', 'modal-close', 'modal-cancel', 'modal-submit',
            'role="tab"', 'data-fund-tab', 'data-chart-period',
            'data-stock-view', 'data-workspace-view', 'fund-detail-tab',
            'fund-period-btn', 'stocks-terminal-tab'
        ]

        for match in matches:
            button_content = match.group()

            if any(k in button_content for k in allowed_btn_keywords):
                continue

            if '{%' in button_content and 'button' in button_content:
                continue

            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'type': 'non_standard_button',
                'line': line_num,
                'content': button_content,
                'message': f'Non-standard button found at line {line_num}. Use button macros instead.'
            })

        return issues

    def check_missing_design_tokens(self, file_path: Path) -> List[Dict]:
        """Design token kullanımını kontrol et"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return [{'type': 'file_error', 'message': str(e)}]

        issues = []
        hardcoded_patterns = [
            (r'padding:\s*\d+px', 'hardcoded_padding'),
            (r'margin:\s*\d+px', 'hardcoded_margin'),
            (r'font-size:\s*\d+px', 'hardcoded_font_size'),
            (r'border-radius:\s*\d+px', 'hardcoded_border_radius'),
        ]

        for pattern, issue_type in hardcoded_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 15)
                context_end = min(len(content), match.end() + 15)
                context = content[context_start:context_end]

                if 'var(' in context or '--' in context:
                    continue

                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': issue_type,
                    'line': line_num,
                    'content': match.group(),
                    'message': f'Hard-coded {issue_type} found at line {line_num}: {match.group()}'
                })

        return issues

    def check_file(self, file_path: Path) -> List[Dict]:
        """Tek dosya için tüm kontrolleri yap"""
        file_issues = []
        if file_path.suffix != '.html':
            return file_issues

        file_issues.extend(self.check_inline_styles(file_path))
        file_issues.extend(self.check_hardcoded_colors(file_path))
        file_issues.extend(self.check_non_standard_buttons(file_path))
        file_issues.extend(self.check_missing_design_tokens(file_path))

        return file_issues

    def check_directory(self, directory: Path) -> Dict:
        """Tüm dizini kontrol et"""
        results = {
            'total_files': 0,
            'files_with_issues': 0,
            'total_issues': 0,
            'issues_by_type': {},
            'file_details': {},
            'file_counts': {}
        }

        html_files = sorted(list(directory.rglob('*.html')))

        for html_file in html_files:
            file_issues = self.check_file(html_file)

            results['total_files'] += 1
            rel_path = str(html_file.relative_to(self.project_root)).replace('\\', '/')
            results['file_counts'][rel_path] = len(file_issues)

            if file_issues:
                results['files_with_issues'] += 1
                results['total_issues'] += len(file_issues)

                for issue in file_issues:
                    issue_type = issue['type']
                    if issue_type not in results['issues_by_type']:
                        results['issues_by_type'][issue_type] = 0
                    results['issues_by_type'][issue_type] += 1

                results['file_details'][rel_path] = file_issues

        return results

    def load_baseline(self) -> Optional[Dict]:
        """Baseline dosyasını oku"""
        if not self.baseline_file.exists():
            return None
        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def save_baseline(self, results: Dict) -> None:
        """Yeni baseline dosyasını kaydet"""
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'total_issues': results['total_issues'],
            'total_files': results['total_files'],
            'file_counts': results['file_counts']
        }
        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Baseline saved to: {self.baseline_file} (Total issues: {results['total_issues']})")

    def check_ratchet(self, results: Dict) -> Tuple[bool, List[str]]:
        """Ratchet kurallarını değerlendir"""
        baseline = self.load_baseline()
        if not baseline:
            self.save_baseline(results)
            return True, ["Initial baseline created."]

        violations = []
        baseline_counts = baseline.get('file_counts', {})
        baseline_total = baseline.get('total_issues', 0)
        current_counts = results.get('file_counts', {})
        current_total = results.get('total_issues', 0)

        # 1. New files must have ZERO violations
        for fpath, count in current_counts.items():
            if fpath not in baseline_counts:
                if count > 0:
                    violations.append(
                        f"NEW FILE VIOLATION: '{fpath}' contains {count} design system violations. "
                        f"All new templates must have 0 violations (use macros from templates/macros/)."
                    )

        # 2. Existing files cannot increase violations
        for fpath, count in current_counts.items():
            if fpath in baseline_counts:
                prev_count = baseline_counts[fpath]
                if count > prev_count:
                    violations.append(
                        f"REGRESSION in '{fpath}': violation count increased from {prev_count} to {count} (+{count - prev_count})."
                    )

        # 3. Overall total cannot increase
        if current_total > baseline_total:
            violations.append(
                f"TOTAL REGRESSION: Total design violations increased from {baseline_total} to {current_total} (+{current_total - baseline_total})."
            )

        if not violations and current_total < baseline_total:
            # Auto-update baseline downward on improvements!
            self.save_baseline(results)

        return (len(violations) == 0), violations

    def print_results(self, results: Dict, verbose: bool = False):
        """Sonuçları yazdır"""
        print("=" * 60)
        print("DESIGN SYSTEM CONSISTENCY CHECK RESULTS")
        print("=" * 60)
        print(f"Total files checked: {results['total_files']}")
        print(f"Files with issues: {results['files_with_issues']}")
        print(f"Total issues found: {results['total_issues']}")
        print()

        if results['issues_by_type']:
            print("Issues by type:")
            for issue_type, count in sorted(results['issues_by_type'].items()):
                print(f"  - {issue_type}: {count}")
            print()

        if results['file_details'] and verbose:
            print("Detailed issues:")
            for file_path, issues in results['file_details'].items():
                print(f"\nFILE: {file_path}:")
                for issue in issues:
                    print(f"  WARNING Line {issue.get('line', '?')}: {issue['message']}")
                    if 'content' in issue:
                        print(f"       Content: {issue['content']}")

        if results['total_issues'] == 0:
            print("SUCCESS: No design system issues found!")
        else:
            print(f"NOTE: Found {results['total_issues']} baseline issues tracked under ratchet governance.")

        print("=" * 60)

    def run_checks(self, verbose: bool = False, ratchet: bool = False) -> int:
        """Tüm kontrolleri çalıştır ve exit code döndür"""
        if not self.templates_dir.exists():
            print(f"[ERROR] Templates directory not found: {self.templates_dir}")
            return 1

        print(f"[CHECK] Checking design system consistency in: {self.templates_dir}")
        print()

        results = self.check_directory(self.templates_dir)
        self.print_results(results, verbose)

        if ratchet:
            passed, violations = self.check_ratchet(results)
            if not passed:
                print("\n[ERROR] DESIGN SYSTEM RATCHET FAILED:")
                for v in violations:
                    print(f"  - {v}")
                print("\nRefer to docs/AI_AGENT_DESIGN_SYSTEM.md for component macros.")
                return 1
            print("\n[PASS] Design system ratchet passed: no regressions, new files clean.")
            return 0

        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Check E-Cüzdan design system consistency'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default=None,
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed issue information'
    )
    parser.add_argument(
        '--ratchet',
        action='store_true',
        help='Enforce ratchet (fail on new file issues or regression)'
    )
    parser.add_argument(
        '--update-baseline',
        action='store_true',
        help='Update design system baseline'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default=None,
        help='Specific directory to check (default: templates/)'
    )

    args = parser.parse_args()
    checker = DesignSystemChecker(args.project_root)

    if args.update_baseline:
        results = checker.check_directory(checker.templates_dir)
        checker.save_baseline(results)
        return 0

    return checker.run_checks(args.verbose, ratchet=args.ratchet)


if __name__ == "__main__":
    sys.exit(main())
