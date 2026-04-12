#!/usr/bin/env python3
"""Call DeliLegal queryListLaw API directly (no MCP dependency)."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


API_URL = "https://openapi.delilegal.com/api/qa/v3/search/queryListLaw"
APP_ID = os.getenv("LEGAL_APP_ID", "")
SECRET = os.getenv("LEGAL_SECRET", "")

if not APP_ID or not SECRET:
    print(json.dumps({"ok": False, "error": "Missing env vars LEGAL_APP_ID and/or LEGAL_SECRET"}, ensure_ascii=False))
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", help="JSON payload string")
    parser.add_argument("--payload-file", help="Path to JSON payload file")
    parser.add_argument("--query", help="Natural language query for law retrieval")
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=5)
    parser.add_argument("--sort-field", default="correlation")
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--field-name", default="semantic", choices=["title", "semantic"])
    args = parser.parse_args()

    selected_count = sum(bool(x) for x in [args.payload, args.payload_file, args.query])
    if selected_count != 1:
        print(
            json.dumps(
                {"ok": False, "error": "Provide exactly one of --payload, --payload-file, or --query"},
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)

    if args.query:
        payload = {
            "pageNo": args.page_no,
            "pageSize": args.page_size,
            "sortField": args.sort_field,
            "sortOrder": args.sort_order,
            "condition": {
                "keywords": [args.query],
                "fieldName": args.field_name,
            },
        }
        payload_text = json.dumps(payload, ensure_ascii=False)
    elif args.payload_file:
        with open(args.payload_file, "r", encoding="utf-8-sig") as f:
            payload_text = f.read()
    else:
        payload_text = args.payload or ""

    data = payload_text.encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "appid": APP_ID,
            "secret": SECRET,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            print(body)
    except urllib.error.HTTPError as exc:
        print(json.dumps({"ok": False, "status": exc.code, "error": exc.reason}, ensure_ascii=False))
        raise SystemExit(1)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
