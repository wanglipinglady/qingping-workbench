"""四大专家角色定义

集中管理专家的基本信息（名称、图标、颜色、描述、System Prompt）。
每个专家对应状态机中的一个核心状态节点。
"""

from typing import Dict, Optional

from app.plugins.tech_experts.prompts import (
    ARCHITECT_SYSTEM_PROMPT,
    CODER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    TESTER_SYSTEM_PROMPT,
)


class ExpertType:
    """专家类型常量"""
    ARCHITECT = "architect"    # 架构师
    CODER = "coder"            # 程序员
    REVIEWER = "reviewer"      # 审查员
    TESTER = "tester"          # 测试工程师


# 专家配置字典
EXPERT_CONFIG: Dict[str, dict] = {
    ExpertType.ARCHITECT: {
        "name": "架构师",
        "icon": "🏗️",
        "color": "#4a7c6f",
        "description": "系统架构设计师，负责需求分析、技术选型、整体架构设计",
        "system_prompt": ARCHITECT_SYSTEM_PROMPT,
        "state": "arch_design",
    },
    ExpertType.CODER: {
        "name": "程序员",
        "icon": "💻",
        "color": "#7a6b9d",
        "description": "高级开发工程师，负责根据架构方案编写高质量可运行代码",
        "system_prompt": CODER_SYSTEM_PROMPT,
        "state": "code_impl",
    },
    ExpertType.REVIEWER: {
        "name": "审查员",
        "icon": "🔍",
        "color": "#c47c4a",
        "description": "代码审查专家，负责审查代码质量、安全性、性能和规范性",
        "system_prompt": REVIEWER_SYSTEM_PROMPT,
        "state": "code_review",
    },
    ExpertType.TESTER: {
        "name": "测试工程师",
        "icon": "🧪",
        "color": "#b85450",
        "description": "测试工程师，负责设计测试用例、验证功能、发现边界问题",
        "system_prompt": TESTER_SYSTEM_PROMPT,
        "state": "testing",
    },
}


def get_expert_config(expert_type: str) -> Optional[dict]:
    """获取指定专家的配置信息

    Args:
        expert_type: 专家类型 (architect/coder/reviewer/tester)

    Returns:
        专家配置字典，不存在则返回 None
    """
    return EXPERT_CONFIG.get(expert_type)


def get_expert_name(expert_type: str) -> str:
    """获取专家的中文名称"""
    config = get_expert_config(expert_type)
    return config["name"] if config else expert_type


def get_expert_system_prompt(expert_type: str) -> str:
    """获取专家的 System Prompt"""
    config = get_expert_config(expert_type)
    return config["system_prompt"] if config else ""


def get_all_experts() -> list:
    """获取所有专家的列表信息（用于 API 返回）"""
    result = []
    for expert_type, config in EXPERT_CONFIG.items():
        result.append({
            "type": expert_type,
            "name": config["name"],
            "icon": config["icon"],
            "color": config["color"],
            "description": config["description"],
            "state": config["state"],
        })
    return result


def get_expert_by_state(state: str) -> Optional[str]:
    """根据状态获取对应的专家类型

    Args:
        state: 状态名称

    Returns:
        专家类型，没有对应专家则返回 None
    """
    for expert_type, config in EXPERT_CONFIG.items():
        if config["state"] == state:
            return expert_type
    return None
