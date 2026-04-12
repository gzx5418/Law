# Law Query Standard

## API
- URL: `https://openapi.delilegal.com/api/qa/v3/search/queryListLaw`
- Method: `POST`
- Stream mode: 非流式
- Auth: Header 鉴权（`appid` + `secret`），凭据来自环境变量 `LEGAL_APP_ID` / `LEGAL_SECRET`
- Headers:
  - `Content-Type: application/json`
  - `appid: ${LEGAL_APP_ID}`
  - `secret: ${LEGAL_SECRET}`

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
