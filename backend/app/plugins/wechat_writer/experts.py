"""专家角色配置 - 微信公众号写作助手

定义 4 个写作专家角色及其与状态的映射关系。
"""

from typing import Dict, Any, Optional
from enum import Enum


class ExpertType(str, Enum):
    """专家类型枚举"""
    TOPIC_EDITOR = "topic_editor"    # 选题编辑
    RESEARCHER = "researcher"         # 研究员
    OUTLINER = "outliner"             # 结构师
    WRITER = "writer"                 # 撰稿人


# 状态与专家的映射关系
STATE_TO_EXPERT: Dict[str, str] = {
    "topic_confirm": ExpertType.TOPIC_EDITOR.value,
    "research": ExpertType.RESEARCHER.value,
    "outline": ExpertType.OUTLINER.value,
    "draft": ExpertType.WRITER.value,
    "polish": ExpertType.WRITER.value,
}


# 专家配置
EXPERT_CONFIG: Dict[str, Dict[str, Any]] = {
    ExpertType.TOPIC_EDITOR.value: {
        "name": "选题编辑",
        "name_en": "Topic Editor",
        "state": "topic_confirm",
        "color": "#4a7c6f",  # 绿色系
        "description": "分析主题、拆解需求、给出写作角度建议",
        "prompt_key": "TOPIC_EDITOR_SYSTEM_PROMPT",
    },
    ExpertType.RESEARCHER.value: {
        "name": "研究员",
        "name_en": "Researcher",
        "state": "research",
        "color": "#5a7c9d",  # 蓝色系
        "description": "从 Obsidian 和互联网搜集资料，整理为结构化卡片",
        "prompt_key": "RESEARCHER_SYSTEM_PROMPT",
    },
    ExpertType.OUTLINER.value: {
        "name": "结构师",
        "name_en": "Outliner",
        "state": "outline",
        "color": "#c17f59",  # 橙色系
        "description": "搭建文章结构，分配论据，输出完整大纲",
        "prompt_key": "OUTLINER_SYSTEM_PROMPT",
    },
    ExpertType.WRITER.value: {
        "name": "撰稿人",
        "name_en": "Writer",
        "state": "draft",
        "color": "#7a6b9d",  # 紫色系
        "description": "根据大纲和资料撰写完整文章，并进行润色优化",
        "prompt_key": "WRITER_SYSTEM_PROMPT",
    },
}


def get_expert_config(expert_type: str) -> Optional[Dict[str, Any]]:
    """获取专家配置"""
    return EXPERT_CONFIG.get(expert_type)


def get_expert_name(expert_type: Optional[str]) -> str:
    """获取专家中文名"""
    if not expert_type:
        return "系统"
    config = EXPERT_CONFIG.get(expert_type)
    return config["name"] if config else expert_type


def get_expert_by_state(state: str) -> Optional[str]:
    """根据状态获取对应的专家类型"""
    return STATE_TO_EXPERT.get(state)


def get_expert_system_prompt(expert_type: str) -> str:
    """获取专家的 System Prompt"""
    from app.plugins.wechat_writer import prompts as prompts_module

    config = EXPERT_CONFIG.get(expert_type)
    if not config:
        raise ValueError(f"未知的专家类型: {expert_type}")

    prompt_key = config["prompt_key"]
    return getattr(prompts_module, prompt_key, "")


def get_all_experts() -> list:
    """获取所有专家的信息列表"""
    return [
        {
            "type": expert_type,
            "name": config["name"],
            "name_en": config["name_en"],
            "state": config["state"],
            "color": config["color"],
            "description": config["description"],
        }
        for expert_type, config in EXPERT_CONFIG.items()
    ]
