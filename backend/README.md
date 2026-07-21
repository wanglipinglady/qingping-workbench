# 青萍小台 MVP 后端

青萍小台（Qingping）MVP 后端项目，基于 FastAPI + MySQL + ChromaDB + MiniMax API 构建的智能知识库平台。

## 技术栈

- **Web 框架**: FastAPI 0.109+
- **数据库**: MySQL 8.0 + SQLAlchemy 2.0 + PyMySQL
- **向量数据库**: ChromaDB（本地持久化）
- **大模型**: MiniMax API（abab6.5s-chat / embo-01）
- **认证**: JWT（python-jose + passlib[bcrypt]）
- **服务端口**: 8080

## 项目结构

```
backend/
├── app/
│   ├── core/                    # 核心模块
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── auth.py              # JWT 认证
│   │   ├── plugin_manager.py    # 插件管理器
│   │   ├── state_machine.py     # 状态机引擎
│   │   └── exceptions.py        # 统一异常处理
│   ├── capabilities/            # 能力层
│   │   ├── llm/
│   │   │   └── minimax_client.py  # MiniMax API 封装
│   │   └── rag/
│   │       ├── vector_store.py    # ChromaDB 封装
│   │       └── text_splitter.py   # 文本分块
│   ├── plugins/                 # 插件目录
│   │   ├── user/                # 用户插件
│   │   └── knowledge_base/      # 知识库插件
│   └── api/
│       └── app.py               # FastAPI 应用入口
├── data/
│   └── chroma/                  # ChromaDB 持久化目录
├── sql/
│   └── init.sql                 # MySQL 初始化脚本
├── uploads/                     # 文档上传目录
├── main.py                      # 启动入口
├── requirements.txt             # 依赖包
├── .env.example                 # 环境变量模板
└── README.md                    # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- MiniMax API Key

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下内容：

- `DATABASE_URL`: MySQL 数据库连接
- `MINIMAX_API_KEY`: MiniMax API 密钥
- `JWT_SECRET_KEY`: JWT 签名密钥（生产环境请修改）

### 4. 初始化数据库

方式一：使用 SQL 脚本手动初始化

```bash
mysql -u root -p < sql/init.sql
```

方式二：启动应用时自动建表（推荐开发环境）

应用启动时会自动调用 `create_all` 创建所有表结构。

> 注意：自动建表不会插入初始数据，初始管理员账号需要手动执行 SQL 脚本插入。

### 5. 启动服务

```bash
python main.py
```

或使用 uvicorn 直接启动：

```bash
uvicorn app.api.app:app --host 0.0.0.0 --port 8080 --reload
```

### 6. 访问 API 文档

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 默认账号

执行 `sql/init.sql` 后会创建默认管理员账号：

- 用户名: `admin`
- 密码: `admin123`

## API 接口

### 统一响应格式

所有接口返回统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "timestamp": 1700000000000
}
```

- `code`: 状态码，0 表示成功，非 0 表示失败
- `message`: 状态描述
- `data`: 响应数据
- `timestamp`: 时间戳（毫秒）

### 用户接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/users/register | 用户注册 | 否 |
| POST | /api/users/login | 用户登录 | 否 |
| GET | /api/users/me | 获取当前用户信息 | 是 |
| PUT | /api/users/me | 更新当前用户信息 | 是 |

### 知识库接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/knowledge-bases | 创建知识库 | 是 |
| GET | /api/knowledge-bases | 获取知识库列表 | 是 |
| GET | /api/knowledge-bases/{id} | 获取知识库详情 | 是 |
| PUT | /api/knowledge-bases/{id} | 更新知识库 | 是 |
| DELETE | /api/knowledge-bases/{id} | 删除知识库 | 是 |
| POST | /api/knowledge-bases/{id}/documents/upload | 上传文档 | 是 |
| GET | /api/knowledge-bases/{id}/documents | 获取文档列表 | 是 |
| DELETE | /api/knowledge-bases/{id}/documents/{doc_id} | 删除文档 | 是 |
| POST | /api/knowledge-bases/{id}/search | 语义搜索 | 是 |

### 系统接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/health | 健康检查 | 否 |
| GET | /api/plugins | 获取插件列表 | 否 |

## 插件开发

项目采用插件化架构，新增功能只需在 `app/plugins/` 下创建插件目录。

### 插件结构

```
plugins/
└── my_plugin/
    ├── __init__.py
    ├── plugin.py      # 插件注册入口（必须有 register 函数）
    ├── models.py      # 数据模型
    ├── schemas.py     # Pydantic 模式
    ├── service.py     # 业务逻辑
    └── routes.py      # API 路由
```

### plugin.py 示例

```python
from app.core.plugin_manager import PluginManager, PluginInfo
from app.plugins.my_plugin.routes import router

def register(plugin_manager: PluginManager) -> None:
    plugin_info = PluginInfo(
        name="my_plugin",
        description="我的插件",
        version="0.1.0",
        routes=[router],
    )
    plugin_manager.register_plugin(plugin_info)
```

## 支持的文档格式

- `.txt` - 纯文本
- `.md` / `.markdown` - Markdown
- `.pdf` - PDF 文档（使用 PyPDF2 提取文本）

## 开发说明

- 所有接口统一使用 `/api` 前缀
- 业务异常使用 `BusinessException` 抛出
- 数据库操作使用 SQLAlchemy 2.0 风格
- 向量数据存储在 ChromaDB，每个知识库对应一个 collection（命名：`kb_{id}`）

## License

MIT
