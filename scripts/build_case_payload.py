#!/usr/bin/env python3
"""Build queryListCase payload from simple CLI args."""

from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", nargs="*", default=[])
    parser.add_argument("--long-text", default="")
    parser.add_argument("--sort-field", default="correlation", choices=["correlation", "time"])
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=5)
    parser.add_argument("--court-level", nargs="*", default=[])
    parser.add_argument("--judgement-type", nargs="*", default=[])
    parser.add_argument("--case-year-start", default="")
    parser.add_argument("--case-year-end", default="")
    args = parser.parse_args()

    condition: dict[str, object] = {}
    if args.long_text.strip():
        condition["longText"] = args.long_text.strip()
    elif args.keywords:
        condition["keywordArr"] = args.keywords

    if args.court_level:
        condition["courtLevelArr"] = args.court_level
    if args.judgement_type:
        condition["judgementTypeArr"] = args.judgement_type
    if args.case_year_start:
        condition["caseYearStart"] = args.case_year_start
    if args.case_year_end:
        condition["caseYearEnd"] = args.case_year_end

    payload = {
        "pageNo": args.page_no,
        "pageSize": args.page_size,
        "sortField": args.sort_field,
        "sortOrder": args.sort_order,
        "condition": condition,
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()

