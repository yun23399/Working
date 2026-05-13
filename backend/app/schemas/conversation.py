"""对话模块的请求与响应模型定义"""

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreateSchema(BaseModel):
    """创建对话请求模型，接收对话标题"""

    title: str = Field(min_length=1, max_length=120)
    manager_role: str = Field(default="general_manager", min_length=1, max_length=50)


class ConversationManagerRoleUpdateSchema(BaseModel):
    """更新总代理角色的请求模型"""

    manager_role: str = Field(min_length=1, max_length=50)


class ManagerProgressSchema(BaseModel):
    """总代理需求收集进度模型，供前端展示理解程度与下一步动作"""

    selected_role: str
    completion_score: int = Field(ge=0, le=100)
    readiness_threshold: int = Field(ge=50, le=100)
    is_ready_to_start: bool
    missing_slots: list[str]
    collected_points: list[str]
    suggested_next_questions: list[str]
    summary: str


class ConversationResponseSchema(BaseModel):
    """对话响应模型，返回对话基础信息"""

    id: int
    title: str
    manager_role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponseSchema(BaseModel):
    """消息响应模型，返回消息详情与时间信息"""

    id: int
    conversation_id: int
    role: str
    content: str
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequestSchema(BaseModel):
    """发送消息请求模型，接收用户输入内容"""

    content: str = Field(min_length=1, max_length=4000)


class ChatAcceptedSchema(BaseModel):
    """聊天请求受理响应模型，表示消息已入队处理"""

    message_id: int
    conversation_id: int
    accepted: bool


class ConversationManagerStateResponseSchema(BaseModel):
    """总代理状态响应模型，供聊天页轮询查看任务准备进度"""

    conversation_id: int
    title: str
    manager_progress: ManagerProgressSchema
