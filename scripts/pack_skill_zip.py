#!/usr/bin/env python3
"""Pack legal-copilot skill into a clean portable zip (POSIX paths)."""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


EXCLUDED_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
EXCLUDED_FILE_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".log"}
EXCLUDED_NAME_PREFIXES = {"tmp_"}


def _should_include(path: Path) -> bool:
    rel_parts = set(path.parts)
    if rel_parts & EXCLUDED_DIR_NAMES:
        return False
    if path.name in EXCLUDED_FILE_NAMES:
        return False
    if any(path.name.startswith(prefix) for prefix in EXCLUDED_NAME_PREFIXES):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def build_zip(skill_dir: Path, out_zip: Path) -> None:
    if not skill_dir.exists() or not skill_dir.is_dir():
        raise SystemExit(f"skill_dir not found: {skill_dir}")
    if not (skill_dir / "SKILL.md").exists():
        raise SystemExit(f"SKILL.md not found under: {skill_dir}")

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in skill_dir.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(skill_dir)
            if not _should_include(rel):
                continue
            zf.write(p, arcname=rel.as_posix())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True, help="Path to legal-copilot root")
    parser.add_argument("--out", required=True, help="Output zip path")
    args = parser.parse_args()

    build_zip(Path(args.skill_dir), Path(args.out))
    print(args.out)


if __name__ == "__main__":
    main()
