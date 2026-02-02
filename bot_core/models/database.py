"""
Tezbarakat Telegram Bot - 数据库连接和 ORM 模型
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Float,
    DateTime, Date, ForeignKey, JSON, Index, CheckConstraint,
    create_engine, event
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

import os
import sys

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import bot_settings as settings


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


class Account(Base):
    """机器人账号表"""
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    session_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default='logging_in')
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    daily_message_count: Mapped[int] = mapped_column(Integer, default=0)
    daily_reset_date: Mapped[date] = mapped_column(Date, default=func.current_date())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    replies: Mapped[List["Reply"]] = relationship("Reply", back_populates="account")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="account")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="account")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('logging_in', 'active', 'cooling_down', 'limited', 'banned')",
            name='valid_status'
        ),
        Index('idx_accounts_status', 'status'),
        Index('idx_accounts_last_used', 'last_used_at'),
    )


class Group(Base):
    """监听群组表"""
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    group_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hourly_reply_count: Mapped[int] = mapped_column(Integer, default=0)
    hourly_reset_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_groups_active', 'is_active'),
        Index('idx_groups_group_id', 'group_id'),
    )


class Keyword(Base):
    """关键词表"""
    __tablename__ = "keywords"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_keywords_active', 'is_active'),
    )


class User(Base):
    """目标用户表"""
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_private_message_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_messages_received: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_users_last_pm', 'last_private_message_time'),
    )


class Message(Base):
    """监听消息记录表"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triggered_keyword: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_keyword: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    triggered_dify: Mapped[bool] = mapped_column(Boolean, default=False)
    dify_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_messages_timestamp', 'timestamp'),
        Index('idx_messages_group', 'group_id'),
        Index('idx_messages_user', 'user_id'),
        Index('idx_messages_triggered', 'triggered_keyword', 'triggered_dify'),
    )


class Reply(Base):
    """回复记录表"""
    __tablename__ = "replies"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    sent_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='sent')
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="replies")
    
    __table_args__ = (
        CheckConstraint("type IN ('group', 'private')", name='valid_reply_type'),
        Index('idx_replies_timestamp', 'timestamp'),
        Index('idx_replies_account', 'account_id'),
        Index('idx_replies_user', 'user_id'),
        Index('idx_replies_type', 'type'),
    )


class Conversation(Base):
    """对话记录表"""
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    dify_conversation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='active')
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    # 多轮对话状态管理
    current_stage: Mapped[int] = mapped_column(Integer, default=0)  # 当前对话阶段 0-6
    conversation_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 对话历史
    original_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 原始意图
    user_language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 用户语言 ru/tj/mixed
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="conversations")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'closed', 'expired')", name='valid_conv_status'),
        Index('idx_conversations_user', 'user_id'),
        Index('idx_conversations_status', 'status'),
    )


class AppConfig(Base):
    """应用配置表"""
    __tablename__ = "app_config"
    
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Alert(Base):
    """告警记录表"""
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default='info')
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="alerts")
    
    __table_args__ = (
        CheckConstraint("severity IN ('info', 'warning', 'error', 'critical')", name='valid_severity'),
        Index('idx_alerts_created', 'created_at'),
    )


class Statistic(Base):
    """统计数据表"""
    __tablename__ = "statistics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, default=func.current_date())
    total_messages_monitored: Mapped[int] = mapped_column(Integer, default=0)
    keyword_triggered_count: Mapped[int] = mapped_column(Integer, default=0)
    dify_triggered_count: Mapped[int] = mapped_column(Integer, default=0)
    group_replies_sent: Mapped[int] = mapped_column(Integer, default=0)
    private_messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    new_users_count: Mapped[int] = mapped_column(Integer, default=0)
    active_accounts_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_statistics_date', 'date'),
    )


async def get_db() -> AsyncSession:
    """获取数据库会话的依赖注入函数"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
