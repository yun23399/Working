"""对话模块的请求与响应模型定义"""

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreateSchema(BaseModel):
    """创建对话请求模型，接收对话标题"""

    title: str = Field(min_length=1, max_length=120)


class ConversationResponseSchema(BaseModel):
    """对话响应模型，返回对话基础信息"""

    id: int
    title: str
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
