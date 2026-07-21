"""
插件管理器
实现插件的自动发现、注册和路由挂载
"""
import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any

from fastapi import APIRouter, FastAPI


@dataclass
class MenuItem:
    """菜单项数据类"""
    # 菜单键名（唯一标识）
    key: str
    # 菜单显示名称
    label: str
    # 菜单图标（可选）
    icon: Optional[str] = None
    # 菜单路径（前端路由）
    path: Optional[str] = None
    # 子菜单
    children: List["MenuItem"] = field(default_factory=list)
    # 排序
    order: int = 0


@dataclass
class PluginInfo:
    """插件信息数据类"""
    # 插件名称（唯一标识）
    name: str
    # 插件描述
    description: str = ""
    # 插件版本
    version: str = "0.1.0"
    # 插件路由列表
    routes: List[APIRouter] = field(default_factory=list)
    # 插件菜单项
    menu_items: List[MenuItem] = field(default_factory=list)
    # 插件模型模块名（用于数据库建表时导入）
    models_module: Optional[str] = None
    # 插件元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginManager:
    """
    插件管理器（单例模式）
    负责插件的注册、发现和管理
    """

    _instance: Optional["PluginManager"] = None

    def __new__(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: Dict[str, PluginInfo] = {}
        return cls._instance

    def __init__(self) -> None:
        # 确保初始化只执行一次
        if not hasattr(self, "_plugins"):
            self._plugins: Dict[str, PluginInfo] = {}

    def register_plugin(self, plugin_info: PluginInfo) -> None:
        """
        注册插件

        Args:
            plugin_info: 插件信息
        """
        if plugin_info.name in self._plugins:
            print(f"[警告] 插件 {plugin_info.name} 已存在，将被覆盖")
        self._plugins[plugin_info.name] = plugin_info
        print(f"[插件] 已注册插件: {plugin_info.name} v{plugin_info.version}")

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """
        根据名称获取插件

        Args:
            name: 插件名称

        Returns:
            插件信息，不存在则返回 None
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[PluginInfo]:
        """
        获取所有已注册的插件

        Returns:
            插件信息列表
        """
        return list(self._plugins.values())

    def get_all_menu_items(self) -> List[MenuItem]:
        """
        获取所有插件的菜单项（按 order 排序）

        Returns:
            菜单项列表
        """
        all_menus: List[MenuItem] = []
        for plugin in self._plugins.values():
            all_menus.extend(plugin.menu_items)
        # 按 order 排序
        all_menus.sort(key=lambda x: x.order)
        return all_menus

    def mount_routes(self, app: FastAPI, prefix: str = "/api") -> None:
        """
        将所有插件的路由挂载到 FastAPI 应用

        Args:
            app: FastAPI 应用实例
            prefix: 路由前缀
        """
        for plugin in self._plugins.values():
            for router in plugin.routes:
                app.include_router(router, prefix=prefix)

    def discover_plugins(self, package_path: str = "app.plugins") -> None:
        """
        自动发现并加载插件目录下的所有插件

        每个插件目录下需有 plugin.py 文件，其中定义 register 函数，
        该函数接收 PluginManager 实例并调用 register_plugin 注册插件。

        Args:
            package_path: 插件包路径
        """
        try:
            package = importlib.import_module(package_path)
        except ImportError as e:
            print(f"[错误] 无法导入插件包 {package_path}: {e}")
            return

        # 遍历插件包下的所有子模块
        for importer, mod_name, is_pkg in pkgutil.iter_modules(
            package.__path__, package.__name__ + "."
        ):
            if not is_pkg:
                continue

            # 尝试导入插件的 plugin.py 模块
            plugin_module_name = f"{mod_name}.plugin"
            try:
                plugin_module = importlib.import_module(plugin_module_name)
                # 检查是否有 register 函数
                if hasattr(plugin_module, "register") and callable(
                    plugin_module.register
                ):
                    register_func: Callable[[PluginManager], None] = (
                        plugin_module.register
                    )
                    register_func(self)
                else:
                    print(f"[警告] 插件 {mod_name} 未定义 register 函数，跳过")
            except ImportError as e:
                print(f"[警告] 无法导入插件 {plugin_module_name}: {e}")
            except Exception as e:
                print(f"[错误] 加载插件 {mod_name} 时出错: {e}")
                import traceback
                traceback.print_exc()


# 全局插件管理器实例
plugin_manager = PluginManager()
