"""应用配置定义，统一从环境变量读取参数"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置对象，集中管理服务运行参数"""

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    workspace_dir: str = "./workspace"
    log_dir: str = "./logs"
    max_concurrent_workflows: int = 3
    code_exec_timeout: int = 30
    sandbox_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
