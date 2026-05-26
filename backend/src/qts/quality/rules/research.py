"""Research operating-system guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.quality.guardrails import GuardrailViolation

PROMOTION_CANDIDATE_STATUSES = frozenset({"candidate", "paper_candidate", "small_live_candidate"})
PROMOTION_CONFIG_DIR = Path("configs/research/promotion")
PROMOTION_RESEARCH_ONLY_PARAMS = frozenset(
    {
        "ablation_id",
        "candidate_tags",
        "factor_filters",
        "idea_id",
        "trial_budget",
        "trial_count",
    }
)
RESEARCH_REPORT_DIR = Path("runs/research")
RESEARCH_WORKFLOW_ROUTE_DIR = Path("configs/research/workflows/routes")
RESEARCH_STRATEGY_DIR = Path("strategies/research")
STALE_RESEARCH_STRATEGY_TEXT = "lives under examples"


class EvidenceBundleRequiredForPromotionRule:
    """Require promotion review specs to cite an immutable evidence bundle."""

    code = "EVIDENCE_BUNDLE_REQUIRED_FOR_PROMOTION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        violations: list[GuardrailViolation] = []
        for path, payload in yaml_payloads(repo_root / PROMOTION_CONFIG_DIR):
            if payload.get("evidence_bundle_id"):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=1,
                    message="promotion specs must cite evidence_bundle_id before review",
                    remediation=(
                        "Create a research evidence bundle and reference its immutable id "
                        "from the promotion candidate spec."
                    ),
                    symbol=str(payload.get("promotion_candidate_id", path.stem)),
                )
            )
        return violations


class IdeaRegistryRequiredForCandidateRule:
    """Require promotion candidates to remain linked to an idea registry entry."""

    code = "IDEA_REGISTRY_REQUIRED_FOR_CANDIDATE"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        violations: list[GuardrailViolation] = []
        for path, payload in yaml_payloads(repo_root / PROMOTION_CONFIG_DIR):
            if str(payload.get("status", "")) not in PROMOTION_CANDIDATE_STATUSES:
                continue
            if payload.get("idea_id"):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=1,
                    message="candidate promotion specs must cite idea_id",
                    remediation=(
                        "Register the idea with source, hypothesis, taxonomy, kill criteria, "
                        "and trial budget before marking it candidate-ready."
                    ),
                    symbol=str(payload.get("promotion_candidate_id", path.stem)),
                )
            )
        return violations


class TradeDiagnosticsRequiredForPaperRule:
    """Require paper candidates to include required review evidence."""

    code = "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        violations: list[GuardrailViolation] = []
        for path, payload in yaml_payloads(repo_root / PROMOTION_CONFIG_DIR):
            if str(payload.get("status", "")) != "paper_candidate":
                continue
            readiness = payload.get("paper_readiness")
            missing_field = _missing_paper_readiness_field(readiness)
            if missing_field is None:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=1,
                    message=f"paper candidates require {missing_field} evidence",
                    remediation=(
                        "Attach trade-level diagnostics, validation scorecard, and cost "
                        "stress evidence before marking a candidate paper-ready."
                    ),
                    symbol=str(payload.get("promotion_candidate_id", path.stem)),
                )
            )
        return violations


class PromotionCandidateSpecBoundaryRule:
    """Require promotion YAML to respect review and production parameter boundaries."""

    code = "PROMOTION_CANDIDATE_SPEC_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        violations: list[GuardrailViolation] = []
        for path, payload in yaml_payloads(repo_root / PROMOTION_CONFIG_DIR):
            source = path.read_text(encoding="utf-8")
            candidate_id = str(payload.get("promotion_candidate_id", path.stem))
            source_module = str(payload.get("source_module", ""))
            if (
                source_module.startswith("examples.")
                and payload.get("examples_migration_reviewed") is not True
            ):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(path.relative_to(repo_root)),
                        line=line_number(source, "source_module") or 1,
                        message="examples source modules require explicit migration review",
                        remediation=(
                            "Move strategy code behind a reviewed production boundary or set "
                            "examples_migration_reviewed only after human migration review."
                        ),
                        symbol=candidate_id,
                    )
                )
            production_params = payload.get("production_params", {})
            if not isinstance(production_params, dict):
                continue
            research_only_keys = sorted(
                str(key) for key in production_params if str(key) in PROMOTION_RESEARCH_ONLY_PARAMS
            )
            if not research_only_keys:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=line_number(source, "production_params") or 1,
                    message=(
                        "promotion production_params contain research-only keys: "
                        f"{', '.join(research_only_keys)}"
                    ),
                    remediation=(
                        "Keep trial budgets, candidate filters, and idea registry metadata in "
                        "research evidence; production params must contain only runtime inputs."
                    ),
                    symbol=candidate_id,
                )
            )
        return violations


class RouteMetadataRequiredRule:
    """Require route workflow configs to declare route metadata."""

    code = "ROUTE_METADATA_REQUIRED"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        violations: list[GuardrailViolation] = []
        for path, payload in yaml_payloads(repo_root / RESEARCH_WORKFLOW_ROUTE_DIR):
            if payload.get("route"):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=1,
                    message="route workflow configs must declare route metadata",
                    remediation=(
                        "Add route_id, status, owner, selection policy, and period role "
                        "boundaries before adding route workflows."
                    ),
                    symbol=str(payload.get("workflow_id", path.stem)),
                )
            )
        return violations


class ResearchReportDecisionRequiredRule:
    """Require generated research reports to contain a review-decision block."""

    code = "RESEARCH_REPORT_DECISION_REQUIRED"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        root = repo_root / RESEARCH_REPORT_DIR
        if not root.exists():
            return []
        if is_gitignored_repository_path(repo_root, RESEARCH_REPORT_DIR):
            return []

        violations: list[GuardrailViolation] = []
        for path in sorted(root.rglob("*.md")):
            source = path.read_text(encoding="utf-8")
            if "# Research Workflow Report" not in source:
                continue
            if "## Review Decision" in source:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=1,
                    message="research workflow reports must contain a review decision block",
                    remediation=(
                        "Regenerate the report with a machine-readable Review Decision "
                        "section before citing it as evidence."
                    ),
                    symbol=path.name,
                )
            )
        return violations


class ResearchStrategyStaleDocstringRule:
    """Reject stale examples wording in research strategy modules."""

    code = "RESEARCH_STRATEGY_STALE_DOCSTRING"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        root = repo_root / RESEARCH_STRATEGY_DIR
        if not root.exists():
            return []

        violations: list[GuardrailViolation] = []
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            line = line_number(source, STALE_RESEARCH_STRATEGY_TEXT)
            if line is None:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(path.relative_to(repo_root)),
                    line=line,
                    message="research strategy docstrings must not claim examples ownership",
                    remediation=(
                        "Describe the module as research-only under strategies/research "
                        "and keep promotion behind the review boundary."
                    ),
                    symbol=STALE_RESEARCH_STRATEGY_TEXT,
                )
            )
        return violations


def yaml_payloads(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Return YAML mapping payloads under a repository subdirectory."""
    if not root.exists():
        return []

    payloads: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payloads.append((path, payload))
    return payloads


def line_number(source: str, token: str) -> int | None:
    """Return the one-based line containing a token."""
    normalized_token = token.lower()
    for line_number_, line in enumerate(source.splitlines(), start=1):
        if normalized_token in line.lower():
            return line_number_
    return None


def _missing_paper_readiness_field(readiness: Any) -> str | None:
    if not isinstance(readiness, dict):
        return "paper_readiness"
    for field_name in (
        "trade_diagnostics_available",
        "validation_scorecard_available",
        "cost_stress_available",
    ):
        if readiness.get(field_name) is not True:
            return field_name
    return None


def is_gitignored_repository_path(repo_root: Path, relative_path: Path) -> bool:
    """Return whether a repository-root path is ignored by a simple .gitignore entry."""
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        return False

    path_text = relative_path.as_posix()
    for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if line.endswith("/"):
            ignored_dir = line.rstrip("/")
            if path_text == ignored_dir or path_text.startswith(f"{ignored_dir}/"):
                return True
            continue
        if path_text == line:
            return True
    return False


__all__ = [
    "EvidenceBundleRequiredForPromotionRule",
    "IdeaRegistryRequiredForCandidateRule",
    "PromotionCandidateSpecBoundaryRule",
    "ResearchReportDecisionRequiredRule",
    "ResearchStrategyStaleDocstringRule",
    "RouteMetadataRequiredRule",
    "TradeDiagnosticsRequiredForPaperRule",
]
