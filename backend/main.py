"""
青萍小台 MVP 后端启动入口
使用 uvicorn 启动 FastAPI 应用
"""
import uvicorn

from app.core.config import settings


def main():
    """主启动函数"""
    uvicorn.run(
        "app.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )


if __name__ == "__main__":
    main()
