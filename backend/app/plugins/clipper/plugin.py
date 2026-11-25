"""
选材剪藏插件注册
"""
from app.core.plugin_manager import MenuItem, PluginInfo, PluginManager
from app.plugins.clipper.routes import router


def register(plugin_manager: PluginManager) -> None:
    """注册选材剪藏插件"""
    plugin_info = PluginInfo(
        name="clipper",
        description="选材剪藏插件，抓取网页正文并自动归档到知识库",
        version="0.1.0",
        routes=[router],
        menu_items=[
            MenuItem(
                key="clipper",
                label="选材剪藏",
                icon="scissors",
                path="/clipper",
                order=15,
            ),
        ],
        models_module="app.plugins.clipper.models",
    )
    plugin_manager.register_plugin(plugin_info)
