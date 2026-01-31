"""
Tezbarakat Telegram Bot - 数据库服务层
提供所有数据库操作的封装
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func, and_, or_, desc, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

import sys
sys.path.append('..')
from models.database import (
    Account, Group, Keyword, User, Message, Reply,
    Conversation, AppConfig, Alert, Statistic
)


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =====================================================
    # 账号操作
    # =====================================================
    
    async def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """根据 ID 获取账号"""
        result = await self.session.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()
    
    async def get_account_by_phone(self, phone_number: str) -> Optional[Account]:
        """根据手机号获取账号"""
        result = await self.session.execute(
            select(Account).where(Account.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
    
    async def get_all_accounts(self, status: Optional[str] = None) -> List[Account]:
        """获取所有账号"""
        query = select(Account).order_by(Account.created_at.desc())
        if status:
            query = query.where(Account.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_available_account(self) -> Optional[Account]:
        """获取一个可用的账号（用于发送消息）"""
        # 优先选择 last_used_at 最早的 active 账号
        result = await self.session.execute(
            select(Account)
            .where(Account.status == 'active')
            .where(or_(
                Account.daily_reset_date < date.today(),
                Account.daily_message_count < 20  # 每日限制
            ))
            .order_by(Account.last_used_at.asc().nullsfirst())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def create_account(self, phone_number: str, session_name: str) -> Account:
        """创建新账号"""
        account = Account(
            phone_number=phone_number,
            session_name=session_name,
            status='logging_in'
        )
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account
    
    async def update_account_status(self, account_id: int, status: str) -> Optional[Account]:
        """更新账号状态"""
        account = await self.get_account_by_id(account_id)
        if account:
            account.status = status
            account.updated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(account)
        return account
    
    async def update_account_last_used(self, account_id: int) -> Optional[Account]:
        """更新账号最后使用时间"""
        account = await self.get_account_by_id(account_id)
        if account:
            account.last_used_at = datetime.now()
            # 检查是否需要重置每日计数
            if account.daily_reset_date < date.today():
                account.daily_message_count = 1
                account.daily_reset_date = date.today()
            else:
                account.daily_message_count += 1
            await self.session.commit()
            await self.session.refresh(account)
        return account
    
    async def delete_account(self, account_id: int) -> bool:
        """删除账号"""
        result = await self.session.execute(
            delete(Account).where(Account.id == account_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_account_stats(self) -> Dict[str, int]:
        """获取账号统计"""
        result = await self.session.execute(
            select(Account.status, func.count(Account.id))
            .group_by(Account.status)
        )
        stats = {row[0]: row[1] for row in result.all()}
        return {
            'total': sum(stats.values()),
            'active': stats.get('active', 0),
            'logging_in': stats.get('logging_in', 0),
            'cooling_down': stats.get('cooling_down', 0),
            'limited': stats.get('limited', 0),
            'banned': stats.get('banned', 0)
        }
    
    # =====================================================
    # 群组操作
    # =====================================================
    
    async def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """根据数据库 ID 获取群组"""
        result = await self.session.execute(
            select(Group).where(Group.id == group_id)
        )
        return result.scalar_one_or_none()
    
    async def get_group_by_telegram_id(self, telegram_group_id: int) -> Optional[Group]:
        """根据 Telegram 群组 ID 获取群组"""
        result = await self.session.execute(
            select(Group).where(Group.group_id == telegram_group_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_groups(self, active_only: bool = False) -> List[Group]:
        """获取所有群组"""
        query = select(Group).order_by(Group.created_at.desc())
        if active_only:
            query = query.where(Group.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_active_group_ids(self) -> List[int]:
        """获取所有活跃群组的 Telegram ID"""
        result = await self.session.execute(
            select(Group.group_id).where(Group.is_active == True)
        )
        return [row[0] for row in result.all()]
    
    async def create_group(
        self,
        group_id: int,
        group_name: Optional[str] = None,
        group_username: Optional[str] = None
    ) -> Group:
        """创建新群组"""
        group = Group(
            group_id=group_id,
            group_name=group_name,
            group_username=group_username
        )
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group
    
    async def update_group(
        self,
        group_db_id: int,
        group_name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Group]:
        """更新群组"""
        group = await self.get_group_by_id(group_db_id)
        if group:
            if group_name is not None:
                group.group_name = group_name
            if is_active is not None:
                group.is_active = is_active
            await self.session.commit()
            await self.session.refresh(group)
        return group
    
    async def delete_group(self, group_db_id: int) -> bool:
        """删除群组"""
        result = await self.session.execute(
            delete(Group).where(Group.id == group_db_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def check_group_reply_limit(self, telegram_group_id: int, limit: int = 3) -> bool:
        """检查群组每小时回复是否超限"""
        group = await self.get_group_by_telegram_id(telegram_group_id)
        if not group:
            return False
        
        # 检查是否需要重置计数
        if group.hourly_reset_time < datetime.now() - timedelta(hours=1):
            group.hourly_reply_count = 0
            group.hourly_reset_time = datetime.now()
            await self.session.commit()
        
        return group.hourly_reply_count < limit
    
    async def increment_group_reply_count(self, telegram_group_id: int):
        """增加群组回复计数"""
        group = await self.get_group_by_telegram_id(telegram_group_id)
        if group:
            group.hourly_reply_count += 1
            await self.session.commit()
    
    # =====================================================
    # 关键词操作
    # =====================================================
    
    async def get_keyword_by_id(self, keyword_id: int) -> Optional[Keyword]:
        """根据 ID 获取关键词"""
        result = await self.session.execute(
            select(Keyword).where(Keyword.id == keyword_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_keywords(self, active_only: bool = False) -> List[Keyword]:
        """获取所有关键词"""
        query = select(Keyword).order_by(Keyword.hit_count.desc())
        if active_only:
            query = query.where(Keyword.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_active_keywords_list(self) -> List[str]:
        """获取所有活跃关键词的文本列表"""
        result = await self.session.execute(
            select(Keyword.keyword).where(Keyword.is_active == True)
        )
        return [row[0] for row in result.all()]
    
    async def create_keyword(self, keyword: str) -> Keyword:
        """创建新关键词"""
        kw = Keyword(keyword=keyword.lower().strip())
        self.session.add(kw)
        await self.session.commit()
        await self.session.refresh(kw)
        return kw
    
    async def create_keywords_batch(self, keywords: List[str]) -> List[Keyword]:
        """批量创建关键词"""
        created = []
        for kw_text in keywords:
            kw_text = kw_text.lower().strip()
            if not kw_text:
                continue
            # 检查是否已存在
            existing = await self.session.execute(
                select(Keyword).where(Keyword.keyword == kw_text)
            )
            if existing.scalar_one_or_none():
                continue
            kw = Keyword(keyword=kw_text)
            self.session.add(kw)
            created.append(kw)
        await self.session.commit()
        return created
    
    async def update_keyword(
        self,
        keyword_id: int,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Keyword]:
        """更新关键词"""
        kw = await self.get_keyword_by_id(keyword_id)
        if kw:
            if keyword is not None:
                kw.keyword = keyword.lower().strip()
            if is_active is not None:
                kw.is_active = is_active
            await self.session.commit()
            await self.session.refresh(kw)
        return kw
    
    async def delete_keyword(self, keyword_id: int) -> bool:
        """删除关键词"""
        result = await self.session.execute(
            delete(Keyword).where(Keyword.id == keyword_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def increment_keyword_hit(self, keyword_text: str):
        """增加关键词命中计数"""
        await self.session.execute(
            update(Keyword)
            .where(Keyword.keyword == keyword_text.lower())
            .values(hit_count=Keyword.hit_count + 1)
        )
        await self.session.commit()
    
    # =====================================================
    # 用户操作
    # =====================================================
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_users(
        self,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[User], int]:
        """获取所有用户（分页）"""
        # 获取总数
        count_result = await self.session.execute(select(func.count(User.user_id)))
        total = count_result.scalar()
        
        # 获取分页数据
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
    
    async def create_or_update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """创建或更新用户"""
        user = await self.get_user(user_id)
        if user:
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
            self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def check_user_cooldown(self, user_id: int, cooldown_days: int = 3) -> bool:
        """检查用户是否在冷却期"""
        user = await self.get_user(user_id)
        if not user or not user.last_private_message_time:
            return False
        
        cooldown_end = user.last_private_message_time + timedelta(days=cooldown_days)
        return datetime.now() < cooldown_end
    
    async def update_user_last_pm_time(self, user_id: int):
        """更新用户最后私信时间"""
        user = await self.get_user(user_id)
        if user:
            user.last_private_message_time = datetime.now()
            user.total_messages_received += 1
            await self.session.commit()
    
    # =====================================================
    # 消息操作
    # =====================================================
    
    async def create_message(
        self,
        group_id: int,
        user_id: int,
        text: Optional[str] = None,
        message_id: Optional[int] = None,
        triggered_keyword: bool = False,
        matched_keyword: Optional[str] = None,
        triggered_dify: bool = False,
        dify_confidence: Optional[float] = None
    ) -> Message:
        """创建消息记录"""
        message = Message(
            timestamp=datetime.now(),
            group_id=group_id,
            user_id=user_id,
            message_id=message_id,
            text=text,
            triggered_keyword=triggered_keyword,
            matched_keyword=matched_keyword,
            triggered_dify=triggered_dify,
            dify_confidence=dify_confidence
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_messages(
        self,
        page: int = 1,
        page_size: int = 50,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        triggered_only: bool = False
    ) -> Tuple[List[Message], int]:
        """获取消息列表（分页）"""
        query = select(Message)
        count_query = select(func.count(Message.id))
        
        if group_id:
            query = query.where(Message.group_id == group_id)
            count_query = count_query.where(Message.group_id == group_id)
        if user_id:
            query = query.where(Message.user_id == user_id)
            count_query = count_query.where(Message.user_id == user_id)
        if triggered_only:
            query = query.where(or_(
                Message.triggered_keyword == True,
                Message.triggered_dify == True
            ))
            count_query = count_query.where(or_(
                Message.triggered_keyword == True,
                Message.triggered_dify == True
            ))
        
        # 获取总数
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # 获取分页数据
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Message.timestamp.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
    
    # =====================================================
    # 回复操作
    # =====================================================
    
    async def create_reply(
        self,
        user_id: int,
        reply_type: str,
        account_id: Optional[int] = None,
        group_id: Optional[int] = None,
        sent_text: Optional[str] = None,
        conversation_id: Optional[str] = None,
        status: str = 'sent',
        error_message: Optional[str] = None
    ) -> Reply:
        """创建回复记录"""
        reply = Reply(
            timestamp=datetime.now(),
            account_id=account_id,
            user_id=user_id,
            group_id=group_id,
            type=reply_type,
            sent_text=sent_text,
            conversation_id=conversation_id,
            status=status,
            error_message=error_message
        )
        self.session.add(reply)
        await self.session.commit()
        await self.session.refresh(reply)
        return reply
    
    async def get_replies(
        self,
        page: int = 1,
        page_size: int = 50,
        reply_type: Optional[str] = None,
        account_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Tuple[List[Reply], int]:
        """获取回复列表（分页）"""
        query = select(Reply)
        count_query = select(func.count(Reply.id))
        
        if reply_type:
            query = query.where(Reply.type == reply_type)
            count_query = count_query.where(Reply.type == reply_type)
        if account_id:
            query = query.where(Reply.account_id == account_id)
            count_query = count_query.where(Reply.account_id == account_id)
        if user_id:
            query = query.where(Reply.user_id == user_id)
            count_query = count_query.where(Reply.user_id == user_id)
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Reply.timestamp.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
    
    # =====================================================
    # 对话操作
    # =====================================================
    
    async def get_or_create_conversation(
        self,
        user_id: int,
        account_id: Optional[int] = None
    ) -> Conversation:
        """获取或创建对话"""
        result = await self.session.execute(
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
            self.session.add(conversation)
            await self.session.commit()
            await self.session.refresh(conversation)
        
        return conversation
    
    async def update_conversation(
        self,
        conversation_id: int,
        dify_conversation_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Conversation]:
        """更新对话"""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            if dify_conversation_id:
                conversation.dify_conversation_id = dify_conversation_id
            if status:
                conversation.status = status
            conversation.message_count += 1
            conversation.last_message_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(conversation)
        
        return conversation
    
    # =====================================================
    # 配置操作
    # =====================================================
    
    async def get_config(self, key: str) -> Optional[Any]:
        """获取配置值"""
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        config = result.scalar_one_or_none()
        return config.value if config else None
    
    async def get_all_configs(self) -> List[AppConfig]:
        """获取所有配置"""
        result = await self.session.execute(select(AppConfig))
        return list(result.scalars().all())
    
    async def set_config(self, key: str, value: Any, description: Optional[str] = None) -> AppConfig:
        """设置配置值"""
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = AppConfig(key=key, value=value, description=description)
            self.session.add(config)
        
        await self.session.commit()
        await self.session.refresh(config)
        return config
    
    async def set_configs_batch(self, configs: Dict[str, Any]):
        """批量设置配置"""
        for key, value in configs.items():
            await self.set_config(key, value)
    
    # =====================================================
    # 告警操作
    # =====================================================
    
    async def create_alert(
        self,
        alert_type: str,
        title: str,
        message: Optional[str] = None,
        severity: str = 'info',
        account_id: Optional[int] = None
    ) -> Alert:
        """创建告警"""
        alert = Alert(
            type=alert_type,
            title=title,
            message=message,
            severity=severity,
            account_id=account_id
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
    
    async def get_alerts(
        self,
        page: int = 1,
        page_size: int = 50,
        unread_only: bool = False
    ) -> Tuple[List[Alert], int, int]:
        """获取告警列表"""
        query = select(Alert)
        count_query = select(func.count(Alert.id))
        
        if unread_only:
            query = query.where(Alert.is_read == False)
            count_query = count_query.where(Alert.is_read == False)
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # 获取未读数量
        unread_result = await self.session.execute(
            select(func.count(Alert.id)).where(Alert.is_read == False)
        )
        unread_count = unread_result.scalar()
        
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Alert.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total, unread_count
    
    async def mark_alerts_read(self, alert_ids: List[int]):
        """标记告警已读"""
        await self.session.execute(
            update(Alert)
            .where(Alert.id.in_(alert_ids))
            .values(is_read=True)
        )
        await self.session.commit()
    
    async def mark_all_alerts_read(self):
        """标记所有告警已读"""
        await self.session.execute(
            update(Alert).values(is_read=True)
        )
        await self.session.commit()
    
    # =====================================================
    # 统计操作
    # =====================================================
    
    async def get_or_create_today_stats(self) -> Statistic:
        """获取或创建今日统计"""
        result = await self.session.execute(
            select(Statistic).where(Statistic.date == date.today())
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = Statistic(date=date.today())
            self.session.add(stats)
            await self.session.commit()
            await self.session.refresh(stats)
        
        return stats
    
    async def increment_stat(self, field: str, value: int = 1):
        """增加统计计数"""
        stats = await self.get_or_create_today_stats()
        current_value = getattr(stats, field, 0)
        setattr(stats, field, current_value + value)
        await self.session.commit()
    
    async def get_statistics(self, days: int = 7) -> List[Statistic]:
        """获取最近几天的统计"""
        start_date = date.today() - timedelta(days=days - 1)
        result = await self.session.execute(
            select(Statistic)
            .where(Statistic.date >= start_date)
            .order_by(Statistic.date.asc())
        )
        return list(result.scalars().all())
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        today_stats = await self.get_or_create_today_stats()
        account_stats = await self.get_account_stats()
        
        # 群组统计
        group_result = await self.session.execute(
            select(
                func.count(Group.id).label('total'),
                func.sum(func.cast(Group.is_active, Integer)).label('active')
            )
        )
        group_stats = group_result.one()
        
        # 关键词统计
        keyword_result = await self.session.execute(
            select(
                func.count(Keyword.id).label('total'),
                func.sum(func.cast(Keyword.is_active, Integer)).label('active')
            )
        )
        keyword_stats = keyword_result.one()
        
        # 未读告警
        alert_result = await self.session.execute(
            select(func.count(Alert.id))
            .where(Alert.is_read == False)
            .where(Alert.created_at > datetime.now() - timedelta(hours=24))
        )
        unread_alerts = alert_result.scalar()
        
        return {
            'today_messages': today_stats.total_messages_monitored,
            'today_keyword_triggers': today_stats.keyword_triggered_count,
            'today_dify_triggers': today_stats.dify_triggered_count,
            'today_group_replies': today_stats.group_replies_sent,
            'today_private_messages': today_stats.private_messages_sent,
            'today_new_users': today_stats.new_users_count,
            'total_accounts': account_stats['total'],
            'active_accounts': account_stats['active'],
            'limited_accounts': account_stats['limited'],
            'banned_accounts': account_stats['banned'],
            'total_groups': group_stats.total or 0,
            'active_groups': group_stats.active or 0,
            'total_keywords': keyword_stats.total or 0,
            'active_keywords': keyword_stats.active or 0,
            'unread_alerts': unread_alerts or 0
        }
