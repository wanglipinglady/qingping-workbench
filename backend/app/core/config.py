"""
应用配置模块
使用 Pydantic BaseSettings 从环境变量和 .env 文件读取配置
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用全局配置"""

    # ========== 基础配置 ==========
    # 应用名称
    APP_NAME: str = Field(default="青萍小台", description="应用名称")
    # 应用版本
    APP_VERSION: str = Field(default="0.1.0", description="应用版本号")
    # 监听地址
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    # 监听端口（云服务器已占用8501、8000、3306、443、22、80，所以用8080）
    PORT: int = Field(default=8080, description="服务监听端口")
    # 是否开启调试模式
    DEBUG: bool = Field(default=False, description="调试模式开关")

    # ========== 数据库配置 ==========
    # 数据库连接 URL
    # 本地开发默认 SQLite（无需额外安装，开箱即用）
    # 生产部署请改为 MySQL，格式：
    #   mysql+pymysql://用户名:密码@主机:3306/数据库名?charset=utf8mb4
    # 示例：mysql+pymysql://root:yourpassword@localhost:3306/qingping?charset=utf8mb4
    DATABASE_URL: str = Field(
        default="sqlite:///./data/qingping.db",
        description="数据库连接 URL（支持 MySQL 和 SQLite）",
    )

    # ========== JWT 认证配置 ==========
    # JWT 密钥（生产环境请修改为强随机字符串）
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-please-change-this",
        description="JWT 签名密钥",
    )
    # JWT 签名算法
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 签名算法")
    # 访问令牌过期时间（分钟），默认 24 小时
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440, description="访问令牌过期时间（分钟）"
    )

    # ========== MiniMax API 配置 ==========
    # MiniMax API 密钥
    MINIMAX_API_KEY: str = Field(default="", description="MiniMax API 密钥")
    # MiniMax API 基础地址
    # 新版 API: https://api.minimaxi.com/v1  (API Key 以 sk-cp- 开头)
    # 旧版 API: https://api.minimax.chat/v1  (API Key 以 ab- 开头)
    MINIMAX_BASE_URL: str = Field(
        default="https://api.minimaxi.com/v1", description="MiniMax API 基础 URL"
    )
    # 对话模型名称
    MINIMAX_CHAT_MODEL: str = Field(
        default="MiniMax-M2.7-highspeed", description="MiniMax 对话模型名称"
    )
    # Embedding 模型名称
    MINIMAX_EMBEDDING_MODEL: str = Field(
        default="embo-01", description="MiniMax Embedding 模型名称"
    )

    # ========== ChromaDB 向量数据库配置 ==========
    # ChromaDB 持久化目录
    CHROMA_PERSIST_DIR: str = Field(
        default="./data/chroma", description="ChromaDB 持久化存储目录"
    )

    # 向量存储后端: "chromadb" (默认, 高性能但需要原生扩展) 或 "simple" (纯 Python, 跨平台兼容)
    VECTOR_STORE_BACKEND: str = Field(
        default="chromadb", description="向量存储后端: chromadb 或 simple"
    )

    # ========== 文件上传配置 ==========
    # 上传文件存储目录
    UPLOAD_DIR: str = Field(default="./uploads", description="文件上传存储目录")
    # 单个文件最大大小（MB）
    MAX_UPLOAD_SIZE: int = Field(default=50, description="单个文件最大上传大小（MB）")

    # ========== Obsidian 配置 ==========
    # Obsidian Vault 根路径（本地开发时指向你的知识库目录）
    OBSIDIAN_VAULT_PATH: str = Field(
        default="",
        description="Obsidian Vault 根路径，如 D:/obsidian/knowledge_base",
    )
    # Obsidian 同步时排除的目录（相对 Vault 根路径，逗号分隔）
    OBSIDIAN_EXCLUDE_DIRS: str = Field(
        default=".git,.obsidian,.trash,templates",
        description="Obsidian 同步排除目录（逗号分隔）",
    )
    # Obsidian 包含标签（只索引包含这些标签的笔记，空表示全部）
    OBSIDIAN_INCLUDE_TAGS: str = Field(
        default="",
        description="只索引包含指定标签的笔记（逗号分隔，空=全部）",
    )

    # ========== 学习日报定时任务配置 ==========
    # 是否启用每日定时生成学习日报
    DAILY_REPORT_ENABLED: bool = Field(
        default=True, description="是否启用每日定时生成学习日报"
    )
    # 触发小时（本地时区 24 小时制）
    DAILY_REPORT_HOUR: int = Field(
        default=22, ge=0, le=23, description="每日生成日报的小时（本地时区）"
    )
    # 触发分钟
    DAILY_REPORT_MINUTE: int = Field(
        default=0, ge=0, le=59, description="每日生成日报的分钟"
    )

    # ========== 日志配置 ==========
    # 日志级别: DEBUG / INFO / WARNING / ERROR
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    # 日志文件路径
    LOG_FILE: str = Field(default="./logs/app.log", description="日志文件路径")

    # ========== CORS 配置 ==========
    # 允许跨域的来源，多个用逗号分隔，如: "https://a.com,https://b.com"
    # 全部允许请写 "*"
    CORS_ORIGINS: str = Field(
        default="*", description="允许跨域请求的来源列表（逗号分隔）"
    )

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # 忽略 .env 中未在 Settings 定义的字段，避免启动报错
        extra = "ignore"


# 全局配置实例
settings = Settings()
