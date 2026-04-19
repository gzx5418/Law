"""Import and normalize external contract template catalog into legal-copilot."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def looks_mojibake(text: str) -> bool:
    markers = ("涓", "鍚", "鎴", "甯", "绗", "妯", "鏍")
    return any(marker in text for marker in markers)


def repair_mojibake(text: str) -> str:
    if not text:
        return text
    try:
        repaired = text.encode("gbk", errors="ignore").decode("utf-8", errors="ignore")
        return repaired if repaired.strip() else text
    except Exception:
        return text


def normalize_title(raw_title: str) -> str:
    title = html.unescape(raw_title or "").strip()
    if looks_mojibake(title):
        fixed = repair_mojibake(title).strip()
        if fixed:
            return fixed
    return title


def build_download_url(template_id: str, file_type: int) -> str:
    return f"https://htsfwb.samr.gov.cn/api/File/DownTemplate?id={template_id}&type={file_type}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Import external contract template library")
    skill_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--input",
        required=True,
        help="Input catalog JSON path (e.g., path/to/all_templates.json)",
    )
    parser.add_argument(
        "--output",
        default=str(skill_root / "references" / "samr_contract_templates.json"),
        help="Output normalized JSON path",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    templates = payload.get("templates", [])

    normalized_items: list[dict[str, str]] = []
    for item in templates:
        template_id = str(item.get("id", "")).strip()
        if not template_id:
            continue
        title = normalize_title(str(item.get("title", "")))
        source = str(item.get("source", "")).strip() or "SAMR"
        view_url = str(item.get("url", "")).strip() or f"https://htsfwb.samr.gov.cn/View?id={template_id}"
        normalized_items.append(
            {
                "id": template_id,
                "title": title,
                "source": source,
                "view_url": view_url,
                "download_word_url": build_download_url(template_id, 1),
                "download_pdf_url": build_download_url(template_id, 2),
            }
        )

    normalized_items.sort(key=lambda x: x["title"])
    result = {
        "source": "SAMR contract templates",
        "total": len(normalized_items),
        "items": normalized_items,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()

