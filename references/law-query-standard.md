# 法条检索标准（律言）

## API
- **列表接口**: `https://openapi.delilegal.com/api/qa/v3/search/queryListLaw`
  - Method: `POST`
  - 返回法规**元数据**（名称、效力等级、发布机关等），content 字段为空
- **详情接口**: `https://openapi.delilegal.com/api/qa/v3/search/lawInfo?lawId={law_id}&merge=true`
  - Method: `GET`
  - 参数: `lawId` 来自列表接口返回的 id 字段；`merge=true` 表示合并内容不作拆分
  - 返回完整法规正文：`body.lawDetailContent` 字段
- Stream mode: 非流式
- Auth: Header 鉴权（`appid` + `secret`），凭据来自环境变量 `LEGAL_APP_ID` / `LEGAL_SECRET`
- Headers:
  - `Content-Type: application/json`
  - `appid: ${LEGAL_APP_ID}`
  - `secret: ${LEGAL_SECRET}`

## 检索流程 (两步式)

```
Step 1: queryListLaw → 获取法规列表（含 id, title, levelName 等）
         ↓ 遍历每条记录的 id
Step 2: lawInfo(lawId) → 获取每条法规的完整正文内容
         ↓ 合并输出
Result: 包含元数据 + 完整正文的增强结果数组
```

### 脚本调用方式

```bash
# 模式1: 仅列表（快速）
python scripts/query_law_api.py --query "民法典租赁合同"

# 模式2: 列表+详情（推荐，获取完整法条内容）
python scripts/query_law_api.py --query "民法典租赁合同" --fetch-detail
python scripts/query_law_api.py --query "劳动法" --page-size 10 --fetch-detail --max-details 5
```

## Request body rules
- 默认参数：`pageNo=1`, `pageSize=5`, `sortField=correlation`, `sortOrder=desc`
- `condition.keywords`: 必填数组（关键词或语义问题）
- `condition.fieldName`:
  - `title`: 关键词检索
  - `semantic`: 语义检索
  - 默认：`title`

## Interpretation standard
- 法条原文必须准确，不得改写原文内容
- 按效力位阶排序展示：
  - 法律
  - 行政法规
  - 地方法规（含地方性法规、地方政府规章）
- 每条法条后必须给出场景化解读：
  - 适用前提
  - 支持点
  - 不利点
  - 举证建议
