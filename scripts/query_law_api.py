#!/usr/bin/env python3
"""
Call DeliLegal Law API — 支持两种模式：
  Mode 1: 列表查询 (queryListLaw) — 仅返回法规元数据
  Mode 2: 详情增强 (--fetch-detail) — 先查列表，再逐条调用 lawInfo 获取完整内容
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Fix Windows console encoding for Chinese characters
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# API Endpoints
LIST_URL = "https://openapi.delilegal.com/api/qa/v3/search/queryListLaw"
DETAIL_URL_TEMPLATE = "https://openapi.delilegal.com/api/qa/v3/search/lawInfo?lawId={law_id}&merge=true"

APP_ID = os.getenv("LEGAL_APP_ID", "")
SECRET = os.getenv("LEGAL_SECRET", "")


def get_headers() -> dict:
    """Build auth headers from environment variables."""
    if not APP_ID or not SECRET:
        return {}
    return {
        "Content-Type": "application/json",
        "appid": APP_ID,
        "secret": SECRET,
    }


def check_env() -> bool:
    """Verify environment variables are set."""
    if not APP_ID or not SECRET:
        print(json.dumps(
            {"ok": False, "error": "Missing env vars LEGAL_APP_ID and/or LEGAL_SECRET"},
            ensure_ascii=False,
        ))
        return False
    return True


def query_law_list(payload_text: str, timeout: int = 30) -> dict:
    """
    Step 1: Call queryListLaw API to get law metadata list.
    
    Args:
        payload_text: JSON-encoded request body string
        
    Returns:
        Parsed JSON response dict
    """
    data = payload_text.encode("utf-8")
    req = urllib.request.Request(
        LIST_URL,
        data=data,
        method="POST",
        headers=get_headers(),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
        except Exception:
            pass
        return {"ok": False, "status": exc.code, "error": exc.reason, "detail": error_body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def fetch_law_detail(law_id: str, timeout: int = 30) -> dict:
    """
    Step 2: Call lawInfo API to get full law content by ID.
    
    Args:
        law_id: The law ID from queryListLaw response
        
    Returns:
        Parsed JSON response containing lawDetailContent field
    """
    url = DETAIL_URL_TEMPLATE.format(law_id=law_id)
    req = urllib.request.Request(url, method="GET", headers=get_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": exc.reason, "lawId": law_id}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "lawId": law_id}


def enrich_with_details(list_result: dict, delay: float = 0.15, max_details: int = 20) -> dict:
    """
    Enrich law list results with full content from lawInfo API.
    
    Iterates over each law item in the queryListLaw result,
    calls lawInfo for each one, and merges the detail content back.
    
    Args:
        list_result: The parsed JSON from queryListLaw
        delay: Delay between API calls (rate limiting)
        max_details: Maximum number of details to fetch (safety limit)
        
    Returns:
        Enhanced result with 'body.data' items containing 'lawDetailContent'
    """
    if list_result.get("ok") is False:
        return list_result
    
    # Extract data array from nested structure: body -> data
    body = list_result.get("body", {})
    laws = body.get("data", [])
    
    if not laws:
        return list_result
    
    total = len(laws)
    fetch_count = min(total, max_details)
    
    enriched_items = []
    success_count = 0
    fail_count = 0
    
    for i, law in enumerate(laws[:max_details]):
        law_id = law.get("id", "")
        
        if not law_id:
            enriched_items.append({**law, "_detail_error": "No ID found"})
            continue
        
        # Rate limiting between requests
        if i > 0:
            time.sleep(delay)
        
        # Fetch detail
        detail = fetch_law_detail(law_id)
        
        # Check if successful
        if detail.get("success") and detail.get("code") == 0:
            detail_body = detail.get("body", {})
            
            # Merge original metadata + full content
            merged_item = {
                **law,
                "lawDetailContent": detail_body.get("lawDetailContent", ""),
                "items": detail_body.get("items"),
                "_detail_fetched": True,
            }
            success_count += 1
        else:
            merged_item = {
                **law,
                "lawDetailContent": "",
                "_detail_fetched": False,
                "_detail_error": detail.get("error", "Unknown error"),
            }
            fail_count += 1
        
        enriched_items.append(merged_item)
    
    # Build enhanced response
    enhanced_result = {
        **list_result,
        "body": {
            **body,
            "data": enriched_items,
            "_enriched": True,
            "_detail_stats": {
                "total_in_list": total,
                "fetched": fetch_count,
                "success": success_count,
                "failed": fail_count,
                "skipped": max(0, total - max_details),
            },
        },
    }
    
    return enhanced_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeliLegal 法规检索 API (支持列表+详情双模式)",
        epilog="示例:\n"
               "  python query_law_api.py --query \"民法典租赁合同\"\n"
               "  python query_law_api.py --query \"劳动法\" --page-size 3 --fetch-detail\n"
               "  python query_law_api.py --payload-file input.json --fetch-detail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--payload", help="JSON payload string")
    parser.add_argument("--payload-file", help="Path to JSON payload file")
    parser.add_argument("--query", help="Natural language query for law retrieval")
    parser.add_argument("--page-no", type=int, default=1, help="Page number (default: 1)")
    parser.add_argument("--page-size", type=int, default=5, help="Results per page (default: 5)")
    parser.add_argument("--sort-field", default="correlation", choices=["correlation", "activeDate"])
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--field-name", default="semantic", choices=["title", "semantic"],
                        help="'title' for keyword search, 'semantic' for semantic search (default: semantic)")
    parser.add_argument("--fetch-detail", action="store_true",
                        help="Enable: after getting list, call lawInfo API for each law to get full content")
    parser.add_argument("--detail-delay", type=float, default=0.15,
                        help="Delay in seconds between detail API calls (default: 0.15)")
    parser.add_argument("--max-details", type=int, default=20,
                        help="Maximum number of detail calls (safety limit, default: 20)")
    parser.add_argument("--output", "-o",
                        help="Write result to file instead of stdout (avoids Windows encoding issues)")
    args = parser.parse_args()

    # Validate env
    if not check_env():
        raise SystemExit(1)

    # Validate exactly one input source
    selected_count = sum(bool(x) for x in [args.payload, args.payload_file, args.query])
    if selected_count != 1:
        print(json.dumps(
            {"ok": False, "error": "Provide exactly one of --payload, --payload-file, or --query"},
            ensure_ascii=False,
        ))
        raise SystemExit(1)

    # Build payload
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

    # Step 1: Query law list
    print(f"{'='*60}", file=sys.stderr)
    print(f"[Step 1] 查询法规列表...", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    list_result = query_law_list(payload_text)
    
    # Check for immediate failure
    if list_result.get("ok") is False:
        print(json.dumps(list_result, ensure_ascii=False))
        raise SystemExit(1)

    # If no detail needed, output list result directly
    if not args.fetch_detail:
        _output_result(list_result, args.output)
        print(file=sys.stderr)
        print(f"[Done] 返回 {len(list_result.get('body', {}).get('data', []))} 条法规元数据", file=sys.stderr)
        return

    # Step 2: Fetch details for each law
    total_laws = len(list_result.get("body", {}).get("data", []))
    fetch_limit = min(total_laws, args.max_details)
    
    print(file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"[Step 2] 获取法规详情内容 ({fetch_limit}/{total_laws}条)...", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    enriched_result = enrich_with_details(
        list_result,
        delay=args.detail_delay,
        max_details=args.max_details,
    )

    stats = enriched_result.get("body", {}).get("_detail_stats", {})
    print(file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"[Done] 详情获取完成:", file=sys.stderr)
    print(f"  成功: {stats.get('success', 0)} | 失败: {stats.get('failed', 0)} | 跳过: {stats.get('skipped', 0)}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    # Output final result (compact JSON)
    _output_result(enriched_result, args.output)


def _output_result(result: dict, output_path: str = None) -> None:
    """Output result to stdout or file (file avoids Windows encoding issues)."""
    text = json.dumps(result, ensure_ascii=False, indent=None)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
