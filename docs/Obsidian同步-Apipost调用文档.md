# 青萍小台 - Apipost 接口调用文档

> 适用范围：Obsidian 同步功能 L3 验证
> 基础地址：`http://127.0.0.1:8080/api`
> 认证方式：Bearer Token（先登录获取）

---

## 0. 环境变量配置

在 `backend/.env` 中添加：

```
OBSIDIAN_VAULT_PATH=D:\00-工作日志\04-个人技术文章\obsidian\knowledge_base
```

保存后重启后端。

---

## 1. 登录获取 Token

**必须先做这一步，后续所有请求都需要 Token。**

### Apipost 配置

| 项 | 值 |
|----|----|
| 请求方式 | POST |
| URL | `http://127.0.0.1:8080/api/users/login` |
| Header | `Content-Type: application/json` |
| Body (raw JSON) | `{"username": "admin", "password": "admin123"}` |

### cURL 命令（直接复制到 Apipost → 导入 → cURL）

```bash
curl -X POST http://127.0.0.1:8080/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 预期响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...这里是很长的token...",
    "token_type": "bearer"
  }
}
```

👉 **复制 `access_token` 的值，后面要用。**

---

## 2. 配置全局 Authorization（在 Apipost 中）

登录成功后，在 Apipost 的「项目设置」或「全局参数」中配置：

| 项 | 值 |
|----|----|
| 参数名 | `Authorization` |
| 参数值 | `Bearer eyJhbGciOiJIUzI1NiIs...这里粘贴你的token...` |
| 作用域 | 全部请求 |

或者每个请求单独在 Header 中加：
```
Authorization: Bearer 你的token值
```

---

## 3. Obsidian API 列表

以下所有请求都需要 **Authorization Header**。

---

### API 1：获取同步状态

**用途**：查看 Obsidian Vault 路径是否正确配置、是否已同步过

| 项 | 值 |
|----|----|
| 请求方式 | GET |
| URL | `http://127.0.0.1:8080/api/wechat-writer/obsidian/status` |
| Header | `Authorization: Bearer 你的token` |
| Body | 无 |

#### cURL

```bash
curl -X GET http://127.0.0.1:8080/api/wechat-writer/obsidian/status \
  -H "Authorization: Bearer 你的token值"
```

#### 预期响应（未同步过）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "vault_path": "D:\\00-工作日志\\...\\knowledge_base",
    "vault_exists": true,
    "last_sync_time": 0,
    "total_notes": 0,
    "total_chunks": 0
  }
}
```

✅ **检查点**：`vault_exists` 应该是 `true`。如果是 `false`，说明路径配置有误。

---

### API 2：手动触发同步（全量/增量）

**用途**：扫描 Vault 中所有 .md 文件，解析后向量化存入 ChromaDB

| 项 | 值 |
|----|----|
| 请求方式 | POST |
| URL | `http://127.0.0.1:8080/api/wechat-writer/obsidian/sync` |
| Header | `Authorization: Bearer 你的token` |
| Body | 无 |

#### cURL

```bash
curl -X POST http://127.0.0.1:8080/api/wechat-writer/obsidian/sync \
  -H "Authorization: Bearer 你的token值"
```

#### 预期响应（第一次同步）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_files": 156,
    "added": 150,
    "updated": 0,
    "deleted": 0,
    "skipped": 6,
    "errors": 0,
    "last_sync_time": 1721654321.123
  }
}
```

✅ **检查点**：
- `total_files` 应该 ≈ 你 Vault 中的 .md 文件总数
- `added` > 0（第一次同步）
- `errors` = 0
- 如果 `skipped` > 0，可能是标签过滤或解析失败的文件

⚠️ **注意**：如果笔记很多（>100篇），第一次同步可能需要几十秒到几分钟（需要调用 Embedding API），请耐心等待。

---

### API 3：验证增量同步（第二次调用 sync）

**用途**：验证第二次 sync 只处理变更的文件

直接再次调用 API 2（同一个 sync 接口）。

#### 预期响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_files": 156,
    "added": 0,
    "updated": 0,
    "deleted": 0,
    "skipped": 0,
    "errors": 0,
    "last_sync_time": 1721654500.456
  }
}
```

✅ **检查点**：`added` 和 `updated` 都应该是 0（没有文件变更）。

---

### API 4：语义搜索

**用途**：在已索引的 Obsidian 笔记中搜索相关内容

| 项 | 值 |
|----|----|
| 请求方式 | POST |
| URL | `http://127.0.0.1:8080/api/wechat-writer/obsidian/search` |
| Header | `Content-Type: application/json` + `Authorization: Bearer 你的token` |
| Body (raw JSON) | 见下方 |

#### Body 示例

```json
{
  "query": "Python Agent 开发",
  "top_k": 5
}
```

#### cURL

```bash
curl -X POST http://127.0.0.1:8080/api/wechat-writer/obsidian/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的token值" \
  -d '{"query":"Python Agent 开发","top_k":5}'
```

#### 预期响应

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "path": "技术/Python-Agent开发指南.md",
      "title": "Python Agent 开发指南",
      "content": "Agent 是一种能够自主决策的程序...（匹配的内容片段）",
      "tags": ["Python", "Agent", "AI"],
      "score": 0.8234,
      "date": "2024-06-20",
      "word_count": 3521
    },
    ...
  ]
}
```

✅ **检查点**：
- 返回的笔记内容应该和查询关键词相关
- `score` 越高表示越相关（0~1 之间）
- 每条结果都有 `path`、`title`、`content`、`tags`、`score`

---

## 4. 验证步骤完整清单

按顺序执行：

| 步骤 | API | 验证点 | 结果 |
|------|-----|--------|------|
| 1 | 配置 `.env` + 重启后端 | - | ☐ |
| 2 | `POST /users/login` | 获取到 access_token | ☐ |
| 3 | `GET /obsidian/status` | `vault_exists: true` | ☐ |
| 4 | `POST /obsidian/sync`（第1次） | `added` > 0 | ☐ |
| 5 | `GET /obsidian/status` | `total_notes` > 0 | ☐ |
| 6 | `POST /obsidian/sync`（第2次） | `added: 0, updated: 0` | ☐ |
| 7 | 修改一篇笔记，第3次 `POST /obsidian/sync` | `updated: 1` | ☐ |
| 8 | `POST /obsidian/search` | 返回相关笔记，有 score | ☐ |
| 9 | 新增笔记 → sync → 删除笔记 → sync | 第一次 `added: 1`，第二次 `deleted: 1` | ☐ |

---

## 5. 常见问题

### Q: 提示 401 Unauthorized？
A: Token 过期或未配置。重新调用登录接口获取新 Token。

### Q: vault_exists 是 false？
A: 检查 `.env` 中的 `OBSIDIAN_VAULT_PATH` 路径是否正确，Windows 路径用双反斜杠 `\\` 或正斜杠 `/`。修改后必须重启后端。

### Q: sync 报 500 错误？
A: 查看后端控制台日志，大概率是 MiniMax API Key 未配置或 Embedding 调用失败。检查 `.env` 中的 `MINIMAX_API_KEY`。

### Q: 同步很慢？
A: 每篇笔记需要调用 MiniMax Embedding API 生成向量。笔记多时请耐心等待。可以在同步前设置 `OBSIDIAN_INCLUDE_TAGS` 只索引需要的标签（如 `OBSIDIAN_INCLUDE_TAGS=Python,AI,技术`）。
