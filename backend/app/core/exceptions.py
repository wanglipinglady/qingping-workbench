"""
统一异常处理模块
定义业务异常类和全局异常处理器，统一响应格式
"""
import time
from typing import Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings


class BusinessException(Exception):
    """
    业务异常基类
    所有业务逻辑中的异常都应使用此异常抛出
    """

    def __init__(
        self,
        message: str = "业务异常",
        code: int = 1000,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None,
    ):
        """
        初始化业务异常

        Args:
            message: 异常消息
            code: 业务错误码（非 0 表示错误）
            http_status: HTTP 状态码
            data: 附加数据
        """
        self.message = message
        self.code = code
        self.http_status = http_status
        self.data = data
        super().__init__(message)


def unified_response(
    code: int = 0,
    message: str = "success",
    data: Any = None,
) -> dict:
    """
    构造统一响应格式

    Args:
        code: 状态码，0 表示成功，非 0 表示失败
        message: 消息
        data: 数据

    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }


def register_exception_handlers(app) -> None:
    """
    注册全局异常处理器

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(BusinessException)
    async def business_exception_handler(
        request: Request, exc: BusinessException
    ) -> JSONResponse:
        """处理业务异常"""
        return JSONResponse(
            status_code=exc.http_status,
            content=unified_response(
                code=exc.code,
                message=exc.message,
                data=exc.data,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """处理 HTTP 异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content=unified_response(
                code=exc.status_code,
                message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """处理请求参数验证异常"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "参数验证失败")
            errors.append(f"{field}: {msg}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=unified_response(
                code=422,
                message="请求参数验证失败",
                data={"errors": errors},
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """处理所有未捕获的异常"""
        # 打印异常信息，便于调试
        import traceback
        traceback.print_exc()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=unified_response(
                code=500,
                message=f"服务器内部错误: {str(exc)}" if settings.DEBUG else "服务器内部错误",
                data=None,
            ),
        )
