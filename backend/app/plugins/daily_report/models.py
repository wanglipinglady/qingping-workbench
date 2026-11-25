"""
学习日报模型
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app.core.database import Base


class DailyReport(Base):
    """每日学习日报"""

    __tablename__ = "daily_reports"
    __table_args__ = (
        # 同一用户同一天只保留一份日报（重新生成时覆盖）
        UniqueConstraint("user_id", "report_date", name="uq_daily_report_user_date"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 所属用户
    user_id = Column(Integer, index=True, nullable=False)
    # 日报日期（YYYY-MM-DD，本地时区）
    report_date = Column(String(10), index=True, nullable=False)
    # 日报正文（Markdown）
    content_md = Column(Text, nullable=False, default="")
    # 当日数据统计（JSON 字符串）
    stats = Column(Text, nullable=True, default="{}")
    # 生成方式：llm（模型生成）/ fallback（规则兜底）
    generated_by = Column(String(20), default="llm", nullable=False)
    # 失败原因（兜底时记录）
    error_msg = Column(Text, nullable=True)
    # 创建 / 更新时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
