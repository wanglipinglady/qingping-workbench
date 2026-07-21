"""
微信公众号写作助手插件注册
将写作助手插件注册到插件管理器
"""
from app.core.plugin_manager import PluginManager, PluginInfo, MenuItem
from app.plugins.wechat_writer.routes import router


def register(plugin_manager: PluginManager) -> None:
    """
    注册微信公众号写作助手插件

    Args:
        plugin_manager: 插件管理器实例
    """
    plugin_info = PluginInfo(
        name="wechat_writer",
        description="微信公众号写作助手，基于状态机和多专家角色协作，从选题到成稿的全流程辅助",
        version="0.1.0",
        routes=[router],
        menu_items=[
            MenuItem(
                key="wechat-writer",
                label="公众号写作",
                icon="edit",
                path="/wechat-writer",
                order=20,
            ),
        ],
        models_module="app.plugins.wechat_writer.models",
    )
    plugin_manager.register_plugin(plugin_info)
