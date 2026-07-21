# 青萍小台 MVP 版本详细设计说明书
## 01 文档概述
### 1.1 编写目的
本文档为**青萍小台**（个人AI工作台）MVP版本的详细技术设计说明书，旨在为开发团队提供可直接落地实施的技术方案。文档涵盖从基础框架搭建到各业务模块的完整设计，包括数据模型、API接口、前端页面、工作流设计等核心内容，确保开发人员能够依据本文档完成MVP版本的全部开发工作。
### 1.2 文档范围
本文档覆盖青萍小台MVP版本的**全部技术设计内容**，包括：
- 基础框架设计（插件体系、配置管理、数据库、认证系统等）
- 知识库模块详细设计（文档上传、处理、检索全流程）
- 技术专家组模块详细设计（多角色AI对话、工作流、SSE流式输出）
- 实现步骤与里程碑规划
- 测试方案与部署方案
- MiniMax大模型集成指南
本文档不包含UI/UX视觉设计稿、产品需求文档（PRD）、运营推广方案等内容。
### 1.3 目标读者
- **后端开发工程师**：依据API设计、数据模型、服务层逻辑进行后端功能开发
- **前端开发工程师**：依据页面设计、状态管理、接口规范进行前端功能开发
- **测试工程师**：依据测试方案和用例清单进行功能与性能测试
- **运维/DevOps工程师**：依据部署方案进行服务器配置与上线部署
### 1.4 术语表
| 术语/缩写 | 英文全称 | 中文释义 |
| --- | --- | --- |
| MVP | Minimum Viable Product | 最小可行产品，具备核心功能的最早交付版本 |
| RAG | Retrieval-Augmented Generation | 检索增强生成，结合知识库检索与大模型生成的技术 |
| SSE | Server-Sent Events | 服务器推送事件，一种服务端向客户端单向推送数据的HTTP协议 |
| JWT | JSON Web Token | 基于JSON的开放标准令牌，用于身份验证 |
| ORM | Object-Relational Mapping | 对象关系映射，将对象模型与关系数据库进行映射的技术 |
| ChromaDB | Chroma Database | 开源向量数据库，用于存储和检索嵌入向量 |
| Embedding | Text Embedding | 文本嵌入，将文本转换为高维向量表示的技术 |
| MiniMax | MiniMax AI | 国内大模型服务商，提供abab系列对话模型 |
| CRUD | Create, Read, Update, Delete | 增删改查，数据操作的基本四种操作 |
| CORS | Cross-Origin Resource Sharing | 跨域资源共享，允许不同源的Web页面访问资源 |
| Systemd | System Daemon | Linux系统服务管理器，用于管理后台服务 |
### 1.5 版本记录
| 版本号 | 日期 | 修订人 | 修订内容 |
| --- | --- | --- | --- |
| v1.0 | 2026-07-13 | 产品技术团队 | 初始版本，完成MVP完整设计文档 |
## 02 MVP版本定义
### 2.1 MVP目标
青萍小台MVP版本以**「个人AI工作台」**为核心定位，聚焦开发者的日常工作场景，通过知识库与技术专家组两大核心模块，提供一个轻量、高效、可扩展的AI辅助开发平台。
> **🎯 MVP核心目标**
>
> 验证「知识库 + 多专家AI协作」的产品价值，用最小的功能集合完成从0到1的产品闭环，为后续迭代积累用户反馈和技术基础。
具体目标包括：
- **技术验证**：验证插件化架构、RAG检索、多Agent工作流等核心技术方案的可行性
- **功能闭环**：完成知识库上传-处理-检索、技术专家对话-流式输出的完整业务流程
- **性能基线**：建立核心功能的性能基准，确保用户体验在可接受范围内
- **可扩展性**：构建插件化的基础框架，为后续功能模块的快速接入预留扩展点
### 2.2 MVP范围
#### 包含功能（In Scope）
#### 基础框架
- FastAPI 后端项目脚手架
- React + Vite + TypeScript 前端脚手架
- 插件化架构（自动发现与注册）
- JWT 用户认证系统
- MySQL 数据库与 SQLAlchemy ORM
- 统一响应格式与异常处理
- MiniMax API 集成封装
#### 业务模块
- 用户注册/登录
- 知识库 CRUD 管理
- 文档上传与解析（PDF/MD/TXT/Word）
- 文本分块与向量化存储
- 知识库语义检索
- 技术专家组对话（4角色流水线）
- SSE 流式输出
- 对话历史管理
#### 不包含功能（Out of Scope）
> **⚠️ MVP暂不包含**
>
> 多用户协作与权限管理 工作流可视化编排 插件市场与第三方插件接入 移动端适配（仅保证桌面端体验） 完整的运营后台与数据分析 消息推送与通知系统 付费订阅与计费系统
### 2.3 成功标准
| 维度 | 衡量指标 | MVP目标值 |
| --- | --- | --- |
| 功能完整性 | 知识库文档上传成功率 | ≥ 95% |
| 知识库检索召回准确率 | ≥ 80%（基于测试用例集） |
| 技术专家对话完整率 | ≥ 98% |
| 性能指标 | 首屏加载时间 | ≤ 2s |
| 接口平均响应时间 | ≤ 500ms（不含大模型调用） |
| SSE首字响应时间 | ≤ 5s |
| 稳定性 | 系统可用性 | ≥ 99% |
| 并发用户数 | 支持 50 并发用户 |
| 技术债务 | 代码覆盖率 | 核心模块 ≥ 60% |
| 文档完整性 | API 文档覆盖率 100% |
## 03 基础框架详细设计
### 3.1 项目初始化
#### 3.1.1 技术选型
| 层级 | 技术栈 | 版本 | 选型理由 |
| --- | --- | --- | --- |
| 后端 | Python + FastAPI | 3.10+ / 0.100+ | 高性能异步框架，自动生成API文档，开发效率高 |
| SQLAlchemy | 2.x | 成熟的Python ORM，支持多种数据库 |
| Pydantic | v2 | 数据验证与序列化，与FastAPI深度集成 |
| 前端 | React + TypeScript | 18+ / 5.x | 生态成熟，类型安全，社区资源丰富 |
| Vite | 5.x | 极速开发服务器，构建速度快 |
| Tailwind CSS | 3.x | 原子化CSS，开发效率高，易于定制 |
| 数据存储 | MySQL | 8.0 | 主流关系型数据库，稳定可靠 |
| ChromaDB | 0.4+ | 轻量级向量数据库，Python原生支持 |
| 大模型 | MiniMax API | abab6.5s-chat | 中文能力强，性价比高，支持流式输出 |
#### 3.1.2 后端项目结构
backend/ 目录结构
```
backend/
├── main.py                  # 应用入口
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量
├── .env.example             # 环境变量示例
├── data/                    # 数据目录（运行时生成）
│   ├── uploads/             # 上传文件存储
│   └── chroma/              # ChromaDB 持久化数据
└── app/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   └── app.py           # FastAPI 应用实例创建
    ├── core/                # 核心基础设施
    │   ├── __init__.py
    │   ├── config.py        # 配置管理
    │   ├── database.py      # 数据库连接与会话
    │   ├── auth.py          # JWT认证与密码哈希
    │   ├── exceptions.py    # 统一异常处理
    │   └── plugin_manager.py # 插件管理器
    ├── capabilities/        # 通用能力层
    │   ├── __init__.py
    │   ├── llm/             # 大模型服务封装
    │   │   ├── __init__.py
    │   │   └── service.py
    │   ├── rag/             # RAG检索服务
    │   │   ├── __init__.py
    │   │   └── service.py
    │   └── agent/           # Agent工作流基类
    │       ├── __init__.py
    │       └── workflow.py
    └── plugins/             # 业务插件目录
        ├── __init__.py
        ├── user/            # 用户插件
        │   ├── __init__.py
        │   ├── plugin.py    # 插件注册入口
        │   ├── models.py    # 数据模型
        │   ├── api.py       # API路由
        │   └── service.py   # 业务逻辑
        ├── knowledge_base/  # 知识库插件
        │   ├── __init__.py
        │   ├── plugin.py
        │   ├── models.py
        │   ├── api.py
        │   ├── service.py
        │   └── document_processor.py
        └── tech_experts/    # 技术专家组插件
            ├── __init__.py
            ├── plugin.py
            ├── models.py
            ├── api.py
            ├── service.py
            ├── agents/      # 专家Agent
            │   ├── __init__.py
            │   ├── expert_agent.py
            │   └── prompts.py
            └── workflows/   # 工作流定义
                ├── __init__.py
                └── expert_workflow.py
```
#### 3.1.3 前端项目结构
frontend/ 目录结构
```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.tsx             # 应用入口
    ├── App.tsx              # 根组件
    ├── index.css            # 全局样式
    ├── api/
    │   └── index.ts         # API请求封装
    ├── store/               # 状态管理（Zustand）
    │   ├── auth.ts          # 认证状态
    │   └── app.ts           # 应用全局状态
    ├── components/          # 通用组件
    │   └── Layout.tsx       # 布局组件
    └── pages/               # 页面组件
        ├── Home.tsx         # 首页
        ├── Login.tsx        # 登录页
        ├── KnowledgeBase.tsx # 知识库页
        └── TechExperts.tsx   # 技术专家组页
```
### 3.2 插件管理器详细设计
青萍小台采用**插件化架构**，每个业务模块作为独立插件存在。插件管理器负责插件的自动发现、加载、路由注册和数据表创建。
#### 3.2.1 PluginInfo 类定义
app/core/plugin_manager.py - PluginInfo 类
```
class PluginInfo:
    """插件信息类，描述一个插件的元数据与资源"""
    def __init__(
        self,
        id: str,                    # 插件唯一标识（英文，如 "knowledge_base"）
        name: str,                  # 插件名称（中文展示名）
        description: str = "",      # 插件描述
        version: str = "0.1.0",     # 插件版本
        router: Any = None,         # FastAPI APIRouter 实例
        models: List[Any] = None,   # SQLAlchemy 模型类列表
        menu_items: List[dict] = None, # 前端菜单项配置
        prefix: str = "",           # 路由前缀（默认 /{id}）
        tags: List[str] = None,     # OpenAPI 标签
    ):
        self.id = id
        self.name = name
        self.description = description
        self.version = version
        self.router = router
        self.models = models or []
        self.menu_items = menu_items or []
        self.prefix = prefix or f"/{id}"
        self.tags = tags or [name]
```
#### 3.2.2 PluginManager 类设计
PluginManager 采用**单例模式**，提供以下核心能力：
- `discover_plugins()` — 自动发现 plugins 目录下的所有插件包
- `register_routes(app)` — 将所有插件的路由注册到 FastAPI 应用
- `create_tables()` — 创建所有插件定义的数据表
- `get_all_menus()` — 获取所有插件的菜单项（供前端动态菜单使用）
#### 3.2.3 自动发现机制
插件管理器通过 Python 的 `pkgutil` 模块遍历 `app.plugins` 包下的所有子包，每个子包即为一个插件。插件必须提供 `plugin.py` 文件，并导出 `register()` 函数。
插件注册示例 - knowledge_base/plugin.py
```
"""知识库插件注册入口"""
from app.core.plugin_manager import PluginInfo
def register() -> PluginInfo:
    """注册插件，返回插件信息"""
    from app.plugins.knowledge_base.api import router
    from app.plugins.knowledge_base.models import KnowledgeBase, Document
    return PluginInfo(
        id="knowledge_base",
        name="知识库",
        description="文档上传、解析、向量化与语义检索",
        version="0.1.0",
        router=router,
        models=[KnowledgeBase, Document],
        menu_items=[{
            "id": "knowledge_base",
            "name": "知识库",
            "path": "/knowledge-base",
            "icon": "📚",
            "order": 1,
        }],
    )
```
#### 3.2.4 路由注册流程
插件路由统一注册在 `/api/v1/{plugin_prefix}` 路径下，由 PluginManager 在应用启动时调用 `register_routes()` 完成。
app/api/app.py - 应用初始化
```
from fastapi import FastAPI
from app.core.plugin_manager import plugin_manager
from app.core.config import settings
from app.core.exceptions import app_exception_handler, AppException
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )
    # 注册异常处理器
    app.add_exception_handler(AppException, app_exception_handler)
    # 发现并加载插件
    plugin_manager.discover_plugins()
    # 注册插件路由
    plugin_manager.register_routes(app, prefix="/api/v1")
    # 创建数据表
    plugin_manager.create_tables()
    return app
```
#### 3.2.5 数据表创建机制
每个插件在 `models.py` 中定义 SQLAlchemy 模型（继承自 `Base`），插件注册时将模型类传入 PluginInfo。PluginManager 在 `create_tables()` 中通过 `Base.metadata.create_all()` 统一创建所有表。
### 3.3 配置管理
#### 3.3.1 Pydantic Settings 设计
使用 `pydantic-settings` 进行配置管理，支持从 `.env` 文件和环境变量加载配置。配置类为单例模式。
app/core/config.py
```
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    """应用全局配置"""
    # ===== 应用信息 =====
    APP_NAME: str = "青萍小台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    # ===== 服务配置 =====
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # ===== 数据库（MySQL） =====
    DATABASE_URL: str = "mysql+pymysql://user:pass@localhost:3306/qingping"
    # ===== 认证 =====
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    # ===== 大模型（MiniMax） =====
    LLM_PROVIDER: str = "minimax"
    MINIMAX_API_KEY: str = ""
    MINIMAX_MODEL: str = "abab6.5s-chat"
    MINIMAX_BASE_URL: str = "https://api.minimax.chat/v1"
    # ===== 向量数据库 =====
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "embo-01"  # MiniMax 嵌入模型
    # ===== 文件存储 =====
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    # ===== 插件配置 =====
    PLUGINS_PACKAGE: str = "app.plugins"
    # ===== CORS =====
    CORS_ORIGINS: list = ["http://localhost:5173"]
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
    )
settings = Settings()
```
#### 3.3.2 .env 配置项清单
| 配置项 | 示例值 | 说明 | 是否必填 |
| --- | --- | --- | --- |
| APP_NAME | 青萍小台 | 应用名称 | 否 |
| DEBUG | True | 调试模式开关 | 否 |
| HOST | 0.0.0.0 | 服务监听地址 | 否 |
| PORT | 8000 | 服务监听端口 | 否 |
| DATABASE_URL | mysql+pymysql://user:pass@localhost:3306/qingping | MySQL连接串 | 是 |
| SECRET_KEY | (随机字符串) | JWT签名密钥 | 是 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 10080 | Token过期时间（分钟） | 否 |
| MINIMAX_API_KEY | eyJhbGciOiJ...（实际Key） | MiniMax API密钥 | 是 |
| MINIMAX_MODEL | abab6.5s-chat | 对话模型名称 | 否 |
| CHROMA_PERSIST_DIR | ./data/chroma | 向量库持久化目录 | 否 |
| UPLOAD_DIR | ./data/uploads | 上传文件存储目录 | 否 |
| MAX_UPLOAD_SIZE | 52428800 | 最大上传大小（字节） | 否 |
| CORS_ORIGINS | ["http://localhost:5173"] | 允许的跨域源 | 否 |
### 3.4 数据库设计
#### 3.4.1 MySQL 连接配置
使用 SQLAlchemy 2.x 连接 MySQL 8.0，驱动采用 `pymysql`。连接池配置为生产环境优化参数。
app/core/database.py
```
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,           # 连接前检测
    pool_size=10,                 # 连接池大小
    max_overflow=20,              # 最大溢出连接
    pool_recycle=3600,            # 连接回收时间（秒）
)
# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
# 模型基类
Base = declarative_base()
def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
#### 3.4.2 SQLAlchemy Base 与模型约定
所有模型类必须继承自 `Base`，并遵循以下约定：
- 表名使用蛇形命名，复数形式：`knowledge_bases`, `documents`
- 主键统一为 `id`（Integer, autoincrement）
- 时间字段使用 `DateTime(timezone=True)`，默认值用 `server_default=func.now()`
- 外键关联使用 `ForeignKey` + `relationship`
- 用户隔离字段统一为 `user_id`（Integer, index=True）
#### 3.4.3 会话管理
采用 FastAPI 依赖注入模式管理数据库会话，每个请求获取独立会话，请求结束后自动关闭。
> **💡 最佳实践**
>
> 在 Service 层接受 `db: Session` 作为参数，由路由层通过 `Depends(get_db)` 注入。避免在 Service 内部直接创建会话，确保事务一致性。
### 3.5 认证系统
#### 3.5.1 JWT 实现方案
采用 `python-jose` 库实现 JWT 令牌签发与验证，使用 HS256 算法。令牌中存储用户ID作为 `sub` 声明。
app/core/auth.py - 核心函数
```
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/user/login",
    auto_error=False,
)
def hash_password(password: str) -> str:
    """密码哈希（bcrypt）"""
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```
#### 3.5.2 密码哈希
使用 `passlib` 的 bcrypt 方案进行密码哈希，默认 rounds=12。哈希后的密码以 `$2b$` 开头存储。
#### 3.5.3 依赖注入设计
提供两级依赖：
- `get_current_user` — 可选认证，未登录返回 None
- `require_current_user` — 强制认证，未登录返回 401
app/core/auth.py - 依赖函数
```
async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """获取当前登录用户（可选）"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    from app.plugins.user.models import User
    return db.query(User).filter(User.id == user_id).first()
async def require_current_user(
    current_user = Depends(get_current_user),
):
    """要求必须登录，否则抛出 401"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
```
#### 3.5.4 登录注册流程
*图 3-1：用户登录注册流程图*
```mermaid
flowchart TD
    A[用户访问登录页] --> B{是否已注册?}
    B -->|否| C[点击注册]
    C --> D[填写用户名/密码]
    D --> E[POST /api/v1/user/register]
    E --> F{用户名是否存在?}
    F -->|是| G[返回 400: 用户名已存在]
    F -->|否| H[密码哈希 + 创建用户]
    H --> I[生成 JWT Token]
    I --> J[返回 Token + 用户信息]
    B -->|是| K[填写用户名/密码]
    K --> L[POST /api/v1/user/login]
    L --> M{验证密码?}
    M -->|失败| N[返回 401: 用户名或密码错误]
    M -->|成功| I
    J --> O[前端存储 Token 到 localStorage]
    N --> P[前端提示错误]
    G --> P
```
### 3.6 统一响应格式与异常处理
#### 3.6.1 统一响应格式
所有 API 接口返回统一的 JSON 格式：
统一响应结构
```
{
  "code": 0,          // 业务状态码，0 表示成功
  "message": "success", // 消息描述
  "data": {...}       // 响应数据（对象/数组/null）
}
```
| code | 含义 | HTTP状态码 |
| --- | --- | --- |
| 0 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突（如用户名已存在） | 409 |
| 413 | 文件过大 | 413 |
| 500 | 服务器内部错误 | 500 |
| 1001 | 文档解析失败 | 400 |
| 1002 | 不支持的文件类型 | 400 |
| 2001 | 大模型调用失败 | 500 |
| 2002 | 大模型调用超时 | 504 |
#### 3.6.2 异常处理机制
定义 `AppException` 基础异常类，配合全局异常处理器实现统一错误返回。
app/core/exceptions.py
```
class AppException(Exception):
    """应用基础异常类"""
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器（捕获未处理异常）"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None,
        },
    )
```
### 3.7 CORS与中间件
#### 3.7.1 CORS 配置
使用 FastAPI 内置的 `CORSMiddleware`，允许前端开发服务器和生产域名的跨域请求。
CORS 中间件配置
```
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
#### 3.7.2 请求日志中间件
自定义中间件记录每个请求的方法、路径、状态码和耗时，用于调试和监控。
请求日志中间件
```
import time
from fastapi import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    print(f"[{request.method}] {request.url.path} "
          f"- {response.status_code} - {process_time:.1f}ms")
    return response
```
## 04 知识库模块详细设计
### 4.1 模块概述
知识库模块是青萍小台的核心基础模块，提供文档的上传、解析、分块、向量化存储和语义检索能力。它既是一个独立可用的功能模块，也是技术专家组等其他模块的**知识支撑底座**。
- **文档上传**：支持 PDF、Markdown、TXT、Word 等多种格式文档上传，单文件最大 50MB
- **语义检索**：基于向量相似度的语义检索，支持自然语言查询，快速定位相关内容
- **知识库管理**：按知识库组织文档，支持创建、删除、重命名，多知识库隔离
- **异步处理**：文档解析与向量化后台异步处理，上传后立即可见，处理完成自动可用
### 4.2 数据模型
#### 4.2.1 KnowledgeBase（知识库表）
| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | 知识库主键ID |
| name | VARCHAR(100) | NOT NULL | 知识库名称 |
| description | VARCHAR(500) | DEFAULT '' | 知识库描述 |
| user_id | Integer | NOT NULL, INDEX | 所属用户ID（用户隔离） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |
app/plugins/knowledge_base/models.py - KnowledgeBase
```
class KnowledgeBase(Base):
    """知识库"""
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="")
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    documents = relationship(
        "Document",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
```
#### 4.2.2 Document（文档表）
| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | 文档主键ID |
| title | VARCHAR(200) | NOT NULL | 文档标题（文件名） |
| content | TEXT | DEFAULT '' | 提取的纯文本内容 |
| file_path | VARCHAR(500) | DEFAULT '' | 原始文件存储路径 |
| file_type | VARCHAR(20) | DEFAULT '' | 文件类型：md/txt/pdf/docx |
| status | VARCHAR(20) | DEFAULT 'pending' | 处理状态：pending/processing/ready/error |
| chunk_count | Integer | DEFAULT 0 | 分块数量 |
| error_msg | VARCHAR(500) | DEFAULT '' | 处理失败时的错误信息 |
| knowledge_base_id | Integer | FOREIGN KEY, NOT NULL | 所属知识库ID |
| user_id | Integer | NOT NULL, INDEX | 所属用户ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 上传时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |
> **📌 状态枚举说明**
>
> pending 待处理 — 已上传，等待处理队列 processing 处理中 — 正在解析/分块/向量化 ready 就绪 — 处理完成，可检索 error 失败 — 处理失败，查看 error_msg
### 4.3 后端API设计
#### 4.3.1 知识库 CRUD 接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/knowledge_base` | GET | 获取知识库列表 | 无（Header: Authorization） | 数组：{id, name, description, document_count, created_at} | 401 未认证 |
| `/api/v1/knowledge_base` | POST | 创建知识库 | Body: {name: string, description?: string} | {id, name, description} | 400 参数错误 / 401 未认证 |
| `/api/v1/knowledge_base/{kb_id}` | DELETE | 删除知识库 | Path: kb_id | {message: "删除成功"} | 401 未认证 / 404 不存在 |
| `/api/v1/knowledge_base/{kb_id}` | GET | 获取知识库详情 | Path: kb_id | {id, name, description, document_count, created_at} | 401 / 404 |
| `/api/v1/knowledge_base/{kb_id}` | PUT | 更新知识库 | Path: kb_id, Body: {name?, description?} | {id, name, description} | 400 / 401 / 404 |
#### 4.3.2 文档管理接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/knowledge_base/{kb_id}/documents` | GET | 获取文档列表 | Path: kb_id, Query: page?, page_size?, status? | {items: [...], total, page, page_size} | 401 / 404 |
| `/api/v1/knowledge_base/{kb_id}/documents/upload` | POST | 上传文档 | Path: kb_id, FormData: file | {id, title, status, file_type} | 400 不支持类型 / 401 / 404 / 413 文件过大 |
| `/api/v1/knowledge_base/{kb_id}/documents/{doc_id}` | GET | 获取文档详情 | Path: kb_id, doc_id | {id, title, content, file_type, status, chunk_count, ...} | 401 / 404 |
| `/api/v1/knowledge_base/{kb_id}/documents/{doc_id}` | DELETE | 删除文档 | Path: kb_id, doc_id | {message: "删除成功"} | 401 / 404 |
| `/api/v1/knowledge_base/{kb_id}/documents/{doc_id}/reprocess` | POST | 重新处理文档 | Path: kb_id, doc_id | {id, status: "processing"} | 401 / 404 |
#### 4.3.3 检索接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/knowledge_base/{kb_id}/search` | POST | 知识库语义检索 | Path: kb_id Body: {query: string, n_results?: int = 5, min_score?: float = 0.0} | 数组：{content, score, metadata: {doc_id, title, chunk_index}} | 400 query为空 / 401 / 404 |
检索接口响应示例
```
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "content": "FastAPI 是一个现代、高性能的 Web 框架...",
      "score": 0.875,
      "metadata": {
        "doc_id": 12,
        "title": "FastAPI入门指南.md",
        "chunk_index": 3,
        "file_type": "md"
      }
    },
    {
      "content": "使用 Pydantic 进行数据验证...",
      "score": 0.742,
      "metadata": {
        "doc_id": 12,
        "title": "FastAPI入门指南.md",
        "chunk_index": 7,
        "file_type": "md"
      }
    }
  ]
}
```
### 4.4 文档处理流程
文档上传后，系统在后台异步执行完整的处理流水线，从文件提取到向量化存储共分为 5 个阶段。
*图 4-1：文档处理流程图*
```mermaid
flowchart LR
    A[文件上传] --> B[文本提取]
    B --> C[文本分块]
    C --> D[向量化]
    D --> E[存储到向量库]
    A -.->|更新状态: processing| F[(MySQL)]
    B -.->|保存文本内容| F
    C -.->|更新 chunk_count| F
    E -.->|更新状态: ready| F
    style A fill:#e8f0ed,stroke:#4a7c6f,stroke-width:2px
    style B fill:#f7ede4,stroke:#c47c4a,stroke-width:2px
    style C fill:#e8f0ed,stroke:#4a7c6f,stroke-width:2px
    style D fill:#f7ede4,stroke:#c47c4a,stroke-width:2px
    style E fill:#e8f0ed,stroke:#4a7c6f,stroke-width:2px
```
| 阶段 | 输入 | 处理逻辑 | 输出 | 失败处理 |
| --- | --- | --- | --- | --- |
| 1. 文件上传 | 用户上传的文件 | 保存文件到 UPLOAD_DIR，创建 Document 记录（status=pending） | 文件路径 + Document ID | 413 文件过大 / 400 不支持类型 |
| 2. 文本提取 | 文件路径 + 文件类型 | 调用对应解析器提取纯文本，保存到 content 字段 | 纯文本字符串 | status=error, error_msg="文本提取失败" |
| 3. 文本分块 | 纯文本内容 | 按段落+句子策略分块，默认 500 字符/块，重叠 50 字符 | 文本块数组 + 块数 | status=error, error_msg="文本分块失败" |
| 4. 向量化 | 文本块数组 | 调用 MiniMax Embedding API 生成向量（embo-01 模型） | 向量数组（每个块一个向量） | 重试 2 次后失败，status=error |
| 5. 向量存储 | 文本块 + 向量 + 元数据 | 写入 ChromaDB 对应知识库集合，更新状态为 ready | 存储成功确认 | status=error, error_msg="向量存储失败" |
### 4.5 文档解析器设计
采用**策略模式**设计文档解析器，每种文件类型对应一个解析器类，统一继承自 `BaseParser` 基类。
解析器类层次结构
```
class BaseParser(ABC):
    """文档解析器基类"""
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """提取纯文本内容"""
        pass
class TxtParser(BaseParser):
    """TXT 纯文本解析器"""
class MarkdownParser(BaseParser):
    """Markdown 解析器（保留结构化信息）"""
class PDFParser(BaseParser):
    """PDF 解析器（基于 pypdf）"""
class WordParser(BaseParser):
    """Word 解析器（基于 python-docx）"""
class ParserFactory:
    """解析器工厂，根据文件类型返回对应解析器"""
    _parsers = {
        "txt": TxtParser,
        "md": MarkdownParser,
        "markdown": MarkdownParser,
        "pdf": PDFParser,
        "docx": WordParser,
    }
    @classmethod
    def get_parser(cls, file_type: str) -> BaseParser:
        parser_cls = cls._parsers.get(file_type.lower())
        if not parser_cls:
            raise ValueError(f"不支持的文件类型: {file_type}")
        return parser_cls()
```
#### 各格式解析实现方案
| 格式 | 依赖库 | 实现方案 | 注意事项 |
| --- | --- | --- | --- |
| TXT | Python 内置 | 直接 UTF-8 读取，自动忽略编码错误 | 需处理 GBK、UTF-8 BOM 等编码问题 |
| Markdown | Python 内置 | 直接读取文本，分块时保留标题层级信息 | 可考虑按标题层级分块以提高检索质量 |
| PDF | pypdf | 逐页提取文本，页间添加分页标记 | 扫描件PDF无法提取文本；复杂排版可能乱序 |
| Word (.docx) | python-docx | 遍历 paragraphs 提取文本，保留段落结构 | 不支持 .doc 旧格式；表格内容需单独处理 |
### 4.6 文本分块策略
#### 4.6.1 分块算法
采用**基于段落的递归分块算法**，优先保持语义完整性：
1. **段落级分割**：按双换行符（`\n\n`）将文本分割为段落
2. **段落合并**：将连续段落合并，直到接近目标块大小
3. **句子级分割**：若单个段落超过目标大小，按句子（。！？）进一步分割
4. **字符级分割**：若单个句子仍超过限制，按字符硬切割
#### 4.6.2 重叠策略
相邻块之间保留部分重叠内容，确保语义连续性不被切断。
- **重叠大小**：默认 50 字符（约占块大小的 10%）
- **重叠方向**：每个块的开头包含前一个块末尾的内容
- **可配置性**：通过配置参数 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 调整
#### 4.6.3 分块参数配置
| 参数 | 默认值 | 说明 | 建议范围 |
| --- | --- | --- | --- |
| CHUNK_SIZE | 500 | 目标块大小（字符数） | 300 - 1000 |
| CHUNK_OVERLAP | 50 | 重叠字符数 | 30 - 150 |
| MIN_CHUNK_SIZE | 50 | 最小块大小（小于则合并） | 20 - 100 |
> **💡 优化方向（MVP后）**
>
> MVP 版本采用简单的字符计数分块。后续可优化为：按 Markdown 标题层级分块、语义分块（基于嵌入相似度）、添加元数据（块所属章节、页码等）以提高检索精度。
### 4.7 RAG检索设计
#### 4.7.1 ChromaDB 集合格式
每个知识库对应 ChromaDB 中的一个 Collection，命名格式为 `kb_{kb_id}`。
ChromaDB 集合结构
```
Collection Name: "kb_1"  (kb_{knowledge_base_id})
Document (文本块内容):
  "FastAPI 是一个现代、高性能的 Web 框架，用于构建 API..."
ID (块唯一标识):
  "doc_12_chunk_3"  (doc_{document_id}_chunk_{index})
Metadata (元数据):
  {
    "doc_id": 12,           // 文档ID
    "title": "FastAPI入门指南.md",  // 文档标题
    "chunk_index": 3,       // 块在文档中的序号
    "file_type": "md",      // 文件类型
    "user_id": 1            // 用户ID（用于权限过滤）
  }
Embedding (向量):
  [0.123, -0.456, ...]     // MiniMax embo-01 模型，1536维
```
#### 4.7.2 检索参数
| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| n_results | 5 | 返回结果数量 |
| min_score | 0.0 | 最小相似度阈值（低于此分数的结果被过滤） |
| where_filter | {"user_id": xxx} | 元数据过滤条件，确保用户隔离 |
#### 4.7.3 结果排序与相似度计算
- **相似度度量**：ChromaDB 默认使用余弦相似度（L2 归一化后等价）
- **分数转换**：ChromaDB 返回的是距离值，转换为相似度分数：`score = 1 - distance`
- **排序方式**：按相似度分数从高到低排序
- **去重逻辑**：同一文档的多个块均可能返回，通过 metadata 中的 doc_id 区分
#### 4.7.4 相似度阈值策略
MVP 版本默认不设阈值（min_score=0.0），返回所有匹配结果。建议在实际使用中根据场景调整：
- **宽松匹配**（默认）：阈值 0.0，返回 top-N，适合探索性查询
- **中等匹配**：阈值 0.5，过滤明显不相关结果
- **严格匹配**：阈值 0.7，仅返回高度相关内容，适合精确问答
### 4.8 前端页面设计
#### 4.8.1 页面布局
知识库页面采用**左右两栏布局**，左侧为知识库列表，右侧为文档与搜索区域。
页面结构示意
```
┌───────────────────────────────────────────────────────┐
│  青萍小台        [知识库] [技术专家组]       [用户头像] │
├──────────┬────────────────────────────────────────────┤
│          │  🔍 搜索框 [选择知识库▼]                    │
│ 知识库列表│  ─────────────────────────────────────    │
│          │                                            │
│ 📚 技术文档│  当前知识库：技术文档    [上传文档]       │
│ 📚 产品资料│  ────────────────────────────────        │
│ 📚 学习笔记│                                            │
│          │  📄 FastAPI入门指南.md    [就绪]  12块      │
│ + 新建   │  📄 系统架构设计.pdf      [处理中]  -       │
│          │  📄 数据库设计.docx       [就绪]  8块       │
│          │  📄 接口规范.md          [失败]  -         │
│          │                                            │
└──────────┴────────────────────────────────────────────┘
```
#### 4.8.2 左侧知识库列表
- 展示当前用户的所有知识库，按创建时间倒序排列
- 点击切换当前选中的知识库
- 底部「+ 新建」按钮创建新知识库
- 悬停显示「删除」操作（二次确认）
- 支持知识库重命名（右键菜单或点击编辑图标）
#### 4.8.3 右侧文档与搜索区域
- **顶部搜索栏**：输入查询内容，回车触发语义检索；支持选择知识库范围
- **知识库信息栏**：显示当前知识库名称、文档数量、上传按钮
- **文档列表**：展示当前知识库的所有文档，包含标题、状态、块数、上传时间
- **搜索结果**：搜索时替换文档列表，展示匹配的文本块及来源文档
#### 4.8.4 上传交互
1. 点击「上传文档」按钮，打开文件选择器
2. 选择文件后，前端立即显示「上传中」状态的卡片
3. 上传成功后，卡片状态变为「处理中」，显示进度动画
4. 前端每 3 秒轮询文档状态，处理完成后自动更新为「就绪」
5. 支持拖拽上传（拖拽文件到文档列表区域触发上传）
#### 4.8.5 搜索结果展示
- 按相似度从高到低排列，每个结果显示：文本片段、相似度分数、来源文档标题
- 文本片段高亮匹配关键词（前端模糊高亮）
- 点击结果跳转到文档详情，定位到对应段落
- 结果按文档分组展示（可选，MVP后优化）
### 4.9 状态管理设计
前端使用 **Zustand** 进行状态管理，知识库模块的状态切片设计如下：
src/store/knowledgeBase.ts
```
import { create } from 'zustand'
interface KnowledgeBase {
  id: number
  name: string
  description: string
  documentCount: number
  createdAt: string
}
interface Document {
  id: number
  title: string
  fileType: string
  status: 'pending' | 'processing' | 'ready' | 'error'
  chunkCount: number
  errorMsg?: string
  createdAt: string
}
interface SearchResult {
  content: string
  score: number
  metadata: Record
}
interface KBState {
  // 知识库列表
  knowledgeBases: KnowledgeBase[]
  currentKbId: number | null
  // 文档列表
  documents: Document[]
  documentsLoading: boolean
  // 搜索
  searchQuery: string
  searchResults: SearchResult[]
  searchLoading: boolean
  // Actions
  fetchKnowledgeBases: () => Promise
  createKnowledgeBase: (name: string, desc: string) => Promise
  deleteKnowledgeBase: (id: number) => Promise
  setCurrentKb: (id: number) => void
  fetchDocuments: (kbId: number) => Promise
  uploadDocument: (kbId: number, file: File) => Promise
  deleteDocument: (kbId: number, docId: number) => Promise
  reprocessDocument: (kbId: number, docId: number) => Promise
  search: (kbId: number, query: string) => Promise
  clearSearch: () => void
}
export const useKBStore = create<KBState>((set, get) => ({
  // ... state & actions
}))
```
## 05 技术专家组模块详细设计
### 5.1 模块概述
技术专家组模块是青萍小台的核心特色功能，模拟一个由**四位AI专家**组成的技术团队，采用**状态图式协作（State Graph）+ 人工介入**模式为用户的技术问题提供全方位分析。用户提出问题后，系统按照状态机定义的阶段依次推进，每个阶段完成后暂停等待用户确认，用户可手动切换专家、确认进入下一阶段或回退修改。MVP阶段聚焦Step 1：状态图驱动 + 人工介入 + 手动切换专家，同时预留Step 2的Evaluator自动评估与Loop迭代扩展接口。
- **状态图协作**：基于有限状态机，五状态流转，支持人工确认、回退、手动切换专家
- **流式输出**：基于 SSE 的实时流式输出，专家回复逐字呈现，无需等待完整响应
- **知识库增强**：可选接入知识库，专家回答基于用户私有文档，更精准更贴合业务
- **对话历史**：完整保存每轮对话，支持多会话管理，随时回顾专家分析过程
### 5.2 四大专家角色详细定义
#### 5.2.1 架构师（Architect）
🏗️
架构师
Architect · 技术方案设计
**职责定位**：负责技术方案的整体设计和把关，从宏观视角分析问题，给出架构级解决方案。
**核心能力**：需求分析、架构设计、技术选型、风险识别、性能考量
**颜色标识**：`#4a7c6f`（深绿色，代表稳重与全局观）
架构师 System Prompt
```
你是一位资深软件架构师，负责技术方案的整体设计和把关。
你的职责：
1. 分析需求，给出清晰的技术方案和架构设计
2. 考虑系统的可扩展性、可维护性和性能
3. 给出关键技术选型建议和理由
4. 识别潜在风险和技术难点
输出要求：
- 先给出总体思路，再分点详细说明
- 使用代码或伪代码说明核心逻辑
- 注意边界条件和异常处理
- 语气专业、简洁、有条理
```
#### 5.2.2 程序员（Coder）
💻
程序员
Coder · 代码实现
**职责定位**：负责将架构方案转化为可运行的代码实现，注重代码质量和工程实践。
**核心能力**：代码编写、最佳实践应用、边界处理、注释文档
**颜色标识**：`#7a6b9d`（紫色，代表创造力与逻辑性）
程序员 System Prompt
```
你是一位实战经验丰富的程序员，擅长把想法变成可运行的代码。
你的职责：
1. 根据需求和架构方案，编写高质量的实现代码
2. 确保代码的可读性和可维护性
3. 处理各种边界情况和异常
4. 写出清晰的注释和说明
输出要求：
- 代码要完整、可直接运行
- 关键部分要有注释说明
- 遵循语言的最佳实践和编码规范
- 给出使用示例和测试方法
```
#### 5.2.3 代码审查员（Reviewer）
🔍
代码审查员
Reviewer · 质量把关
**职责定位**：负责审查程序员输出的代码，发现问题并提出改进建议，确保代码质量。
**核心能力**：Bug发现、性能优化、安全审查、代码规范检查、改进建议
**颜色标识**：`#c47c4a`（橙色，代表警示与关注）
审查员 System Prompt
```
你是一位严格的代码审查专家，擅长发现代码中的问题和改进点。
你的职责：
1. 审查代码质量，发现 Bug、性能问题、安全隐患
2. 检查代码规范和最佳实践
3. 提出具体的改进建议
4. 给出代码优化的具体方案
输出要求：
- 按严重程度列出问题（严重/一般/建议）
- 每个问题给出具体位置和修改建议
- 提供修改后的代码示例
- 既要指出问题，也要肯定做得好的地方
```
#### 5.2.4 测试工程师（Tester）
🧪
测试工程师
Tester · 质量保障
**职责定位**：负责设计测试用例和测试方案，从质量保障角度验证方案的完备性。
**核心能力**：测试用例设计、边界场景覆盖、自动化测试、质量评估
**颜色标识**：`#b85450`（红色，代表严谨与质量）
测试工程师 System Prompt
```
你是一位严谨的测试工程师，擅长设计测试用例和质量保障。
你的职责：
1. 根据需求设计全面的测试用例
2. 考虑各种边界情况和异常场景
3. 给出测试策略和测试计划
4. 提供自动化测试代码
输出要求：
- 按功能模块列出测试用例
- 覆盖正常路径、边界情况、异常场景
- 给出具体的输入输出预期
- 提供可运行的测试代码示例
```
> **🔄 协作模式：状态图式 + 人工介入**
>
> **Step 1（MVP）**：采用状态图式协作模式，定义 5 个核心状态节点（idle / arch_design / code_impl / code_review / testing / done），每个状态完成后自动暂停，等待用户人工介入。用户可以确认进入下一状态、回退到上一状态，或手动切换到任意专家进行补充分析。 **Step 2（预留扩展）**：引入 Evaluator 评估节点，支持配置验收标准，实现自动化的质量评估与 Loop 迭代闭环。相关数据表字段与API接口已预留。
#### 5.2.5 专家角色与状态对应关系
| 状态节点 | 对应专家 | 状态标识 | 说明 |
| --- | --- | --- | --- |
| `idle` | - | 待开始 | 会话创建后初始状态，等待用户输入 |
| `arch_design` | 🏗️ 架构师 | 架构设计 | 架构师进行技术方案设计阶段 |
| `code_impl` | 💻 程序员 | 代码实现 | 程序员进行代码实现阶段 |
| `code_review` | 🔍 审查员 | 代码审查 | 审查员进行代码质量审查阶段 |
| `testing` | 🧪 测试工程师 | 测试验证 | 测试工程师进行测试用例设计阶段 |
| `done` | - | 已完成 | 所有阶段完成，会话结束 |
### 5.3 数据模型
#### 5.3.1 ExpertSession（专家会话表）
| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | 会话主键ID |
| title | VARCHAR(200) | DEFAULT '新对话' | 会话标题（取用户首条消息前30字） |
| user_id | Integer | NOT NULL, INDEX | 所属用户ID |
| status | VARCHAR(20) | DEFAULT 'active' | 会话状态：active / completed / error |
| current_state | VARCHAR(50) | DEFAULT 'idle' | 当前状态节点：idle / arch_design / code_impl / code_review / testing / done |
| iteration_count | Integer | DEFAULT 1 | 当前迭代轮次（从第1轮开始） |
| max_iterations | Integer | DEFAULT 5 | 最大迭代轮次（防止无限循环） |
| acceptance_criteria | JSON | DEFAULT NULL | 验收标准配置（Step 2 预留，Evaluator 使用） |
| kb_id | Integer | NULL | 关联的知识库ID（可选） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |
#### 5.3.2 ExpertMessage（专家消息表）
| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | 消息主键ID |
| session_id | Integer | NOT NULL, INDEX | 所属会话ID |
| role | VARCHAR(20) | NOT NULL | 消息角色：user / assistant / system |
| expert_role | VARCHAR(50) | DEFAULT '' | 专家角色：architect / coder / reviewer / tester |
| state_label | VARCHAR(50) | DEFAULT '' | 所属状态节点：arch_design / code_impl / code_review / testing |
| iteration | Integer | DEFAULT 1 | 所属迭代轮次 |
| content | TEXT | DEFAULT '' | 消息内容（Markdown格式） |
| metadata | JSON | DEFAULT {} | 元数据：专家名称、图标、颜色等 |
| token_usage | Integer | DEFAULT 0 | 消耗的 token 数量（统计用） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
app/plugins/tech_experts/models.py
```
class ExpertSession(Base):
    """专家会话"""
    __tablename__ = "expert_sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="新对话")
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(String(20), default="active")
    current_state = Column(String(50), default="idle")  # 状态机当前状态
    iteration_count = Column(Integer, default=1)          # 当前迭代轮次
    max_iterations = Column(Integer, default=5)           # 最大迭代轮次
    acceptance_criteria = Column(JSON, default=None)      # 验收标准（Step 2 预留）
    kb_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
class ExpertMessage(Base):
    """专家消息"""
    __tablename__ = "expert_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False)
    expert_role = Column(String(50), default="")
    state_label = Column(String(50), default="")          # 所属状态节点
    iteration = Column(Integer, default=1)                # 所属迭代轮次
    content = Column(Text, default="")
    metadata_ = Column("metadata", JSON, default={})
    token_usage = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class ExpertStateTransition(Base):
    """专家状态转移历史表"""
    __tablename__ = "expert_state_transitions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    from_state = Column(String(50), nullable=False)       # 源状态
    to_state = Column(String(50), nullable=False)         # 目标状态
    transition_type = Column(String(20), default="auto")  # 转移类型：auto / manual_confirm / manual_rollback / manual_switch
    triggered_by = Column(String(20), default="system")   # 触发者：system / user
    iteration = Column(Integer, default=1)                # 转移时的迭代轮次
    reason = Column(String(500), default="")              # 转移原因/备注
    metadata = Column(JSON, default={})                   # 附加信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```
### 5.4 后端API设计
#### 5.4.1 会话管理接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/tech_experts/sessions` | GET | 获取会话列表 | Query: page?, page_size? | {items: [{id, title, status, current_phase, updated_at}], total} | 401 未认证 |
| `/api/v1/tech_experts/sessions` | POST | 创建会话 | Body: {title?: string, kb_id?: number} | {id, title, status} | 400 / 401 |
| `/api/v1/tech_experts/sessions/{session_id}` | GET | 获取会话详情 | Path: session_id | {id, title, status, current_phase, kb_id, created_at} | 401 / 404 |
| `/api/v1/tech_experts/sessions/{session_id}` | DELETE | 删除会话 | Path: session_id | {message: "删除成功"} | 401 / 404 |
#### 5.4.2 消息接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/tech_experts/sessions/{session_id}/messages` | GET | 获取消息列表 | Path: session_id | 数组：{id, role, expert_role, content, metadata, created_at} | 401 / 404 |
#### 5.4.3 对话接口（SSE 流式）
| 端点 | 方法 | 功能 | 请求参数 | 响应格式 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/tech_experts/chat` | POST | 与技术专家组对话（新建会话） | Body: {message: string, kb_id?: number, session_id?: number} | text/event-stream（SSE流式） | 400 / 401 / 2001 模型调用失败 |
#### 5.4.4 专家列表接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 |
| --- | --- | --- | --- | --- |
| `/api/v1/tech_experts/experts` | GET | 获取专家角色列表 | 无（公开接口） | 数组：{role, name, icon, color, description} |
#### 5.4.5 状态控制接口
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 | 错误码 |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/tech_experts/sessions/{id}/state` | GET | 获取当前状态 | Path: id | {current_state, iteration_count, max_iterations, can_confirm, can_rollback, available_experts} | 401 / 404 |
| `/api/v1/tech_experts/sessions/{id}/confirm-state` | POST | 确认当前状态，进入下一阶段 | Path: id Body: {feedback?: string} | {new_state, message} | 400 / 401 / 404 / 2002 状态不可确认 |
| `/api/v1/tech_experts/sessions/{id}/rollback` | POST | 回退到上一状态 | Path: id Body: {target_state?: string, reason?: string} | {new_state, message} | 400 / 401 / 404 / 2003 无法回退 |
| `/api/v1/tech_experts/sessions/{id}/switch-expert` | POST | 手动切换到指定专家 | Path: id Body: {expert_role: string, instruction?: string} | {new_state, expert_role, message} | 400 / 401 / 404 / 2004 无效专家角色 |
#### 5.4.6 验收标准配置接口（Step 2 预留）
> **📌 Step 2 预留接口**
>
> 以下接口为 Step 2 Evaluator 自动评估与 Loop 迭代的扩展接口，MVP 阶段仅定义数据结构，暂不实现业务逻辑。
| 端点 | 方法 | 功能 | 请求参数 | 响应数据 |
| --- | --- | --- | --- | --- |
| `/api/v1/tech_experts/sessions/{id}/acceptance-criteria` | PUT | 配置验收标准 | Path: id Body: {criteria: JSON} | {message: "配置成功"} |
| `/api/v1/tech_experts/sessions/{id}/acceptance-criteria` | GET | 获取验收标准 | Path: id | {criteria: JSON} |
### 5.5 工作流设计
#### 5.5.1 状态图模式（State Graph）
技术专家组采用**状态图式协作（State Graph）+ 人工介入**模式。区别于传统的顺序流水线，状态图模式下工作流以**有限状态机（FSM）**驱动，每个状态对应一位专家的工作阶段。每个状态完成后工作流自动暂停，等待用户人工介入（确认/回退/切换专家），而非自动推进到下一阶段。这种设计给予用户完全的控制权，同时为 Step 2 引入 Evaluator 自动评估与 Loop 迭代预留了扩展空间。
> **🎯 MVP 定位：Step 1**
>
> **Step 1（MVP 实现）**：状态机 + 人工介入 + 手动切换专家。每个状态完成后暂停，等待用户确认。 **Step 2（后续扩展）**：引入 Evaluator 评估节点 + 验收标准配置 + 自动 Loop 迭代。
#### 5.5.2 状态定义
共定义 **6 个状态节点**，其中 4 个为专家工作状态，1 个初始状态，1 个结束状态。
| 状态 | 名称 | 对应专家 | 状态类型 | 描述 |
| --- | --- | --- | --- | --- |
| `idle` | 待开始 | - | 初始状态 | 会话创建后的初始状态，等待用户输入问题 |
| `arch_design` | 架构设计 | 🏗️ 架构师 | 工作状态 | 架构师进行技术方案设计与架构选型 |
| `code_impl` | 代码实现 | 💻 程序员 | 工作状态 | 程序员将架构方案转化为可运行的代码 |
| `code_review` | 代码审查 | 🔍 审查员 | 工作状态 | 审查员对代码质量进行审查并提出改进建议 |
| `testing` | 测试验证 | 🧪 测试工程师 | 工作状态 | 测试工程师设计测试用例并验证方案完备性 |
| `done` | 已完成 | - | 结束状态 | 所有阶段通过确认，会话正常结束 |
#### 5.5.3 状态转移图
*图 5-1：技术专家组状态转移图（State Graph）*
```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> arch_design : 用户发送问题\n(自动进入)
    arch_design --> code_impl : 用户确认\n[确认进入下一阶段]
    code_impl --> code_review : 用户确认
    code_review --> testing : 用户确认
    testing --> done : 用户确认\n[全部完成]
    code_impl --> arch_design : 用户回退\n[回退修改]
    code_review --> code_impl : 用户回退
    testing --> code_review : 用户回退
    arch_design --> arch_design : 手动切换到架构师\n(重新生成)
    arch_design --> code_impl : 手动切换到程序员
    code_impl --> arch_design : 手动切换到架构师
    code_impl --> code_review : 手动切换到审查员
    code_review --> arch_design : 手动切换到架构师
    code_review --> code_impl : 手动切换到程序员
    code_review --> testing : 手动切换到测试工程师
    testing --> arch_design : 手动切换到架构师
    testing --> code_impl : 手动切换到程序员
    testing --> code_review : 手动切换到审查员
    done --> [*]
    note right of arch_design
      人工介入点：
      架构设计完成后
      暂停等待用户确认
    end note
    note right of code_impl
      人工介入点：
      代码实现完成后
      暂停等待用户确认
    end note
    note right of code_review
      人工介入点：
      代码审查完成后
      暂停等待用户确认
    end note
    note right of testing
      人工介入点：
      测试验证完成后
      暂停等待用户确认
    end note
```
#### 5.5.4 转移条件说明
| 转移类型 | 触发方式 | 转移方向 | 说明 |
| --- | --- | --- | --- |
| **自动转移** | 系统自动 | idle → arch_design | 用户首次发送问题后，自动进入架构设计状态并启动架构师 |
| **确认转移** | 用户点击「确认进入下一阶段」 | arch_design → code_impl code_impl → code_review code_review → testing testing → done | 每个工作状态完成后暂停，用户确认后推进到下一状态 |
| **回退转移** | 用户点击「回退修改」 | code_impl → arch_design code_review → code_impl testing → code_review | 用户对当前阶段不满意，可回退到上一状态重新生成 |
| **手动切换** | 用户手动选择专家 | 任意工作状态 ↔ 任意工作状态 | 用户可随时手动切换到任意专家，灵活调整分析方向 |
#### 5.5.5 人工介入点设计
每个专家工作状态完成后，系统自动暂停并展示操作面板，等待用户决策。这是 MVP 版本的核心交互设计。
人工介入点操作面板结构
```
{
  "session_id": 123,
  "current_state": "arch_design",
  "current_expert": "architect",
  "iteration": 1,
  "status": "paused",          // 暂停中，等待人工介入
  "available_actions": {
    "can_confirm": true,       // 可确认进入下一阶段
    "can_rollback": false,     // 不可回退（已是第一阶段）
    "can_switch": true,        // 可手动切换专家
    "switch_options": [        // 可切换的专家列表
      {"role": "architect", "name": "架构师", "icon": "🏗️", "color": "#4a7c6f"},
      {"role": "coder", "name": "程序员", "icon": "💻", "color": "#7a6b9d"},
      {"role": "reviewer", "name": "审查员", "icon": "🔍", "color": "#c47c4a"},
      {"role": "tester", "name": "测试工程师", "icon": "🧪", "color": "#b85450"}
    ]
  },
  "next_state_label": "代码实现",
  "prev_state_label": null
}
```
#### 5.5.6 回退机制
- **回退方向**：默认回退到上一相邻状态（如 code_review → code_impl）
- **回退操作**：回退后触发目标状态的专家重新生成输出
- **迭代计数**：每次回退并重新推进时，迭代轮次 +1
- **历史保留**：回退不删除历史消息，旧版本消息保留在对话中，新版本追加显示
- **最大迭代**：通过 max_iterations 限制最大迭代轮次（默认 5 轮），防止无限循环
#### 5.5.7 迭代计数与终止条件
| 条件 | 触发时机 | 结果 |
| --- | --- | --- |
| 正常完成 | testing 状态用户确认 | 进入 done 状态，会话结束 |
| 达到最大迭代 | iteration_count >= max_iterations | 强制暂停，提示用户已达最大迭代轮次，需手动确认结束 |
| 用户主动结束 | 任意状态用户点击「结束会话」 | 直接进入 done 状态 |
#### 5.5.8 状态流转结构
状态机在执行过程中维护全局状态上下文，包含所有专家输出与状态元数据：
状态机上下文结构
```
{
  "user_input": "如何实现一个用户登录系统?",
  "kb_context": "...",
  "current_state": "code_impl",
  "iteration_count": 1,
  "max_iterations": 5,
  "expert_outputs": {
    "arch_design": {        // 按状态存储输出
      "architect": ["### 架构设计方案\n..."]  // 每轮迭代的输出
    },
    "code_impl": {
      "coder": ["### 实现代码\n..."]
    },
    "code_review": {
      "reviewer": []        // 未执行的为空数组
    },
    "testing": {
      "tester": []
    }
  },
  "state_history": [        // 状态转移历史
    {"from": "idle", "to": "arch_design", "type": "auto", "iteration": 1, "time": "..."},
    {"from": "arch_design", "to": "code_impl", "type": "manual_confirm", "iteration": 1, "time": "..."}
  ],
  "session_id": 123,
  "user_id": 1,
  "acceptance_criteria": null  // Step 2 预留
}
```
*图 5-2：状态机驱动的 SSE 交互时序图（含人工介入）*
```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as 后端API
    participant S as 状态机引擎
    participant L as MiniMax LLM
    participant R as RAG服务
    U->>F: 输入问题，点击发送
    F->>B: POST /tech_experts/chat (message, kb_id?)
    B->>B: 创建会话 + 保存用户消息
    B-->>F: 200 OK (SSE 连接建立)
    alt 启用知识库
        B->>R: 检索相关文档(query)
        R-->>B: 返回Top-N相关片段
    end
    B->>S: 启动状态机(user_input, kb_context)
    B-->>F: SSE: state_enter(arch_design)
    Note over S,L: 状态1: 架构设计
    S->>L: Chat Completions (架构师Prompt + 输入)
    L-->>S: 流式返回架构设计内容
    S-->>B: yield expert_output(architect)
    B-->>F: SSE: expert_output(architect, state=arch_design)
    S-->>B: yield state_pause(arch_design)
    B-->>F: SSE: state_pause(can_confirm, can_rollback)
    Note over U,F: ⏸ 暂停，等待人工介入
    U->>F: 点击「确认进入下一阶段」
    F->>B: POST /confirm-state
    B->>S: 确认转移到 code_impl
    B-->>F: SSE: state_transition(arch->code, manual_confirm)
    B-->>F: SSE: state_enter(code_impl)
    Note over S,L: 状态2: 代码实现
    S->>L: Chat Completions (程序员Prompt + 上下文)
    L-->>S: 流式返回代码实现
    S-->>B: yield expert_output(coder)
    B-->>F: SSE: expert_output(coder, state=code_impl)
    S-->>B: yield state_pause(code_impl)
    B-->>F: SSE: state_pause(can_confirm, can_rollback)
    Note over U,F: ⏸ 再次暂停，等待人工介入
    U->>F: 点击「回退修改」
    F->>B: POST /rollback
    B->>S: 回退到 arch_design
    B-->>F: SSE: state_transition(code->arch, manual_rollback)
    B-->>F: SSE: state_enter(arch_design)
    Note right of S: 重新生成架构设计...
    Note over S,L: ... (后续状态 / 最终完成)
    S-->>B: yield complete(summary, total_iterations)
    B-->>F: SSE: complete(message, total_iterations)
    B->>B: 更新会话状态为 done / completed
    F->>U: 展示完整分析结果
```
### 5.6 SSE流式输出设计
#### 5.6.1 事件类型
| 事件类型 (type) | 触发时机 | 数据字段 | 说明 |
| --- | --- | --- | --- |
| `state_enter` | 进入新状态时 | {type, state, state_label, expert_role?, expert_name?, icon?, color?} | 通知前端当前进入哪个状态节点 |
| `state_pause` | 当前状态完成，暂停等待人工介入时 | {type, state, can_confirm, can_rollback, iteration} | 通知前端展示人工介入操作面板 |
| `state_transition` | 状态转移发生时 | {type, from_state, to_state, transition_type, triggered_by, iteration} | 通知前端状态转移事件（确认/回退/切换） |
| `expert_output` | 每个专家输出完成时 | {type, role, name, icon, color, content, state_label, iteration} | 专家的完整输出内容（Markdown） |
| `token` | 每收到一个 token 时 | {type, role, delta, state_label} | 流式增量输出（MVP可选，简化版用完整输出） |
| `complete` | 所有阶段完成（进入 done 状态） | {type, message, summary, total_iterations} | 工作流完成，附带总结和总迭代轮次 |
| `error` | 发生错误时 | {type, message, code} | 错误信息 |
#### 5.6.2 数据格式
所有 SSE 事件遵循标准格式，以 `data:` 开头，JSON 编码，事件间以空行分隔。
SSE 事件格式示例
```
data: {"type":"state_enter","state":"arch_design","state_label":"架构设计","expert_role":"architect","name":"架构师","icon":"🏗️","color":"#4a7c6f"}
data: {"type":"expert_output","role":"architect","name":"架构师","icon":"🏗️","color":"#4a7c6f","state_label":"arch_design","iteration":1,"content":"### 技术方案设计\n\n根据需求分析..."}
data: {"type":"state_pause","state":"arch_design","can_confirm":true,"can_rollback":false,"iteration":1}
data: {"type":"state_transition","from_state":"arch_design","to_state":"code_impl","transition_type":"manual_confirm","triggered_by":"user","iteration":1}
data: {"type":"state_enter","state":"code_impl","state_label":"代码实现","expert_role":"coder","name":"程序员","icon":"💻","color":"#7a6b9d"}
data: {"type":"complete","message":"所有阶段分析完成","summary":"## 专家组分析总结\n...","total_iterations":1}
```
#### 5.6.3 前端处理逻辑
前端 SSE 处理逻辑
```
// 创建 SSE 连接（使用 fetch + ReadableStream 实现 POST + SSE）
async function startChat(message, kbId) {
  const response = await fetch('/api/v1/tech_experts/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ message, kb_id: kbId }),
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        handleSSEEvent(data)
      }
    }
  }
}
// 事件处理
function handleSSEEvent(event) {
  switch (event.type) {
    case 'state_enter':
      // 更新顶部状态进度条，高亮当前状态
      setCurrentState(event.state, event.state_label)
      break
    case 'state_pause':
      // 显示人工介入操作面板（确认/回退/切换专家）
      showActionPanel(event)
      break
    case 'state_transition':
      // 状态转移动画效果
      animateStateTransition(event.from_state, event.to_state)
      break
    case 'expert_output':
      // 添加专家消息到对话列表
      addExpertMessage(event)
      break
    case 'complete':
      // 对话完成，更新状态为 done
      setChatStatus('completed')
      hideActionPanel()
      break
    case 'error':
      // 显示错误提示
      showError(event.message)
      break
  }
}
```
*图 5-3：SSE 交互时序图*
```mermaid
sequenceDiagram
    participant F as 前端
    participant B as 后端
    F->>B: POST /chat (message)
    B-->>F: HTTP 200 + SSE Headers
    B-->>F: data: {type:"phase_start", role:"architect"}
    Note right of F: 显示「架构师正在思考...」
    B-->>F: data: {type:"expert_output", role:"architect", content:"..."}
    Note right of F: 渲染架构师输出卡片
    B-->>F: data: {type:"phase_start", role:"coder"}
    Note right of F: 显示「程序员正在编码...」
    B-->>F: data: {type:"expert_output", role:"coder", content:"..."}
    Note right of F: 渲染程序员输出卡片
    B-->>F: ... (reviewer / tester)
    B-->>F: data: {type:"complete"}
    Note right of F: 标记对话完成
```
### 5.7 知识库RAG接入设计
#### 5.7.1 检索时机
知识库 RAG 检索发生在**工作流启动前**，即第一个专家（架构师）开始工作之前。检索结果作为上下文注入到所有专家的 Prompt 中。
1. 用户发起对话时可选指定 `kb_id`
2. 若指定了知识库，工作流启动前先调用 RAG 服务检索相关文档
3. 检索结果组装成上下文文本，注入到每个专家的 System Prompt 中
4. 所有专家基于用户问题 + 知识库上下文进行回答
#### 5.7.2 上下文注入方式
采用**System Prompt 追加**方式注入知识库上下文，放在系统提示的末尾。
上下文注入 Prompt 模板
```
## 参考资料（来自知识库）
以下是从用户知识库中检索到的相关内容，请基于这些内容回答问题：
{context}
---
请基于以上参考资料和你的专业知识回答用户的问题。
如果参考资料中有相关内容，请优先参考。
如果参考资料中没有相关信息，可以基于通用知识回答，但请明确说明。
```
#### 5.7.3 上下文组装逻辑
上下文组装函数
```
def build_kb_context(search_results: list[dict], max_chars: int = 3000) -> str:
    """
    将检索结果组装为上下文文本
    - 按相似度排序
    - 控制总字符数不超过 max_chars
    - 保留来源信息
    """
    parts = []
    total_chars = 0
    for i, result in enumerate(search_results, 1):
        content = result["content"]
        title = result["metadata"].get("title", "未知文档")
        part = f"### 参考资料 {i}（来自：{title}）\n{content}"
        if total_chars + len(part) > max_chars:
            # 截断剩余空间
            remaining = max_chars - total_chars
            if remaining > 100:
                parts.append(part[:remaining] + "...\n")
            break
        parts.append(part)
        total_chars += len(part)
    return "\n\n".join(parts)
```
### 5.8 前端页面设计
#### 5.8.1 页面布局
技术专家组页面采用**三栏布局 + 顶部状态进度条**：左侧会话列表、中间对话区（含状态进度条和操作区）、底部输入框。
页面结构示意
```
┌──────────────────────────────────────────────────────────────┐
│  青萍小台         [知识库] [技术专家组]            [用户头像] │
├──────────┬───────────────────────────────────────────────────┤
│          │  🏗️ 技术专家组              第 1 轮迭代  ⚙️验收标准 │
│          │  ─────────────────────────────────────────────    │
│ 会话列表  │  ○架构设计 → ○代码实现 → ○代码审查 → ○测试验证    │
│          │  ✓已完成      当前        待开始       待开始     │
│ 📝 如何实 │  ─────────────────────────────────────────────    │
│   现登录 │                                                   │
│ 📝 微服 │  ┌──────────────────────────────────┐             │
│   务架构 │  │ 用户：如何实现一个用户登录系统？    │             │
│ 📝 API │  └──────────────────────────────────┘             │
│   设计  │  ┌──────────────────────────────────┐             │
│          │  │ 🏗️ 架构师     [切换专家 ▼]        │             │
│ + 新建  │  │ ### 技术方案设计                  │             │
│          │  │ 采用 JWT + bcrypt 方案...        │             │
│          │  └──────────────────────────────────┘             │
│          │  [✓ 确认进入下一阶段]  [↩ 回退修改]  [切换到...]  │
│          │                                                   │
│          ├───────────────────────────────────────────────────┤
│          │ 💬 请输入您的技术问题...                [发送]     │
│          │ [附件] [选择知识库]                                │
└──────────┴───────────────────────────────────────────────────┘
```
#### 5.8.2 顶部状态进度条
- **功能**：展示当前所处的工作阶段，支持点击查看状态详情
- **状态节点**：架构设计 → 代码实现 → 代码审查 → 测试验证
- **状态样式**：已完成（绿色勾号）、进行中（高亮+动画）、待开始（灰色）
- **迭代轮次**：右上角显示「第 N 轮迭代」标识
- **验收标准**：右上角设置按钮（Step 2 预留，灰显状态）
#### 5.8.3 人工介入操作区
每个专家输出完成后，在其消息下方显示操作面板：
- **确认按钮**：「✓ 确认进入下一阶段」—— 主色按钮，确认当前结果并推进到下一个状态
- **回退按钮**：「↩ 回退修改」—— 次色按钮，回退到上一状态重新生成
- **切换专家**：「切换到 XX 专家 ▼」—— 下拉菜单，手动选择任意专家进行补充分析
- **状态提示**：操作区上方显示当前状态说明，如「架构设计已完成，请确认后进入代码实现阶段」
#### 5.8.4 左侧会话列表
- 按更新时间倒序展示用户的所有专家对话会话
- 每个会话显示：标题（首条消息摘要）、最后更新时间、当前状态标签
- 状态标签：进行中 / 已完成 / 待确认
- 点击切换到对应会话，加载历史消息和状态
- 「+ 新建对话」按钮开启新会话
- 悬停会话项显示删除按钮
#### 5.8.5 中间对话区
- **用户消息**：右侧气泡，浅色背景
- **专家消息**：左侧卡片，每个专家一个独立卡片
- **专家卡片样式**：顶部专家头像 + 名称 + 角色标识 + 迭代轮次标签 + 切换专家下拉
- **状态色条**：左侧色条标识当前所属状态/角色颜色
- **Markdown 渲染**：专家输出内容以 Markdown 格式渲染，支持标题、列表、代码块等
- **代码高亮**：代码块使用 Prism.js 或 highlight.js 进行语法高亮
- **代码复制**：每个代码块右上角提供「复制」按钮
- **加载状态**：等待专家输出时显示「正在思考...」动画
#### 5.8.6 底部输入框
- 多行文本输入框，支持 Shift+Enter 换行，Enter 发送
- 「发送」按钮（主色填充，深绿色）
- 知识库选择下拉框（可选，选择后对话会接入知识库上下文）
- 附件按钮（MVP暂不支持，预留UI位置）
- 状态暂停时输入框可用，可补充说明后手动触发专家
#### 5.8.7 验收标准配置入口（Step 2 预留）
> **📌 Step 2 预留功能**
>
> 页面右上角设置「验收标准」配置按钮，MVP 阶段灰显并标注「即将上线」。Step 2 将支持配置质量验收标准，由 Evaluator 节点自动评估并触发 Loop 迭代。
#### 5.8.8 Markdown 渲染与代码高亮
- **Markdown 解析**：使用 `react-markdown` 库
- **代码高亮**：使用 `react-syntax-highlighter` + Prism 风格
- **支持语法**：python、javascript、typescript、bash、json、sql、html、css 等
- **数学公式**：MVP 暂不支持，后续可集成 KaTeX
- **安全考虑**：开启 sanitize 防止 XSS 攻击
### 5.9 状态管理设计
src/store/techExperts.ts
```
import { create } from 'zustand'
interface Expert {
  role: string
  name: string
  icon: string
  color: string
  description: string
}
interface ExpertMessage {
  id?: number
  role: 'user' | 'assistant' | 'system'
  expert_role?: string
  expert_name?: string
  expert_icon?: string
  expert_color?: string
  state_label?: string       // 所属状态节点
  iteration?: number         // 所属迭代轮次
  content: string
  metadata?: Record<string, any>
  createdAt?: string
}
interface Session {
  id: number
  title: string
  status: 'active' | 'completed' | 'error'
  current_state: string      // 当前状态节点
  iteration_count: number    // 当前迭代轮次
  max_iterations: number     // 最大迭代轮次
  updatedAt: string
}
// 状态机状态
interface StateMachineState {
  currentState: string       // 当前状态：idle/arch_design/code_impl/code_review/testing/done
  iteration: number          // 当前迭代轮次
  isPaused: boolean          // 是否暂停等待人工介入
  canConfirm: boolean        // 是否可确认进入下一阶段
  canRollback: boolean       // 是否可回退
  availableExperts: Expert[] // 可切换的专家列表
  stateHistory: Array<{      // 状态转移历史
    from_state: string
    to_state: string
    transition_type: string
    triggered_by: string
    iteration: number
    time: string
  }>
}
interface TechExpertsState {
  // 专家列表
  experts: Expert[]
  // 会话
  sessions: Session[]
  currentSessionId: number | null
  sessionsLoading: boolean
  // 消息
  messages: ExpertMessage[]
  messagesLoading: boolean
  // 状态机
  stateMachine: StateMachineState
  // 对话状态
  isChatting: boolean
  // Actions
  fetchExperts: () => Promise<void>
  fetchSessions: () => Promise<void>
  createSession: (title?: string, kbId?: number) => Promise<number>
  deleteSession: (id: number) => Promise<void>
  setCurrentSession: (id: number) => void
  fetchMessages: (sessionId: number) => Promise<void>
  fetchState: (sessionId: number) => Promise<void>
  // 状态控制
  confirmState: () => Promise<void>    // 确认进入下一阶段
  rollbackState: () => Promise<void>   // 回退修改
  switchExpert: (role: string, instruction?: string) => Promise<void>  // 手动切换专家
  // SSE 对话
  startChat: (message: string, kbId?: number, sessionId?: number) => Promise<void>
  stopChat: () => void
}
export const useTechExpertsStore = create<TechExpertsState>((set, get) => ({
  // ... state & actions
}))
```
## 06 实现步骤与里程碑
### 6.1 开发环境搭建
#### 6.1.1 后端环境
后端环境准备步骤
```
# 1. 安装 Python 3.10+
python3 --version  # 需 >= 3.10
# 2. 创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
# 3. 安装依赖
pip install -r requirements.txt
# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入数据库连接、MiniMax API Key 等
# 5. 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 6. 验证
curl http://localhost:8000/docs
# 应能打开 Swagger UI 文档页面
```
requirements.txt 核心依赖
```
# Web 框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
# 数据库
SQLAlchemy==2.0.23
PyMySQL==1.1.0
cryptography==41.0.7
# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
# 大模型
openai==1.3.7
httpx==0.25.2
# 向量数据库
chromadb==0.4.18
# 文档解析
pypdf==3.17.1
python-docx==1.1.0
# 工具库
python-dotenv==1.0.0
```
#### 6.1.2 前端环境
前端环境准备步骤
```
# 1. 安装 Node.js 18+
node --version  # 需 >= 18.0.0
# 2. 安装依赖
cd frontend
npm install
# 3. 启动开发服务器
npm run dev
# 4. 验证
# 浏览器访问 http://localhost:5173
```
package.json 核心依赖
```
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16"
  }
}
```
#### 6.1.3 数据库环境
MySQL 数据库初始化
```
# 1. 连接 MySQL
mysql -u root -p
# 2. 创建数据库
CREATE DATABASE qingping CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# 3. 创建用户（可选）
CREATE USER 'qingping'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON qingping.* TO 'qingping'@'localhost';
FLUSH PRIVILEGES;
# 4. 表结构由应用启动时自动创建（SQLAlchemy create_all）
# 无需手动建表
```
### 6.2 阶段一：基础框架（3天）
**Day 1：项目初始化与配置**（第 1 天）
  - 创建后端 FastAPI 项目骨架，搭建目录结构
  - 实现 Pydantic Settings 配置管理，编写 .env.example
  - 集成 SQLAlchemy + MySQL，实现数据库连接与会话管理
  - 实现 PluginManager 插件管理器骨架（自动发现 + 路由注册）
  - 创建前端 React + Vite + TypeScript 项目
  - 配置 Tailwind CSS，搭建基础布局组件
**Day 2：认证系统与用户模块**（第 2 天）
  - 实现 JWT 认证（token 签发、验证、依赖注入）
  - 实现密码哈希（bcrypt）
  - 创建用户插件：User 模型 + 用户 CRUD API
  - 实现注册、登录接口
  - 实现统一响应格式与异常处理器
  - 前端：实现登录/注册页面 + AuthStore 状态管理
**Day 3：插件体系完善与大模型封装**（第 3 天）
  - 完善 PluginManager：数据表自动创建、菜单收集
  - 实现 CORS 中间件、请求日志中间件
  - 封装 MiniMax LLM 服务（对话 + 流式对话 + 嵌入）
  - 实现 RAG 服务基类（ChromaDB 封装）
  - 实现 Agent 工作流基类
  - 前端：实现 Layout 布局 + 动态菜单 + 路由守卫
> **✅ 阶段一验收标准**
>
> 后端服务可正常启动，Swagger UI 可访问 用户注册/登录流程完整，JWT 认证有效 插件能被自动发现并注册路由和数据表 前端页面可正常访问，路由跳转正常 MiniMax API 调用测试通过
### 6.3 阶段二：知识库模块（4天）
**Day 4：数据模型与基础 CRUD**（第 4 天）
  - 设计并实现 KnowledgeBase、Document 数据模型
  - 实现知识库 CRUD API（列表、创建、删除、更新）
  - 实现文档列表、文档详情、文档删除 API
  - 实现 Service 层业务逻辑（权限校验、用户隔离）
  - 注册知识库插件到 PluginManager
**Day 5：文档解析与分块**（第 5 天）
  - 实现文档上传接口（multipart/form-data）
  - 实现文件存储管理（保存到本地文件系统）
  - 实现 TXT、Markdown 解析器
  - 实现 PDF 解析器（pypdf）
  - 实现 Word 解析器（python-docx）
  - 实现文本分块算法（段落+句子+重叠策略）
  - 实现后台异步处理（BackgroundTasks）
**Day 6：向量化与 RAG 检索**（第 6 天）
  - 集成 MiniMax Embedding API（embo-01 模型）
  - 完善 RAG 服务：添加文档、检索、删除
  - 实现文档完整处理流水线（上传→解析→分块→向量化→存储）
  - 实现知识库语义检索 API
  - 实现相似度阈值过滤
  - 实现文档删除时同步删除向量数据
**Day 7：知识库前端页面**（第 7 天）
  - 实现知识库列表侧边栏组件
  - 实现文档列表组件（状态标签、上传时间）
  - 实现文档上传功能（拖拽上传 + 进度显示）
  - 实现搜索功能（输入框 + 搜索结果列表）
  - 实现 KBStore 状态管理
  - 实现 API 请求封装（axios 拦截器 + Token 管理）
> **✅ 阶段二验收标准**
>
> 可创建/删除知识库，用户间数据隔离 支持上传 PDF/MD/TXT/DOCX 文档，后台自动处理 文档处理状态可追踪（pending → processing → ready/error） 语义检索返回相关结果，相似度排序正确 前端页面交互完整，用户体验流畅
### 6.4 阶段三：技术专家组模块（6天）
**Day 8：专家角色与数据模型**（第 8 天）
  - 定义四大专家角色（架构师/程序员/审查员/测试工程师）的 System Prompt
  - 实现 ExpertAgent 基类与各专家 Agent
  - 设计并实现 ExpertSession、ExpertMessage 数据模型
  - 设计并实现 ExpertStateTransition 状态转移历史表
  - 实现会话 CRUD API（列表、创建、删除、详情）
  - 实现消息列表 API
**Day 9：状态机引擎**（第 9 天）
  - 实现 StateMachine 状态机基类（状态定义、转移规则、事件触发）
  - 定义 6 个状态节点：idle / arch_design / code_impl / code_review / testing / done
  - 实现状态转移逻辑：自动转移、确认转移、回退转移、手动切换
  - 实现状态转移历史记录（ExpertStateTransition 写入）
  - 实现迭代计数与 max_iterations 终止条件
  - 实现 TechExpertStateMachine 技术专家状态机
**Day 10：状态控制 API 与 SSE 流式输出**（第 10 天）
  - 实现状态获取 API：GET /sessions/{id}/state
  - 实现状态确认 API：POST /sessions/{id}/confirm-state
  - 实现状态回退 API：POST /sessions/{id}/rollback
  - 实现手动切换专家 API：POST /sessions/{id}/switch-expert
  - 实现 SSE 流式对话接口（/chat）
  - 定义 SSE 事件格式（state_enter / state_pause / state_transition / expert_output / complete / error）
**Day 11：RAG 接入与消息持久化**（第 11 天）
  - 实现知识库 RAG 接入（检索 → 上下文组装 → Prompt 注入）
  - 实现对话消息持久化（异步保存到数据库）
  - 实现会话状态更新（current_state、iteration_count、status）
  - 实现各专家节点的 Prompt 组装（含上下文注入、迭代历史）
  - 实现状态机执行结果的异步生成器模式
  - 预留 acceptance_criteria 字段与 Evaluator 扩展接口
**Day 12：前端对话页面与状态进度条**（第 12 天）
  - 实现会话列表侧边栏组件（含状态标签）
  - 实现顶部状态进度条组件（架构设计 → 代码实现 → 代码审查 → 测试验证）
  - 实现迭代轮次指示器
  - 实现对话消息展示区（用户消息气泡 + 专家卡片 + 迭代标签）
  - 实现 Markdown 渲染 + 代码高亮
  - 实现 SSE 前端处理逻辑（fetch + ReadableStream）
  - 实现输入框组件（多行输入 + 发送按钮 + 知识库选择）
**Day 13：人工介入交互与状态管理**（第 13 天）
  - 实现人工介入操作面板（确认按钮 / 回退按钮 / 切换专家下拉）
  - 实现手动切换专家交互（下拉选择 + 确认对话框）
  - 实现 TechExpertsStore 完整状态管理（含 StateMachineState）
  - 实现状态转移动画与加载效果
  - 实现对话历史加载（进入会话加载历史消息与状态）
  - 实现新建对话、删除会话功能
  - 预留验收标准配置入口（灰显 + 即将上线提示）
  - 联调测试：知识库 + 技术专家组 RAG 联动
> **✅ 阶段三验收标准**
>
> 状态机正常工作：可自动进入首状态、支持确认/回退/手动切换 四个工作状态（架构设计/代码实现/代码审查/测试验证）输出内容符合角色定位 SSE 流式输出正常，前端实时展示状态变化与专家输出 顶部状态进度条正确显示当前阶段，已完成状态打勾 人工介入操作面板功能完整：确认进入下一阶段、回退修改、切换专家 迭代计数正确，达到 max_iterations 时正确处理 对话历史完整保存，多会话管理正常 接入知识库后，专家回答能引用知识库内容 Markdown 渲染与代码高亮显示正确
### 6.5 阶段四：联调与测试（2天）
**Day 13：全链路联调**（第 13 天）
  - 前后端全链路联调（注册 → 登录 → 知识库 → 技术专家对话）
  - 修复联调中发现的 Bug 和接口不一致问题
  - 优化错误处理和用户提示
  - 边界场景测试（大文件、长文本、网络异常等）
  - 性能初步评估（接口响应时间、并发能力）
**Day 14：测试与修复**（第 14 天）
  - 编写核心模块单元测试（认证、知识库服务、工作流）
  - 执行功能测试用例（详见第 7 章）
  - 修复测试发现的问题
  - 代码 Review 与重构优化
  - 编写 README 和部署文档
### 6.6 阶段五：部署上线（1天）
**Day 15：生产环境部署**（第 15 天）
  - 云服务器环境准备（Ubuntu 22.04 + MySQL 8.0）
  - 后端部署（虚拟环境 + Systemd 服务）
  - 前端部署（构建 + Nginx 配置）
  - 域名解析与 HTTPS 配置（Let's Encrypt）
  - 生产环境冒烟测试
  - 备份策略配置（数据库定时备份）
> **📅 总工期**
>
> MVP 版本总开发周期：**16 个工作日**（约 3 周+1 天）。其中：基础框架 3 天 + 知识库 4 天 + 技术专家组 6 天 + 联调测试 2 天 + 部署上线 1 天。
## 07 测试方案
### 7.1 功能测试用例清单
#### 7.1.1 用户系统测试用例
| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- |
| US-001 | 正常注册 | 用户名未被使用 | 输入用户名+密码 → 点击注册 | 注册成功，返回 Token，自动登录 | P0 |
| US-002 | 用户名重复注册 | 用户名已存在 | 输入已存在的用户名 → 点击注册 | 返回 409 错误，提示用户名已存在 | P0 |
| US-003 | 空用户名注册 | - | 用户名为空 → 点击注册 | 返回 400 错误，提示用户名不能为空 | P1 |
| US-004 | 密码过短注册 | - | 密码少于 6 位 → 点击注册 | 返回 400 错误，提示密码长度不足 | P1 |
| US-005 | 正常登录 | 用户已注册 | 输入正确用户名密码 → 点击登录 | 登录成功，返回 Token 和用户信息 | P0 |
| US-006 | 密码错误登录 | 用户已注册 | 输入错误密码 → 点击登录 | 返回 401 错误，提示用户名或密码错误 | P0 |
| US-007 | Token 验证 | 用户已登录 | 携带有效 Token 访问需认证接口 | 正常返回数据 | P0 |
| US-008 | Token 过期 | Token 已过期 | 携带过期 Token 访问需认证接口 | 返回 401 错误，提示重新登录 | P0 |
| US-009 | 未认证访问 | 未登录 | 不携带 Token 访问需认证接口 | 返回 401 错误 | P0 |
#### 7.1.2 知识库测试用例
| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- |
| KB-001 | 创建知识库 | 已登录 | 输入知识库名称+描述 → 提交 | 创建成功，列表中显示新知识库 | P0 |
| KB-002 | 知识库列表 | 已登录，有多个知识库 | 进入知识库页面 | 显示当前用户所有知识库 | P0 |
| KB-003 | 删除知识库 | 已登录，有知识库 | 点击删除 → 确认 | 知识库及其所有文档被删除，向量数据同步删除 | P0 |
| KB-004 | 用户数据隔离 | 两个用户各有知识库 | 用户A登录查看知识库列表 | 只能看到用户A的知识库，看不到用户B的 | P0 |
| KB-005 | 上传 TXT 文档 | 已登录，有知识库 | 选择 .txt 文件上传 | 上传成功，状态变为 processing → ready | P0 |
| KB-006 | 上传 Markdown 文档 | 已登录，有知识库 | 选择 .md 文件上传 | 上传成功，正确解析内容，状态变为 ready | P0 |
| KB-007 | 上传 PDF 文档 | 已登录，有知识库 | 选择 .pdf 文件上传 | 上传成功，正确提取文本，状态变为 ready | P0 |
| KB-008 | 上传 Word 文档 | 已登录，有知识库 | 选择 .docx 文件上传 | 上传成功，正确提取文本，状态变为 ready | P1 |
| KB-009 | 上传超大文件 | 已登录，有知识库 | 上传超过 50MB 的文件 | 返回 413 错误，提示文件过大 | P1 |
| KB-010 | 上传不支持格式 | 已登录，有知识库 | 上传 .exe 文件 | 返回 400 错误，提示不支持的文件类型 | P1 |
| KB-011 | 语义检索 | 知识库中有就绪文档 | 输入查询内容 → 搜索 | 返回相关文档片段，按相似度排序 | P0 |
| KB-012 | 空查询搜索 | 已登录，有知识库 | 搜索内容为空 | 返回 400 错误，提示查询内容不能为空 | P1 |
| KB-013 | 删除文档 | 知识库中有文档 | 点击删除文档 → 确认 | 文档被删除，向量数据同步删除 | P0 |
| KB-014 | 重新处理文档 | 文档处理失败 | 点击重新处理 | 状态变为 processing，重新走处理流水线 | P1 |
#### 7.1.3 技术专家组测试用例
| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- |
| TE-001 | 新建对话 | 已登录 | 输入问题 → 发送 | 创建新会话，四位专家依次输出，最后完成 | P0 |
| TE-002 | 会话列表 | 有历史对话 | 进入技术专家组页面 | 显示所有历史会话，按时间倒序 | P0 |
| TE-003 | 查看历史消息 | 有历史对话 | 点击历史会话 | 加载并显示该会话的所有消息 | P0 |
| TE-004 | 删除会话 | 有历史对话 | 点击删除会话 → 确认 | 会话及其所有消息被删除 | P0 |
| TE-005 | SSE 流式输出 | 已登录 | 发送消息 | SSE 连接建立，逐步接收各专家输出 | P0 |
| TE-006 | 四专家顺序执行 | 已登录 | 发送一条技术问题 | 架构师→程序员→审查员→测试工程师依次输出 | P0 |
| TE-007 | 专家角色符合定位 | 已登录 | 发送一条技术问题 | 各专家输出内容符合其角色职责描述 | P1 |
| TE-008 | 知识库 RAG 接入 | 有就绪的知识库 | 选择知识库 → 发送相关问题 | 专家回答引用了知识库中的内容 | P0 |
| TE-009 | Markdown 渲染 | 有对话历史 | 查看专家输出 | 标题、列表、代码块等正确渲染 | P0 |
| TE-010 | 代码高亮 | 专家输出包含代码 | 查看代码块 | 代码语法高亮显示正确 | P1 |
| TE-011 | 代码复制 | 专家输出包含代码 | 点击代码块复制按钮 | 代码内容复制到剪贴板 | P2 |
| TE-012 | 对话中网络异常 | 已登录 | 对话过程中断网 | 显示错误提示，可重试 | P1 |
| TE-013 | 大模型调用失败 | MiniMax API 不可用 | 发送消息 | 返回错误事件，提示大模型调用失败 | P1 |
| TE-014 | 空消息发送 | 已登录 | 消息为空 → 点击发送 | 按钮禁用或提示消息不能为空 | P2 |
### 7.2 接口测试方案
#### 7.2.1 测试工具
- **自动化测试**：pytest + httpx（FastAPI 官方推荐）
- **手动测试**：Swagger UI（FastAPI 自动生成）/ Postman
- **SSE 测试**：curl -N 或 Postman SSE 预览
#### 7.2.2 测试策略
1. **单元测试**：Service 层核心逻辑，Mock 数据库和外部 API
2. **集成测试**：API 层端到端测试，使用测试数据库
3. **冒烟测试**：核心路径快速验证（登录→建库→上传→对话）
pytest 测试示例 - 知识库 API
```
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.core.database import Base, get_db
# 测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
def test_create_knowledge_base(client):
    # 先注册登录获取 token
    client.post("/api/v1/user/register", json={
        "username": "testuser", "password": "testpass123"
    })
    resp = client.post("/api/v1/user/login", json={
        "username": "testuser", "password": "testpass123"
    })
    token = resp.json()["data"]["access_token"]
    # 创建知识库
    resp = client.post(
        "/api/v1/knowledge_base",
        json={"name": "测试知识库", "description": "测试用"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "测试知识库"
    assert "id" in data
```
### 7.3 性能测试指标
| 指标 | 测试场景 | MVP目标值 | 测试工具 |
| --- | --- | --- | --- |
| 接口响应时间 | 知识库列表/创建/删除等简单接口 | P95 ≤ 500ms | wrk / ab |
| 文档上传响应 | 上传 1MB 文档（仅上传，不含处理） | P95 ≤ 2s | curl / 脚本 |
| 文档处理耗时 | 处理 10 页 PDF 文档（解析+分块+向量化） | ≤ 30s | 日志统计 |
| 检索响应时间 | 1000 个向量块的知识库中检索 | P95 ≤ 1s | wrk / ab |
| SSE 首字延迟 | 从发送请求到收到第一个 expert_output | ≤ 10s | 手动计时 |
| 并发用户数 | 同时 50 个用户在线操作 | 系统稳定，无错误 | Locust / JMeter |
| 前端首屏加载 | 桌面端 Chrome，宽带网络 | ≤ 2s | Lighthouse |
| 数据库连接池 | 峰值并发请求 | 连接池不耗尽 | MySQL 监控 |
## 08 部署方案
### 8.1 服务器准备
#### 8.1.1 配置清单
| 资源 | 最低配置 | 推荐配置 | 说明 |
| --- | --- | --- | --- |
| CPU | 2 核 | 4 核 | Python 异步 + 向量化计算需要一定算力 |
| 内存 | 4 GB | 8 GB | ChromaDB + MySQL + Python 进程内存占用 |
| 系统盘 | 40 GB SSD | 80 GB SSD | 系统 + 应用 + 日志 |
| 数据盘 | - | 100 GB SSD | 上传文件 + 向量数据 + 数据库 |
| 操作系统 | Ubuntu 22.04 LTS | 稳定、社区支持好 |
| 带宽 | 5 Mbps | 10 Mbps | 文件上传下载带宽 |
#### 8.1.2 安全组配置
| 方向 | 协议 | 端口 | 源地址 | 说明 |
| --- | --- | --- | --- | --- |
| 入站 | TCP | 22 | 0.0.0.0/0（建议限制为运维IP） | SSH 远程登录 |
| 入站 | TCP | 80 | 0.0.0.0/0 | HTTP 访问 |
| 入站 | TCP | 443 | 0.0.0.0/0 | HTTPS 访问 |
| 入站 | TCP | 8000 | 127.0.0.1 | 后端服务（仅本机访问，Nginx 反向代理） |
| 出站 | ALL | ALL | 0.0.0.0/0 | 访问外部 API（MiniMax） |
### 8.2 MySQL安装与配置
MySQL 8.0 安装步骤
```
# 1. 更新包列表
sudo apt update
# 2. 安装 MySQL 8.0
sudo apt install -y mysql-server
# 3. 启动并设置开机自启
sudo systemctl start mysql
sudo systemctl enable mysql
# 4. 安全配置
sudo mysql_secure_installation
# 按提示设置 root 密码，移除匿名用户，禁止远程 root 登录
# 5. 创建数据库和用户
sudo mysql -u root -p
# 进入 MySQL 后执行：
# CREATE DATABASE qingping CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# CREATE USER 'qingping'@'localhost' IDENTIFIED BY 'StrongPassword123!';
# GRANT ALL PRIVILEGES ON qingping.* TO 'qingping'@'localhost';
# FLUSH PRIVILEGES;
# EXIT;
# 6. 配置 MySQL 优化（编辑 /etc/mysql/mysql.conf.d/mysqld.cnf）
# [mysqld]
# max_connections = 200
# innodb_buffer_pool_size = 2G  # 约为内存的 50-70%
# innodb_log_file_size = 256M
# character-set-server = utf8mb4
# collation-server = utf8mb4_unicode_ci
# 7. 重启 MySQL 使配置生效
sudo systemctl restart mysql
```
### 8.3 后端部署
#### 8.3.1 部署方式
采用 **Python 虚拟环境 + Systemd 服务** 方式部署，简单可靠，适合 MVP 阶段。
后端部署步骤
```
# 1. 创建应用目录
sudo mkdir -p /opt/qingping/backend
sudo chown -R $USER:$USER /opt/qingping
# 2. 上传代码（git clone 或 scp）
cd /opt/qingping/backend
# git clone  .
# 或手动上传文件
# 3. 安装 Python 3.10 和依赖
sudo apt install -y python3.10 python3.10-venv python3-pip
# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
# 5. 安装 Python 依赖
pip install -r requirements.txt
pip install uvicorn gunicorn
# 6. 创建数据目录
mkdir -p data/uploads data/chroma
# 7. 配置环境变量
cp .env.example .env
nano .env
# 填入生产环境配置（数据库密码、API Key 等）
# 8. 初始化数据库表（首次启动自动创建，也可手动触发）
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```
#### 8.3.2 Systemd 服务配置
/etc/systemd/system/qingping-backend.service
```
[Unit]
Description=Qingping Backend Service
After=network.target mysql.service
[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/qingping/backend
Environment="PATH=/opt/qingping/backend/venv/bin"
ExecStart=/opt/qingping/backend/venv/bin/gunicorn \
    -w 4 -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/qingping/access.log \
    --error-logfile /var/log/qingping/error.log \
    main:app
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
```
服务管理命令
```
# 创建日志目录
sudo mkdir -p /var/log/qingping
sudo chown www-data:www-data /var/log/qingping
# 启动服务
sudo systemctl start qingping-backend
# 设置开机自启
sudo systemctl enable qingping-backend
# 查看状态
sudo systemctl status qingping-backend
# 重启服务
sudo systemctl restart qingping-backend
# 查看日志
sudo journalctl -u qingping-backend -f
```
### 8.4 前端部署
前端构建与部署
```
# 1. 本地构建（或在服务器上构建）
cd frontend
npm install
npm run build
# 构建产物在 dist/ 目录
# 2. 上传到服务器
scp -r dist/* user@server:/var/www/qingping/
# 3. 服务器安装 Nginx
sudo apt install -y nginx
# 4. 创建站点目录
sudo mkdir -p /var/www/qingping
sudo chown -R www-data:www-data /var/www/qingping
```
#### Nginx 配置
/etc/nginx/sites-available/qingping
```
server {
    listen 80;
    server_name your-domain.com;
    # 前端静态文件
    location / {
        root /var/www/qingping;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由支持
    }
    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1024;
}
```
启用站点配置
```
# 启用站点
sudo ln -s /etc/nginx/sites-available/qingping /etc/nginx/sites-enabled/
# 删除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default
# 测试配置
sudo nginx -t
# 重载 Nginx
sudo systemctl reload nginx
```
### 8.5 域名与HTTPS配置
Let's Encrypt 免费 SSL 证书
```
# 1. 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx
# 2. 申请证书并自动配置 Nginx
sudo certbot --nginx -d your-domain.com
# 3. 按提示输入邮箱和同意条款
# Certbot 会自动修改 Nginx 配置，添加 HTTPS 和重定向
# 4. 证书自动续期（Let's Encrypt 证书有效期 90 天）
# Certbot 会自动添加 systemd timer 进行续期
# 手动测试续期：
sudo certbot renew --dry-run
```
### 8.6 备份与监控
#### 8.6.1 数据库备份
/opt/qingping/scripts/backup.sh
```
#!/bin/bash
# 数据库每日备份脚本
BACKUP_DIR="/opt/qingping/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="qingping"
DB_USER="qingping"
DB_PASS="your_password"
# 创建备份目录
mkdir -p $BACKUP_DIR
# 备份数据库
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/${DB_NAME}_${DATE}.sql
# 压缩备份文件
gzip $BACKUP_DIR/${DB_NAME}_${DATE}.sql
# 保留最近 30 天的备份
find $BACKUP_DIR -name "${DB_NAME}_*.sql.gz" -mtime +30 -delete
echo "Backup completed: ${DB_NAME}_${DATE}.sql.gz"
```
设置定时任务（crontab）
```
# 编辑 crontab
crontab -e
# 每天凌晨 2 点执行备份
0 2 * * * /opt/qingping/scripts/backup.sh >> /var/log/qingping/backup.log 2>&1
```
#### 8.6.2 文件备份
- **上传文件**：定期备份 `/opt/qingping/backend/data/uploads/` 目录
- **向量数据**：定期备份 `/opt/qingping/backend/data/chroma/` 目录
- **备份方式**：rsync 同步到对象存储或其他服务器
#### 8.6.3 基础监控
- **服务存活监控**：Systemd 自动重启 + 简单健康检查脚本
- **资源监控**：使用 htop、df 等工具查看 CPU/内存/磁盘
- **日志查看**：journalctl 查看系统日志，Nginx 访问日志
- **告警方式**：MVP 阶段可用简单脚本 + 邮件/钉钉通知
## 09 MiniMax集成指南
### 9.1 MiniMax账号注册与API Key获取
1. **注册账号**：访问 [MiniMax 官网](https://www.minimaxi.com)，使用手机号注册
2. **实名认证**：完成个人或企业实名认证
3. **获取 API Key**： 登录后进入「API 平台」→「API Keys」 点击「创建 API Key」，填写名称和描述 创建后立即复制保存（仅显示一次）
  - 登录后进入「API 平台」→「API Keys」
  - 点击「创建 API Key」，填写名称和描述
  - 创建后立即复制保存（仅显示一次）
4. **充值**：在「账户中心」→「充值」页面进行充值
> **⚠️ 安全注意**
>
> API Key 等同于账户密码，请勿提交到代码仓库或公开场合 生产环境使用环境变量注入，不要硬编码在代码中 建议定期轮换 API Key，可创建多个 Key 用于不同环境 设置合理的账户预警，避免超额消费
### 9.2 可用模型清单与选型建议
| 模型名称 | 类型 | 定位 | 上下文 | 适用场景 |
| --- | --- | --- | --- | --- |
| `abab6.5s-chat` | 对话模型 | 主力模型，速度与质量均衡 | 245K tokens | 日常对话、代码生成、知识库问答（推荐） |
| `abab6.5-chat` | 对话模型 | 高质量模型，更强的推理能力 | 245K tokens | 复杂推理、深度分析、架构设计 |
| `abab5.5-chat` | 对话模型 | 轻量模型，速度快成本低 | 128K tokens | 简单问答、文本处理、分类摘要 |
| `embo-01` | 嵌入模型 | 文本向量化 | - | 知识库向量检索、语义相似度计算 |
> **💡 MVP 选型建议**
>
> **对话模型**：`abab6.5s-chat` 作为主力模型，性价比最高，速度快，适合日常技术对话 **嵌入模型**：`embo-01` 作为知识库向量化模型，与 abab 系列模型语义对齐效果好 后续可根据实际使用效果考虑切换到更高质量的 `abab6.5-chat` 或增加模型选择功能
### 9.3 API调用示例
#### 9.3.1 对话补全（非流式）
Python - 对话 API 调用
```
import httpx
MINIMAX_API_KEY = "your-api-key"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
async def chat_completion(
    model: str = "abab6.5s-chat",
    messages: list[dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    """调用 MiniMax 对话补全 API"""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()
# 使用示例
async def main():
    result = await chat_completion(
        messages=[
            {"role": "system", "content": "你是一位专业的Python开发工程师。"},
            {"role": "user", "content": "用Python实现一个快速排序算法"},
        ]
    )
    print(result["choices"][0]["message"]["content"])
```
#### 9.3.2 流式对话
Python - SSE 流式对话
```
import httpx
import json
async def chat_completion_stream(
    model: str = "abab6.5s-chat",
    messages: list[dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
):
    """流式调用 MiniMax 对话 API，逐 token 返回"""
    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream(
            "POST",
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        pass
# 使用示例
async def main():
    async for token in chat_completion_stream(
        messages=[
            {"role": "user", "content": "写一首关于春天的诗"},
        ]
    ):
        print(token, end="", flush=True)
```
#### 9.3.3 文本嵌入
Python - 嵌入 API 调用
```
import httpx
async def create_embeddings(
    texts: list[str],
    model: str = "embo-01",
) -> list[list[float]]:
    """调用 MiniMax 嵌入 API，生成文本向量"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{MINIMAX_BASE_URL}/embeddings/create",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "texts": texts,
                "type": "db",  # "db" 用于存储, "query" 用于查询
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]
# 使用示例
async def main():
    embeddings = await create_embeddings([
        "你好，世界",
        "Hello, World",
    ])
    print(f"向量维度: {len(embeddings[0])}")
    print(f"向量数量: {len(embeddings)}")
```
### 9.4 费用估算
| 模型 | 输入价格 | 输出价格 | 单轮对话估算 | 日均100轮月费用 |
| --- | --- | --- | --- | --- |
| abab6.5s-chat | ¥0.015 / 1K tokens | ¥0.015 / 1K tokens | 约 ¥0.03（输入2K + 输出0，单专家） | 约 ¥90（4专家 × 100轮 × 30天） |
| abab6.5-chat | ¥0.03 / 1K tokens | ¥0.03 / 1K tokens | 约 ¥0.06（单专家） | 约 ¥180（4专家 × 100轮 × 30天） |
| abab5.5-chat | ¥0.003 / 1K tokens | ¥0.003 / 1K tokens | 约 ¥0.006（单专家） | 约 ¥18（4专家 × 100轮 × 30天） |
| embo-01（嵌入） | ¥0.005 / 1K tokens | 约 ¥0.0025/文档（500字） | 约 ¥1.5（100篇文档/天 × 30天） |
> **💰 MVP 费用预估**
>
> 按日均 100 轮技术专家对话 + 日均 10 篇文档上传估算： **对话费用**：4 专家 × 100 轮 × 30 天 × ¥0.03 ≈ **¥360/月** **嵌入费用**：10 篇 × 30 天 × ¥0.005 ≈ **¥1.5/月** **总计**：约 **¥360 - 400/月**（MVP 初期个人使用完全可承受）
### 9.5 错误处理与重试机制
#### 9.5.1 常见错误码
| HTTP状态码 | 错误类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 400 | InvalidRequestError | 请求参数错误 | 检查请求参数格式、模型名称等 |
| 401 | AuthenticationError | API Key 无效或过期 | 检查 API Key 是否正确，账户是否有效 |
| 403 | PermissionError | 权限不足 | 检查账户权限和模型访问权限 |
| 429 | RateLimitError | 请求频率超限 | 实现指数退避重试，降低请求频率 |
| 500 | InternalServerError | 服务器内部错误 | 重试 2-3 次，仍失败则上报 |
| 503 | ServiceUnavailable | 服务不可用 | 重试，间隔逐步增加 |
| 超时 | TimeoutError | 请求超时 | 设置合理超时时间，流式请求设置更长超时 |
#### 9.5.2 重试机制实现
带重试的 API 调用封装
```
import asyncio
import httpx
from typing import Callable, Any
class MiniMaxService:
    """MiniMax API 服务封装，含重试机制"""
    def __init__(self, api_key: str, base_url: str, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=120)
    async def chat_completion_with_retry(
        self, messages: list[dict], model: str = "abab6.5s-chat", **kwargs
    ) -> dict:
        """带重试的对话调用"""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await self._chat_completion(messages, model, **kwargs)
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code in (429, 500, 502, 503, 504):
                    # 可重试的错误，指数退避
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # 不可重试的错误，直接抛出
                    raise
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                continue
        # 重试耗尽
        raise last_exception
    async def _chat_completion(self, messages, model, **kwargs):
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, **kwargs},
        )
        resp.raise_for_status()
        return resp.json()
```
> **⚠️ 注意事项**
>
> 429（频率限制）错误一定要实现退避重试，避免被进一步限流。流式请求的重试需要特别处理，避免重复输出。建议在应用层实现 Token 消耗统计，便于成本监控。设置合理的超时时间，流式对话建议 300s 以上。生产环境建议使用 Sentry 等工具监控 API 错误率。
