# 青萍小台 - 变更日志 (CHANGELOG)

所有重要变更都会记录在此文件中。

---

## [2026-07-21] M1·T3 — 状态机引擎 + 选题编辑角色

### 任务概述
完成写作助手状态机引擎、4 个专家角色配置、选题编辑角色（含 System Prompt），以及状态机操作的完整 API。

### 变更内容
- 新增 `state_machine.py`：写作助手状态机引擎（7 个状态、正向流转、回退、重新生成、专家切换、SSE 流式）
- 新增 `experts.py`：4 个专家角色配置（选题编辑/研究员/结构师/撰稿人）+ 状态映射 + Prompt 加载
- 新增 `prompts.py`：4 个专家的完整 System Prompt（每题约 4000-6000 字，含职责、输出格式、工作原则）
- 重写 `service.py`：接入状态机引擎，实现 start_topic_confirm / confirm_state / regenerate / rollback 四大操作
- 重写 `routes.py`：状态操作 API 从 1 个拆分为 4 个（/start /confirm /regenerate /rollback）
- 新增 `.env`：MySQL + MiniMax 配置（API 地址修正为 api.minimaxi.com）

### 修改文件
```
backend/app/plugins/wechat_writer/state_machine.py  (新建)
backend/app/plugins/wechat_writer/experts.py         (新建)
backend/app/plugins/wechat_writer/prompts.py         (新建)
backend/app/plugins/wechat_writer/service.py         (重写)
backend/app/plugins/wechat_writer/routes.py          (重写)
backend/.env                                           (新建)
```

### 测试结果
- ✅ **状态机基础**：7 状态正向流转、回退、暂停确认全部通过
- ✅ **专家角色**：4 个专家配置完整，状态映射正确，System Prompt 已加载
- ✅ **真实 MiniMax 调用**：选题编辑成功生成选题确认单（3500+ 字符）
- ✅ **确认前进**：topic_confirm → research，confirmed_topic 正确保存
- ✅ **回退**：research → topic_confirm，状态正确回退
- ✅ **重新生成**：带用户建议调用 MiniMax，版本号从 1 递增到 2，feedback 正确存储
- ✅ **消息记录**：每次 AI 调用都会记录 user/assistant 消息历史
- ✅ **输出版本**：每次生成都会保存输出版本，支持历史回溯

---

## [2026-07-21] M1·T2 — 插件注册 + 路由骨架

### 任务概述
完成微信公众号写作助手的插件注册、路由骨架、Schema 定义和服务层骨架。

### 变更内容
- 新增 `plugin.py`：插件注册，挂载 1 个菜单项「公众号写作」
- 新增 `schemas.py`：20+ 个 Pydantic Schema（会话/状态/资料/输出的请求响应）
- 新增 `routes.py`：10 个 API 端点（会话 CRUD + 状态操作 + 资料卡片 + 输出版本 + SSE 占位）
- 新增 `service.py`：服务层骨架（会话管理 + 状态机占位 + 资料/输出接口）

### 修改文件
```
backend/app/plugins/wechat_writer/plugin.py      (新建)
backend/app/plugins/wechat_writer/schemas.py     (新建)
backend/app/plugins/wechat_writer/routes.py      (新建)
backend/app/plugins/wechat_writer/service.py     (新建)
```

### 测试结果
- ✅ **自动化测试**：插件注册成功（4 个插件），10 个 API 端点全部正常响应
- ✅ **会话 CRUD**：创建/列表/详情/更新/删除 全部通过
- ✅ **接口响应**：资料卡片、输出版本、状态操作接口全部正常

---

## [2026-07-21] M1·T1 — 数据模型 + 数据库迁移

### 任务概述
为微信公众号写作助手创建 4 张核心数据表的 SQLAlchemy 模型，并完成数据库初始化。

### 变更内容
- 新增 `wechat_writer_sessions` 表模型（写作会话，基于状态机驱动）
- 新增 `wechat_writer_materials` 表模型（资料卡片，来源 Obsidian/KB/Web）
- 新增 `wechat_writer_messages` 表模型（消息记录，带专家角色和状态标签）
- 新增 `wechat_writer_outputs` 表模型（输出版本，支持版本对比和回滚）
- 更新 `init_full.sql` 数据库名从 `qingping` 改为 `dream`
- 在 `database.py` 的 `init_db()` 中注册 wechat_writer 模型
- 创建 `backend/.env` 配置文件（MySQL + MiniMax）

### 修改文件
```
backend/app/plugins/wechat_writer/__init__.py   (新建)
backend/app/plugins/wechat_writer/models.py       (新建)
backend/sql/init_full.sql                           (修改)
backend/app/core/database.py                        (修改)
backend/.env                                        (新建)
```

### 测试结果
- ✅ **自动化测试（SQLite）**：10 张表全部创建成功，wechat_writer 4 张表字段完整
- ✅ **SQLAlchemy 模型验证**：模型定义正确，关系映射无误
- ⚠️ **远程 MySQL**：当前环境无法连接（3306 端口防火墙限制），需在可访问环境执行 `init_full.sql`

### 人工测试
需要你在能访问远程 MySQL 的环境下执行：见下方"远程 MySQL 初始化步骤"。

### 备注
- SQLite 不支持外键约束，在 MySQL 上执行时会完整创建 11 张表（含外键）
- 远程 MySQL 连接超时：从当前 TRAE 环境无法访问 `118.190.148.121:3306`，可能是云服务器安全组限制
