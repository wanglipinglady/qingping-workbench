"""
数据库模块
使用 SQLAlchemy 2.0 风格进行数据库操作
同时支持 MySQL（生产）和 SQLite（本地开发）
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

from app.core.config import settings

# 判断是否使用 SQLite
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# 数据库引擎配置（根据数据库类型自适应）
_engine_args = {
    "echo": settings.DEBUG,  # 调试模式下输出 SQL
}
if _is_sqlite:
    # SQLite 需要加上 check_same_thread=False
    _engine_args["connect_args"] = {"check_same_thread": False}
else:
    # MySQL 连接池配置
    _engine_args.update({
        "pool_pre_ping": True,    # 连接前检测连接是否有效
        "pool_size": 10,          # 连接池大小
        "max_overflow": 20,       # 最大溢出连接数
        "pool_recycle": 3600,     # 连接回收时间（秒）
    })

engine = create_engine(settings.DATABASE_URL, **_engine_args)

# 会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# 声明式基类，所有模型继承此类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数
    用于 FastAPI 依赖注入，自动管理会话生命周期
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库：创建所有表 + 初始化默认数据
    在应用启动时调用
    """
    # 导入所有模型，确保 Base 能识别到它们
    # 注意：必须在调用 create_all 之前导入模型
    from app.plugins.user import models as user_models  # noqa: F401
    from app.plugins.knowledge_base import models as kb_models  # noqa: F401
    from app.plugins.tech_experts import models as tech_models  # noqa: F401
    from app.plugins.wechat_writer import models as wechat_models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # 初始化默认管理员用户
    _init_default_user()


def _init_default_user() -> None:
    """初始化默认管理员用户（如果不存在的话）"""
    from app.plugins.user.models import User
    from app.core.auth import hash_password

    db = SessionLocal()
    try:
        # 检查 admin 用户是否已存在
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            return

        # 创建默认 admin 用户
        admin = User(
            username="admin",
            email="admin@qingping.local",
            hashed_password=hash_password("admin123"),
        )
        db.add(admin)
        db.commit()
        print("✅ 默认管理员用户已创建: admin / admin123")
    except Exception as e:
        print(f"⚠️  初始化默认用户失败（可能已存在）: {e}")
        db.rollback()
    finally:
        db.close()
