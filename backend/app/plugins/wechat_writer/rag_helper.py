"""
RAG（检索增强生成）辅助模块
为写作流程提供知识库检索和上下文构建能力
"""
from typing import List, Dict, Any, Optional


def format_rag_context(search_results: List[Dict[str, Any]], max_snippets: int = 8) -> str:
    """
    将语义搜索结果格式化为 RAG 上下文文本，注入到 LLM Prompt 中

    Args:
        search_results: obsidian_reader.search() 返回的搜索结果列表
        max_snippets: 最多包含多少条资料片段

    Returns:
        格式化后的 RAG 上下文字符串
    """
    if not search_results:
        return ""

    # 去重（同一篇文档只保留一条最相关的）
    seen_paths = set()
    unique_results = []
    for r in search_results:
        path = r.get("path", "")
        if path not in seen_paths:
            seen_paths.add(path)
            unique_results.append(r)
        if len(unique_results) >= max_snippets:
            break

    if not unique_results:
        return ""

    # 构建上下文
    lines = []
    lines.append("=" * 60)
    lines.append("【从 Obsidian 知识库检索到的参考资料】")
    lines.append(f"共检索到 {len(unique_results)} 篇相关笔记：")
    lines.append("")

    for i, r in enumerate(unique_results, 1):
        title = r.get("title", "未知标题")
        path = r.get("path", "")
        content = r.get("content", "")
        score = r.get("score", 0)
        date = r.get("date", "")

        # 截断过长的内容
        if len(content) > 500:
            content = content[:500] + "..."

        lines.append(f"--- 资料 #{i} ---")
        lines.append(f"📄 标题：{title}")
        lines.append(f"📁 来源：{path}")
        if date:
            lines.append(f"📅 日期：{date}")
        lines.append(f"🔍 相关度：{score:.2f}")
        lines.append(f"📝 内容摘要：")
        lines.append(content)
        lines.append("")

    lines.append("=" * 60)
    lines.append("")
    lines.append("【使用说明】")
    lines.append("1. 以上资料来自用户的 Obsidian 个人知识库，可信度较高")
    lines.append("2. 请优先引用这些资料中的观点和数据作为论据")
    lines.append("3. 引用时请注明来源（资料编号或文档标题）")
    lines.append("4. 如果资料中的内容与你的知识冲突，以资料内容为准并标注")
    lines.append("5. 如果资料不足以支撑写作，请明确指出缺少哪些方面的信息")

    return "\n".join(lines)


def build_search_queries(topic: str, confirmed_topic: Optional[str] = None) -> List[str]:
    """
    根据写作主题生成多个搜索关键词，提高 RAG 召回率

    Args:
        topic: 用户原始主题
        confirmed_topic: 确认后的细化主题（可选）

    Returns:
        搜索关键词列表（按优先级排序）
    """
    queries = []

    # 原始主题
    if topic:
        queries.append(topic.strip())

    # 确认后的主题（通常更具体）
    if confirmed_topic and confirmed_topic != topic:
        # 从确认主题中提取关键词（简单取前 50 字）
        clean = confirmed_topic.strip()[:50]
        if clean and clean not in queries:
            queries.append(clean)

    return queries
