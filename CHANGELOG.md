# 青萍小台 - 变更日志 (CHANGELOG)

所有重要变更都会记录在此文件中。

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
