"""
Obsidian 读取器 - 微信公众号写作助手
扫描 Obsidian Vault 中的 .md 文件，解析 Frontmatter，
增量同步到 ChromaDB 向量数据库，支持语义搜索。

核心功能：
1. 文件扫描：递归遍历 Vault，排除指定目录
2. Frontmatter 解析：提取 YAML 格式的 title/tags/date 等元数据
3. 增量同步：按文件 mtime 判断变更，只处理新增/修改的文件
4. 标签过滤：支持按标签筛选需要索引的笔记
5. 向量化存储：使用 MiniMax Embedding + ChromaDB
6. 语义搜索：在 Obsidian 笔记中进行相似度检索
"""

import os
import re
import json
import time
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# 确保日志级别是 INFO
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

from app.core.config import settings
from app.capabilities.rag.vector_store import vector_store
from app.capabilities.rag.text_splitter import TextSplitter


# =============================================================================
# 常量定义
# =============================================================================

# Obsidian 笔记在 ChromaDB 中的集合名前缀
OBSIDIAN_COLLECTION_PREFIX = "obsidian_"

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {".md", ".markdown"}

# 默认排除目录（除了配置中的，还会排除这些）
DEFAULT_EXCLUDE_DIRS = {".git", ".obsidian", ".trash", "templates"}

# 文本分块参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# 同步状态存储文件（相对项目根目录）
SYNC_STATE_FILE = "./data/obsidian_sync_state.json"


# =============================================================================
# Frontmatter 解析
# =============================================================================

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """解析 Markdown 文件的 YAML Frontmatter

    Frontmatter 格式：
        ---
        title: 我的笔记
        tags: [Python, AI]
        date: 2024-01-01
        ---
        正文内容...

    Args:
        content: 完整的 Markdown 文件内容

    Returns:
        (metadata_dict, body_text) 元数据字典和正文内容
    """
    if not content:
        return {}, ""

    # 匹配 --- 开头的 Frontmatter
    pattern = r'^---\s*\n(.*?)\n---\s*\n?(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    frontmatter_raw = match.group(1)
    body = match.group(2)

    # 简单解析 YAML（不依赖第三方 yaml 库，满足常见格式）
    metadata: Dict[str, Any] = {}

    for line in frontmatter_raw.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # 匹配 key: value 格式
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()

            # 解析列表格式：[tag1, tag2] 或 - tag1
            if value.startswith('[') and value.endswith(']'):
                items = value[1:-1].split(',')
                metadata[key] = [item.strip().strip('"\'') for item in items if item.strip()]
            elif value:
                # 尝试解析数字
                try:
                    if '.' in value:
                        metadata[key] = float(value)
                    else:
                        metadata[key] = int(value)
                except ValueError:
                    # 字符串，去除引号
                    metadata[key] = value.strip('"\'')
            else:
                metadata[key] = ""

    return metadata, body


def extract_tags(content: str, metadata: Dict[str, Any]) -> List[str]:
    """从笔记中提取所有标签

    标签来源：
    1. Frontmatter 中的 tags 字段
    2. 正文中的 #标签 格式

    Args:
        content: 完整的 Markdown 内容
        metadata: 已解析的 Frontmatter 元数据

    Returns:
        去重后的标签列表
    """
    tags = set()

    # 从 Frontmatter 提取
    if 'tags' in metadata:
        meta_tags = metadata['tags']
        if isinstance(meta_tags, list):
            tags.update(meta_tags)
        elif isinstance(meta_tags, str):
            for t in meta_tags.split(','):
                t = t.strip()
                if t:
                    tags.add(t)

    # 从正文中提取 #标签（标签名以字母开头，可包含字母数字下划线连字符斜杠）
    body_tags = re.findall(r'#([a-zA-Z\u4e00-\u9fa5][\w\u4e00-\u9fa5\-/]*)', content)
    tags.update(body_tags)

    return sorted(list(tags))


# =============================================================================
# Obsidian 读取器类
# =============================================================================

class ObsidianReader:
    """Obsidian 知识库读取器

    负责扫描 Obsidian Vault、解析笔记、增量同步到向量数据库。

    Attributes:
        vault_path: Obsidian Vault 根路径
        exclude_dirs: 排除的目录列表
        include_tags: 只索引包含这些标签的笔记（空列表表示全部）
        text_splitter: 文本分块器
    """

    def __init__(
        self,
        vault_path: Optional[str] = None,
        exclude_dirs: Optional[List[str]] = None,
        include_tags: Optional[List[str]] = None,
    ):
        """初始化 Obsidian 读取器

        Args:
            vault_path: Vault 根路径，默认从配置读取
            exclude_dirs: 排除目录，默认从配置读取 + 默认值
            include_tags: 包含标签，默认从配置读取
        """
        self.vault_path = Path(vault_path or settings.OBSIDIAN_VAULT_PATH)

        # 解析排除目录
        config_excludes = settings.OBSIDIAN_EXCLUDE_DIRS.split(',') if settings.OBSIDIAN_EXCLUDE_DIRS else []
        self.exclude_dirs = set(exclude_dirs or [d.strip() for d in config_excludes])
        self.exclude_dirs.update(DEFAULT_EXCLUDE_DIRS)

        # 解析包含标签
        config_tags = settings.OBSIDIAN_INCLUDE_TAGS.split(',') if settings.OBSIDIAN_INCLUDE_TAGS else []
        self.include_tags = [t.strip() for t in (include_tags or config_tags) if t.strip()]

        self.text_splitter = TextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

        # 确保数据目录存在
        os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)

    # ------------------------------------------------------------------
    # 公共 API：文件扫描
    # ------------------------------------------------------------------

    def scan_files(self) -> List[Dict[str, Any]]:
        """扫描 Vault 中所有符合条件的 .md 文件

        Returns:
            文件信息列表，每项包含：
            - path: 绝对路径 (str)
            - relative_path: 相对 Vault 的路径 (str)
            - mtime: 修改时间戳 (float)
            - size: 文件大小 (int)
        """
        if not self.vault_path.exists():
            return []

        files = []

        for root, dirs, filenames in os.walk(self.vault_path):
            # 过滤排除目录（修改 dirs 列表，os.walk 会跳过被删除的目录）
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                abs_path = os.path.join(root, filename)
                try:
                    stat = os.stat(abs_path)
                    rel_path = os.path.relpath(abs_path, self.vault_path)
                    files.append({
                        "path": abs_path,
                        "relative_path": rel_path.replace('\\', '/'),
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                    })
                except (OSError, PermissionError):
                    # 跳过无法读取的文件
                    continue

        return files

    # ------------------------------------------------------------------
    # 公共 API：文件解析
    # ------------------------------------------------------------------

    def parse_note(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析单个 Obsidian 笔记文件

        Args:
            file_info: scan_files 返回的文件信息

        Returns:
            解析后的笔记数据，包含：
            - path: 相对路径
            - title: 标题
            - tags: 标签列表
            - metadata: 完整 Frontmatter 元数据
            - content: 正文内容（去除 Frontmatter）
            - mtime: 修改时间
            - word_count: 字数
            解析失败返回 None
        """
        abs_path = file_info["path"]
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(abs_path, "r", encoding="gbk", errors="ignore") as f:
                    raw_content = f.read()
            except Exception:
                return None
        except Exception:
            return None

        metadata, body = parse_frontmatter(raw_content)
        tags = extract_tags(raw_content, metadata)

        # 标签过滤：如果配置了 include_tags，只索引匹配的笔记
        if self.include_tags:
            if not any(t in tags for t in self.include_tags):
                return None

        # 标题优先级：Frontmatter title > 文件名
        title = metadata.get("title") or os.path.splitext(os.path.basename(abs_path))[0]

        # 日期：Frontmatter date > 文件 mtime
        date_str = metadata.get("date")
        if not date_str:
            date_str = datetime.fromtimestamp(file_info["mtime"]).strftime("%Y-%m-%d")

        word_count = len(body)

        return {
            "path": file_info["relative_path"],
            "title": str(title),
            "tags": tags,
            "metadata": metadata,
            "content": body,
            "raw_content": raw_content,
            "mtime": file_info["mtime"],
            "date": str(date_str),
            "word_count": word_count,
        }

    # ------------------------------------------------------------------
    # 公共 API：同步状态管理
    # ------------------------------------------------------------------

    def _load_sync_state(self) -> Dict[str, Any]:
        """加载同步状态

        Returns:
            同步状态字典，格式：
            {
                "user_id": {
                    "last_sync_time": timestamp,
                    "files": {
                        "relative_path": {"mtime": float, "hash": str, "indexed": bool}
                    }
                }
            }
        """
        if not os.path.exists(SYNC_STATE_FILE):
            return {}
        try:
            with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_sync_state(self, state: Dict[str, Any]) -> None:
        """保存同步状态"""
        os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)
        with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def clear_sync_state(self, user_id: int) -> None:
        """清除指定用户的同步状态（用于强制全量重新同步）"""
        state = self._load_sync_state()
        if str(user_id) in state:
            del state[str(user_id)]
            self._save_sync_state(state)
            print(f"[Obsidian] 已清除 user_id={user_id} 的同步状态")

    @staticmethod
    def _get_collection_name(user_id: int) -> str:
        """获取用户的 Obsidian 集合名"""
        return f"{OBSIDIAN_COLLECTION_PREFIX}{user_id}"

    # ------------------------------------------------------------------
    # 公共 API：增量同步
    # ------------------------------------------------------------------

    def sync(self, user_id: int) -> Dict[str, Any]:
        """执行增量同步

        流程：
        1. 扫描所有文件
        2. 对比上次同步状态，找出新增/修改/删除的文件
        3. 处理新增/修改的文件（解析+向量化+存储）
        4. 处理删除的文件（从向量库移除）
        5. 更新同步状态

        Args:
            user_id: 用户 ID

        Returns:
            同步结果统计：
            {
                "total_files": 扫描到的文件总数,
                "added": 新增文件数,
                "updated": 更新文件数,
                "deleted": 删除文件数,
                "skipped": 跳过文件数（标签不匹配）,
                "errors": 错误数,
                "last_sync_time": 本次同步时间戳,
            }
        """
        result = {
            "total_files": 0,
            "added": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
            "last_sync_time": time.time(),
        }

        print(f"[Obsidian] 开始同步 user_id={user_id}, vault={self.vault_path}", flush=True)

        # 检查 Vault 路径
        if not self.vault_path.exists():
            print(f"[Obsidian] Vault 路径不存在: {self.vault_path}", flush=True)
            result["errors"] = 1
            return result

        collection_name = self._get_collection_name(user_id)
        print(f"[Obsidian] 集合名: {collection_name}", flush=True)

        # 加载上次同步状态
        sync_state = self._load_sync_state()
        user_state = sync_state.get(str(user_id), {"last_sync_time": 0, "files": {}})
        old_files = user_state.get("files", {})

        # 扫描当前文件
        current_files = self.scan_files()
        result["total_files"] = len(current_files)
        print(f"[Obsidian] 扫描到 {len(current_files)} 个文件, 上次已同步 {len(old_files)} 个", flush=True)

        # 构建当前文件的路径索引
        current_paths = {f["relative_path"]: f for f in current_files}

        # 找出需要删除的文件（上次有，这次没有）
        deleted_paths = set(old_files.keys()) - set(current_paths.keys())
        for rel_path in deleted_paths:
            try:
                # 从向量库删除该文件的所有分块
                where = {"path": rel_path}
                vector_store.delete_documents(collection_name, where=where)
                result["deleted"] += 1
            except Exception as e:
                print(f"[Obsidian] 删除向量数据失败: {rel_path}, 错误: {e}", flush=True)
                result["errors"] += 1

        # 处理新增和修改的文件
        new_files_state = {}

        for rel_path, file_info in current_paths.items():
            new_files_state[rel_path] = {
                "mtime": file_info["mtime"],
                "indexed": True,
            }

            old_record = old_files.get(rel_path)

            # 判断是否需要处理：新增 或 mtime 变化
            is_new = old_record is None
            is_modified = old_record and old_record.get("mtime") != file_info["mtime"]

            if not is_new and not is_modified:
                # 文件未变化，跳过
                continue

            # 解析笔记
            note = self.parse_note(file_info)
            if note is None:
                # 标签不匹配或解析失败
                if is_new:
                    result["skipped"] += 1
                new_files_state[rel_path]["indexed"] = False
                continue

            try:
                # 如果是更新，先删除旧的分块
                if is_modified:
                    vector_store.delete_documents(collection_name, where={"path": rel_path})

                # 文本分块
                chunks = self.text_splitter.split_text(note["content"])
                if not chunks:
                    chunks = [note["content"]]

                print(f"[Obsidian] 正在向量化: {rel_path} ({len(chunks)} 个分块)", flush=True)

                # 构建 ID 和元数据
                chunk_ids = [f"obsidian_{user_id}_{self._path_to_id(rel_path)}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{
                    "path": rel_path,
                    "title": note["title"],
                    "tags": json.dumps(note["tags"], ensure_ascii=False),
                    "date": note["date"],
                    "chunk_index": i,
                    "user_id": user_id,
                    "word_count": note["word_count"],
                } for i in range(len(chunks))]

                # 存入向量库
                vector_store.add_documents(
                    collection_name=collection_name,
                    documents=chunks,
                    ids=chunk_ids,
                    metadatas=metadatas,
                )

                print(f"[Obsidian] 完成向量化: {rel_path}", flush=True)

                if is_new:
                    result["added"] += 1
                else:
                    result["updated"] += 1

            except Exception as e:
                print(f"[Obsidian] 处理文件失败: {rel_path}, 错误: {e}", flush=True)
                print(traceback.format_exc(), flush=True)
                result["errors"] += 1
                new_files_state[rel_path]["indexed"] = False

        # 更新同步状态
        user_state["last_sync_time"] = result["last_sync_time"]
        user_state["files"] = new_files_state
        sync_state[str(user_id)] = user_state
        self._save_sync_state(sync_state)

        return result

    # ------------------------------------------------------------------
    # 公共 API：语义搜索
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_complete_sentence(text: str, max_len: int = 500) -> str:
        """
        从文本中提取从完整句子开始的片段

        策略：
        1. 如果文本开头就是句子中间（不是换行/标题/标点后），回溯到最近的句子开头
        2. 句子开头包括：换行、标题标记（#）、句号/问号/感叹号后、段首
        3. 返回的内容不超过 max_len 字符

        Args:
            text: 原始文本片段
            max_len: 最大返回长度

        Returns:
            从完整句子开始的文本片段
        """
        if not text:
            return ""

        # 先截断到最大长度
        truncated = text[:max_len] if len(text) > max_len else text

        # 定义句子开头的模式（向前查找）
        # 匹配: 段首、标题行、句号/问号/感叹号/冒号后、换行后
        sentence_start_pattern = r'(?:^|\n|\r|。|！|？|\.|!|\?|：|:)\s*'

        import re
        # 找到所有句子开头的位置
        positions = [0]  # 默认从开头开始
        for match in re.finditer(sentence_start_pattern, truncated):
            end_pos = match.end()
            if end_pos < len(truncated) - 1:  # 至少还有内容
                positions.append(end_pos)

        # 如果开头就是不完整的（前面有重叠字符导致截断），找到最近的句子开头
        # 检查文本开头是否像一个完整句子的开头
        first_chars = truncated[:20]
        looks_like_incomplete = (
            not first_chars.strip() == first_chars  # 不以空白开头
            and not first_chars.startswith('#')  # 不是标题
            and not first_chars.startswith('\n')  # 不是换行
            and len(positions) > 1  # 有其他可选的句子开头
        )

        if looks_like_incomplete:
            # 找到最接近开头的句子开头位置
            # 取第二个位置（第一个是位置0）
            start_pos = positions[1] if len(positions) > 1 else 0
            result = truncated[start_pos:].lstrip()
        else:
            result = truncated.lstrip()

        # 如果结果太短，尝试返回更多
        if len(result) < 50 and len(text) > len(result):
            result = text[:max_len].lstrip()

        return result

    @staticmethod
    def _diversified_rerank(results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        多样性重排：确保返回结果来自不同的文档

        策略：
        1. 第一轮：每个文档选一个最高分的结果
        2. 第二轮：如果还不够 top_k，按分数从高到低补充

        Args:
            results: 原始搜索结果（按分数降序）
            top_k: 需要返回的数量

        Returns:
            多样性重排后的结果
        """
        if len(results) <= top_k:
            return results

        # 第一轮：每个文档选一个最高分
        seen_paths = set()
        picked = []
        remaining = []

        for r in results:
            path = r.get("path", "")
            if path not in seen_paths:
                seen_paths.add(path)
                picked.append(r)
                if len(picked) >= top_k:
                    break
            else:
                remaining.append(r)

        # 如果不够，按分数补充
        if len(picked) < top_k:
            for r in remaining:
                picked.append(r)
                if len(picked) >= top_k:
                    break

        return picked[:top_k]

    def search(
        self,
        user_id: int,
        query: str,
        top_k: int = 5,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """在 Obsidian 笔记中进行语义搜索

        Args:
            user_id: 用户 ID
            query: 查询文本
            top_k: 返回结果数量
            tags: 按标签过滤（可选）

        Returns:
            搜索结果列表，每项包含：
            - path: 笔记相对路径
            - title: 笔记标题
            - content: 匹配的内容片段（从完整句子开始）
            - tags: 笔记标签
            - score: 相似度分数 (0-1)
        """
        collection_name = self._get_collection_name(user_id)

        # 标签过滤（通过 where 条件）
        where = None
        if tags and len(tags) > 0:
            # ChromaDB 的 where 条件支持 $contains 操作符
            # 这里先不过滤，在结果中过滤
            pass

        # 多取一些结果（3倍），用于多样性重排 + 标签过滤
        fetch_count = max(top_k * 3, 15)

        results = vector_store.search_with_score(
            collection_name=collection_name,
            query=query,
            n_results=fetch_count,
        )

        # 标签过滤 + 结果格式化
        formatted = []
        for r in results:
            metadata = r.get("metadata", {})
            note_tags = []
            tags_str = metadata.get("tags", "[]")
            try:
                note_tags = json.loads(tags_str)
            except (json.JSONDecodeError, TypeError):
                pass

            # 标签过滤
            if tags and len(tags) > 0:
                if not any(t in note_tags for t in tags):
                    continue

            # 优化内容：从完整句子开始
            raw_content = r.get("content", "")
            clean_content = self._extract_complete_sentence(raw_content, max_len=600)

            formatted.append({
                "path": metadata.get("path", ""),
                "title": metadata.get("title", ""),
                "content": clean_content,
                "tags": note_tags,
                "score": r.get("score", 0),
                "date": metadata.get("date", ""),
                "word_count": metadata.get("word_count", 0),
            })

        # 多样性重排：确保不同文档的结果都能出现
        diversified = self._diversified_rerank(formatted, top_k)

        return diversified

    # ------------------------------------------------------------------
    # 公共 API：状态查询
    # ------------------------------------------------------------------

    def get_sync_status(self, user_id: int) -> Dict[str, Any]:
        """获取同步状态

        Args:
            user_id: 用户 ID

        Returns:
            {
                "vault_path": Vault 路径,
                "vault_exists": Vault 是否存在,
                "last_sync_time": 上次同步时间 (timestamp, 0 表示未同步),
                "total_notes": 已索引的笔记数量,
                "total_chunks": 向量分块总数,
            }
        """
        sync_state = self._load_sync_state()
        user_state = sync_state.get(str(user_id), {})
        last_sync = user_state.get("last_sync_time", 0)

        collection_name = self._get_collection_name(user_id)
        total_chunks = vector_store.count_documents(collection_name)

        # 统计已索引的笔记数（去重 path）
        total_notes = 0
        if user_state.get("files"):
            total_notes = sum(
                1 for f in user_state["files"].values()
                if f.get("indexed", False)
            )

        return {
            "vault_path": str(self.vault_path),
            "vault_exists": self.vault_path.exists(),
            "last_sync_time": last_sync,
            "total_notes": total_notes,
            "total_chunks": total_chunks,
        }

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _path_to_id(rel_path: str) -> str:
        """将文件相对路径转换为安全的 ID 字符串"""
        # 替换非字母数字字符为下划线
        safe = re.sub(r'[^a-zA-Z0-9]', '_', rel_path)
        return safe[:80]  # 限制长度


# 全局实例
obsidian_reader = ObsidianReader()
