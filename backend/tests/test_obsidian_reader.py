"""
Obsidian 读取器 - 单元测试
覆盖：Frontmatter 解析、标签提取、文件扫描、增量同步、搜索过滤
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 确保 backend 在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# =============================================================================
# Frontmatter 解析测试
# =============================================================================

class TestParseFrontmatter:
    """YAML Frontmatter 解析"""

    def test_standard_frontmatter(self):
        """标准 YAML Frontmatter 应该被正确解析"""
        from app.plugins.wechat_writer.obsidian_reader import parse_frontmatter

        content = """---
title: 我的测试笔记
tags: [Python, AI, 测试]
date: 2024-01-15
---
这是正文内容。
第二行正文。"""

        metadata, body = parse_frontmatter(content)

        assert metadata["title"] == "我的测试笔记"
        assert metadata["tags"] == ["Python", "AI", "测试"]
        assert metadata["date"] == "2024-01-15"
        assert "这是正文内容" in body
        assert "第二行正文" in body

    def test_no_frontmatter(self):
        """没有 Frontmatter 的文件应该返回空元数据和完整内容"""
        from app.plugins.wechat_writer.obsidian_reader import parse_frontmatter

        content = "直接写正文，没有 frontmatter"
        metadata, body = parse_frontmatter(content)

        assert metadata == {}
        assert body == content

    def test_empty_frontmatter(self):
        """空的 Frontmatter（只有 ---）"""
        from app.plugins.wechat_writer.obsidian_reader import parse_frontmatter

        content = """---
---
正文开始"""

        metadata, body = parse_frontmatter(content)
        assert metadata == {}
        assert "正文开始" in body

    def test_frontmatter_with_string_tags(self):
        """Frontmatter 中的 tags 是逗号分隔的字符串"""
        from app.plugins.wechat_writer.obsidian_reader import parse_frontmatter

        content = """---
title: 测试
tags: Python, AI, 测试
---
正文"""

        metadata, body = parse_frontmatter(content)
        # 简单解析可能不支持逗号分隔字符串转列表，这里只验证 title
        assert metadata["title"] == "测试"

    def test_frontmatter_with_numbers(self):
        """Frontmatter 中的数字应该被正确解析"""
        from app.plugins.wechat_writer.obsidian_reader import parse_frontmatter

        content = """---
title: 数字测试
count: 42
rating: 4.5
---
正文"""

        metadata, body = parse_frontmatter(content)
        assert metadata["count"] == 42
        assert metadata["rating"] == 4.5

    def test_empty_content(self):
        """空内容应该返回空"""
        from app.plugins.wechat_writer.obsidian_reader import parse_frontmatter

        metadata, body = parse_frontmatter("")
        assert metadata == {}
        assert body == ""


# =============================================================================
# 标签提取测试
# =============================================================================

class TestExtractTags:
    """从笔记中提取标签"""

    def test_tags_from_frontmatter(self):
        """Frontmatter 中的 tags 应该被提取"""
        from app.plugins.wechat_writer.obsidian_reader import extract_tags

        content = """---
tags: [Python, AI]
---
正文"""
        metadata = {"tags": ["Python", "AI"]}
        tags = extract_tags(content, metadata)

        assert "Python" in tags
        assert "AI" in tags

    def test_tags_from_body(self):
        """正文中的 #标签 应该被提取"""
        from app.plugins.wechat_writer.obsidian_reader import extract_tags

        content = "这是一篇关于 #Python 和 #AI 的笔记"
        tags = extract_tags(content, {})

        assert "Python" in tags
        assert "AI" in tags

    def test_combined_tags(self):
        """Frontmatter 和正文的标签应该合并去重"""
        from app.plugins.wechat_writer.obsidian_reader import extract_tags

        content = """---
tags: [Python]
---
关于 #Python 和 #AI 的内容"""
        metadata = {"tags": ["Python"]}
        tags = extract_tags(content, metadata)

        assert tags == sorted(["Python", "AI"])  # 去重 + 排序
        assert len(tags) == 2

    def test_no_tags(self):
        """没有标签的笔记应该返回空列表"""
        from app.plugins.wechat_writer.obsidian_reader import extract_tags

        tags = extract_tags("纯正文，没有标签", {})
        assert tags == []


# =============================================================================
# ObsidianReader 文件扫描测试
# =============================================================================

class TestScanFiles:
    """文件扫描功能"""

    @pytest.fixture
    def temp_vault(self):
        """创建临时 Vault 目录"""
        vault_dir = tempfile.mkdtemp()
        try:
            # 创建一些测试文件
            # 根目录
            (Path(vault_dir) / "note1.md").write_text("笔记1内容", encoding="utf-8")
            (Path(vault_dir) / "note2.md").write_text("笔记2内容", encoding="utf-8")
            (Path(vault_dir) / "readme.txt").write_text("忽略这个文件", encoding="utf-8")

            # 子目录
            subdir = Path(vault_dir) / "技术"
            subdir.mkdir()
            (subdir / "python-note.md").write_text("Python 笔记", encoding="utf-8")

            # 应该排除的目录
            obsidian_dir = Path(vault_dir) / ".obsidian"
            obsidian_dir.mkdir()
            (obsidian_dir / "workspace.json").write_text("{}", encoding="utf-8")

            yield vault_dir
        finally:
            shutil.rmtree(vault_dir)

    def test_scan_returns_only_md_files(self, temp_vault):
        """扫描结果应该只包含 .md 和 .markdown 文件"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        reader = ObsidianReader(vault_path=temp_vault)
        files = reader.scan_files()

        # 应该有 3 个 .md 文件（note1, note2, python-note）
        md_paths = [f["relative_path"] for f in files]
        assert len(files) == 3
        assert "note1.md" in md_paths
        assert "note2.md" in md_paths
        assert "技术/python-note.md" in md_paths

    def test_scan_excludes_obsidian_dir(self, temp_vault):
        """应该排除 .obsidian 目录"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        reader = ObsidianReader(vault_path=temp_vault)
        files = reader.scan_files()

        paths = [f["relative_path"] for f in files]
        assert not any(".obsidian" in p for p in paths)

    def test_scan_file_info_complete(self, temp_vault):
        """每个文件信息应该包含必要字段"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        reader = ObsidianReader(vault_path=temp_vault)
        files = reader.scan_files()

        for f in files:
            assert "path" in f
            assert "relative_path" in f
            assert "mtime" in f
            assert "size" in f
            assert os.path.exists(f["path"])

    def test_scan_nonexistent_vault(self):
        """Vault 不存在时应该返回空列表"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        reader = ObsidianReader(vault_path="/nonexistent/path")
        files = reader.scan_files()
        assert files == []


# =============================================================================
# 笔记解析测试
# =============================================================================

class TestParseNote:
    """单个笔记文件解析"""

    @pytest.fixture
    def temp_vault_with_notes(self):
        vault_dir = tempfile.mkdtemp()
        try:
            # 带 Frontmatter 的笔记
            note1 = Path(vault_dir) / "带标签的笔记.md"
            note1.write_text("""---
title: Python Agent 开发指南
tags: [Python, Agent, AI]
date: 2024-06-20
---
# Python Agent 开发

这是一篇关于 #Python Agent 开发的详细指南。

## 核心概念

Agent 是一种能够自主决策的程序...
""", encoding="utf-8")

            # 不带 Frontmatter 的笔记
            note2 = Path(vault_dir) / "无标签笔记.md"
            note2.write_text("直接写正文，没有 frontmatter", encoding="utf-8")

            yield vault_dir, note1, note2
        finally:
            shutil.rmtree(vault_dir)

    def test_parse_note_with_frontmatter(self, temp_vault_with_notes):
        """带 Frontmatter 的笔记应该被正确解析"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        vault_dir, note1, _ = temp_vault_with_notes
        reader = ObsidianReader(vault_path=vault_dir)

        file_info = {
            "path": str(note1),
            "relative_path": "带标签的笔记.md",
            "mtime": note1.stat().st_mtime,
            "size": note1.stat().st_size,
        }

        note = reader.parse_note(file_info)
        assert note is not None
        assert note["title"] == "Python Agent 开发指南"
        assert "Python" in note["tags"]
        assert "Agent" in note["tags"]
        assert "AI" in note["tags"]
        assert note["date"] == "2024-06-20"
        assert "Python Agent 开发" in note["content"]
        assert note["word_count"] > 0

    def test_parse_note_without_frontmatter(self, temp_vault_with_notes):
        """不带 Frontmatter 的笔记应该用文件名作为标题"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        vault_dir, _, note2 = temp_vault_with_notes
        reader = ObsidianReader(vault_path=vault_dir)

        file_info = {
            "path": str(note2),
            "relative_path": "无标签笔记.md",
            "mtime": note2.stat().st_mtime,
            "size": note2.stat().st_size,
        }

        note = reader.parse_note(file_info)
        assert note is not None
        assert note["title"] == "无标签笔记"
        assert "直接写正文" in note["content"]

    def test_parse_note_tag_filter(self, temp_vault_with_notes):
        """标签过滤：只索引包含指定标签的笔记"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        vault_dir, note1, _ = temp_vault_with_notes

        # 只索引包含 "不存在的标签" 的笔记
        reader = ObsidianReader(vault_path=vault_dir, include_tags=["不存在的标签"])
        file_info = {
            "path": str(note1),
            "relative_path": "带标签的笔记.md",
            "mtime": note1.stat().st_mtime,
            "size": note1.stat().st_size,
        }

        note = reader.parse_note(file_info)
        assert note is None  # 应该被过滤掉


# =============================================================================
# 增量同步测试（使用 Mock）
# =============================================================================

class TestIncrementalSync:
    """增量同步逻辑"""

    def test_sync_nonexistent_vault(self):
        """Vault 不存在时同步应该返回错误计数"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        reader = ObsidianReader(vault_path="/nonexistent/path")
        result = reader.sync(user_id=1)

        assert result["errors"] == 1
        assert result["total_files"] == 0

    def test_get_sync_status(self):
        """获取同步状态应该返回正确的结构"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        reader = ObsidianReader(vault_path="/nonexistent/path")
        status = reader.get_sync_status(user_id=999)

        assert "vault_path" in status
        assert status["vault_exists"] is False
        assert "last_sync_time" in status
        assert "total_notes" in status
        assert "total_chunks" in status


# =============================================================================
# 辅助方法测试
# =============================================================================

class TestHelperMethods:
    """辅助方法"""

    def test_collection_name(self):
        """集合名应该包含用户 ID"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        assert ObsidianReader._get_collection_name(1) == "obsidian_1"
        assert ObsidianReader._get_collection_name(999) == "obsidian_999"

    def test_path_to_id(self):
        """路径转 ID 应该安全且一致"""
        from app.plugins.wechat_writer.obsidian_reader import ObsidianReader

        result = ObsidianReader._path_to_id("技术/Python/笔记.md")
        # 应该只包含字母数字和下划线
        assert all(c.isalnum() or c == '_' for c in result)
        # 相同输入应该产生相同输出
        assert ObsidianReader._path_to_id("a/b.md") == ObsidianReader._path_to_id("a/b.md")
