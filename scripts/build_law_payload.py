#!/usr/bin/env python3
"""Build queryListLaw payload from simple CLI args."""

from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", nargs="+", required=True)
    parser.add_argument("--field-name", default="title", choices=["title", "semantic"])
    parser.add_argument("--sort-field", default="correlation")
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=5)
    args = parser.parse_args()

    payload = {
        "pageNo": args.page_no,
        "pageSize": args.page_size,
        "sortField": args.sort_field,
        "sortOrder": args.sort_order,
        "condition": {
            "keywords": args.keywords,
            "fieldName": args.field_name,
        },
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()

