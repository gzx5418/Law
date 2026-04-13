#!/usr/bin/env python3
"""Call DeliLegal queryListCase API directly (no MCP dependency)."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


API_URL = "https://openapi.delilegal.com/api/qa/v3/search/queryListCase"
APP_ID = os.getenv("LEGAL_APP_ID", "")
SECRET = os.getenv("LEGAL_SECRET", "")

if not APP_ID or not SECRET:
    print(json.dumps({"ok": False, "error": "Missing env vars LEGAL_APP_ID and/or LEGAL_SECRET"}, ensure_ascii=False))
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", help="JSON payload string")
    parser.add_argument("--payload-file", help="Path to JSON payload file")
    parser.add_argument("--query", help="Natural language query for case retrieval")
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=5)
    parser.add_argument("--sort-field", default="correlation", choices=["correlation", "time"])
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--output", "-o", help="Write result to file instead of stdout (avoids encoding issues)")
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
                "longText": args.query,
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
            raw = resp.read()
            # Auto-detect encoding: try UTF-8 first (standard), fallback to GBK/GB2312 (common for CN legal APIs)
            body = _decode_bytes(raw)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(body)
            else:
                print(body)
    except urllib.error.HTTPError as exc:
        result = json.dumps({"ok": False, "status": exc.code, "error": exc.reason}, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            print(result)
        raise SystemExit(1)
    except Exception as exc:
        result = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            print(result)
        raise SystemExit(1)


def _decode_bytes(raw: bytes) -> str:
    """Decode API response with automatic encoding detection."""
    # Try UTF-8 first (standard JSON encoding)
    for enc in ["utf-8", "gbk", "gb2312", "gb18030"]:
        try:
            text = raw.decode(enc)
            # Validate: decoded text must be valid JSON with no replacement chars
            parsed = json.loads(text)
            return json.dumps(parsed, ensure_ascii=False, indent=None)
        except (UnicodeDecodeError, ValueError):
            continue
    # Last resort: utf-8 with error replacement
    return raw.decode("utf-8", errors="replace")


if __name__ == "__main__":
    main()
