"""
知识库插件注册
将知识库插件注册到插件管理器
"""
from app.core.plugin_manager import PluginManager, PluginInfo, MenuItem
from app.plugins.knowledge_base.routes import router


def register(plugin_manager: PluginManager) -> None:
    """
    注册知识库插件

    Args:
        plugin_manager: 插件管理器实例
    """
    plugin_info = PluginInfo(
        name="knowledge_base",
        description="知识库插件，提供文档上传、向量化存储和语义搜索功能",
        version="0.1.0",
        routes=[router],
        menu_items=[
            MenuItem(
                key="knowledge-base",
                label="知识库",
                icon="book",
                path="/knowledge-bases",
                order=10,
            ),
        ],
        models_module="app.plugins.knowledge_base.models",
    )
    plugin_manager.register_plugin(plugin_info)
