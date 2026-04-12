# Case Analysis Standard

## API
- URL: `https://openapi.delilegal.com/api/qa/v3/search/queryListCase`
- Method: `POST`
- Stream mode: 非流式
- Auth: Header 鉴权（`appid` + `secret`），凭据来自环境变量 `LEGAL_APP_ID` / `LEGAL_SECRET`
- Headers:
  - `Content-Type: application/json`
  - `appid: ${LEGAL_APP_ID}`
  - `secret: ${LEGAL_SECRET}`

## Request body rules
- 默认参数：`pageNo=1`, `pageSize=5`, `sortField=correlation`, `sortOrder=desc`
- `sortField`: `correlation` 或 `time`
- `sortOrder`: `asc` 或 `desc`
- `condition.caseYearStart` / `condition.caseYearEnd`: 可选裁判年份区间
- `condition.courtLevelArr`:
  - `"0"`: 最高法院
  - `"1"`: 高级法院
  - `"2"`: 中级法院
  - `"3"`: 基层人民法院
- `condition.keywordArr` 与 `condition.longText` 通常二选一
- `condition.judgementTypeArr`:
  - `"30"`: 判决书
  - `"31"`: 裁定书
  - `"32"`: 调解书
  - `"33"`: 决定书
  - `"34"`: 通知书
  - `"99"`: 其他

## Analysis format
使用“总-分-总”结构：
1. 总：裁判趋势、胜诉率区间、关键影响因素
2. 分：逐条类案拆解（裁判要旨、与本案关联点）
3. 总：维权路径、证据补强、应对建议

## Win-rate rule
- 仅给区间，不给绝对值
- 示例：`45%-60%`
- 必须说明影响因素
