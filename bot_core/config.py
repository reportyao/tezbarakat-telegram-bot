"""
Tezbarakat Telegram Bot - Bot 核心服务配置
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache
import os


class BotSettings(BaseSettings):
    """Bot 核心服务配置类"""
    
    # Telegram API 配置
    telegram_api_id: int = Field(
        default=0,
        description="Telegram API ID"
    )
    telegram_api_hash: str = Field(
        default="",
        description="Telegram API Hash"
    )
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/tezbarakat_bot",
        description="PostgreSQL 数据库连接字符串"
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
    dify_confidence_threshold: float = Field(
        default=0.7,
        description="Dify 置信度阈值"
    )
    
    # 防风控配置
    private_message_interval_minutes: int = Field(
        default=5,
        description="同一账号对不同用户发送私信的最小间隔（分钟）"
    )
    user_cooldown_days: int = Field(
        default=3,
        description="对同一用户的私信间隔（天）"
    )
    daily_private_message_limit: int = Field(
        default=20,
        description="单账号每日私信上限"
    )
    hourly_group_reply_limit: int = Field(
        default=3,
        description="单群每小时回复上限"
    )
    
    # 延迟配置
    reply_delay_min_seconds: int = Field(
        default=10,
        description="回复延迟最小秒数"
    )
    reply_delay_max_seconds: int = Field(
        default=60,
        description="回复延迟最大秒数"
    )
    typing_duration_min_seconds: int = Field(
        default=2,
        description="打字状态最小持续秒数"
    )
    typing_duration_max_seconds: int = Field(
        default=5,
        description="打字状态最大持续秒数"
    )
    
    # 活跃时段配置
    active_hours_start: int = Field(
        default=8,
        description="活跃时段开始（小时，塔吉克斯坦时间）"
    )
    active_hours_end: int = Field(
        default=24,
        description="活跃时段结束（小时，塔吉克斯坦时间）"
    )
    
    # 功能开关
    enable_group_reply: bool = Field(
        default=True,
        description="是否启用群内回复"
    )
    enable_private_message: bool = Field(
        default=True,
        description="是否启用私信"
    )
    enable_dify_analysis: bool = Field(
        default=True,
        description="是否启用 Dify 意图分析"
    )
    
    # 回复模板
    group_reply_template: str = Field(
        default="您好 {username}！感谢您的咨询，我们的专业顾问会尽快与您联系。",
        description="群内回复模板"
    )
    private_reply_template: str = Field(
        default="您好！感谢您对我们服务的关注。我是 Tezbarakat 的客服，很高兴为您服务。请问有什么可以帮助您的？",
        description="私信回复模板"
    )
    
    # 简单延迟配置（兼容旧代码）
    reply_delay_seconds: int = Field(
        default=30,
        description="回复延迟秒数（简化版）"
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
    
    # 内部 API 配置
    api_host: str = Field(
        default="0.0.0.0",
        description="内部 API 监听地址"
    )
    api_port: int = Field(
        default=8001,
        description="内部 API 监听端口"
    )
    
    # Web 后台 API 地址（用于回调）
    web_backend_url: str = Field(
        default="http://localhost:8000",
        description="Web 后台 API 地址"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_bot_settings() -> BotSettings:
    """获取配置单例"""
    return BotSettings()


# 导出配置实例
bot_settings = get_bot_settings()
