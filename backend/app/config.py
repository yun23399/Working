"""应用配置定义，统一从环境变量读取参数"""

import os
from pathlib import Path
from secrets import token_urlsafe

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
ROOT_DIR = ROOT_ENV_FILE.parent


class Settings(BaseSettings):
    """应用配置对象，集中管理服务运行参数"""

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    frontend_app_url: str = "http://127.0.0.1:5173"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    image_model: str = "gpt-image-1"
    image_size: str = "1024x1024"
    image_quality: str = "medium"
    image_timeout_seconds: int = 60
    llm_provider: str = "auto"
    llm_model: str = ""
    llm_timeout_seconds: int = 60
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
    notifications_enabled: bool = True
    notification_sound_enabled: bool = True
    max_concurrent_workflows: int = 3
    code_exec_timeout: int = 30
    sandbox_enabled: bool = False

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    @property
    def workspace_dir_path(self) -> Path:
        """返回基于仓库根目录解析后的工作区路径"""

        workspace_path = Path(self.workspace_dir)
        if workspace_path.is_absolute():
            return workspace_path
        return (ROOT_DIR / workspace_path).resolve()

    @property
    def log_dir_path(self) -> Path:
        """返回基于仓库根目录解析后的日志目录路径"""

        log_path = Path(self.log_dir)
        if log_path.is_absolute():
            return log_path
        return (ROOT_DIR / log_path).resolve()

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """将逗号分隔的跨域来源配置转换为列表"""

        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]


settings = Settings()


def reload_settings() -> None:
    """重新从环境变量和根目录 `.env` 载入配置，供设置页实时生效使用"""

    refreshed_settings = Settings()
    for field_name in Settings.model_fields:
        setattr(settings, field_name, getattr(refreshed_settings, field_name))

    os.environ["MAX_CONCURRENT_WORKFLOWS"] = str(settings.max_concurrent_workflows)
