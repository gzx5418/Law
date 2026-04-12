# Legal Copilot 法律副驾驶

一个 AI Agent Skill，为日常法律咨询与诉讼分析提供专业级智能辅助。基于真实法律 API 检索，覆盖中国大陆法律体系。

> ⚠️ **免责声明：** 本技能辅助法律工作流程，**不构成正式法律意见**。所有分析结果应由持证律师审核后方可依赖。

---

## ✨ 功能亮点

### 四阶段智能工作流

```
┌──────────────────────────────────────────────────────────────┐
│  USER: "房东不退押金怎么办？"                                  │
├──────────────────────────────────────────────────────────────┤
│  Stage 1  CLASSIFY ─ 意图识别 + 关键事实补全                   │
│           → 租赁纠纷 / light / both                           │
│                                                              │
│  Stage 2  RETRIEVE ─ 法条 API + 案例 API 并行检索              │
│           → 《民法典》第714条 + 3条类案                        │
│                                                              │
│  Stage 3  COMPOSE ─ 风险分级 + 结构化输出                      │
│           → 🟢 低风险：可自行处理                              │
│           → 🟡 中风险：建议律师复核                             │
│           → 🔴 高风险：必须委托律师                             │
│                                                              │
│  Stage 4  DOCUMENT ─ 法律文书生成 + DOCX 导出                  │
│           → 起诉状.docx ✅                                    │
└──────────────────────────────────────────────────────────────┘
```

### 双模式自适应响应

| 模式 | 适用场景 | 输出内容 |
|------|---------|---------|
| **Light (轻量)** | 日常咨询、快速建议 | 一句话结论 + 行动建议 + 渐进展开入口 |
| **Deep (深度)** | 诉讼分析、胜诉率评估 | 裁判思维模拟 + 证据缺口诊断 + 类案差异分析 |

轻量回答末尾可一键展开为深度分析，**复用已有检索结果，不重复调用 API**。

---

## 📦 项目结构

```
Law/
├── SKILL.md                      # Agent 操作手册（AI 读取入口）
├── README.md                     # 本文件
├── references/                   # 规则标准与参考文档（14 份）
│   ├── workflow-and-intent.md    #   意图识别与复杂度分级
│   ├── judicial-reasoning-standard.md  #   裁判思维模拟器标准
│   ├── evidence-gap-diagnostic-standard.md  #   证据缺口诊断标准
│   ├── evidence-burden-matrix.md #   案由举证要件矩阵
│   ├── case-analysis-standard.md #   类案检索与分析标准
│   ├── document-processing-standard.md  #   合同审查与文书生成标准
│   └── ...
├── assets/
│   └── templates/                # 可复用文书模板
│       ├── civil_complaint.md    #   民事起诉状
│       ├── lawyer_letter.md      #   律师函
│       ├── contract_review_report.md  #   合同审查报告
│       ├── evidence_gap_diagnostic.md  #   证据缺口诊断
│       └── official/             #   官方示范模板（.docx）
│           ├── 离婚纠纷起诉状_官方示范.docx
│           ├── 劳动争议纠纷起诉状_官方示范.docx
│           ├── 买卖合同纠纷起诉状_官方示范.docx
│           ├── 部分案件起诉状答辩状示范文本_67类_官方汇编.docx
│           └── samr/             #   市监局合同示范文本
├── scripts/                      # API 脚本与工具
│   ├── query_law_api.py          #   法条检索
│   ├── query_case_api.py         #   案例检索
│   ├── validate_output.py        #   输出结构校验
│   ├── export_to_docx.ps1       #   Markdown → Word 导出
│   ├── health_check.py           #   环境完整性检查
│   ├── fetch_samr_template.py    #   市监局模板按需下载
│   └── ...
└── .git/
```

---

## 🚀 安装

### 前置依赖

| 依赖 | 必需 | 安装方式 |
|------|------|---------|
| Python ≥ 3.9 | ✅ | `winget install Python.Python.3.12` |
| `requests` | ✅ | `pip install -r scripts/requirements.txt` |
| `python-docx` | ✅ | 同上 |
| pandoc | 可选（DOCX 导出） | [pandoc.org](https://pandoc.org/installing.html) |

### 安装到 Claude Code / Amp

**方法 1：直接克隆到全局 skills 目录**

```bash
git clone https://github.com/XimilalaXiang/Law.git ~/.claude/skills/law
```

**方法 2：手动复制**

将整个 `Law/` 目录复制到 `~/.claude/skills/law/` 或 `~/.agents/skills/law/`。

### 配置 API 凭证

```bash
# 设置环境变量（必须）
export LEGAL_APP_ID="your_app_id"
export LEGAL_SECRET="your_secret"
```

Windows PowerShell：
```powershell
$env:LEGAL_APP_ID = "your_app_id"
$env:LEGAL_SECRET = "your_secret"
```

### 验证安装

```bash
python scripts/health_check.py
```

返回 `{"ok": true}` 即安装成功。

---

## 💬 使用示例

安装后在 Claude Code / Amp 中直接对话即可自动触发：

```
帮我看看这个合同有没有问题
```

```
房东不退押金，我能告他吗？
```

```
上班路上出了车祸算工伤吗？
```

```
帮我写一份民事起诉状
```

```
这种情况胜诉率有多大？需要准备哪些证据？
```

### 进阶用法

```
# 法条检索
python scripts/query_law_api.py --query "深圳市房地产相关的法律规定有哪些？"

# 案例检索
python scripts/query_case_api.py --query "上班途中车祸工伤案例"

# 输出校验
python scripts/validate_output.py ./result.md

# Word 导出
powershell -ExecutionPolicy Bypass -File scripts/export_to_docx.ps1 -InputMarkdown .\result.md -OutputDocx .\result.docx

# 市监局合同模板下载
python scripts/fetch_samr_template.py --keyword 商品房买卖合同 --type word
```

---

## 🔧 核心能力

### 法律检索引擎

| 接口 | 脚本 | 数据来源 |
|------|------|---------|
| 法条检索 `queryListLaw` | `query_law_api.py` | 法律法规数据库 |
| 案例检索 `queryListCase` | `query_case_api.py` | 裁判文书数据库 |

**检索硬约束：** 绝不在未成功检索时给出实质性法律结论。API 失败时自动重试 → 精简关键词重试 → 单接口降级 → 征得用户同意后 web search 补充。

### 深度分析模块

| 模块 | 触发条件 | 说明 |
|------|---------|------|
| **裁判思维模拟器** | 用户提及诉讼/胜诉率 | 模拟法官视角分析争议焦点与裁判倾向 |
| **证据缺口诊断器** | 用户问"证据够不够" | 诊断缺失证据、评估风险、给出补强建议 |
| **类案差异解释器** | 检索返回类案结果时 | 对比本案与类案的关键差异及影响 |
| **合同审查** | 用户要求审查合同 | 条款风险扫描 + 修改建议 |

### 文书生成

内置 **9 种文书模板** + **67 类官方示范文本**：

| 模板 | 文件 |
|------|------|
| 日常咨询回复 | `light_consult_response.md` |
| 民事起诉状 | `civil_complaint.md` |
| 律师函 | `lawyer_letter.md` |
| 合同审查报告 | `contract_review_report.md` |
| 案例分析报告 | `case_analysis_report.md` |
| 法条查询报告 | `law_query_report.md` |
| 裁判思维模拟报告 | `judicial_reasoning_simulator.md` |
| 类案差异分析 | `case_difference_explainer.md` |
| 证据缺口诊断 | `evidence_gap_diagnostic.md` |

所有文书支持导出为 `.docx` 格式。

### 风险分级系统

每个分析结论和行动建议均标注风险等级：

| 等级 | 含义 | 建议行动 |
|------|------|---------|
| 🟢 **低风险** | 法律关系清晰，胜率高 | 可自行处理 |
| 🟡 **中风险** | 存在争议空间或证据不足 | 建议律师复核 |
| 🔴 **高风险** | 可能败诉或涉及重大权益 | 必须委托律师 |

---

## 🌍 适用范围

- ✅ **中国大陆法律体系**（民法、劳动法、合同法、侵权法等）
- ❌ 不覆盖港澳台法律
- ❌ 不覆盖涉外/跨境法律（涉及大陆法部分除外）
- ❌ 不覆盖非中国法律（US、EU、日本等）

---

## 🤝 贡献

1. Fork 本仓库
2. 在 `references/` 中添加或完善规则标准
3. 在 `assets/templates/` 中补充文书模板
4. 运行 `python scripts/health_check.py` 确认文件完整性
5. 提交 PR

---

## 📄 License

[MIT License](LICENSE)
