"""应用配置定义，统一从环境变量读取参数"""

from secrets import token_urlsafe

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置对象，集中管理服务运行参数"""

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    jwt_secret_key: str = token_urlsafe(32)
    jwt_expire_minutes: int = 10080
    workspace_dir: str = "./workspace"
    log_dir: str = "./logs"
    cors_allow_origins: str = (
        "http://127.0.0.1:5173,"
        "http://localhost:5173,"
        "http://127.0.0.1:5174,"
        "http://localhost:5174,"
        "http://127.0.0.1:4173,"
        "http://localhost:4173"
    )
    max_concurrent_workflows: int = 3
    code_exec_timeout: int = 30
    sandbox_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """将逗号分隔的跨域来源配置转换为列表"""

        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
