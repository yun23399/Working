"""数据库连接与会话工厂定义"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

if settings.database_url.startswith("sqlite:///"):
    database_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
