"""
插件解耦单元测试
覆盖：动态模型导入建表、菜单数据序列化、插件自动发现
注意：mock 插件管理器，不依赖真实数据库
"""
import pytest
from unittest.mock import MagicMock, patch

from app.core.plugin_manager import PluginInfo, MenuItem, PluginManager


class TestImportPluginModels:
    """动态导入插件模型（新增插件无需改 database.py）"""

    def test_imports_all_plugin_models(self):
        """每个声明了 models_module 的插件都应被导入"""
        from app.core import database

        p1 = MagicMock()
        p1.name, p1.models_module = "user", "app.plugins.user.models"
        p2 = MagicMock()
        p2.name, p2.models_module = "knowledge_base", "app.plugins.knowledge_base.models"
        p3 = MagicMock()
        p3.name, p3.models_module = "no_models", None

        with patch.object(database, "ensure_plugins_loaded"), patch(
            "app.core.plugin_manager.plugin_manager.get_all_plugins",
            return_value=[p1, p2, p3],
        ), patch("importlib.import_module") as mock_import:
            loaded = database.import_plugin_models()

        assert loaded == ["user", "knowledge_base"]
        assert mock_import.call_count == 2
        mock_import.assert_any_call("app.plugins.user.models")
        mock_import.assert_any_call("app.plugins.knowledge_base.models")

    def test_import_failure_is_tolerated(self):
        """单个插件模型导入失败不应阻断其他插件"""
        from app.core import database

        p_ok = MagicMock()
        p_ok.name, p_ok.models_module = "ok", "app.plugins.ok.models"
        p_bad = MagicMock()
        p_bad.name, p_bad.models_module = "bad", "app.plugins.bad.models"

        with patch.object(database, "ensure_plugins_loaded"), patch(
            "app.core.plugin_manager.plugin_manager.get_all_plugins",
            return_value=[p_bad, p_ok],
        ), patch("importlib.import_module") as mock_import:
            def side_effect(name):
                if "bad" in name:
                    raise ImportError("simulated")
                return MagicMock()
            mock_import.side_effect = side_effect
            loaded = database.import_plugin_models()

        assert loaded == ["ok"]


class TestMenuData:
    """菜单数据序列化（供前端动态渲染）"""

    def test_get_menu_data_serializes(self):
        """菜单项应转成可序列化字典，含 children"""
        pm = PluginManager()
        info = PluginInfo(
            name="demo",
            menu_items=[
                MenuItem(
                    key="demo",
                    label="演示",
                    icon="star",
                    path="/demo",
                    order=5,
                    children=[
                        MenuItem(key="demo-sub", label="子项", path="/demo/sub", order=1)
                    ],
                )
            ],
        )
        pm.register_plugin(info)

        data = pm.get_menu_data()
        assert len(data) == 1
        assert data[0]["key"] == "demo"
        assert data[0]["label"] == "演示"
        assert data[0]["path"] == "/demo"
        assert data[0]["order"] == 5
        assert data[0]["children"][0]["key"] == "demo-sub"

        # 恢复单例状态，避免测试间污染
        pm._plugins.pop("demo", None)
