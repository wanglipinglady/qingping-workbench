"""
用户插件注册
将用户插件注册到插件管理器
"""
from app.core.plugin_manager import PluginManager, PluginInfo, MenuItem
from app.plugins.user.routes import router


def register(plugin_manager: PluginManager) -> None:
    """
    注册用户插件

    Args:
        plugin_manager: 插件管理器实例
    """
    plugin_info = PluginInfo(
        name="user",
        description="用户管理插件，提供用户注册、登录、信息维护等功能",
        version="0.1.0",
        routes=[router],
        menu_items=[
            MenuItem(
                key="user-profile",
                label="个人中心",
                icon="user",
                path="/profile",
                order=100,
            ),
        ],
        models_module="app.plugins.user.models",
    )
    plugin_manager.register_plugin(plugin_info)
