#!/usr/bin/env python3
"""Extract readable plain text from a .docx template without external deps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def _paragraph_to_text(p: ET.Element) -> str:
    chunks: list[str] = []
    for node in p.iter():
        tag = node.tag
        if tag == f"{{{W_NS}}}t":
            chunks.append(node.text or "")
        elif tag == f"{{{W_NS}}}tab":
            chunks.append("\t")
        elif tag in {f"{{{W_NS}}}br", f"{{{W_NS}}}cr"}:
            chunks.append("\n")
    return "".join(chunks).strip()


def extract_docx_text(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path, "r") as zf:
        with zf.open("word/document.xml") as f:
            root = ET.parse(f).getroot()

    lines: list[str] = []
    for p in root.findall(".//w:p", NS):
        txt = _paragraph_to_text(p)
        if txt:
            lines.append(txt)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input .docx path")
    parser.add_argument("--output", help="Output .txt path (optional)")
    parser.add_argument("--max-lines", type=int, default=0, help="Trim output to first N lines")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(json.dumps({"ok": False, "error": f"File not found: {input_path}"}, ensure_ascii=False))
        raise SystemExit(1)
    if input_path.suffix.lower() != ".docx":
        print(json.dumps({"ok": False, "error": "Input must be a .docx file"}, ensure_ascii=False))
        raise SystemExit(1)

    try:
        text = extract_docx_text(input_path)
    except KeyError:
        print(json.dumps({"ok": False, "error": "Invalid .docx: missing word/document.xml"}, ensure_ascii=False))
        raise SystemExit(1)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)

    lines = text.splitlines()
    if args.max_lines and args.max_lines > 0:
        lines = lines[: args.max_lines]
    final_text = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(final_text, encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(out_path), "line_count": len(lines)}, ensure_ascii=False))
    else:
        print(final_text)


if __name__ == "__main__":
    main()

