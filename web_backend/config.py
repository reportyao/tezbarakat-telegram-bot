"""
Tezbarakat Telegram Bot - 配置管理模块
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "Tezbarakat Telegram Bot"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/tezbarakat_bot",
        description="PostgreSQL 数据库连接字符串"
    )
    
    # Redis 配置（可选，用于缓存）
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis 连接字符串"
    )
    
    # Telegram 配置
    telegram_api_id: str = Field(
        default="",
        description="Telegram API ID"
    )
    telegram_api_hash: str = Field(
        default="",
        description="Telegram API Hash"
    )
    
    # Dify 配置
    dify_api_url: str = Field(
        default="http://localhost/v1",
        description="Dify API 地址"
    )
    dify_api_key: str = Field(
        default="",
        description="Dify API 密钥"
    )
    dify_workflow_id: str = Field(
        default="",
        description="Dify 意图分析工作流 ID"
    )
    dify_knowledge_workflow_id: str = Field(
        default="",
        description="Dify 知识库对话工作流 ID"
    )
    
    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 密钥"
    )
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,  # 7 天
        description="访问令牌过期时间（分钟）"
    )
    
    # 管理员配置
    admin_username: str = Field(
        default="admin",
        description="管理员用户名"
    )
    admin_password: str = Field(
        default="admin123",
        description="管理员密码"
    )
    
    # 时区配置
    timezone: str = Field(
        default="Asia/Dushanbe",
        description="塔吉克斯坦时区"
    )
    
    # Session 文件存储路径
    sessions_path: str = Field(
        default="./sessions",
        description="Telethon session 文件存储路径"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    log_path: str = Field(
        default="./logs",
        description="日志文件存储路径"
    )
    
    # CORS 配置
    cors_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="允许的跨域来源"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出配置实例
settings = get_settings()
