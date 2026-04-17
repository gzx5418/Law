#!/usr/bin/env python3
"""
DeliLegal 案例检索 API
  - 关键词智能映射：用户自然语言 → API优化关键词
  - 静默模式：--quiet 减少输出噪音
  - 文件输出：-o 避免Windows编码问题
  - 自动编码检测：UTF-8 / GBK / GB2312
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


API_URL = "https://openapi.delilegal.com/api/qa/v3/search/queryListCase"
APP_ID = os.getenv("LEGAL_APP_ID", "")
SECRET = os.getenv("LEGAL_SECRET", "")

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# ════════════════════════════════════════════════════════════════
#  案例检索关键词映射表（与法规共享逻辑，但针对案例库优化）
#  案例 API 使用 longText 字段，语义搜索效果更好
# ════════════════════════════════════════════════════════════════
CASE_KEYWORD_MAP: dict[str, list[str]] = {
    # ── 借贷 ──
    "借贷": ["民间借贷纠纷 微信转账", "民间借贷 借款证据", "民间借贷 判决"],
    "借钱": ["朋友借钱不还", "微信转账借款", "民间借贷 转账记录"],
    "借款": ["借款合同纠纷", "民间借贷案件", "借款不还"],
    "不还钱": ["被告不还款", "欠款不还 判决", "强制执行"],
    "转账": ["微信转账 借贷关系", "支付宝转账 借款", "电子数据证据"],
    "借条": ["借条效力", "欠条 借条 区别", "债权凭证"],

    # ── 租赁 ──
    "租赁": ["房屋租赁合同纠纷", "租房 押金 返还", "租赁合同 解除"],
    "押金": ["押金返还纠纷", "押金退还 房屋租赁", "定金 押金"],
    "房东": ["房东违约", "房东不退押金", "租赁纠纷"],
    "退租": ["提前退租 违约金", "解除租赁合同", "退房 纠纷"],
    "租金": ["拖欠租金", "租金纠纷", "房租 不交"],

    # ── 劳动 ──
    "劳动": ["劳动争议纠纷", "劳动合同纠纷", "劳动仲裁"],
    "工资": ["拖欠工资", "工资支付纠纷", "未签劳动合同 双倍工资"],
    "辞退": ["违法解除劳动合同", "无故辞退赔偿", "经济补偿金"],
    "裁员": ["经济性裁员补偿", "公司裁员 赔偿", "N+1赔偿"],
    "加班费": ["加班费纠纷", "加班工资 未支付", "工时制度"],
    "社保": ["社保补缴纠纷", "未缴社会保险", "工伤保险待遇"],
    "工伤": ["工伤认定纠纷", "工伤赔偿标准", "交通事故 工伤"],
    "离职": ["被迫离职 经济补偿", "辞职 赔偿", "离职补偿金"],

    # ── 合同 ──
    "合同": ["合同纠纷", "买卖合同纠纷", "服务合同纠纷"],
    "违约": ["违约责任纠纷", "合同违约赔偿", "根本违约"],
    "退款": ["退款纠纷", "预付款退还", "消费者维权 退款"],
    "诈骗": ["合同诈骗罪", "刑事诈骗 民事", "虚假宣传 欺诈"],

    # ── 侵权 ──
    "侵权": ["侵权责任纠纷", "人身损害赔偿", "财产损害赔偿"],
    "车祸": ["交通事故责任纠纷", "机动车交通事故", "交通肇事赔偿"],
    "医疗": ["医疗损害责任纠纷", "医疗事故赔偿", "医患纠纷"],
    "离婚": ["离婚纠纷", "离婚诉讼 子女抚养", "夫妻共同财产分割"],

    # ── 公司 ──
    "公司": ["公司纠纷", "股东资格确认", "公司决议效力"],
    "股权": ["股权转让纠纷", "股权回购", "隐名股东"],
    "破产": ["破产清算纠纷", "债务清偿顺序", "企业破产"],

    # ── 刑事 ──
    "刑事": ["刑事案件", "公诉案件", "自诉案件"],
    "盗窃": ["盗窃罪判决", "数额较大 盗窃", "入室盗窃"],
    "醉驾": ["危险驾驶罪", "醉驾判刑", "酒驾处罚"],

    # ── 通用程序 ──
    "起诉": ["一审起诉状", "立案条件", "管辖权异议"],
    "证据": ["举证责任分配", "电子数据证据", "微信聊天记录 证据"],
    "执行": ["强制执行申请", "执行异议", "失信被执行人"],
}


def _map_case_keywords(user_query: str) -> str:
    """
    将用户自然语言查询映射为案例API优化关键词。
    
    Case API uses longText field with semantic search,
    so we use more natural, case-specific phrasing.
    
    Returns:
        Single optimized query string (case API works best with one rich query)
    """
    user_q = user_query.strip()
    
    # Direct match — return first matching case-specific keyword
    for key, keywords in CASE_KEYWORD_MAP.items():
        if key in user_q:
            return keywords[0]  # Return the primary (most effective) keyword
    
    # Partial match
    best_match: str | None = None
    best_overlap: int = 0
    
    for key, keywords in CASE_KEYWORD_MAP.items():
        if key in user_q:
            if len(key) > best_overlap:
                best_match = keywords[0]
                best_overlap = len(key)
        else:
            # Check if any part of the keyword is in the user query
            for kw in keywords:
                kw_short = kw.split()[0] if ' ' in kw else kw[:4]
                if kw_short in user_q and len(kw_short) > best_overlap:
                    best_match = kw
                    best_overlap = len(kw_short)
    
    if best_match:
        return best_match
    
    # No mapping found — return original
    return user_q


def log(msg: str, quiet: bool = False) -> None:
    """Print to stderr unless quiet mode."""
    if not quiet:
        print(msg, file=sys.stderr)


def check_env() -> bool:
    """Verify environment variables."""
    if not APP_ID or not SECRET:
        print(json.dumps({"ok": False, "error": "Missing env vars LEGAL_APP_ID and/or LEGAL_SECRET"}, ensure_ascii=False))
        return False
    return True


def _decode_bytes(raw: bytes) -> str:
    """Decode API response with automatic encoding detection."""
    for enc in ["utf-8", "gbk", "gb2312", "gb18030"]:
        try:
            text = raw.decode(enc)
            parsed = json.loads(text)
            return json.dumps(parsed, ensure_ascii=False, indent=None)
        except (UnicodeDecodeError, ValueError):
            continue
    return raw.decode("utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeliLegal 案例检索 API — 支持智能关键词映射",
        epilog=(
            "示例:\n"
            "  python query_case_api.py -q \"朋友借钱不还\" -o case.json\n"
            "  python query_case_api.py -q \"房东不退押金\" --quiet -o case.json\n"
            "  python query_case_api.py --payload-file custom.json -o case.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-q", "--query", help="Natural language query (will be auto-mapped)")
    parser.add_argument("--payload", help="Raw JSON payload string")
    parser.add_argument("--payload-file", help="Path to JSON payload file (bypasses keyword mapping)")
    parser.add_argument("--page-size", type=int, default=5, help="Results per page (default: 5)")
    parser.add_argument("--sort-field", default="correlation", choices=["correlation", "time"])
    parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--output", "-o", help="Write JSON result to FILE instead of stdout")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    args = parser.parse_args()

    if not check_env():
        raise SystemExit(1)

    selected_count = sum(bool(x) for x in [args.payload, args.payload_file, args.query])
    if selected_count != 1:
        print(json.dumps(
            {"ok": False, "error": "Provide exactly one of --query (-q), --payload, or --payload-file"},
            ensure_ascii=False,
        ))
        raise SystemExit(1)

    # Determine the actual query string
    if args.query:
        mapped_query = _map_case_keywords(args.query)
        
        log(f"[Case Query] 用户输入: \"{args.query}\"", args.quiet)
        log(f"[Keyword Mapping] → \"{mapped_query}\"", args.quiet)
        
        payload = {
            "pageNo": 1,
            "pageSize": args.page_size,
            "sortField": args.sort_field,
            "sortOrder": args.sort_order,
            "condition": {
                "longText": mapped_query,
            },
        }
        payload_text = json.dumps(payload, ensure_ascii=False)
    elif args.payload_file:
        with open(args.payload_file, "r", encoding="utf-8-sig") as f:
            payload_text = f.read()
        log("[Raw Payload Mode]", args.quiet)
    else:
        payload_text = args.payload or ""
        log("[Raw Payload Mode]", args.quiet)

    data = payload_text.encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, method="POST", headers={
        "Content-Type": "application/json",
        "appid": APP_ID,
        "secret": SECRET,
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            body = _decode_bytes(raw)
            
            # Add search metadata
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                if "body" not in parsed:
                    parsed = {"body": parsed}
                parsed["_search_meta"] = {
                    "user_query": getattr(args, 'query', ''),
                    "used_keyword": mapped_query if args.query else "(raw payload)",
                    "keyword_mapped": bool(args.query),
                }
                body = json.dumps(parsed, ensure_ascii=False, indent=None)
            
            if args.output:
                out_dir = os.path.dirname(os.path.abspath(args.output))
                os.makedirs(out_dir, exist_ok=True)
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(body)
                result_data = json.loads(body)
                total = result_data.get("body", {}).get("totalCount", "?")
                count = len(result_data.get("body", {}).get("data", []))
                log(f"[Done] ✅ {total} 条匹配, 本页 {count} 条 → {args.output}", args.quiet)
            else:
                print(body)

    except urllib.error.HTTPError as exc:
        err_result = {"ok": False, "status": exc.code, "error": exc.reason}
        body = json.dumps(err_result, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(body)
        else:
            print(body)
        raise SystemExit(1)
    except Exception as exc:
        err_result = {"ok": False, "error": str(exc)}
        body = json.dumps(err_result, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(body)
        else:
            print(body)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
