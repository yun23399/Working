"""认证模块的请求与响应模型定义"""

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequestSchema(BaseModel):
    """注册请求模型，接收用户名与密码"""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequestSchema(BaseModel):
    """登录请求模型，接收用户名与密码"""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserResponseSchema(BaseModel):
    """用户响应模型，返回用户基础信息"""

    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponseSchema(BaseModel):
    """登录成功响应模型，返回访问令牌与用户信息"""

    access_token: str
    token_type: str
    user: UserResponseSchema
