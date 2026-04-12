"""Search and download SAMR contract templates for legal-copilot."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path


def slugify(name: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    safe = re.sub(r"\s+", "_", safe)
    return safe or "template"


def load_catalog(catalog_path: Path) -> dict:
    if not catalog_path.exists():
        raise SystemExit(
            f"Catalog not found: {catalog_path}. Run scripts/import_contract_library.py first."
        )
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def find_candidates(items: list[dict], keyword: str, limit: int = 10) -> list[dict]:
    keyword_norm = keyword.strip().lower()
    if not keyword_norm:
        return items[:limit]

    scored: list[tuple[int, dict]] = []
    for item in items:
        title = str(item.get("title", ""))
        title_norm = title.lower()
        score = 0
        if keyword_norm in title_norm:
            score += 100
        for token in keyword_norm.split():
            if token and token in title_norm:
                score += 10
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        output_path.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SAMR template by id or keyword")
    skill_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--catalog",
        default=str(skill_root / "references" / "samr_contract_templates.json"),
        help="Normalized SAMR catalog path",
    )
    parser.add_argument("--id", help="Template id")
    parser.add_argument("--keyword", help="Keyword search in title")
    parser.add_argument(
        "--type",
        choices=["word", "pdf"],
        default="word",
        help="Download file type",
    )
    parser.add_argument(
        "--out-dir",
        default=str(skill_root / "assets" / "templates" / "official" / "samr"),
        help="Output directory",
    )
    args = parser.parse_args()

    catalog = load_catalog(Path(args.catalog))
    items = catalog.get("items", [])
    if not isinstance(items, list) or not items:
        raise SystemExit("Catalog is empty.")

    selected: dict | None = None
    if args.id:
        selected = next((item for item in items if item.get("id") == args.id), None)
        if selected is None:
            raise SystemExit(f"Template id not found: {args.id}")
    elif args.keyword:
        candidates = find_candidates(items, args.keyword, limit=5)
        if not candidates:
            raise SystemExit(f"No template matched keyword: {args.keyword}")
        selected = candidates[0]
    else:
        raise SystemExit("Provide --id or --keyword")

    template_id = str(selected.get("id"))
    title = str(selected.get("title", template_id))
    file_type = args.type
    download_key = "download_word_url" if file_type == "word" else "download_pdf_url"
    download_url = str(selected.get(download_key, "")).strip()
    if not download_url:
        raise SystemExit(f"Missing {download_key} for template: {template_id}")

    extension = ".docx" if file_type == "word" else ".pdf"
    filename = f"{slugify(title)}_{template_id}{extension}"
    output_path = Path(args.out_dir) / filename

    download_file(download_url, output_path)

    result = {
        "ok": True,
        "id": template_id,
        "title": title,
        "type": file_type,
        "saved_path": str(output_path),
        "view_url": selected.get("view_url"),
        "download_url": download_url,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

