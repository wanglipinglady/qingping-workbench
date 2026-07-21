"""
微信公众号写作助手 - 服务层
提供会话、状态机、资料卡片的业务逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.plugins.wechat_writer.models import (
    WeChatWriterSession,
    WeChatWriterMaterial,
    WeChatWriterMessage,
    WeChatWriterOutput,
)
from app.plugins.wechat_writer.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    WriterState,
    SessionStatus,
)


class WeChatWriterService:
    """微信公众号写作助手服务类"""

    # ========== 会话管理 ==========

    def create_session(self, db: Session, user_id: int, req: SessionCreateRequest) -> WeChatWriterSession:
        """创建写作会话"""
        title = req.title or req.topic[:50]
        session = WeChatWriterSession(
            user_id=user_id,
            title=title,
            topic=req.topic,
            current_state=WriterState.IDLE.value,
            status=SessionStatus.ACTIVE.value,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session_list(
        self, db: Session, user_id: int, page: int = 1, page_size: int = 20,
        status: Optional[str] = None, keyword: Optional[str] = None,
    ) -> Tuple[List[WeChatWriterSession], int]:
        """获取会话列表"""
        query = db.query(WeChatWriterSession).filter(WeChatWriterSession.user_id == user_id)

        if status:
            query = query.filter(WeChatWriterSession.status == status)
        if keyword:
            query = query.filter(
                (WeChatWriterSession.title.like(f"%{keyword}%")) |
                (WeChatWriterSession.topic.like(f"%{keyword}%"))
            )

        total = query.count()
        items = (
            query.order_by(WeChatWriterSession.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_session(self, db: Session, user_id: int, session_id: int) -> WeChatWriterSession:
        """获取会话详情"""
        session = (
            db.query(WeChatWriterSession)
            .filter(
                WeChatWriterSession.id == session_id,
                WeChatWriterSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            raise BusinessException("会话不存在或无权限访问")
        return session

    def update_session(
        self, db: Session, user_id: int, session_id: int, req: SessionUpdateRequest
    ) -> WeChatWriterSession:
        """更新会话"""
        session = self.get_session(db, user_id, session_id)
        update_data = req.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(session, key, value)
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    def delete_session(self, db: Session, user_id: int, session_id: int) -> None:
        """删除会话"""
        session = self.get_session(db, user_id, session_id)
        db.delete(session)
        db.commit()

    # ========== 状态机操作（占位实现，T3 完善） ==========

    def confirm_state(self, db: Session, user_id: int, session_id: int) -> WeChatWriterSession:
        """确认当前状态，进入下一步"""
        session = self.get_session(db, user_id, session_id)
        # T3 实现完整状态流转
        return session

    def regenerate(
        self, db: Session, user_id: int, session_id: int, feedback: Optional[str] = None
    ) -> WeChatWriterSession:
        """重新生成当前步骤的输出"""
        session = self.get_session(db, user_id, session_id)
        # T3/T10 实现
        return session

    def rollback(self, db: Session, user_id: int, session_id: int, target_state: str) -> WeChatWriterSession:
        """回退到指定状态"""
        session = self.get_session(db, user_id, session_id)
        # T3 实现
        return session

    # ========== 资料卡片（占位，T7 完善） ==========

    def get_materials(
        self, db: Session, user_id: int, session_id: int,
        source_type: Optional[str] = None, is_useful: Optional[bool] = None,
    ) -> List[WeChatWriterMaterial]:
        """获取资料卡片列表"""
        session = self.get_session(db, user_id, session_id)
        query = db.query(WeChatWriterMaterial).filter(WeChatWriterMaterial.session_id == session.id)
        if source_type:
            query = query.filter(WeChatWriterMaterial.source_type == source_type)
        if is_useful is not None:
            query = query.filter(WeChatWriterMaterial.is_useful == (1 if is_useful else 0))
        return query.order_by(WeChatWriterMaterial.created_at.desc()).all()

    # ========== 输出版本（占位，T10 完善） ==========

    def get_outputs(
        self, db: Session, user_id: int, session_id: int, step: Optional[str] = None
    ) -> List[WeChatWriterOutput]:
        """获取输出版本列表"""
        session = self.get_session(db, user_id, session_id)
        query = db.query(WeChatWriterOutput).filter(WeChatWriterOutput.session_id == session.id)
        if step:
            query = query.filter(WeChatWriterOutput.step == step)
        return query.order_by(WeChatWriterOutput.step, WeChatWriterOutput.version).all()


# 全局服务实例
wechat_writer_service = WeChatWriterService()
