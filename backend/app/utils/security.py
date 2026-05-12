"""安全工具模块，提供密码哈希与 JWT 读写能力"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """对明文密码执行 bcrypt 哈希，返回可持久化摘要"""

    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与数据库中的 bcrypt 摘要是否匹配"""

    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    """根据用户标识签发带过期时间的访问令牌"""

    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": subject, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """解析访问令牌并返回其中的用户标识"""

    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise JWTError("Token subject is invalid")
    return subject
