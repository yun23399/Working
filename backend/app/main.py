"""FastAPI 应用入口，提供基础健康检查接口"""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.database import Base, engine

app = FastAPI(title="Multi Agent Platform API")

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """返回服务健康状态，供本地启动验证使用"""

    return {"status": "ok"}
