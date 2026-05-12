"""WebSocket 路由模块，负责连接管理与实时消息推送"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.database import SessionLocal
from app.services.auth_service import get_user_by_id
from app.services.conversation_service import (
    ConversationNotFoundError,
    get_conversation_by_owner,
)
from app.utils.security import decode_access_token

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器，维护每个对话的活动连接列表"""

    def __init__(self) -> None:
        """初始化连接池映射，按对话编号维护连接集合"""

        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket) -> None:
        """接受连接并将其加入指定对话的连接池"""

        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket) -> None:
        """移除断开的连接，并在列表为空时清理对话键"""

        connections = self.active_connections.get(conversation_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and conversation_id in self.active_connections:
            del self.active_connections[conversation_id]

    async def broadcast(
        self, message_type: str, conversation_id: int, payload: dict[str, Any]
    ) -> None:
        """向指定对话的所有连接广播标准化 WebSocket 消息"""

        message = {
            "type": message_type,
            "conversation_id": str(conversation_id),
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        for websocket in list(self.active_connections.get(conversation_id, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(conversation_id, websocket)


connection_manager = ConnectionManager()


def extract_token_from_websocket(websocket: WebSocket) -> str | None:
    """从查询参数或请求头提取 WebSocket 鉴权令牌"""

    token = websocket.query_params.get("token")
    if token:
        return token

    authorization = websocket.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return None


def ensure_conversation_access(token: str, conversation_id: int) -> None:
    """校验令牌与对话归属，防止越权建立实时连接"""

    user_id = int(decode_access_token(token))
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        if user is None:
            raise JWTError("User not found")

        try:
            get_conversation_by_owner(db, conversation_id, user)
        except ConversationNotFoundError as exc:
            raise PermissionError("Conversation access forbidden") from exc


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int) -> None:
    """建立对话级 WebSocket 连接，并在连接期间维持事件监听"""

    try:
        token = extract_token_from_websocket(websocket)
        if token is None:
            await websocket.close(code=4401, reason="Missing token")
            return

        ensure_conversation_access(token, conversation_id)
        await connection_manager.connect(conversation_id, websocket)
        await connection_manager.broadcast(
            "log",
            conversation_id,
            {
                "level": "INFO",
                "message": "WebSocket 连接已建立",
                "agent_id": "system",
            },
        )

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(conversation_id, websocket)
    except PermissionError:
        await websocket.close(code=4403, reason="Conversation access forbidden")
    except (JWTError, ValueError):
        await websocket.close(code=4401, reason="Invalid token")
    except Exception:
        connection_manager.disconnect(conversation_id, websocket)
        await websocket.close(code=1011, reason="WebSocket server error")
