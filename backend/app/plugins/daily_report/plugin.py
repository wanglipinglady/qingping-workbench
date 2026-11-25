"""
学习日报插件注册
"""
from app.core.plugin_manager import MenuItem, PluginInfo, PluginManager
from app.plugins.daily_report.routes import router


def register(plugin_manager: PluginManager) -> None:
    """注册学习日报插件"""
    plugin_info = PluginInfo(
        name="daily_report",
        description="学习日报插件，聚合当日剪藏与对话生成结构化日报",
        version="0.1.0",
        routes=[router],
        menu_items=[
            MenuItem(
                key="daily-report",
                label="学习日报",
                icon="calendar",
                path="/daily-reports",
                order=16,
            ),
        ],
        models_module="app.plugins.daily_report.models",
    )
    plugin_manager.register_plugin(plugin_info)
