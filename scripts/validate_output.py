#!/usr/bin/env python3
"""Lightweight markdown output validator for legal-copilot."""

from __future__ import annotations

import argparse
from pathlib import Path


COMMON_SECTIONS = [
    "# 文书处理结果",
    "## 一、任务类型识别",
    "## 二、处理结果",
    "## 三、检索结果清单（原始条目）",
    "## 六、检索执行信息",
    "# 风险提示",
]

NEXT_STEP_SECTION_CANDIDATES = [
    "## 四、需补充信息（如有）",
    "## 五、下一步建议",
]

EXECUTION_INFO_REQUIRED_KEYS = [
    "queryListLaw",
    "queryListCase",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Markdown output file path")
    args = parser.parse_args()

    text = Path(args.file).read_text(encoding="utf-8")

    missing = [s for s in COMMON_SECTIONS if s not in text]
    if missing:
        print("INVALID")
        for item in missing:
            print(f"- missing section: {item}")
        raise SystemExit(1)

    has_next_step = any(s in text for s in NEXT_STEP_SECTION_CANDIDATES)
    if not has_next_step:
        print("INVALID")
        print("- missing section: ## 四、需补充信息（如有） or ## 五、下一步建议")
        raise SystemExit(1)

    missing_exec_keys = [k for k in EXECUTION_INFO_REQUIRED_KEYS if k not in text]
    if missing_exec_keys:
        print("INVALID")
        for key in missing_exec_keys:
            print(f"- missing retrieval execution key: {key}")
        raise SystemExit(1)

    print("VALID")


if __name__ == "__main__":
    main()
