"""
学习日报服务层

生成逻辑：聚合当日剪藏 / 知识库新增 / 技术专家组对话 / 公众号写作四大来源，
交给模型产出结构化日报；模型不可用时退化为规则版日报，保证每天都有产出。
"""
import json
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.capabilities.llm.minimax_client import minimax_client
from app.core.exceptions import BusinessException
from app.plugins.clipper.models import Clipping
from app.plugins.daily_report.models import DailyReport
from app.plugins.daily_report.schemas import (
    DailyReportDetailResponse,
    DailyReportListResponse,
    DailyReportResponse,
)
from app.plugins.knowledge_base.models import Document, KnowledgeBase
from app.plugins.tech_experts.models import ExpertMessage, ExpertSession
from app.plugins.wechat_writer.models import WeChatWriterMessage, WeChatWriterOutput, WeChatWriterSession

# 单次喂给模型的最大素材条数
MAX_CLIP_ITEMS = 10
# 单条素材摘要最大长度
MAX_SUMMARY_LEN = 120
# 模型 max_tokens
REPORT_MAX_TOKENS = 1600


def _day_range_utc(day: date):
    """
    把本地日期转成 UTC 时间区间

    数据库里 created_at 多为 datetime.utcnow()，因此需要按本地时区换算，
    否则早上生成的日报会漏掉前一天晚上的数据。
    """
    local_start = datetime.combine(day, time.min)
    local_end = local_start + timedelta(days=1)
    offset = datetime.now() - datetime.utcnow()
    return local_start - offset, local_end - offset


class DailyReportService:
    """学习日报服务"""

    # ---------- 数据采集 ----------

    @staticmethod
    def collect_stats(db: Session, user_id: int, day: date) -> Dict[str, Any]:
        """聚合指定日期的四类数据"""
        start, end = _day_range_utc(day)

        clips = (
            db.query(Clipping)
            .filter(
                Clipping.user_id == user_id,
                Clipping.status == "ready",
                Clipping.created_at >= start,
                Clipping.created_at < end,
            )
            .order_by(Clipping.created_at.asc())
            .all()
        )

        kb_ids = [
            kb.id for kb in db.query(KnowledgeBase).filter(KnowledgeBase.user_id == user_id).all()
        ]
        document_count = 0
        if kb_ids:
            document_count = (
                db.query(Document)
                .filter(
                    Document.kb_id.in_(kb_ids),
                    Document.created_at >= start,
                    Document.created_at < end,
                )
                .count()
            )

        session_ids = [
            s.id
            for s in db.query(ExpertSession).filter(ExpertSession.user_id == user_id).all()
        ]
        expert_messages = 0
        if session_ids:
            expert_messages = (
                db.query(ExpertMessage)
                .filter(
                    ExpertMessage.session_id.in_(session_ids),
                    ExpertMessage.created_at >= start,
                    ExpertMessage.created_at < end,
                )
                .count()
            )

        writer_session_ids = [
            s.id
            for s in db.query(WeChatWriterSession)
            .filter(WeChatWriterSession.user_id == user_id)
            .all()
        ]
        writer_messages = 0
        writer_outputs = 0
        if writer_session_ids:
            writer_messages = (
                db.query(WeChatWriterMessage)
                .filter(
                    WeChatWriterMessage.session_id.in_(writer_session_ids),
                    WeChatWriterMessage.created_at >= start,
                    WeChatWriterMessage.created_at < end,
                )
                .count()
            )
            writer_outputs = (
                db.query(WeChatWriterOutput)
                .filter(
                    WeChatWriterOutput.session_id.in_(writer_session_ids),
                    WeChatWriterOutput.created_at >= start,
                    WeChatWriterOutput.created_at < end,
                )
                .count()
            )

        return {
            "clips": len(clips),
            "clip_titles": [c.title for c in clips[:MAX_CLIP_ITEMS]],
            "documents": document_count,
            "expert_messages": expert_messages,
            "writer_messages": writer_messages,
            "writer_outputs": writer_outputs,
            "_clip_details": [
                {
                    "title": c.title,
                    "site": c.site_name or "",
                    "category": c.category or "",
                    "tags": c.tags or "",
                    "summary": (c.summary or "")[:MAX_SUMMARY_LEN],
                }
                for c in clips[:MAX_CLIP_ITEMS]
            ],
        }

    # ---------- Prompt 构建 ----------

    @staticmethod
    def _build_messages(day: date, stats: Dict[str, Any]) -> List[Dict[str, str]]:
        details = stats.get("_clip_details", [])
        if details:
            clip_block = "\n".join(
                f"- [{d['category'] or '未分类'}] {d['title']}（{d['site']}）"
                f"{'：' + d['summary'] if d['summary'] else ''}"
                for d in details
            )
        else:
            clip_block = "（今日没有剪藏）"

        system_prompt = (
            "你是一名严谨的个人知识管理助手，服务于一位工业软件（MOM/MES/WMS）背景、"
            "正在向 AI 落地转型的工程师。你的任务是把一天的输入整理成能直接行动的日报。"
            "要求：只输出 Markdown 正文，不要寒暄、不要解释你在做什么、不要输出思考过程。"
        )

        user_prompt = f"""以下是 {day.isoformat()} 的输入数据：

【剪藏】共 {stats['clips']} 条
{clip_block}

【知识库新增文档】{stats['documents']} 篇
【技术专家组对话】{stats['expert_messages']} 条消息
【公众号写作】{stats['writer_messages']} 条消息，{stats['writer_outputs']} 个产出

请生成日报，严格使用以下五个二级标题，不要增删：
## 今日概览
用 3 句话概括今天在专业、内容、个人成长三条主线上的进展与不足。

## 素材要点
从剪藏中挑最重要的最多 5 条，每条一句话说清「它讲了什么 + 对我有什么用」。没有剪藏就写「今日无新增素材」，并指出这是需要改进的地方。

## 可深挖的点
3 个值得继续研究的方向，每个说明为什么值得深挖、可以从哪里入手。

## 可写选题
1 个可以直接写公众号的选题，给出：标题 / 切入角度 / 三个论点。选题必须来自今日素材或今日对话，不允许凭空编造。

## 明日待办
3 条具体可执行的待办，动词开头，单条不超过 30 字。"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    # ---------- 兜底日报 ----------

    @staticmethod
    def _build_fallback(day: date, stats: Dict[str, Any], error: str) -> str:
        details = stats.get("_clip_details", [])
        clip_lines = (
            "\n".join(
                f"- {d['title']}（{d['site']}）{'：' + d['summary'] if d['summary'] else ''}"
                for d in details
            )
            or "- 今日无新增素材"
        )
        return f"""## 今日概览

今日剪藏 {stats['clips']} 条，知识库新增 {stats['documents']} 篇，技术对话 {stats['expert_messages']} 条，写作消息 {stats['writer_messages']} 条。
模型生成不可用，本日报由规则汇总生成，仅保留客观数据，不含分析与选题。

## 素材要点

{clip_lines}

## 可深挖的点

（模型不可用，未生成）

## 可写选题

（模型不可用，未生成）

## 明日待办

- 恢复模型额度后重新生成今日日报
- 检查今日剪藏是否已归入合适分类
- 从素材要点中手动挑一个切入点

---
> 生成失败原因：{error}
"""

    # ---------- 生成 ----------

    @staticmethod
    def generate(
        db: Session,
        user_id: int,
        report_date: Optional[str] = None,
        force: bool = False,
    ) -> DailyReportDetailResponse:
        """生成（或覆盖）指定日期的日报"""
        day = (
            datetime.strptime(report_date, "%Y-%m-%d").date()
            if report_date
            else datetime.now().date()
        )
        day_str = day.isoformat()

        existing = (
            db.query(DailyReport)
            .filter(DailyReport.user_id == user_id, DailyReport.report_date == day_str)
            .first()
        )
        if existing and not force:
            return DailyReportDetailResponse.model_validate(
                {**existing.__dict__, "stats": json.loads(existing.stats or "{}")}
            )

        stats = DailyReportService.collect_stats(db, user_id, day)

        generated_by = "llm"
        error_msg = None
        try:
            content = minimax_client.get_chat_reply(
                DailyReportService._build_messages(day, stats),
                temperature=0.6,
                max_tokens=REPORT_MAX_TOKENS,
            )
            if not (content or "").strip():
                raise ValueError("模型返回空内容")
            content = content.strip()
        except Exception as e:  # noqa: BLE001 - 任何模型异常都走兜底
            generated_by = "fallback"
            error_msg = str(e)[:300]
            content = DailyReportService._build_fallback(day, stats, error_msg)

        public_stats = {k: v for k, v in stats.items() if not k.startswith("_")}
        stats_json = json.dumps(public_stats, ensure_ascii=False)

        if existing:
            existing.content_md = content
            existing.stats = stats_json
            existing.generated_by = generated_by
            existing.error_msg = error_msg
            existing.updated_at = datetime.utcnow()
            record = existing
        else:
            record = DailyReport(
                user_id=user_id,
                report_date=day_str,
                content_md=content,
                stats=stats_json,
                generated_by=generated_by,
                error_msg=error_msg,
            )
            db.add(record)

        db.commit()
        db.refresh(record)

        return DailyReportDetailResponse.model_validate(
            {**record.__dict__, "stats": json.loads(record.stats or "{}")}
        )

    # ---------- 查询 ----------

    @staticmethod
    def list_reports(
        db: Session, user_id: int, page: int = 1, page_size: int = 20
    ) -> DailyReportListResponse:
        """分页获取日报列表（不含正文）"""
        query = db.query(DailyReport).filter(DailyReport.user_id == user_id)
        total = query.count()
        records = (
            query.order_by(DailyReport.report_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return DailyReportListResponse(
            items=[
                DailyReportResponse.model_validate(
                    {**r.__dict__, "stats": json.loads(r.stats or "{}")}
                )
                for r in records
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_report(db: Session, user_id: int, report_date: str) -> DailyReportDetailResponse:
        """按日期获取日报详情"""
        record = (
            db.query(DailyReport)
            .filter(DailyReport.user_id == user_id, DailyReport.report_date == report_date)
            .first()
        )
        if not record:
            raise BusinessException(message="该日期没有日报", code=4001, http_status=404)
        return DailyReportDetailResponse.model_validate(
            {**record.__dict__, "stats": json.loads(record.stats or "{}")}
        )

    @staticmethod
    def delete_report(db: Session, user_id: int, report_date: str) -> None:
        """删除指定日期的日报"""
        record = (
            db.query(DailyReport)
            .filter(DailyReport.user_id == user_id, DailyReport.report_date == report_date)
            .first()
        )
        if not record:
            raise BusinessException(message="该日期没有日报", code=4001, http_status=404)
        db.delete(record)
        db.commit()


daily_report_service = DailyReportService()
