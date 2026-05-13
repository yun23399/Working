"""FastAPI 应用入口，提供基础健康检查接口"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agent_role_templates import router as agent_role_templates_router
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.plugins import router as plugins_router
from app.api.system_settings import router as system_settings_router
from app.api.workflows import router as workflows_router
from app.api.ws import router as ws_router
from app.config import settings
from app.utils.logger import configure_logger, get_logger

configure_logger()
logger = get_logger()

app = FastAPI(title="Multi Agent Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(agent_role_templates_router)
app.include_router(conversations_router)
app.include_router(system_settings_router)
app.include_router(plugins_router)
app.include_router(workflows_router)
app.include_router(ws_router)


def build_error_response(
    error: str, code: str, detail: str, status_code: int
) -> JSONResponse:
    """构造统一错误响应体，确保接口错误格式符合规范"""

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "code": code,
            "detail": detail,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """将 FastAPI HTTPException 转换为统一错误响应格式"""

    if isinstance(exc.detail, dict):
        error = str(exc.detail.get("error", "请求失败"))
        code = str(exc.detail.get("code", "HTTP_ERROR"))
        detail = str(exc.detail.get("detail", "请求处理失败"))
    else:
        error = "请求失败"
        code = "HTTP_ERROR"
        detail = str(exc.detail)

    return build_error_response(error, code, detail, exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """将请求参数校验失败转换为统一错误响应格式"""

    first_error = exc.errors()[0] if exc.errors() else {"msg": "请求参数不合法"}
    return build_error_response(
        "请求参数校验失败",
        "VALIDATION_ERROR",
        str(first_error.get("msg", "请求参数不合法")),
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """兜底处理未捕获异常，并记录错误日志"""

    logger.exception("未处理异常: {}", exc)
    return build_error_response(
        "服务器内部错误",
        "INTERNAL_SERVER_ERROR",
        str(exc),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.on_event("startup")
def on_startup() -> None:
    """记录应用启动日志，便于本地验证服务运行状态"""

    logger.info("Multi Agent Platform API 已启动")


@app.get("/health")
def health_check() -> dict[str, str]:
    """返回服务健康状态，供本地启动验证使用"""

    return {"status": "ok"}
