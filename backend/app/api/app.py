"""
FastAPI 应用入口
创建并配置 FastAPI 应用实例
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers, unified_response
from app.core.plugin_manager import plugin_manager


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用

    Returns:
        配置好的 FastAPI 应用实例
    """
    # 创建 FastAPI 应用
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=f"{settings.APP_NAME} - MVP 后端 API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ========== 中间件 ==========

    # CORS 中间件
    # 把逗号分隔的字符串分割成列表
    origins = (
        settings.CORS_ORIGINS.split(",")
        if settings.CORS_ORIGINS and settings.CORS_ORIGINS != "*"
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========== 全局异常处理 ==========
    register_exception_handlers(app)

    # ========== 插件系统 ==========

    # 发现并加载插件
    plugin_manager.discover_plugins("app.plugins")

    # 挂载插件路由
    plugin_manager.mount_routes(app, prefix="/api")

    # ========== 基础路由 ==========

    @app.get("/api/health", summary="健康检查", tags=["系统"])
    async def health_check():
        """服务健康检查接口"""
        return unified_response(
            data={
                "status": "ok",
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
            }
        )

    @app.get("/api/plugins", summary="获取插件列表", tags=["系统"])
    async def get_plugins():
        """获取所有已加载的插件信息和菜单项"""
        plugins = plugin_manager.get_all_plugins()
        menus = plugin_manager.get_all_menu_items()

        plugin_list = []
        for p in plugins:
            plugin_list.append({
                "name": p.name,
                "description": p.description,
                "version": p.version,
            })

        menu_list = []
        for m in menus:
            menu_list.append({
                "key": m.key,
                "label": m.label,
                "icon": m.icon,
                "path": m.path,
                "order": m.order,
            })

        return unified_response(
            data={
                "plugins": plugin_list,
                "menus": menu_list,
            }
        )

    # ========== 启动事件 ==========

    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行"""
        print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")
        print(f"[启动] 监听地址: {settings.HOST}:{settings.PORT}")
        print(f"[启动] 调试模式: {'开启' if settings.DEBUG else '关闭'}")

        # 初始化数据库（创建表）
        try:
            init_db()
            print("[启动] 数据库初始化完成")
        except Exception as e:
            print(f"[警告] 数据库初始化失败: {e}")
            print("[提示] 请检查数据库连接配置，或手动执行 sql/init.sql")

        # 打印插件信息
        plugins = plugin_manager.get_all_plugins()
        print(f"[启动] 已加载 {len(plugins)} 个插件:")
        for p in plugins:
            print(f"       - {p.name} v{p.version}: {p.description}")

        print("[启动] 服务启动完成！")
        print(f"[启动] API 文档: http://{settings.HOST}:{settings.PORT}/docs")

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行"""
        print(f"[关闭] {settings.APP_NAME} 正在关闭...")

    return app


# 全局应用实例（供 uvicorn 直接使用）
app = create_app()
