# 青萍小台 MVP

青萍小台（Qingping Workbench）MVP 版本 —— 基于 AI 的个人工作台，包含知识库和技术专家组两大核心模块。

## 功能特性

- **知识库**：文档上传、自动分块、向量化存储、语义检索
- **技术专家组**：状态图式协作 + 人工介入机制，四大专家角色（架构师/程序员/审查员/测试工程师）协同工作
- **插件化架构**：模块化设计，易于扩展新功能
- **API 文档**：自动生成 Swagger UI，便于接口测试

## 技术栈

### 后端
- **Web 框架**: FastAPI 0.109+
- **数据库**: MySQL 8.0 / SQLite（本地开发） + SQLAlchemy 2.0
- **向量数据库**: ChromaDB（本地持久化）
- **大模型**: MiniMax API（abab6.5s-chat / embo-01）
- **认证**: JWT（python-jose + passlib[bcrypt]）
- **服务端口**: 8080

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **样式**: Tailwind CSS 3
- **状态管理**: Zustand
- **开发端口**: 5173

---

## 快速开始

### 环境要求

- Python 3.10 ~ 3.13
- Node.js 18+（前端开发）
- MySQL 8.0（生产部署，本地开发可用 SQLite）
- MiniMax API Key（[注册获取](https://www.minimaxi.com/)）

**注意**: 某些 Python 包（numpy、chromadb）在最新的 Python 3.13 上可能缺少预编译 wheel，如果你遇到安装错误，推荐降级到 Python 3.11 / 3.12 会更顺畅。

### 一、后端启动

```bash
cd backend

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少配置 MINIMAX_API_KEY
# 本地开发默认使用 SQLite，无需配置 MySQL

# 3. 启动服务
python main.py
```

服务启动后访问：
- API 文档（Swagger UI）: http://localhost:8080/docs
- API 文档（ReDoc）: http://localhost:8080/redoc
- 健康检查: http://localhost:8080/api/health

### 二、前端启动

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，配置 VITE_API_BASE_URL

# 3. 启动开发服务器
npm run dev
```

访问: http://localhost:5173

### 三、一键启动（开发模式）

```bash
chmod +x start.sh
./start.sh
```

---

## 配置说明

所有配置通过环境变量管理，后端配置文件位于 `backend/.env`。

### 1. 大模型 API 配置（必填）

```env
# MiniMax API 密钥
MINIMAX_API_KEY=your_minimax_api_key_here
# 对话模型（可选: abab6.5s-chat / abab6.5-chat）
MINIMAX_CHAT_MODEL=abab6.5s-chat
# Embedding 模型
MINIMAX_EMBEDDING_MODEL=embo-01
```

### 2. MySQL 数据库配置

本地开发默认使用 SQLite（`sqlite:///./data/qingping.db`），无需额外安装。

**生产部署切换到 MySQL**：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@主机:3306/数据库名?charset=utf8mb4
```

初始化 MySQL 数据库：

```bash
mysql -u root -p < backend/sql/init.sql
```

默认管理员账号：`admin` / `admin123`（首次登录后请立即修改）

### 3. 服务端口配置

```env
# 后端服务端口
# 注意：云服务器已占用端口 8501、8000、3306、443、22、80
PORT=8080
```

前端端口在 `frontend/vite.config.ts` 中配置（默认 5173）。

---

## 云服务器部署

### 方式一：手动部署

#### 1. 后端部署

```bash
# 上传代码到服务器
cd /opt/qingping-mvp/backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env  # 修改配置

# 初始化数据库（MySQL 方式）
mysql -u root -p < sql/init.sql

# 使用 systemd 管理服务
cp deploy/qingping-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable qingping-backend
systemctl start qingping-backend
```

#### 2. 前端部署

```bash
cd /opt/qingping-mvp/frontend

# 安装依赖并构建
npm install
npm run build

# 方式 A：使用 Nginx 托管静态文件
cp deploy/nginx.conf /etc/nginx/conf.d/qingping.conf
nginx -s reload

# 方式 B：使用 vite preview（简单但性能低，不推荐生产）
npm run preview
```

#### 3. Nginx 配置

配置文件在 `deploy/nginx.conf`，主要功能：
- 监听 8080 端口
- 反向代理 `/api` 到后端服务
- 托管前端静态文件
- 支持 SSE / WebSocket
- 文件上传大小限制 50MB

### 方式二：一键部署脚本

```bash
cd deploy
chmod +x deploy.sh
./deploy.sh
```

### 备份

```bash
cd deploy
chmod +x backup.sh
./backup.sh
```

备份内容：MySQL 数据库、上传文件、配置文件。

---

## API 文档与接口测试

启动后端服务后，访问 **Swagger UI** 进行接口测试：

```
http://你的服务器IP:8080/docs
```

支持的功能：
- 查看所有接口定义
- 在线调试每个接口
- 查看请求/响应示例
- 导出 OpenAPI 规范（可导入 Apifox/Postman）

### 主要接口分组

| 分组 | 路径前缀 | 说明 |
|------|---------|------|
| 用户管理 | `/api/users` | 注册、登录、个人信息 |
| 知识库 | `/api/knowledge-bases` | 知识库CRUD、文档上传、语义搜索 |
| 技术专家组 | `/api/tech-experts` | 会话管理、对话、状态控制 |
| 系统 | `/api/plugins` | 插件列表、菜单 |

### 快速测试流程

```bash
# 1. 注册用户
curl -X POST http://localhost:8080/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123456"}'

# 2. 登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:8080/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123456"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 3. 创建知识库
curl -X POST http://localhost:8080/api/knowledge-bases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"我的知识库","description":"测试用"}'

# 4. 创建技术专家会话
curl -X POST http://localhost:8080/api/tech-experts/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"测试会话"}'
```

---

## 项目结构

```
qingping-mvp/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── core/               # 核心框架
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── database.py     # 数据库连接
│   │   │   ├── auth.py         # JWT 认证
│   │   │   ├── plugin_manager.py  # 插件管理器
│   │   │   ├── state_machine.py   # 状态机引擎基类
│   │   │   └── exceptions.py   # 统一异常处理
│   │   ├── capabilities/       # 能力层
│   │   │   ├── llm/            # 大模型服务
│   │   │   └── rag/            # RAG 检索
│   │   ├── plugins/            # 业务插件
│   │   │   ├── user/           # 用户模块
│   │   │   ├── knowledge_base/ # 知识库模块
│   │   │   └── tech_experts/   # 技术专家组模块
│   │   └── api/
│   │       └── app.py          # FastAPI 入口
│   ├── sql/init.sql            # MySQL 初始化脚本
│   ├── data/                   # 数据目录（自动创建）
│   ├── uploads/                # 上传文件（自动创建）
│   ├── main.py                 # 启动入口
│   ├── requirements.txt        # 依赖列表
│   └── .env.example            # 配置模板
│
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── pages/              # 页面
│   │   ├── components/         # 组件
│   │   ├── store/              # 状态管理
│   │   ├── api/                # API 层
│   │   └── utils/              # 工具函数
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── deploy/                     # 部署脚本
│   ├── nginx.conf
│   ├── qingping-backend.service
│   ├── deploy.sh
│   ├── update.sh
│   └── backup.sh
│
├── start.sh                    # 一键启动（开发）
└── README.md
```

---

## 技术专家组 - 状态图式协作

### 状态定义

| 状态 | 专家 | 说明 |
|------|------|------|
| `idle` | - | 初始状态 |
| `arch_design` | 🏗️ 架构师 | 需求分析、架构设计、技术选型 |
| `code_impl` | 💻 程序员 | 代码实现 |
| `code_review` | 🔍 审查员 | 代码审查、质量把关 |
| `testing` | 🧪 测试工程师 | 测试用例、功能验证 |
| `done` | - | 完成 |

### 协作方式

- **正向流转**：用户确认后进入下一阶段
- **回退修正**：发现问题可回退到之前的状态重新来
- **手动切换**：随时切换到任意专家角色
- **迭代追踪**：记录每次状态变更，迭代轮次清晰可见

### API 接口

```
# 会话管理
GET    /api/tech-experts/sessions              # 会话列表
POST   /api/tech-experts/sessions              # 创建会话
GET    /api/tech-experts/sessions/{id}         # 会话详情
DELETE /api/tech-experts/sessions/{id}         # 删除会话

# 对话
GET    /api/tech-experts/sessions/{id}/messages  # 消息列表
POST   /api/tech-experts/sessions/{id}/chat      # 发送消息
POST   /api/tech-experts/sessions/{id}/chat/stream  # SSE 流式对话

# 状态控制
GET    /api/tech-experts/sessions/{id}/state     # 获取当前状态
POST   /api/tech-experts/sessions/{id}/state/confirm  # 确认进入下一状态
POST   /api/tech-experts/sessions/{id}/state/rollback  # 回退到指定状态
POST   /api/tech-experts/sessions/{id}/state/switch   # 手动切换专家

# 其他
GET    /api/tech-experts/experts                 # 专家列表
```

---

## 扩展新模块

基于插件系统，新增模块非常简单：

```bash
cd backend/app/plugins
mkdir my_module
```

在 `my_module/` 下创建：
- `plugin.py` - 插件注册入口
- `models.py` - 数据模型
- `schemas.py` - Pydantic Schema
- `routes.py` - API 路由
- `service.py` - 业务逻辑

启动时会自动发现并加载新插件。

---

## 常见问题

### 1. 启动报错 "No module named 'xxx'"

安装缺失的依赖：
```bash
pip install -r requirements.txt
```

### 2. MiniMax API 调用失败

检查 `.env` 中的 `MINIMAX_API_KEY` 是否正确配置，以及网络是否能访问 `api.minimax.chat`。

### 3. 数据库连接失败

- 本地开发：确认 `DATABASE_URL` 是 SQLite 格式，且 `./data/` 目录可写
- MySQL 部署：确认 MySQL 服务已启动，用户名密码正确，数据库已创建

### 4. 端口被占用

修改 `.env` 中的 `PORT` 为其他可用端口（避免 8501、8000、3306、443、22、80）。

### 5. 前端跨域问题

确保后端 `.env` 中 `CORS_ORIGINS` 包含前端地址，或设为 `*`。

---

## License

MIT
