"""
学习日报定时调度

项目未引入 APScheduler，这里用 asyncio 后台任务实现最小可用调度：
每 60 秒检查一次是否到达设定时间，到点后为每个用户生成当天日报。
已存在的日报不会覆盖（force=False），因此重复触发安全。
"""
import asyncio
import traceback
from datetime import date, datetime
from typing import Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.plugins.daily_report.service import daily_report_service
from app.plugins.user.models import User


class DailyReportScheduler:
    """日报定时任务"""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._last_run_date: Optional[date] = None
        # 启动时跳过当天已过的触发时间，避免重启后立刻补跑
        self._started_at = datetime.now()

    def start(self) -> None:
        """启动后台任务（幂等）"""
        if not settings.DAILY_REPORT_ENABLED:
            print("[日报] 定时任务已禁用（DAILY_REPORT_ENABLED=false）")
            return
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())
        print(
            f"[日报] 定时任务已启动，每天 "
            f"{settings.DAILY_REPORT_HOUR:02d}:{settings.DAILY_REPORT_MINUTE:02d} 生成"
        )

    def stop(self) -> None:
        """停止后台任务"""
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _loop(self) -> None:
        """事件循环：每分钟检查一次"""
        try:
            while True:
                await asyncio.sleep(60)
                await self._tick()
        except asyncio.CancelledError:
            print("[日报] 定时任务已停止")
            raise

    async def _tick(self) -> None:
        """到点则触发一次生成"""
        now = datetime.now()
        today = now.date()

        if self._last_run_date == today:
            return
        if (now.hour, now.minute) < (
            settings.DAILY_REPORT_HOUR,
            settings.DAILY_REPORT_MINUTE,
        ):
            return
        # 服务在触发时间之后才启动时，不立刻补跑当天的日报
        if self._started_at.date() == today and (
            self._started_at.hour, self._started_at.minute
        ) > (settings.DAILY_REPORT_HOUR, settings.DAILY_REPORT_MINUTE):
            self._last_run_date = today
            return

        self._last_run_date = today
        # 同步数据库操作放到线程池，避免阻塞事件循环
        await asyncio.to_thread(self._run_all, today)

    @staticmethod
    def _run_all(day: date) -> None:
        """为所有用户生成当天日报（已存在则跳过）"""
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_active.is_(True)).all()
            for user in users:
                try:
                    report = daily_report_service.generate(db, user.id, day.isoformat(), force=False)
                    print(f"[日报] 用户 {user.username} {day} 生成完成（{report.generated_by}）")
                except Exception as e:  # noqa: BLE001 - 单个用户失败不影响其他人
                    print(f"[日报] 用户 {user.username} {day} 生成失败: {e}")
                    traceback.print_exc()
                    db.rollback()
        finally:
            db.close()


daily_report_scheduler = DailyReportScheduler()
