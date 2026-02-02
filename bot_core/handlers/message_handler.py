"""
Tezbarakat Telegram Bot - 消息处理器
处理群组消息和私信，支持多轮对话获客
"""

import asyncio
import random
import re
from datetime import datetime
from typing import Optional, List, Set
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser
from loguru import logger
import pytz

from config import bot_settings
from services.telegram_client import client_manager
from services.dify_service import dify_service
from services.database import db_service


def detect_language(text: str) -> str:
    """检测文本语言（俄语/塔吉克语/混合）"""
    # 塔吉克语特有字符
    tajik_chars = set('ғҒӣӢқҚӯҮҳҲҷҶ')
    # 西里尔字母
    cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    
    has_tajik = any(c in tajik_chars for c in text)
    has_cyrillic = any(c in cyrillic_chars for c in text)
    
    if has_tajik:
        return "tj" if not has_cyrillic else "mixed"
    elif has_cyrillic:
        return "ru"
    else:
        return "ru"  # 默认俄语


class MessageHandler:
    """消息处理器类"""
    
    def __init__(self):
        self._keywords: List[str] = []
        self._monitored_groups: Set[int] = set()
        self._timezone = pytz.timezone(bot_settings.timezone)
        self._running = False
        self._our_user_ids: Set[int] = set()  # 存储我们账号的用户ID
    
    async def initialize(self):
        """初始化处理器"""
        # 加载关键词
        await self.reload_keywords()
        
        # 加载监听群组
        await self.reload_groups()
        
        # 注册消息处理器
        client_manager.add_message_handler(self.handle_group_message)
        client_manager.add_private_message_handler(self.handle_private_message)
        
        self._running = True
        logger.info("消息处理器初始化完成")
    
    async def reload_keywords(self):
        """重新加载关键词"""
        try:
            self._keywords = await db_service.get_active_keywords()
            logger.info(f"已加载 {len(self._keywords)} 个关键词")
        except Exception as e:
            logger.error(f"加载关键词失败: {e}")
            self._keywords = []
    
    async def reload_groups(self):
        """重新加载监听群组"""
        try:
            group_ids = await db_service.get_active_group_ids()
            self._monitored_groups = set(group_ids)
            logger.info(f"已加载 {len(self._monitored_groups)} 个监听群组")
        except Exception as e:
            logger.error(f"加载群组失败: {e}")
            self._monitored_groups = set()
    
    def add_group(self, group_id: int):
        """添加监听群组"""
        self._monitored_groups.add(group_id)
        logger.info(f"添加监听群组: {group_id}")
    
    def remove_group(self, group_id: int):
        """移除监听群组"""
        self._monitored_groups.discard(group_id)
        logger.info(f"移除监听群组: {group_id}")
    
    def add_our_user_id(self, user_id: int):
        """添加我们账号的用户ID"""
        self._our_user_ids.add(user_id)
    
    def is_active_hours(self) -> bool:
        """检查是否在活跃时段"""
        now = datetime.now(self._timezone)
        hour = now.hour
        is_active = bot_settings.active_hours_start <= hour < bot_settings.active_hours_end
        if not is_active:
            logger.debug(f"当前不在活跃时段: 当前时间={hour}:00, 活跃时段={bot_settings.active_hours_start}:00-{bot_settings.active_hours_end}:00")
        return is_active
    
    def match_keywords(self, text: str) -> Optional[str]:
        """匹配关键词"""
        if not text:
            return None
        
        text_lower = text.lower()
        for keyword in self._keywords:
            # 支持多语言匹配（塔吉克语、俄语等）
            if keyword.lower() in text_lower:
                return keyword
        
        return None
    
    def _format_template(self, template: str, username: Optional[str] = None, 
                         first_name: Optional[str] = None) -> str:
        """格式化回复模板"""
        name = username or first_name or "朋友"
        return template.format(
            username=f"@{username}" if username else name,
            name=name,
            first_name=first_name or ""
        )
    
    def _build_conversation_history(self, existing_history: str, user_message: str, bot_reply: str) -> str:
        """构建对话历史"""
        new_entry = f"用户: {user_message}\n助手: {bot_reply}"
        if existing_history:
            return f"{existing_history}\n{new_entry}"
        return new_entry
    
    async def handle_group_message(
        self,
        event: events.NewMessage.Event,
        phone: str,
        client: TelegramClient
    ):
        """处理群组消息"""
        try:
            # 检查是否在监听列表
            # Telegram 的 chat_id 对于群组是负数，需要取绝对值比较
            chat_id = event.chat_id
            chat_id_abs = abs(chat_id)
            logger.info(f"收到消息 - chat_id: {chat_id}, chat_id_abs: {chat_id_abs}, monitored: {self._monitored_groups}")
            if chat_id_abs not in self._monitored_groups:
                logger.debug(f"群组 {chat_id_abs} 不在监听列表中")
                return
            
            # 检查是否在活跃时段
            if not self.is_active_hours():
                return
            
            # 获取消息信息
            message = event.message
            text = message.text or message.message or ""
            
            if not text:
                return
            
            # 获取发送者信息
            sender = await event.get_sender()
            if not isinstance(sender, TelegramUser):
                return
            
            user_id = sender.id
            username = sender.username
            first_name = sender.first_name
            last_name = sender.last_name
            
            # 忽略机器人自己的消息
            if user_id in self._our_user_ids:
                return
            
            # 忽略机器人账号
            if sender.bot:
                return
            
            logger.debug(f"收到群消息: {chat_id_abs} - {user_id} - {text[:50]}...")
            
            # 1. 关键词匹配
            matched_keyword = self.match_keywords(text)
            triggered_keyword = matched_keyword is not None
            
            # 2. 检查用户冷却期
            if triggered_keyword:
                is_cooling = await db_service.check_user_cooldown(user_id)
                if is_cooling:
                    logger.debug(f"用户 {user_id} 在冷却期，跳过")
                    # 保存消息记录但不处理
                    await db_service.save_message(
                        group_id=chat_id_abs,
                        user_id=user_id,
                        text=text,
                        message_id=message.id,
                        triggered_keyword=triggered_keyword,
                        matched_keyword=matched_keyword
                    )
                    return
            
            # 3. 处理触发的消息
            dify_result = None
            triggered_dify = False
            dify_confidence = None
            
            if triggered_keyword:
                # 增加关键词命中计数
                await db_service.increment_keyword_hit(matched_keyword)
                
                # 检测用户语言
                user_language = detect_language(text)
                
                # 检查是否启用 Dify 分析
                if bot_settings.enable_dify_analysis:
                    # 调用 Dify 多轮对话工作流（首次触发，stage=0）
                    dify_result = await dify_service.analyze_intent(
                        message_text=text,
                        user_id=user_id,
                        username=username,
                        current_stage=0,  # 首次触发
                        conversation_history="",
                        original_intent=matched_keyword,
                        user_language=user_language
                    )
                    
                    triggered_dify = dify_result.get("should_continue", False)
                    dify_confidence = dify_result.get("confidence", 0)
                    
                    # 如果 Dify 返回应该继续对话，创建对话记录
                    if triggered_dify:
                        # 创建新的对话记录
                        conversation = await db_service.get_or_create_conversation(
                            user_id=user_id,
                            original_intent=matched_keyword,
                            user_language=user_language
                        )
                        
                        # 更新对话状态
                        next_stage = dify_result.get("next_stage", 1)
                        reply_text = dify_result.get("private_reply", "") or dify_result.get("group_reply", "")
                        new_history = self._build_conversation_history("", text, reply_text)
                        
                        await db_service.update_conversation(
                            conversation_id=conversation.id,
                            current_stage=next_stage,
                            conversation_history=new_history,
                            original_intent=matched_keyword,
                            user_language=user_language
                        )
                        
                        logger.info(f"创建多轮对话: user={user_id}, stage=0->{next_stage}, intent={matched_keyword}")
                        
                        # 统计：新对话开始
                        await db_service.increment_conversation_started()
                        await db_service.increment_stage_stat(next_stage)
                else:
                    # 不使用 Dify，直接使用模板回复
                    triggered_dify = True  # 关键词匹配即触发
                    dify_confidence = 1.0
                    
                    # 构建模板回复
                    dify_result = {
                        "is_opportunity": True,
                        "should_continue": True,
                        "confidence": 1.0,
                        "group_reply": self._format_template(
                            bot_settings.group_reply_template,
                            username=username,
                            first_name=first_name
                        ),
                        "private_reply": self._format_template(
                            bot_settings.private_reply_template,
                            username=username,
                            first_name=first_name
                        ),
                        "category": "keyword_match",
                        "next_stage": 1
                    }
            
            # 4. 保存消息记录
            await db_service.save_message(
                group_id=chat_id_abs,
                user_id=user_id,
                text=text,
                message_id=message.id,
                triggered_keyword=triggered_keyword,
                matched_keyword=matched_keyword,
                triggered_dify=triggered_dify,
                dify_confidence=dify_confidence
            )
            
            # 5. 创建或更新用户记录
            await db_service.get_or_create_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            # 6. 执行回复策略
            if triggered_dify and dify_result:
                await self._execute_reply_strategy(
                    event=event,
                    user_id=user_id,
                    username=username,
                    group_id=chat_id_abs,
                    dify_result=dify_result
                )
                
        except Exception as e:
            logger.error(f"处理群消息时出错: {e}", exc_info=True)
    
    async def handle_private_message(
        self,
        event: events.NewMessage.Event,
        phone: str,
        client: TelegramClient
    ):
        """处理私信消息（多轮对话）"""
        try:
            # 获取消息信息
            message = event.message
            text = message.text or message.message or ""
            
            if not text:
                return
            
            # 获取发送者信息
            sender = await event.get_sender()
            if not isinstance(sender, TelegramUser):
                return
            
            user_id = sender.id
            username = sender.username
            first_name = sender.first_name
            
            # 忽略机器人自己的消息
            if user_id in self._our_user_ids:
                return
            
            # 忽略机器人账号
            if sender.bot:
                return
            
            logger.info(f"收到私信: {user_id} ({username}) - {text[:50]}...")
            
            # 检查是否启用 Dify 分析
            if bot_settings.enable_dify_analysis:
                # 获取用户的活跃对话
                conversation = await db_service.get_active_conversation(user_id)
                
                if not conversation:
                    # 没有活跃对话，可能是用户主动发起的私信
                    # 创建新对话，从 stage 1 开始
                    user_language = detect_language(text)
                    conversation = await db_service.get_or_create_conversation(
                        user_id=user_id,
                        original_intent="user_initiated",
                        user_language=user_language
                    )
                    logger.info(f"用户 {user_id} 主动发起私信，创建新对话")
                
                # 获取对话状态
                current_stage = getattr(conversation, 'current_stage', 1) or 1
                conversation_history = getattr(conversation, 'conversation_history', "") or ""
                original_intent = getattr(conversation, 'original_intent', "") or ""
                user_language = getattr(conversation, 'user_language', "ru") or "ru"
                
                # 如果对话已经结束（stage >= 6），不再回复
                if current_stage >= 6:
                    logger.info(f"用户 {user_id} 的对话已结束 (stage={current_stage})")
                    return
                
                # 调用 Dify 多轮对话工作流
                reply_text, _, workflow_result = await dify_service.chat_with_knowledge(
                    message_text=text,
                    user_id=user_id,
                    conversation_id=getattr(conversation, 'dify_conversation_id', None),
                    current_stage=current_stage,
                    conversation_history=conversation_history,
                    original_intent=original_intent,
                    user_language=user_language
                )
                
                # 获取下一阶段
                should_continue = workflow_result.get("should_continue", False)
                next_stage = workflow_result.get("next_stage", current_stage + 1)
                
                # 更新对话历史
                if reply_text:
                    new_history = self._build_conversation_history(conversation_history, text, reply_text)
                else:
                    new_history = conversation_history
                
                # 统计：收到用户回复
                await db_service.increment_user_reply_received()
                
                # 更新对话状态
                if should_continue:
                    await db_service.update_conversation(
                        conversation_id=conversation.id,
                        current_stage=next_stage,
                        conversation_history=new_history
                    )
                    logger.info(f"多轮对话继续: user={user_id}, stage={current_stage}->{next_stage}")
                    
                    # 统计：阶段达成
                    await db_service.increment_stage_stat(next_stage)
                    
                    # 如果到达 Stage 5（提供链接），记录完成并附加邀请链接
                    if next_stage >= bot_settings.invite_link_stage:
                        await db_service.increment_conversation_completed()
                        await db_service.increment_stat('links_provided')
                        # 在回复后附加邀请链接
                        if bot_settings.invite_link and reply_text:
                            reply_text = f"{reply_text}\n\n{bot_settings.invite_link}"
                            logger.info(f"已附加邀请链接到回复: user={user_id}")
                else:
                    # 对话结束，但如果还没发送链接，则附加链接
                    if current_stage < bot_settings.invite_link_stage and bot_settings.invite_link and reply_text:
                        reply_text = f"{reply_text}\n\n{bot_settings.invite_link}"
                        await db_service.increment_stat('links_provided')
                        logger.info(f"对话结束前附加邀请链接: user={user_id}")
                    
                    await db_service.update_conversation(
                        conversation_id=conversation.id,
                        current_stage=6,
                        conversation_history=new_history,
                        status='closed'
                    )
                    logger.info(f"多轮对话结束: user={user_id}, stage={current_stage}->6")
                
            else:
                # 不使用 Dify，使用模板回复
                reply_text = self._format_template(
                    bot_settings.private_reply_template,
                    username=username,
                    first_name=first_name
                )
            
            # 发送回复
            if reply_text:
                # 随机延迟
                delay = random.randint(
                    bot_settings.reply_delay_min_seconds,
                    bot_settings.reply_delay_max_seconds
                )
                await asyncio.sleep(delay)
                
                # 发送打字状态
                typing_duration = random.randint(
                    bot_settings.typing_duration_min_seconds,
                    bot_settings.typing_duration_max_seconds
                )
                
                # 发送消息
                try:
                    await client_manager.send_message(
                        phone=phone,
                        chat_id=user_id,
                        text=reply_text,
                        typing_duration=typing_duration
                    )
                    
                    # 保存回复记录
                    await db_service.save_reply(
                        user_id=user_id,
                        reply_type='private',
                        sent_text=reply_text,
                        status='sent'
                    )
                    
                    logger.info(f"已回复私信: {user_id}")
                except Exception as e:
                    logger.error(f"发送私信回复失败: {e}")
                    # 保存失败记录
                    await db_service.save_reply(
                        user_id=user_id,
                        reply_type='private',
                        sent_text=reply_text,
                        status='failed',
                        error_message=str(e)
                    )
                
        except Exception as e:
            logger.error(f"处理私信时出错: {e}", exc_info=True)
    
    async def _execute_reply_strategy(
        self,
        event: events.NewMessage.Event,
        user_id: int,
        username: Optional[str],
        group_id: int,
        dify_result: dict
    ):
        """执行回复策略（多轮对话第一轮）"""
        try:
            group_reply_text = dify_result.get("group_reply", "")
            private_reply_text = dify_result.get("private_reply", "")
            
            # 随机延迟
            delay = random.randint(
                bot_settings.reply_delay_min_seconds,
                bot_settings.reply_delay_max_seconds
            )
            await asyncio.sleep(delay)
            
            # 1. 群内回复（破冰共情阶段）
            if bot_settings.enable_group_reply and group_reply_text:
                # 检查群组回复限制
                can_reply = await db_service.check_group_reply_limit(group_id)
                
                if can_reply:
                    # 获取可用账号
                    account = await db_service.get_available_account_for_sending()
                    
                    if account:
                        # 构建回复文本（不带 @ 提及，更自然）
                        full_reply = group_reply_text.strip()
                        
                        # 发送打字状态和消息
                        typing_duration = random.randint(
                            bot_settings.typing_duration_min_seconds,
                            bot_settings.typing_duration_max_seconds
                        )
                        
                        try:
                            await client_manager.send_message(
                                phone=account.phone_number,
                                chat_id=group_id,
                                text=full_reply,
                                reply_to=event.message.id,
                                typing_duration=typing_duration
                            )
                            
                            # 更新统计（群内回复不更新 last_used_at，只有私信才更新）
                            await db_service.increment_group_reply_count(group_id)
                            # await db_service.update_account_last_used(account.id)  # 移除，避免影响私信发送间隔计算
                            
                            # 保存回复记录
                            await db_service.save_reply(
                                user_id=user_id,
                                reply_type='group',
                                account_id=account.id,
                                group_id=group_id,
                                sent_text=full_reply,
                                status='sent'
                            )
                            
                            logger.info(f"已发送群内回复: {group_id} -> {user_id}")
                            
                        except Exception as e:
                            logger.error(f"发送群内回复失败: {e}")
                            # 保存失败记录
                            await db_service.save_reply(
                                user_id=user_id,
                                reply_type='group',
                                account_id=account.id,
                                group_id=group_id,
                                sent_text=full_reply,
                                status='failed',
                                error_message=str(e)
                            )
                    else:
                        logger.warning("没有可用账号发送群内回复")
                else:
                    logger.debug(f"群组 {group_id} 已达到每小时回复上限")
            
            # 2. 主动发起私聊（多轮对话的第一轮私信）
            if bot_settings.enable_private_message and private_reply_text:
                # 额外延迟，避免立即私信，更自然
                pm_delay = random.randint(30, 90)
                logger.info(f"等待 {pm_delay} 秒后发送私信给用户 {user_id}")
                await asyncio.sleep(pm_delay)
                
                # 获取可用账号
                account = await db_service.get_available_account_for_sending()
                
                if account:
                    typing_duration = random.randint(
                        bot_settings.typing_duration_min_seconds,
                        bot_settings.typing_duration_max_seconds
                    )
                    
                    try:
                        await client_manager.send_message(
                            phone=account.phone_number,
                            chat_id=user_id,
                            text=private_reply_text,
                            typing_duration=typing_duration
                        )
                        
                        # 更新用户私信时间
                        await db_service.update_user_last_pm_time(user_id)
                        await db_service.update_account_last_used(account.id)
                        
                        # 保存回复记录
                        await db_service.save_reply(
                            user_id=user_id,
                            reply_type='private',
                            account_id=account.id,
                            sent_text=private_reply_text,
                            status='sent'
                        )
                        
                        logger.info(f"已主动发送私信: {user_id}")
                        
                    except Exception as e:
                        logger.error(f"发送私信失败: {e}")
                        # 保存失败记录
                        await db_service.save_reply(
                            user_id=user_id,
                            reply_type='private',
                            account_id=account.id,
                            sent_text=private_reply_text,
                            status='failed',
                            error_message=str(e)
                        )
                        
                        # 创建告警
                        await db_service.create_alert(
                            alert_type='send_failed',
                            title='私信发送失败',
                            message=f"向用户 {user_id} 发送私信失败: {str(e)}",
                            severity='warning',
                            account_id=account.id
                        )
                else:
                    logger.warning("没有可用账号发送私信")
                        
        except Exception as e:
            logger.error(f"执行回复策略时出错: {e}", exc_info=True)


# 全局消息处理器实例
message_handler = MessageHandler()
