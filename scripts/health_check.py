#!/usr/bin/env python3
"""Basic integrity checks for legal-copilot skill files."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FILES = [
    "SKILL.md",
    "scripts/query_law_api.py",
    "scripts/query_case_api.py",
    "scripts/extract_docx_text.py",
    "scripts/export_to_docx.ps1",
    "scripts/import_contract_library.py",
    "scripts/fetch_samr_template.py",
    "scripts/validate_output.py",
    "scripts/release_skill.ps1",
    "references/workflow-and-intent.md",
    "references/output-standard.md",
    "references/adaptive-response-standard.md",
    "references/case-difference-explainer-standard.md",
    "references/evidence-gap-diagnostic-standard.md",
    "references/evidence-burden-matrix.md",
    "references/samr_contract_templates.json",
    "assets/templates/light_consult_response.md",
    "assets/templates/civil_complaint.md",
    "assets/templates/lawyer_letter.md",
    "assets/templates/judicial_reasoning_simulator.md",
    "assets/templates/case_difference_explainer.md",
    "assets/templates/evidence_gap_diagnostic.md",
    "assets/templates/official/samr/README.md",
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    missing: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            missing.append(rel)

    official_dir = root / "assets" / "templates" / "official"
    official_docx_count = len(list(official_dir.glob("*.docx"))) if official_dir.exists() else 0

    result = {
        "ok": not missing,
        "root": str(root),
        "missing_files": missing,
        "official_template_docx_count": official_docx_count,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
