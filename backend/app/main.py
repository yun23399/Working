"""FastAPI 应用入口，提供基础健康检查接口"""

from fastapi import FastAPI

app = FastAPI(title="Multi Agent Platform API")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """返回服务健康状态，供本地启动验证使用"""

    return {"status": "ok"}
