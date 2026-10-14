"""RCCALS Duplicate Prevention Scanner.

Analyzes codebase to discover existing classes, functions, and module stems
before new source components are created.

Results:
  - NO_DUPLICATE_FOUND
  - POSSIBLE_DUPLICATE
  - EXISTING_COMPONENT_REUSE
  - REVIEW_REQUIRED
"""

from __future__ import annotations

import ast
import os
import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class DuplicateRiskStatus(str, Enum):
    NO_DUPLICATE_FOUND = "NO_DUPLICATE_FOUND"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    EXISTING_COMPONENT_REUSE = "EXISTING_COMPONENT_REUSE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass
class DuplicateCheckResult:
    status: DuplicateRiskStatus
    component_name: str
    target_path: str
    matches: list[str] = field(default_factory=list)
    message: str = ""


class DuplicatePreventionScanner:
    """Scans repository ASTs to prevent duplicate implementations."""

    def __init__(self, repo_root: str | pathlib.Path | None = None) -> None:
        if repo_root is None:
            self.repo_root = pathlib.Path(__file__).resolve().parents[2]
        else:
            self.repo_root = pathlib.Path(repo_root).resolve()

        self._symbol_index: dict[str, list[str]] = {}
        self._stem_index: dict[str, list[str]] = {}
        self._indexed = False

    def _build_index(self) -> None:
        if self._indexed:
            return

        ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".work", "htmlcov", "node_modules"}

        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            rel_root = os.path.relpath(root, self.repo_root)

            for f in files:
                if not f.endswith(".py"):
                    continue

                rel_path = os.path.normpath(os.path.join(rel_root, f)).replace("\\", "/")
                stem = pathlib.Path(f).stem.lower()

                self._stem_index.setdefault(stem, []).append(rel_path)

                full_path = pathlib.Path(root) / f
                try:
                    tree = ast.parse(full_path.read_text(encoding="utf-8", errors="ignore"))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                            name_lower = node.name.lower()
                            self._symbol_index.setdefault(name_lower, []).append(f"{rel_path}:{node.name}")
                except Exception:
                    pass

        self._indexed = True

    def check_intent(
        self,
        target_path: str,
        *,
        component_names: Iterable[str] | None = None,
        keywords: Iterable[str] | None = None,
    ) -> DuplicateCheckResult:
        """Check if proposed file or component duplicates an existing asset."""
        self._build_index()

        rel_path = os.path.normpath(target_path).replace("\\", "/")
        stem = pathlib.Path(target_path).stem.lower()

        # 1. Exact or near-identical module stem check within same or colliding layer
        existing_stems = self._stem_index.get(stem, [])
        # Filter out self
        existing_stems = [p for p in existing_stems if p != rel_path]

        # Ignore legitimate cross-layer co-existence (e.g. routes/x.py, domain/x/, application/x/)
        target_top = rel_path.split("/")[0] if "/" in rel_path else ""
        colliding_same_layer = [
            p for p in existing_stems
            if p.split("/")[0] == target_top
        ]

        if colliding_same_layer:
            return DuplicateCheckResult(
                status=DuplicateRiskStatus.EXISTING_COMPONENT_REUSE,
                component_name=stem,
                target_path=rel_path,
                matches=colliding_same_layer,
                message=f"Module with identical name already exists in same layer: {', '.join(colliding_same_layer)}",
            )

        # 2. Check symbol names (classes / top-level functions)
        matches: list[str] = []
        if component_names:
            for name in component_names:
                name_clean = name.strip().lower()
                if name_clean in self._symbol_index:
                    matches.extend(self._symbol_index[name_clean])

        if matches:
            return DuplicateCheckResult(
                status=DuplicateRiskStatus.POSSIBLE_DUPLICATE,
                component_name=str(list(component_names or [])),
                target_path=rel_path,
                matches=matches,
                message=f"Symbols with identical names exist: {', '.join(matches[:5])}",
            )

        # 3. Fuzzy/keyword matches if keywords provided
        if keywords:
            fuzzy_matches: list[str] = []
            for kw in keywords:
                kw_lower = kw.strip().lower()
                if len(kw_lower) >= 4:
                    for indexed_stem, paths in self._stem_index.items():
                        if kw_lower in indexed_stem and paths != [rel_path]:
                            fuzzy_matches.extend(paths)

            if fuzzy_matches:
                return DuplicateCheckResult(
                    status=DuplicateRiskStatus.REVIEW_REQUIRED,
                    component_name=str(list(keywords)),
                    target_path=rel_path,
                    matches=list(set(fuzzy_matches))[:5],
                    message=f"Related components found with overlapping keywords: {', '.join(set(fuzzy_matches)[:3])}",
                )

        return DuplicateCheckResult(
            status=DuplicateRiskStatus.NO_DUPLICATE_FOUND,
            component_name=stem,
            target_path=rel_path,
            matches=[],
            message="No duplicate component found. Safe to create.",
        )
