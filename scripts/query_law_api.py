#!/usr/bin/env python3
"""
DeliLegal 法规检索 API
  - 两步式检索：列表(queryListLaw) → 详情(lawInfo)合并完整正文
  - 关键词智能映射：用户自然语言 → API优化关键词
  - 多关键词降级：首关键词无结果时自动切换备选词
  - 静默模式：--quiet 减少输出噪音
  - 文件输出：-o 避免Windows编码问题
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── API Endpoints ──────────────────────────────────────────────
LIST_URL = "https://openapi.delilegal.com/api/qa/v3/search/queryListLaw"
DETAIL_URL_TEMPLATE = "https://openapi.delilegal.com/api/qa/v3/search/lawInfo?lawId={law_id}&merge=true"

APP_ID = os.getenv("LEGAL_APP_ID", "")
SECRET = os.getenv("LEGAL_SECRET", "")


# ════════════════════════════════════════════════════════════════
#  关键词智能映射表
#  用户自然语言 → [API主关键词, 备选关键词1, 备选关键词2, ...]
#  按纠纷类型分类，覆盖常见法律咨询场景
# ════════════════════════════════════════════════════════════════
KEYWORD_MAP: dict[str, list[str]] = {
    # ── 借贷 / 借款 ──
    "借贷": ["民间借贷", "借款合同", "借条", "借贷关系"],
    "借钱": ["民间借贷", "借款", "借条"],
    "借款": ["民间借贷规定", "借款合同", "审理民间借贷案件适用法律若干问题的规定"],
    "不还钱": ["民间借贷", "债权债务", "强制执行"],
    "欠款": ["债权债务", "欠款纠纷", "合同履行"],
    "转账记录": ["民间借贷证据", "电子数据证据", "民事诉讼证据"],

    # ── 租赁 / 押金 ──
    "租赁": ["租赁合同", "房屋租赁", "住房租赁条例", "民法典 合同编"],
    "押金": ["租赁合同 押金", "定金", "民法典 租赁"],
    "退租": ["房屋租赁 解除", "合同解除", "违约责任"],
    "房东": ["房屋租赁", "租赁合同纠纷", "住房租赁条例"],
    "租金": ["租赁合同 租金", "房屋租赁", "合同履行"],

    # ── 劳动 / 工资 ──
    "劳动": ["劳动法", "劳动合同法", "劳动争议调解仲裁法"],
    "工资": ["工资支付", "劳动报酬", "拖欠工资", "最低工资"],
    "辞退": ["解除劳动合同", "经济补偿金", "违法解除"],
    "裁员": ["经济性裁员", "劳动合同解除", "经济补偿"],
    "加班费": ["加班工资", "工时制度", "劳动报酬"],
    "社保": ["社会保险", "工伤保险", "养老保险"],
    "工伤": ["工伤保险条例", "工伤认定", "工伤赔偿标准"],

    # ── 合同 ──
    "合同": ["合同法总则", "民法典 合同编", "合同效力", "违约责任"],
    "违约": ["违约责任", "合同违约", "损害赔偿", "继续履行"],
    "退款": ["消费者权益保护法", "退货", "合同解除"],
    "诈骗": ["合同诈骗", "诈骗罪", "刑事报案"],

    # ── 侵权 / 人身损害 ──
    "侵权": ["侵权责任编", "人身损害赔偿", "精神损害赔偿"],
    "车祸": ["交通事故", "机动车交通事故责任", "交强险"],
    "医疗": ["医疗损害责任", "医疗事故", "医患纠纷"],
    "离婚": ["婚姻家庭编", "离婚诉讼", "夫妻财产分割", "子女抚养"],

    # ── 公司 / 股权 ──
    "公司": ["公司法", "公司治理", "股东权利", "有限责任"],
    "股权": ["股权转让", "股东资格", "股权纠纷"],
    "破产": ["企业破产法", "破产清算", "债务重组"],

    # ── 刑事 ──
    "刑事": ["刑法", "刑事诉讼法", "立案标准", "量刑标准"],
    "盗窃": ["盗窃罪", "数额标准", "刑事处罚"],
    "醉驾": ["危险驾驶罪", "醉酒驾驶", "交通肇事"],

    # ── 程序 / 证据 ──
    "起诉": ["民事诉讼法", "起诉条件", "管辖法院", "立案"],
    "证据": ["民事诉讼证据规定", "举证责任", "电子证据", "微信证据"],
    "胜诉率": ["裁判文书", "类案检索", "司法大数据"],
}


def _map_keywords(user_query: str) -> list[str]:
    """
    将用户的自然语言查询映射为优化的API关键词列表。
    
    Strategy:
      1. 在 KEYWORD_MAP 中查找完全匹配的关键词
      2. 查找包含匹配（如"租房押金"同时命中"租房"和"押金"）
      3. 无匹配时返回原查询作为唯一关键词
    
    Returns:
        [primary_keyword, fallback_1, fallback_2, ...]
    """
    user_q = user_query.strip()
    
    # Direct match in map keys
    for key, keywords in KEYWORD_MAP.items():
        if key in user_q:
            return keywords
    
    # Partial match (e.g., "租房押金" matches both "租赁" and "押金")
    matched_keywords: list[str] = []
    for key, keywords in KEYWORD_MAP.items():
        if key in user_q or any(kw in user_q for kw in keywords):
            matched_keywords.extend(keywords)
    
    if matched_keywords:
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for kw in matched_keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        return unique[:8]  # Limit to 8 fallback keywords
    
    # No mapping found — return original query
    return [user_q]


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


def log(msg: str, quiet: bool = False) -> None:
    """Print to stderr unless quiet mode is on."""
    if not quiet:
        print(msg, file=sys.stderr)


def query_law_list(payload_text: str, timeout: int = 30) -> dict:
    """Call queryListLaw API to get law metadata list."""
    data = payload_text.encode("utf-8")
    req = urllib.request.Request(
        LIST_URL, data=data, method="POST", headers=get_headers(),
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
    """Call lawInfo API to get full law content by ID."""
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


def enrich_with_details(list_result: dict, delay: float = 0.15, max_details: int = 20, quiet: bool = False) -> dict:
    """Enrich law list results with full content from lawInfo API."""
    if list_result.get("ok") is False:
        return list_result
    
    body = list_result.get("body", {})
    laws = body.get("data", [])
    if not laws:
        return list_result
    
    total = len(laws)
    fetch_count = min(total, max_details)
    
    enriched_items: list[dict] = []
    success_count = 0
    fail_count = 0
    
    for i, law in enumerate(laws[:max_details]):
        law_id = law.get("id", "")
        
        if not law_id:
            enriched_items.append({**law, "_detail_error": "No ID found"})
            continue
        
        if i > 0:
            time.sleep(delay)
        
        detail = fetch_law_detail(law_id)
        
        if detail.get("success") and detail.get("code") == 0:
            detail_body = detail.get("body", {})
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
        
        # Progress update
        if not quiet and (i + 1) % 3 == 0 or i == fetch_count - 1:
            log(f"  详情进度: {i+1}/{fetch_count} (✅{success_count} ❌{fail_count})", quiet)
    
    return {
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


def smart_query(
    user_query: str,
    page_size: int = 5,
    field_name: str = "semantic",
    sort_field: str = "correlation",
    sort_order: str = "desc",
    fetch_detail: bool = True,
    max_details: int = 10,
    detail_delay: float = 0.15,
    quiet: bool = False,
) -> dict:
    """
    Smart keyword-aware law retrieval with automatic fallback.
    
    1. Map user query to optimized API keywords via KEYWORD_MAP
    2. Try primary keyword first
    3. If 0 results, try fallback keywords one by one
    4. Return the best result (prefer more results + higher relevance)
    
    Returns:
        Final result dict with metadata about which keywords were used
    """
    mapped_keywords = _map_keywords(user_query)
    
    log(f"{'='*60}", quiet)
    log(f"[Law Query] 用户输入: \"{user_query}\"", quiet)
    log(f"[Keyword Mapping] 映射到 {len(mapped_keywords)} 个候选关键词:", quiet)
    for i, kw in enumerate(mapped_keywords[:5]):
        log(f"  [{i+1}] {kw}", quiet)
    if len(mapped_keywords) > 5:
        log(f"  ... 共 {len(mapped_keywords)} 个候选", quiet)
    
    best_result: dict | None = None
    best_count: int = 0
    used_keyword: str = ""
    
    for idx, keyword in enumerate(mapped_keywords):
        is_primary = (idx == 0)
        label = "主关键词" if is_primary else f"备选#{idx}"
        
        log(f"\n→ 尝试 {label}: \"{keyword}\"", quiet)
        
        payload = {
            "pageNo": 1,
            "pageSize": page_size,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "condition": {
                "keywords": [keyword],
                "fieldName": field_name,
            },
        }
        payload_text = json.dumps(payload, ensure_ascii=False)
        
        result = query_law_list(payload_text)
        
        # Check if successful
        count = 0
        if result.get("success") and result.get("code") == 0:
            data = result.get("body", {}).get("data", [])
            count = len(data)
            total_count = result.get("body", {}).get("totalCount", 0)
            
            log(f"  结果: ✅ {total_count} 条匹配 (本页 {count} 条)", quiet)
            
            if count > best_count or best_result is None:
                best_result = result
                best_count = count
                used_keyword = keyword
                
                # If primary got results AND we have enough, stop here
                if is_primary and count >= min(page_size, 3):
                    log(f"  → 主关键词结果充足，停止搜索", quiet)
                    break
                
                # If any query got decent results (>= half of page_size), stop
                if count >= max(page_size // 2, 2):
                    log(f"  → 结果可接受，停止搜索", quiet)
                    break
        else:
            err = result.get("error", "unknown")
            log(f"  结果: ❌ 失败 ({err})", quiet)
    
    if best_result is None:
        log("\n⚠️ 所有关键词均失败！", quiet)
        return {"ok": False, "error": "All keywords failed", "tried": mapped_keywords}
    
    log(f"\n✅ 最终使用关键词: \"{used_keyword}\" ({best_count} 条本页结果)", quiet)
    
    # Tag result with search metadata
    best_result["_search_meta"] = {
        "user_query": user_query,
        "used_keyword": used_keyword,
        "keywords_tried": len(mapped_keywords),
    }
    
    # Enrich with details if requested
    if fetch_detail:
        total_to_enrich = len(best_result.get("body", {}).get("data", []))
        enrich_limit = min(total_to_enrich, max_details)
        log(f"\n[Detail] 获取法规正文 ({enrich_limit}/{total_to_enrich}条)...", quiet)
        best_result = enrich_with_details(
            best_result, delay=detail_delay, max_details=max_details, quiet=quiet
        )
        stats = best_result.get("body", {}).get("_detail_stats", {})
        log(f"[Done] 成功:{stats.get('success',0)} 失败:{stats.get('failed',0)}", quiet)
    
    return best_result


def _output_result(result: dict, output_path: str = None) -> None:
    """Output result to stdout or file (file avoids Windows encoding issues)."""
    text = json.dumps(result, ensure_ascii=False, indent=None)
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeliLegal 法规检索 API — 支持智能关键词映射",
        epilog=(
            "示例:\n"
            "  python query_law_api.py -q \"朋友借钱不还\" --fetch-detail -o law.json\n"
            "  python query_law_api.py -q \"房租押金\" --max-details 3 -o law.json\n"
            "  python query_law_api.py -q \"劳动纠纷 加班费\" --quiet -o law.json\n"
            "  python query_law_api.py --payload-file custom.json -o law.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-q", "--query", help="Natural language query (will be auto-mapped to optimal keywords)")
    parser.add_argument("--payload", help="Raw JSON payload string")
    parser.add_argument("--payload-file", help="Path to JSON payload file (bypasses keyword mapping)")
    parser.add_argument("--page-size", type=int, default=5, help="Results per page (default: 5)")
    parser.add_argument("--sort-field", default="correlation", choices=["correlation", "activeDate"])
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--field-name", default="semantic", choices=["title", "semantic"],
                        help="'title'=keyword search, 'semantic'=AI semantic search (default)")
    parser.add_argument("--fetch-detail", action="store_true",
                        help="Enable two-step retrieval: list → lawInfo detail merge")
    parser.add_argument("--max-details", type=int, default=10,
                        help="Max lawInfo detail calls (default: 10)")
    parser.add_argument("--detail-delay", type=float, default=0.15,
                        help="Delay between detail API calls in seconds (default: 0.15)")
    parser.add_argument("--output", "-o",
                        help="Write JSON result to FILE instead of stdout (avoids Windows encoding issues)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress messages on stderr")
    args = parser.parse_args()

    # Validate env
    if not check_env():
        raise SystemExit(1)

    # Validate input source
    selected_count = sum(bool(x) for x in [args.payload, args.payload_file, args.query])
    if selected_count != 1:
        print(json.dumps(
            {"ok": False, "error": "Provide exactly one of --query (-q), --payload, or --payload-file"},
            ensure_ascii=False,
        ))
        raise SystemExit(1)

    # ── Mode A: Smart query (with keyword mapping & fallback) ──
    if args.query:
        result = smart_query(
            user_query=args.query,
            page_size=args.page_size,
            field_name=args.field_name,
            sort_field=args.sort_field,
            sort_order=args.sort_order,
            fetch_detail=args.fetch_detail,
            max_details=args.max_details,
            detail_delay=args.detail_delay,
            quiet=args.quiet,
        )
    
    # ── Mode B: Raw payload (no keyword mapping, pass-through) ──
    elif args.payload_file:
        with open(args.payload_file, "r", encoding="utf-8-sig") as f:
            payload_text = f.read()
        
        log("[Raw Payload Mode] Using payload file directly, no keyword mapping.", args.quiet)
        
        if args.fetch_detail:
            list_result = query_law_list(payload_text)
            if list_result.get("ok") is False:
                _output_result(list_result, args.output)
                raise SystemExit(1)
            result = enrich_with_details(list_result, max_details=args.max_details, quiet=args.quiet)
        else:
            result = query_law_list(payload_text)
    
    else:  # --payload string
        payload_text = args.payload or ""
        log("[Raw Payload Mode] Using payload string directly.", args.quiet)
        
        if args.fetch_detail:
            list_result = query_law_list(payload_text)
            if list_result.get("ok") is False:
                _output_result(list_result, args.output)
                raise SystemExit(1)
            result = enrich_with_details(list_result, max_details=args.max_details, quiet=args.quiet)
        else:
            result = query_law_list(payload_text)

    # Output final result
    _output_result(result, args.output)


if __name__ == "__main__":
    main()
