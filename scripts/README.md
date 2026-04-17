# Scripts

## 文件说明
- `build_case_payload.py`: 生成 `queryListCase` 请求体
- `build_law_payload.py`: 生成 `queryListLaw` 请求体
- `query_case_api.py`: 直连 `queryListCase` 接口（支持 `--query` / `--payload` / `--payload-file`）
- `query_law_api.py`: 直连法规检索接口，支持**两步式详情增强模式**
  - **模式1（列表）**: 仅返回法规元数据 — `--query "民法典"`
  - **模式2（列表+详情）**: 获取完整法条正文（推荐）— `--query "民法典" --fetch-detail`
  - 额外参数: `--max-details N`（限制数量）, `--detail-delay S`（限流间隔）
- `validate_output.py`: 校验 Markdown 输出结构
- `export_to_docx.ps1`: 将 Markdown 转为 `.docx`（优先 `markdown_to_docx_converter`，回退 `pandoc`）
- `find_docx_skill.ps1`: 调试脚本（非主流程依赖）
- `pack_skill_zip.py`: 生成可导入 zip（自动过滤 `__pycache__` / `.pyc` / `.tmp` / `.log`）
- `extract_docx_text.py`: 读取官方 `.docx` 模板正文并输出纯文本
- `import_contract_library.py`: 导入并规范化外部合同模板目录（例如 `桌面/合同模板库/all_templates.json`）
- `fetch_samr_template.py`: 通过模板 `id` 或关键词从 SAMR 按需下载模板（Word/PDF）
- `health_check.py`: 一键检查 Skill 关键文件与官方模板完整性
- `release_skill.ps1`: 一键健康检查 + 打包 + 导入发布

## 快速示例
```bash
# 法规检索（推荐：带详情，获取完整法条内容）
python scripts/query_law_api.py --query "深圳市房地产相关的法律规定有哪些？" --fetch-detail
python scripts/query_law_api.py --query "劳动法" --page-size 10 --fetch-detail --max-details 5

# 案例检索（直接返回完整内容）
python scripts/query_case_api.py --query "上班途中车祸工伤案例"
python scripts/build_law_payload.py --keywords 深圳 房地产 法规 --field-name semantic
python scripts/build_case_payload.py --keywords 上班途中 车祸 工伤
python scripts/validate_output.py ./result.md
powershell -ExecutionPolicy Bypass -File scripts/export_to_docx.ps1 -InputMarkdown .\\result.md -OutputDocx .\\result.docx
python scripts/pack_skill_zip.py --skill-dir . --out ../legal-copilot-portable.zip
python scripts/extract_docx_text.py --input ../assets/templates/official/离婚纠纷起诉状_官方示范.docx --output ./tmp_official_template.txt --max-lines 300
python scripts/import_contract_library.py
python scripts/fetch_samr_template.py --keyword 商品房买卖合同 --type word
python scripts/health_check.py
powershell -ExecutionPolicy Bypass -File scripts/release_skill.ps1
```

## 约束
- `query_*_api.py` 三种入参模式必须三选一，不能同时传。
- 建议优先使用 `--query`，减少手工拼装 JSON 出错率。
