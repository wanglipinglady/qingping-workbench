"""
学习日报路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import unified_response
from app.plugins.daily_report.schemas import GenerateReportRequest
from app.plugins.daily_report.service import daily_report_service
from app.plugins.user.models import User

router = APIRouter(prefix="/daily-reports", tags=["学习日报"])


@router.post("/generate", summary="生成学习日报")
async def generate_report(
    request: GenerateReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    生成指定日期的学习日报

    - **report_date**: 日期 YYYY-MM-DD，不传则取今天
    - **force**: 已存在时是否强制覆盖

    日报数据来源：当日剪藏、知识库新增文档、技术专家组对话、公众号写作。
    模型不可用时自动退化为规则版日报，不会返回空。
    """
    result = daily_report_service.generate(
        db, current_user.id, request.report_date, request.force
    )
    return unified_response(data=result.model_dump(), message="日报已生成")


@router.get("", summary="获取日报列表")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分页获取日报列表（不含正文）"""
    result = daily_report_service.list_reports(db, current_user.id, page, page_size)
    return unified_response(data=result.model_dump())


@router.get("/{report_date}", summary="获取某日日报")
async def get_report(
    report_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """按日期（YYYY-MM-DD）获取日报详情"""
    result = daily_report_service.get_report(db, current_user.id, report_date)
    return unified_response(data=result.model_dump())


@router.delete("/{report_date}", summary="删除某日日报")
async def delete_report(
    report_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除指定日期的日报"""
    daily_report_service.delete_report(db, current_user.id, report_date)
    return unified_response(message="删除成功")
