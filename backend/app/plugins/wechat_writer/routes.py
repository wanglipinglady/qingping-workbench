"""
微信公众号写作助手 - 路由
定义写作助手相关的 API 端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, decode_access_token
from app.core.exceptions import unified_response
from app.plugins.user.models import User
from app.plugins.wechat_writer.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
    SessionDetailResponse,
    StateTransitionRequest,
    StateResponse,
    MessageResponse,
    MaterialResponse,
    MaterialCreateRequest,
    MaterialUpdateRequest,
    MaterialParseRequest,
    TemplateResponse,
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplateApplyRequest,
)
from app.plugins.wechat_writer.service import wechat_writer_service
from app.plugins.wechat_writer.obsidian_reader import obsidian_reader

router = APIRouter(
    prefix="/wechat-writer",
    tags=["微信公众号写作助手"],
)


# ========== 会话 CRUD ==========

@router.post("/sessions", summary="创建写作会话")
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建新的写作会话

    - **topic**: 文章主题（1-500字符）
    - **title**: 会话标题（可选，默认用主题）
    """
    result = wechat_writer_service.create_session(db, current_user.id, request)
    return unified_response(data=SessionResponse.model_validate(result).model_dump())


@router.get("/sessions", summary="获取会话列表")
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选: active/completed/archived"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的写作会话列表"""
    items, total = wechat_writer_service.get_session_list(
        db, current_user.id, page, page_size, status, keyword
    )
    data = SessionListResponse(
        items=[SessionResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    return unified_response(data=data.model_dump())


@router.get("/sessions/{session_id}", summary="获取会话详情")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """根据 ID 获取会话详情"""
    result = wechat_writer_service.get_session(db, current_user.id, session_id)
    data = SessionDetailResponse.model_validate(result)
    # 补充统计数据
    data.material_count = len(result.materials) if result.materials else 0
    data.message_count = len(result.messages) if result.messages else 0
    data.output_count = len(result.outputs) if result.outputs else 0
    return unified_response(data=data.model_dump())


@router.put("/sessions/{session_id}", summary="更新会话")
async def update_session(
    session_id: int,
    request: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新会话信息（标题、确认主题、状态等）"""
    result = wechat_writer_service.update_session(db, current_user.id, session_id, request)
    return unified_response(data=SessionResponse.model_validate(result).model_dump())


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除写作会话及其所有关联数据"""
    wechat_writer_service.delete_session(db, current_user.id, session_id)
    return unified_response(message="删除成功")


# ========== 状态机操作 ==========

@router.post("/sessions/{session_id}/start", summary="开始写作（从 idle 进入选题确认）")
async def start_writing(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始写作流程：从 idle 进入选题确认阶段，调用选题编辑专家分析主题

    返回选题编辑的分析结果（选题确认单）
    """
    result = wechat_writer_service.start_topic_confirm(db, current_user.id, session_id)
    return unified_response(data=result)


@router.post("/sessions/{session_id}/confirm", summary="确认当前状态，进入下一步")
async def confirm_current_state(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    确认当前状态的输出，进入下一个状态

    - 在 topic_confirm 状态：保存选题确认单为 confirmed_topic，进入 research
    - 在 research 状态：确认资料卡片，进入 outline
    - 在 outline 状态：确认大纲，进入 draft
    - 在 draft 状态：确认初稿，进入 polish
    - 在 polish 状态：确认润色稿，进入 done
    """
    result = wechat_writer_service.confirm_state(db, current_user.id, session_id)
    return unified_response(data=result)


@router.post("/sessions/{session_id}/generate", summary="在当前状态触发 AI 生成")
async def generate_current_state(
    session_id: int,
    request: StateTransitionRequest = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    在当前状态触发对应专家的 AI 生成

    适用场景：
    - 确认进入新状态后（如 research/outline/draft/polish），调用此接口让专家开始工作
    - research/outline/draft 状态会自动检索 Obsidian 知识库，注入 RAG 上下文

    **feedback**: 修改建议（可选，仅在重新生成时使用）
    """
    feedback = request.feedback if request else None
    result = wechat_writer_service.generate_current_state(
        db, current_user.id, session_id, feedback=feedback
    )
    return unified_response(data=result)


@router.post("/sessions/{session_id}/regenerate", summary="重新生成当前步骤的输出")
async def regenerate_current_step(
    session_id: int,
    request: StateTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    重新生成当前步骤的输出

    - **feedback**: 用户填写的修改建议（可选，留空则 AI 自动换角度）
    """
    result = wechat_writer_service.regenerate(
        db, current_user.id, session_id, feedback=request.feedback
    )
    return unified_response(data=result)


@router.post("/sessions/{session_id}/rollback", summary="回退到指定状态")
async def rollback_to_state(
    session_id: int,
    request: StateTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    回退到指定的前置状态

    - **target_state**: 目标状态（必须是当前状态的前置状态）
    - **feedback**: 回退原因（可选）
    """
    if not request.target_state:
        raise ValueError("target_state 不能为空")
    result = wechat_writer_service.rollback(
        db, current_user.id, session_id,
        target_state=request.target_state.value if hasattr(request.target_state, 'value') else request.target_state,
        reason=request.feedback or "",
    )
    return unified_response(data=result)


# ========== 资料卡片 ==========

@router.get("/sessions/{session_id}/materials", summary="获取资料卡片列表")
async def list_materials(
    session_id: int,
    source_type: Optional[str] = Query(None, description="来源类型: obsidian/knowledge_base/web"),
    is_useful: Optional[bool] = Query(None, description="是否有用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话的资料卡片列表"""
    items = wechat_writer_service.get_materials(db, current_user.id, session_id, source_type, is_useful)
    return unified_response(data=[MaterialResponse.model_validate(m).model_dump() for m in items])


@router.post("/sessions/{session_id}/materials", summary="创建资料卡片")
async def create_material(
    session_id: int,
    request: MaterialCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动创建一条资料卡片"""
    material = wechat_writer_service.create_material(
        db, current_user.id, session_id,
        source_type=request.source_type,
        title=request.title,
        url=request.url,
        core_idea=request.core_idea,
        useful_snippets=request.useful_snippets,
        credibility_score=request.credibility_score,
        suggested_usage=request.suggested_usage,
        tags=request.tags,
    )
    return unified_response(data=MaterialResponse.model_validate(material).model_dump())


@router.put("/materials/{material_id}", summary="更新资料卡片")
async def update_material(
    material_id: int,
    request: MaterialUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新资料卡片（标记有用/无用、编辑标签、调整可信度）"""
    material = wechat_writer_service.update_material(
        db, current_user.id, material_id,
        is_useful=request.is_useful,
        tags=request.tags,
        credibility_score=request.credibility_score,
    )
    return unified_response(data=MaterialResponse.model_validate(material).model_dump())


@router.delete("/materials/{material_id}", summary="删除资料卡片")
async def delete_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除一条资料卡片"""
    wechat_writer_service.delete_material(db, current_user.id, material_id)
    return unified_response(message="删除成功")


@router.post("/sessions/{session_id}/materials/parse", summary="从 AI 输出批量解析资料卡片")
async def parse_materials(
    session_id: int,
    request: MaterialParseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    从研究员的 AI 输出文本中解析资料卡片并批量保存

    研究员生成的资料卡片格式：标题、来源、可信度、核心观点、可用片段等
    """
    materials = wechat_writer_service.parse_and_save_materials(
        db, current_user.id, session_id, request.ai_output
    )
    return unified_response(
        data=[MaterialResponse.model_validate(m).model_dump() for m in materials],
        message=f"成功解析并保存 {len(materials)} 条资料卡片"
    )


# ========== 输出版本 ==========

@router.get("/sessions/{session_id}/outputs", summary="获取输出版本列表")
async def list_outputs(
    session_id: int,
    step: Optional[str] = Query(None, description="步骤筛选: topic/research/outline/draft/polish"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话的输出版本列表"""
    items = wechat_writer_service.get_outputs(db, current_user.id, session_id, step)
    return unified_response(data=[i.__dict__ for i in items])


# ========== SSE 流式输出 ==========

@router.get("/sessions/{session_id}/stream", summary="SSE 流式输出 AI 生成（EventSource 方式）")
async def stream_session_get(
    session_id: int,
    token: str = Query(..., description="JWT 认证令牌（EventSource 不支持 header，用 query 参数）"),
    feedback: Optional[str] = Query(None, description="修改建议（重新生成时使用）"),
    db: Session = Depends(get_db),
):
    """
    SSE 流式输出 AI 生成过程（EventSource 方式）

    **注意**: 原生 EventSource 不支持自定义 header，认证通过 `token` query 参数传递

    推送事件格式（每行都是 SSE data）：
    - `{"type": "chunk", "content": "..."}` - 增量内容块
    - `{"type": "done", "full_content": "...", "state": "...", "expert": "..."}` - 生成完成
    - `{"type": "error", "message": "..."}` - 错误
    """
    from app.core.auth import decode_access_token
    from app.plugins.user.models import User
    import json

    # 通过 query token 认证
    payload = decode_access_token(token)
    if not payload:
        async def _error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': '认证令牌无效'})}\n\n"
        return StreamingResponse(_error_gen(), media_type="text/event-stream")

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        async def _error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': '用户不存在'})}\n\n"
        return StreamingResponse(_error_gen(), media_type="text/event-stream")

    async def _sse_gen():
        try:
            async for data in wechat_writer_service.generate_current_state_stream(
                db, user.id, session_id, feedback=feedback
            ):
                yield f"data: {data}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/generate/stream", summary="SSE 流式输出 AI 生成（POST 方式，推荐）")
async def stream_session_post(
    session_id: int,
    request: StateTransitionRequest = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    SSE 流式输出 AI 生成过程（POST 方式，推荐）

    支持通过 Authorization header 认证，比 GET query token 方式更安全。
    前端请使用 fetch + ReadableStream 方式消费，不要用 EventSource。

    推送事件格式同 GET 版本。
    """
    import json

    feedback = request.feedback if request else None

    async def _sse_gen():
        try:
            async for data in wechat_writer_service.generate_current_state_stream(
                db, current_user.id, session_id, feedback=feedback
            ):
                yield f"data: {data}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


# ========== 导出文章 ==========

@router.get("/sessions/{session_id}/export", summary="导出文章为 Markdown")
async def export_article(
    session_id: int,
    format: str = Query("markdown", description="导出格式: markdown/txt"),
    token: Optional[str] = Query(None, description="JWT 认证令牌（直接链接下载时通过 query 传递）"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    导出文章为 Markdown 或纯文本格式

    认证方式：
    1. 优先从 `token` query 参数获取（支持 `<a>` 链接直接下载）
    2. 其次从 Authorization header 获取 Bearer token（标准方式）

    优先使用润色稿（polish），没有则使用初稿（draft）
    """
    from fastapi.responses import PlainTextResponse

    current_user = None

    # 方式1：从 query param 获取 token
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = int(payload.get("sub"))
            current_user = db.query(User).filter(User.id == user_id).first()

    # 方式2：从 Authorization header 获取
    if not current_user and request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            header_token = auth_header[7:]
            payload = decode_access_token(header_token)
            if payload:
                user_id = int(payload.get("sub"))
                current_user = db.query(User).filter(User.id == user_id).first()

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证令牌，请登录后重试",
            headers={"WWW-Authenticate": "Bearer"},
        )

    article_content, title = wechat_writer_service.export_article(
        db, current_user.id, session_id
    )

    if not article_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="暂无文章内容可导出，请先完成写作",
        )

    filename = f"{title or 'article'}.md"

    if format == "txt":
        import re
        txt_content = re.sub(r'^#{1,6}\s+', '', article_content, flags=re.MULTILINE)
        txt_content = re.sub(r'\*\*(.+?)\*\*', r'\1', txt_content)
        txt_content = re.sub(r'\*(.+?)\*', r'\1', txt_content)
        txt_content = re.sub(r'`(.+?)`', r'\1', txt_content)
        txt_content = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', txt_content)
        filename = f"{title or 'article'}.txt"
        article_content = txt_content

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
    }
    return PlainTextResponse(article_content, headers=headers)


# ========== 写作模板 ==========

@router.get("/templates", summary="获取写作模板列表")
async def list_templates(
    category: Optional[str] = Query(None, description="按分类筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取可用的写作模板（系统预设 + 自己的 + 公开的）"""
    items = wechat_writer_service.list_templates(db, current_user.id, category)
    return unified_response(data=[TemplateResponse.model_validate(t).model_dump() for t in items])


@router.get("/templates/{template_id}", summary="获取模板详情")
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个模板的详细信息"""
    template = wechat_writer_service.get_template(db, current_user.id, template_id)
    if not template:
        from app.core.exceptions import BusinessException
        raise BusinessException("模板不存在或无权限查看")
    return unified_response(data=TemplateResponse.model_validate(template).model_dump())


@router.post("/templates", summary="创建自定义模板")
async def create_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建一个新的写作模板"""
    template = wechat_writer_service.create_template(
        db, current_user.id,
        name=request.name,
        description=request.description,
        category=request.category,
        icon=request.icon,
        topic_prompt=request.topic_prompt,
        research_prompt=request.research_prompt,
        outline_prompt=request.outline_prompt,
        writer_prompt=request.writer_prompt,
        suggested_topics=request.suggested_topics,
        default_style=request.default_style,
        default_audience=request.default_audience,
        is_public=request.is_public,
    )
    return unified_response(data=TemplateResponse.model_validate(template).model_dump())


@router.put("/templates/{template_id}", summary="更新模板")
async def update_template(
    template_id: int,
    request: TemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新自己的模板（名称、描述、Prompt、分类等）"""
    template = wechat_writer_service.update_template(
        db, current_user.id, template_id,
        **request.model_dump(exclude_unset=True),
    )
    return unified_response(data=TemplateResponse.model_validate(template).model_dump())


@router.delete("/templates/{template_id}", summary="删除模板")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除自己的自定义模板"""
    wechat_writer_service.delete_template(db, current_user.id, template_id)
    return unified_response(message="删除成功")


@router.post("/templates/apply", summary="从模板创建写作会话")
async def apply_template(
    request: TemplateApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    从模板创建一个新的写作会话

    - 自动增加模板使用次数
    - 可选：用户自定义主题覆盖模板推荐
    """
    session = wechat_writer_service.apply_template(
        db, current_user.id,
        template_id=request.template_id,
        topic=request.topic,
    )
    from app.plugins.wechat_writer.schemas import SessionResponse
    return unified_response(
        data=SessionResponse.model_validate(session).model_dump(),
        message="已从模板创建写作会话"
    )


# ========== Obsidian 同步 ==========

@router.post("/obsidian/sync", summary="手动触发 Obsidian 同步")
async def sync_obsidian(
    current_user: User = Depends(get_current_user),
    force: bool = Query(False, description="是否强制全量重新同步（忽略之前的同步状态）"),
):
    """
    手动触发 Obsidian Vault 同步

    执行增量同步：
    - 扫描 Vault 中所有 .md 文件
    - 解析 Frontmatter 和标签
    - 新增/修改的文件向量化后存入 ChromaDB
    - 删除的文件从向量库移除

    返回同步结果统计
    """
    print(f"[Obsidian API] 收到同步请求, user_id={current_user.id}, force={force}")
    if force:
        print(f"[Obsidian API] 强制全量重新同步，清除旧状态")
        obsidian_reader.clear_sync_state(current_user.id)
    result = obsidian_reader.sync(current_user.id)
    print(f"[Obsidian API] 同步完成: {result}")
    return unified_response(data=result)


@router.get("/obsidian/status", summary="获取 Obsidian 同步状态")
async def get_obsidian_status(
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的 Obsidian 同步状态

    返回：
    - vault_path: Vault 路径
    - vault_exists: Vault 是否存在
    - last_sync_time: 上次同步时间戳（0 表示未同步）
    - total_notes: 已索引的笔记数量
    - total_chunks: 向量分块总数
    """
    result = obsidian_reader.get_sync_status(current_user.id)
    return unified_response(data=result)


@router.post("/obsidian/search", summary="在 Obsidian 笔记中语义搜索")
async def search_obsidian(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    在 Obsidian 笔记中进行语义搜索

    - **query**: 搜索关键词（必填）
    - **top_k**: 返回结果数量（可选，默认 5）
    - **tags**: 按标签过滤（可选，列表）
    """
    query = request.get("query", "")
    if not query:
        raise ValueError("query 不能为空")
    top_k = request.get("top_k", 5)
    tags = request.get("tags")
    results = obsidian_reader.search(current_user.id, query, top_k=top_k, tags=tags)
    return unified_response(data=results)
