#!/usr/bin/env python3
"""
Law Skill 统一查询脚本 — 一站式调用法规+案例API
  同时调用 query_law_api.py 和 query_case_api.py
  合并为一个输出文件，方便 Agent 读取

用法:
  python query_both.py -q "朋友借钱不还" -o result.json
  python query_both.py -q "租房押金" --max-details 3 --quiet -o result.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAW_SCRIPT = os.path.join(SCRIPT_DIR, "query_law_api.py")
CASE_SCRIPT = os.path.join(SCRIPT_DIR, "query_case_api.py")


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Law Skill 一站式检索 (法规 + 案例)",
        epilog=(
            "示例:\n"
            '  python query_both.py -q "朋友借钱不还" -o result.json\n'
            '  python query_both.py -q "房东不退押金" --max-details 5 --quiet -o result.json\n'
            '  python query_both.py -q "劳动纠纷 加班费" --case-only -o case.json'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-q", "--query", required=True, help="Natural language query")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file path")
    parser.add_argument("--page-size-law", type=int, default=5, help="Law results per page (default: 5)")
    parser.add_argument("--page-size-case", type=int, default=5, help="Case results per page (default: 5)")
    parser.add_argument("--max-details", type=int, default=10, help="Max law detail fetches (default: 10)")
    parser.add_argument("--detail-delay", type=float, default=0.15)
    parser.add_argument("--law-only", action="store_true", help="Only search laws")
    parser.add_argument("--case-only", action="store_true", help="Only search cases")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    
    args = parser.parse_args()
    
    # Determine output file
    output_path = args.output or os.path.join(os.getcwd(), "_law_query_result.json")
    
    # Build env with API credentials
    env = os.environ.copy()
    if not env.get("LEGAL_APP_ID"):
        # Try to read from a local .env file in skill directory
        env_file = os.path.join(SCRIPT_DIR, ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
    
    results = {}
    errors = []
    
    log("=" * 60, args.quiet)
    log("  Law Skill 统一查询", args.quiet)
    log(f'  查询: "{args.query}"', args.quiet)
    log("=" * 60, args.quiet)
    
    # ── Law API ──
    if not args.case_only:
        log("", args.quiet)
        log("▶ [1/2] 检索法规...", args.quiet)
        
        law_out = output_path.replace(".json", "_law.json") if output_path else None
        law_args = [
            sys.executable, LAW_SCRIPT,
            "-q", args.query,
            "--fetch-detail",
            "--page-size", str(args.page_size_law),
            "--max-details", str(args.max_details),
            "--detail-delay", str(args.detail_delay),
            "--quiet",
        ]
        if law_out:
            law_args.extend(["-o", law_out])
        
        r_law = subprocess.run(
            law_args,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            env=env,
            timeout=120,
        )
        
        if law_out and os.path.exists(law_out):
            with open(law_out, "r", encoding="utf-8") as f:
                raw = f.read()
                try:
                    results["law"] = json.loads(raw)
                    body = results["law"].get("body", {})
                    total = body.get("totalCount", "?")
                    count = len(body.get("data", []))
                    stats = body.get("_detail_stats", {})
                    meta = body.get("_search_meta", {})
                    log(f"  ✅ 法规: {total} 条匹配 (本页 {count}, 详情 ✅{stats.get('success','?')} ❌{stats.get('failed','?')})", args.quiet)
                    if meta.get("used_keyword"):
                        log(f"     关键词: \"{meta['used_keyword']}\"", args.quiet)
                except json.JSONDecodeError:
                    results["law"] = {"raw": raw}
                    errors.append("法规结果JSON解析失败")
                    log(f"  ⚠️ 法规: 结果已获取但解析异常 ({len(raw)} bytes)", args.quiet)
        else:
            errors.append(f"法规API返回错误: {r_law.stderr[:200]}")
            log(f"  ❌ 法规: {r_law.stderr.strip()[:100]}", args.quiet)
        
        # Cleanup temp law file
        if law_out and os.path.exists(law_out) and output_path:
            pass  # Keep for reference
    
    # ── Case API ──
    if not args.law_only:
        log("", args.quiet)
        log("▶ [2/2] 检索案例...", args.quiet)
        
        case_out = output_path.replace(".json", "_case.json") if output_path else None
        case_args = [
            sys.executable, CASE_SCRIPT,
            "-q", args.query,
            "--page-size", str(args.page_size_case),
            "--quiet",
        ]
        if case_out:
            case_args.extend(["-o", case_out])
        
        r_case = subprocess.run(
            case_args,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            env=env,
            timeout=60,
        )
        
        if case_out and os.path.exists(case_out):
            with open(case_out, "r", encoding="utf-8") as f:
                raw = f.read()
                try:
                    results["case"] = json.loads(raw)
                    body = results["case"].get("body", {})
                    total = body.get("totalCount", "?")
                    count = len(body.get("data", []))
                    meta = body.get("_search_meta", {})
                    log(f"  ✅ 案例: {total} 条匹配 (本页 {count})", args.quiet)
                    if meta.get("used_keyword"):
                        log(f"     关键词: \"{meta['used_keyword']}\"", args.quiet)
                except json.JSONDecodeError:
                    results["case"] = {"raw": raw}
                    errors.append("案例结果JSON解析失败")
                    log(f"  ⚠️ 案例: 结果已获取但解析异常 ({len(raw)} bytes)", args.quiet)
        else:
            errors.append(f"案例API返回错误: {r_case.stderr[:200]}")
            log(f"  ❌ 案例: {r_case.stderr.strip()[:100]}", args.quiet)
    
    # ── Merge & Output ──
    log("", args.quiet)
    log("=" * 60, args.quiet)
    
    merged = {
        "query": args.query,
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "results": results,
        "errors": errors,
        "status": "success" if not errors else "partial_error",
    }
    
    # Write merged output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    law_count = len(results.get("law", {}).get("body", {}).get("data", [])) if "law" in results else 0
    case_count = len(results.get("case", {}).get("body", {}).get("data", [])) if "case" in results else 0
    
    log(f"[Done] 合并结果 → {output_path}", args.quiet)
    log(f"       法规: {law_count} 条 | 案例: {case_count} 条 | 错误: {len(errors)}", args.quiet)
    if errors:
        log(f"       错误详情: {'; '.join(errors)}", args.quiet)


if __name__ == "__main__":
    main()
