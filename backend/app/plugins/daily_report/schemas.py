"""
学习日报数据模式
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class GenerateReportRequest(BaseModel):
    """生成日报请求"""

    report_date: Optional[str] = Field(
        None, description="日报日期 YYYY-MM-DD，不传则取今天"
    )
    force: bool = Field(False, description="已存在时是否强制重新生成")

    @field_validator("report_date")
    @classmethod
    def _check_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        datetime.strptime(v, "%Y-%m-%d")
        return v


class ReportStats(BaseModel):
    """当日数据统计"""

    clips: int = 0
    clip_titles: List[str] = Field(default_factory=list)
    documents: int = 0
    expert_messages: int = 0
    writer_messages: int = 0
    writer_outputs: int = 0


class DailyReportResponse(BaseModel):
    """日报响应（列表用，不含正文）"""

    id: int
    report_date: str
    stats: Dict[str, Any] = Field(default_factory=dict)
    generated_by: str
    error_msg: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DailyReportDetailResponse(DailyReportResponse):
    """日报详情（含正文）"""

    content_md: str = ""


class DailyReportListResponse(BaseModel):
    """日报列表响应"""

    items: List[DailyReportResponse]
    total: int
    page: int
    page_size: int
