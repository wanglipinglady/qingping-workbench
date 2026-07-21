"""技术专家组插件注册入口

通过 register() 函数将插件注册到 PluginManager。
"""

from app.core.plugin_manager import PluginInfo, PluginManager, MenuItem
from app.plugins.tech_experts.routes import router


def register(plugin_manager: PluginManager) -> None:
    """注册技术专家组插件

    Args:
        plugin_manager: 插件管理器实例
    """
    plugin_info = PluginInfo(
        name="tech_experts",
        description="状态图式协作 + 人工介入机制。架构师 + 程序员 + 审查员 + 测试工程师 四位一体，多智能体协同输出高质量技术方案。",
        version="0.1.0",
        routes=[router],
        menu_items=[
            MenuItem(
                key="tech-experts",
                label="技术专家组",
                icon="🧠",
                path="/tech-experts",
                order=20,
            )
        ],
        models_module="app.plugins.tech_experts.models",
    )
    plugin_manager.register_plugin(plugin_info)
