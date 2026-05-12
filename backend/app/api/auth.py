"""认证路由模块，提供注册、登录和受保护用户信息接口"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequestSchema,
    RegisterRequestSchema,
    TokenResponseSchema,
    UserResponseSchema,
)
from app.services.auth_service import (
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    login_user,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequestSchema,
    db: Session = Depends(get_db),
) -> UserResponseSchema:
    """注册新用户，成功后返回用户基础信息"""

    try:
        user = register_user(db, payload)
        return UserResponseSchema.model_validate(user)
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "用户名已存在",
                "code": "USER_ALREADY_EXISTS",
                "detail": f"用户名 `{exc}` 已被占用",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "用户注册失败",
                "code": "REGISTER_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post("/login", response_model=TokenResponseSchema)
async def login(
    payload: LoginRequestSchema,
    db: Session = Depends(get_db),
) -> TokenResponseSchema:
    """校验用户凭证并返回访问令牌"""

    try:
        access_token, user = login_user(db, payload)
        return TokenResponseSchema(
            access_token=access_token,
            token_type="bearer",
            user=UserResponseSchema.model_validate(user),
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "用户名或密码错误",
                "code": "INVALID_CREDENTIALS",
                "detail": f"账号 `{exc}` 登录失败",
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "用户登录失败",
                "code": "LOGIN_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponseSchema:
    """返回当前登录用户信息，用于鉴权联调验证"""

    return UserResponseSchema.model_validate(current_user)
