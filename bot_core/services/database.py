"""
Tezbarakat Telegram Bot - Bot 核心数据库服务
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, select, update, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger
from contextlib import asynccontextmanager
import pytz

from ..config import bot_settings

# 导入 ORM 模型（从 web_backend 共享）
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'web_backend'))
from models.database import (
    Base, Account, Group, Keyword, User, Message, Reply,
    Conversation, AppConfig, Alert, Statistic
)


# 创建异步引擎
engine = create_async_engine(
    bot_settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
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


def get_current_time():
    """获取当前时间（带时区）"""
    return datetime.now(pytz.timezone(bot_settings.timezone))


def get_utc_now():
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


class BotDatabaseService:
    """Bot 核心数据库服务类"""
    
    def __init__(self):
        self._tz = pytz.timezone(bot_settings.timezone)
    
    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def close_session(self):
        """关闭数据库连接池"""
        await engine.dispose()
    
    # =====================================================
    # 账号操作
    # =====================================================
    
    async def get_active_accounts(self) -> List[Account]:
        """获取所有活跃账号"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Account).where(Account.status == 'active')
            )
            return list(result.scalars().all())
    
    async def get_all_accounts(self) -> List[Account]:
        """获取所有账号"""
        async with self.get_session() as session:
            result = await session.execute(select(Account))
            return list(result.scalars().all())
    
    async def get_available_account_for_sending(self) -> Optional[Account]:
        """获取一个可用于发送消息的账号"""
        async with self.get_session() as session:
            today = date.today()
            
            # 获取所有活跃账号
            result = await session.execute(
                select(Account)
                .where(Account.status == 'active')
                .where(or_(
                    Account.daily_reset_date < today,
                    Account.daily_message_count < bot_settings.daily_private_message_limit
                ))
                .order_by(Account.last_used_at.asc().nullsfirst())
            )
            
            accounts = list(result.scalars().all())
            
            # 检查私信间隔
            min_interval = timedelta(minutes=bot_settings.private_message_interval_minutes)
            now = get_utc_now()
            
            for account in accounts:
                if account.last_used_at is None:
                    return account
                
                # 处理时区问题
                last_used = account.last_used_at
                if last_used.tzinfo is None:
                    last_used = last_used.replace(tzinfo=timezone.utc)
                
                if now - last_used >= min_interval:
                    return account
            
            return None
    
    async def update_account_status(self, phone: str, status: str):
        """更新账号状态"""
        async with self.get_session() as session:
            await session.execute(
                update(Account)
                .where(Account.phone_number == phone)
                .values(status=status, updated_at=get_utc_now())
            )
    
    async def update_account_last_used(self, account_id: int):
        """更新账号最后使用时间"""
        async with self.get_session() as session:
            # 获取账号
            result = await session.execute(
                select(Account).where(Account.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account:
                today = date.today()
                
                # 检查是否需要重置每日计数
                if account.daily_reset_date is None or account.daily_reset_date < today:
                    account.daily_message_count = 1
                    account.daily_reset_date = today
                else:
                    account.daily_message_count += 1
                
                account.last_used_at = get_utc_now()
    
    async def reset_daily_account_counts(self):
        """重置所有账号的每日消息计数"""
        async with self.get_session() as session:
            await session.execute(
                update(Account)
                .values(
                    daily_message_count=0,
                    daily_reset_date=date.today()
                )
            )
            logger.info("已重置所有账号的每日消息计数")
    
    async def recover_cooling_accounts(self):
        """恢复冷却中的账号"""
        async with self.get_session() as session:
            await session.execute(
                update(Account)
                .where(Account.status == 'cooling_down')
                .values(status='active')
            )
            logger.info("已恢复所有冷却中的账号")
    
    # =====================================================
    # 群组操作
    # =====================================================
    
    async def get_active_groups(self) -> List[Group]:
        """获取所有活跃群组"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Group).where(Group.is_active == True)
            )
            return list(result.scalars().all())
    
    async def get_active_group_ids(self) -> List[int]:
        """获取所有活跃群组的 Telegram ID"""
        groups = await self.get_active_groups()
        return [g.group_id for g in groups]
    
    async def check_group_reply_limit(self, group_id: int) -> bool:
        """检查群组每小时回复是否超限"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Group).where(Group.group_id == group_id)
            )
            group = result.scalar_one_or_none()
            
            if not group:
                return False
            
            now = get_utc_now()
            
            # 处理时区问题
            reset_time = group.hourly_reset_time
            if reset_time and reset_time.tzinfo is None:
                reset_time = reset_time.replace(tzinfo=timezone.utc)
            
            # 检查是否需要重置计数
            if reset_time is None or reset_time < now - timedelta(hours=1):
                group.hourly_reply_count = 0
                group.hourly_reset_time = now
            
            return group.hourly_reply_count < bot_settings.hourly_group_reply_limit
    
    async def increment_group_reply_count(self, group_id: int):
        """增加群组回复计数"""
        async with self.get_session() as session:
            await session.execute(
                update(Group)
                .where(Group.group_id == group_id)
                .values(hourly_reply_count=Group.hourly_reply_count + 1)
            )
    
    async def reset_hourly_group_counts(self):
        """重置所有群组的每小时回复计数"""
        async with self.get_session() as session:
            await session.execute(
                update(Group)
                .values(
                    hourly_reply_count=0,
                    hourly_reset_time=get_utc_now()
                )
            )
            logger.info("已重置所有群组的每小时回复计数")
    
    # =====================================================
    # 关键词操作
    # =====================================================
    
    async def get_active_keywords(self) -> List[str]:
        """获取所有活跃关键词"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Keyword.keyword).where(Keyword.is_active == True)
            )
            return [row[0] for row in result.all()]
    
    async def increment_keyword_hit(self, keyword: str):
        """增加关键词命中计数"""
        async with self.get_session() as session:
            # 先尝试精确匹配
            result = await session.execute(
                select(Keyword).where(Keyword.keyword == keyword)
            )
            kw = result.scalar_one_or_none()
            
            if kw:
                kw.hit_count += 1
            else:
                # 尝试不区分大小写匹配
                result = await session.execute(
                    select(Keyword).where(func.lower(Keyword.keyword) == keyword.lower())
                )
                kw = result.scalar_one_or_none()
                if kw:
                    kw.hit_count += 1
    
    # =====================================================
    # 用户操作
    # =====================================================
    
    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """获取或创建用户"""
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # 更新信息
                if username:
                    user.username = username
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
            else:
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                await session.flush()
                
                # 更新统计
                await self._increment_stat_internal(session, 'new_users_count')
            
            return user
    
    async def check_user_cooldown(self, user_id: int) -> bool:
        """检查用户是否在冷却期"""
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.last_private_message_time:
                return False
            
            # 处理时区问题
            last_pm_time = user.last_private_message_time
            if last_pm_time.tzinfo is None:
                last_pm_time = last_pm_time.replace(tzinfo=timezone.utc)
            
            cooldown_end = last_pm_time + timedelta(days=bot_settings.user_cooldown_days)
            return get_utc_now() < cooldown_end
    
    async def update_user_last_pm_time(self, user_id: int):
        """更新用户最后私信时间"""
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(
                    last_private_message_time=get_utc_now(),
                    total_messages_received=User.total_messages_received + 1
                )
            )
    
    # =====================================================
    # 消息操作
    # =====================================================
    
    async def save_message(
        self,
        group_id: int,
        user_id: int,
        text: str,
        message_id: int = None,
        triggered_keyword: bool = False,
        matched_keyword: str = None,
        triggered_dify: bool = False,
        dify_confidence: float = None
    ) -> Message:
        """保存消息记录"""
        async with self.get_session() as session:
            message = Message(
                timestamp=get_utc_now(),
                group_id=group_id,
                user_id=user_id,
                message_id=message_id,
                text=text,
                triggered_keyword=triggered_keyword,
                matched_keyword=matched_keyword,
                triggered_dify=triggered_dify,
                dify_confidence=dify_confidence
            )
            session.add(message)
            await session.flush()
            
            # 更新统计
            await self._increment_stat_internal(session, 'total_messages_monitored')
            if triggered_keyword:
                await self._increment_stat_internal(session, 'keyword_triggered_count')
            if triggered_dify:
                await self._increment_stat_internal(session, 'dify_triggered_count')
            
            return message
    
    # =====================================================
    # 回复操作
    # =====================================================
    
    async def save_reply(
        self,
        user_id: int,
        reply_type: str,
        account_id: int = None,
        group_id: int = None,
        sent_text: str = None,
        conversation_id: str = None,
        status: str = 'sent',
        error_message: str = None
    ) -> Reply:
        """保存回复记录"""
        async with self.get_session() as session:
            reply = Reply(
                timestamp=get_utc_now(),
                account_id=account_id,
                user_id=user_id,
                group_id=group_id,
                type=reply_type,
                sent_text=sent_text,
                conversation_id=conversation_id,
                status=status,
                error_message=error_message
            )
            session.add(reply)
            await session.flush()
            
            # 更新统计
            if status == 'sent':
                if reply_type == 'group':
                    await self._increment_stat_internal(session, 'group_replies_sent')
                elif reply_type == 'private':
                    await self._increment_stat_internal(session, 'private_messages_sent')
            
            return reply
    
    # =====================================================
    # 对话操作
    # =====================================================
    
    async def get_or_create_conversation(
        self,
        user_id: int,
        account_id: int = None
    ) -> Conversation:
        """获取或创建对话"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .where(Conversation.status == 'active')
                .order_by(Conversation.last_message_at.desc())
                .limit(1)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                conversation = Conversation(
                    user_id=user_id,
                    account_id=account_id
                )
                session.add(conversation)
                await session.flush()
            
            return conversation
    
    async def update_conversation(
        self,
        conversation_id: int,
        dify_conversation_id: str = None
    ):
        """更新对话"""
        async with self.get_session() as session:
            values = {
                "message_count": Conversation.message_count + 1,
                "last_message_at": get_utc_now()
            }
            if dify_conversation_id:
                values["dify_conversation_id"] = dify_conversation_id
            
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(**values)
            )
    
    # =====================================================
    # 配置操作
    # =====================================================
    
    async def get_config(self, key: str) -> Any:
        """获取配置值"""
        async with self.get_session() as session:
            result = await session.execute(
                select(AppConfig).where(AppConfig.key == key)
            )
            config = result.scalar_one_or_none()
            return config.value if config else None
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        async with self.get_session() as session:
            result = await session.execute(select(AppConfig))
            configs = result.scalars().all()
            return {c.key: c.value for c in configs}
    
    # =====================================================
    # 告警操作
    # =====================================================
    
    async def create_alert(
        self,
        alert_type: str,
        title: str,
        message: str = None,
        severity: str = 'info',
        account_id: int = None
    ) -> Alert:
        """创建告警"""
        async with self.get_session() as session:
            alert = Alert(
                type=alert_type,
                title=title,
                message=message,
                severity=severity,
                account_id=account_id
            )
            session.add(alert)
            await session.flush()
            return alert
    
    # =====================================================
    # 统计操作
    # =====================================================
    
    async def _get_or_create_today_stats_internal(self, session: AsyncSession) -> Statistic:
        """获取或创建今日统计（内部方法，需要传入session）"""
        today = date.today()
        result = await session.execute(
            select(Statistic).where(Statistic.date == today)
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = Statistic(date=today)
            session.add(stats)
            await session.flush()
        
        return stats
    
    async def _increment_stat_internal(self, session: AsyncSession, field: str, value: int = 1):
        """增加统计计数（内部方法，需要传入session）"""
        stats = await self._get_or_create_today_stats_internal(session)
        current_value = getattr(stats, field, 0) or 0
        setattr(stats, field, current_value + value)
    
    async def get_or_create_today_stats(self) -> Statistic:
        """获取或创建今日统计"""
        async with self.get_session() as session:
            return await self._get_or_create_today_stats_internal(session)
    
    async def increment_stat(self, field: str, value: int = 1):
        """增加统计计数"""
        async with self.get_session() as session:
            await self._increment_stat_internal(session, field, value)


# 全局数据库服务实例
db_service = BotDatabaseService()
