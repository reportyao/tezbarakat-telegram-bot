"""
Tezbarakat Telegram Bot - Telegram 客户端管理器
管理多个 Telethon 客户端实例
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError,
    UserBannedInChannelError,
    ChatWriteForbiddenError,
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    PeerFloodError
)
from telethon.tl.types import User, Chat, Channel, Message
from telethon.tl.functions.messages import SetTypingAction
from telethon.tl.types import SendMessageTypingAction
from loguru import logger

from ..config import bot_settings


class TelegramClientManager:
    """Telegram 客户端管理器"""
    
    def __init__(self):
        self._clients: Dict[str, TelegramClient] = {}  # phone -> client
        self._client_status: Dict[str, str] = {}  # phone -> status
        self._login_states: Dict[str, dict] = {}  # phone -> login state
        self._message_handlers: List[Callable] = []
        self._private_message_handlers: List[Callable] = []
        self._main_client: Optional[TelegramClient] = None
        self._main_phone: Optional[str] = None
        
        # 确保 sessions 目录存在
        os.makedirs(bot_settings.sessions_path, exist_ok=True)
    
    def _get_session_path(self, session_name: str) -> str:
        """获取 session 文件路径"""
        return os.path.join(bot_settings.sessions_path, session_name)
    
    async def create_client(self, phone: str, session_name: str) -> TelegramClient:
        """创建新的 Telegram 客户端"""
        session_path = self._get_session_path(session_name)
        
        client = TelegramClient(
            session_path,
            bot_settings.telegram_api_id,
            bot_settings.telegram_api_hash,
            device_model="Desktop",
            system_version="Windows 10",
            app_version="1.0.0",
            lang_code="ru",
            system_lang_code="ru"
        )
        
        self._clients[phone] = client
        self._client_status[phone] = 'created'
        
        return client
    
    async def start_login(self, phone: str, session_name: str) -> dict:
        """开始登录流程"""
        client = await self.create_client(phone, session_name)
        
        try:
            await client.connect()
            
            if await client.is_user_authorized():
                self._client_status[phone] = 'active'
                logger.info(f"账号 {phone} 已授权，无需重新登录")
                return {"status": "authorized", "phone": phone}
            
            # 发送验证码
            sent_code = await client.send_code_request(phone)
            
            self._login_states[phone] = {
                "phone_code_hash": sent_code.phone_code_hash,
                "session_name": session_name,
                "timestamp": datetime.now()
            }
            self._client_status[phone] = 'logging_in'
            
            logger.info(f"验证码已发送到 {phone}")
            return {
                "status": "code_sent",
                "phone": phone,
                "phone_code_hash": sent_code.phone_code_hash
            }
            
        except FloodWaitError as e:
            logger.error(f"发送验证码被限制，需等待 {e.seconds} 秒")
            return {
                "status": "flood_wait",
                "phone": phone,
                "wait_seconds": e.seconds
            }
        except Exception as e:
            logger.error(f"开始登录失败: {e}")
            raise
    
    async def complete_login(
        self,
        phone: str,
        code: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """完成登录流程"""
        if phone not in self._clients:
            raise ValueError(f"未找到账号 {phone} 的客户端")
        
        client = self._clients[phone]
        login_state = self._login_states.get(phone, {})
        
        try:
            if code:
                # 使用验证码登录
                await client.sign_in(
                    phone,
                    code,
                    phone_code_hash=login_state.get("phone_code_hash")
                )
            elif password:
                # 使用两步验证密码
                await client.sign_in(password=password)
            
            self._client_status[phone] = 'active'
            self._login_states.pop(phone, None)
            
            # 获取用户信息
            me = await client.get_me()
            logger.info(f"账号 {phone} 登录成功: {me.first_name}")
            
            return True
            
        except SessionPasswordNeededError:
            logger.info(f"账号 {phone} 需要两步验证密码")
            self._client_status[phone] = 'need_password'
            return False
        except PhoneCodeInvalidError:
            logger.error(f"账号 {phone} 验证码无效")
            return False
        except PhoneCodeExpiredError:
            logger.error(f"账号 {phone} 验证码已过期")
            return False
        except Exception as e:
            logger.error(f"完成登录失败: {e}")
            raise
    
    async def connect_existing(self, phone: str, session_name: str) -> bool:
        """连接已存在的账号"""
        session_path = self._get_session_path(session_name)
        
        if not os.path.exists(f"{session_path}.session"):
            logger.warning(f"Session 文件不存在: {session_path}")
            return False
        
        client = await self.create_client(phone, session_name)
        
        try:
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.warning(f"账号 {phone} 未授权")
                self._client_status[phone] = 'unauthorized'
                return False
            
            self._client_status[phone] = 'active'
            
            # 注册消息处理器
            await self._register_handlers(client, phone)
            
            me = await client.get_me()
            logger.info(f"账号 {phone} 连接成功: {me.first_name}")
            
            return True
            
        except AuthKeyUnregisteredError:
            logger.error(f"账号 {phone} 已被封禁或注销")
            self._client_status[phone] = 'banned'
            return False
        except Exception as e:
            logger.error(f"连接账号失败: {e}")
            self._client_status[phone] = 'error'
            return False
    
    async def disconnect(self, phone: str):
        """断开账号连接"""
        if phone in self._clients:
            client = self._clients[phone]
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"断开连接失败: {e}")
            finally:
                del self._clients[phone]
                self._client_status.pop(phone, None)
    
    async def disconnect_all(self):
        """断开所有连接"""
        phones = list(self._clients.keys())
        for phone in phones:
            await self.disconnect(phone)
    
    def set_main_client(self, phone: str):
        """设置主监听客户端"""
        if phone in self._clients:
            self._main_client = self._clients[phone]
            self._main_phone = phone
            logger.info(f"设置主监听客户端: {phone}")
    
    def get_main_client(self) -> Optional[TelegramClient]:
        """获取主监听客户端"""
        return self._main_client
    
    def get_client(self, phone: str) -> Optional[TelegramClient]:
        """获取指定账号的客户端"""
        return self._clients.get(phone)
    
    def get_available_client(self, exclude_phone: str = None) -> Optional[tuple]:
        """获取一个可用的客户端（用于发送消息）"""
        for phone, status in self._client_status.items():
            if status == 'active' and phone != exclude_phone:
                return phone, self._clients[phone]
        return None
    
    def get_all_clients(self) -> Dict[str, TelegramClient]:
        """获取所有客户端"""
        return self._clients.copy()
    
    def get_client_status(self, phone: str) -> str:
        """获取客户端状态"""
        return self._client_status.get(phone, 'unknown')
    
    def get_all_status(self) -> Dict[str, str]:
        """获取所有客户端状态"""
        return self._client_status.copy()
    
    def add_message_handler(self, handler: Callable):
        """添加群消息处理器"""
        self._message_handlers.append(handler)
    
    def add_private_message_handler(self, handler: Callable):
        """添加私信处理器"""
        self._private_message_handlers.append(handler)
    
    async def _register_handlers(self, client: TelegramClient, phone: str):
        """为客户端注册事件处理器"""
        
        @client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            """处理新消息"""
            try:
                # 判断是群消息还是私信
                if event.is_private:
                    for handler in self._private_message_handlers:
                        await handler(event, phone, client)
                elif event.is_group or event.is_channel:
                    for handler in self._message_handlers:
                        await handler(event, phone, client)
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
    
    async def send_typing_action(self, client: TelegramClient, chat_id: int, duration: int = 3):
        """发送打字状态"""
        try:
            await client(SetTypingAction(
                peer=chat_id,
                action=SendMessageTypingAction()
            ))
            await asyncio.sleep(duration)
        except Exception as e:
            logger.warning(f"发送打字状态失败: {e}")
    
    async def send_message(
        self,
        phone: str,
        chat_id: int,
        text: str,
        reply_to: int = None,
        typing_duration: int = 3
    ) -> Optional[Message]:
        """发送消息"""
        client = self.get_client(phone)
        if not client:
            logger.error(f"未找到账号 {phone} 的客户端")
            return None
        
        try:
            # 发送打字状态
            await self.send_typing_action(client, chat_id, typing_duration)
            
            # 发送消息
            message = await client.send_message(
                chat_id,
                text,
                reply_to=reply_to
            )
            
            logger.info(f"账号 {phone} 发送消息成功")
            return message
            
        except FloodWaitError as e:
            logger.warning(f"账号 {phone} 被限制，需等待 {e.seconds} 秒")
            self._client_status[phone] = 'limited'
            raise
        except UserBannedInChannelError:
            logger.error(f"账号 {phone} 在该群组被禁言")
            raise
        except ChatWriteForbiddenError:
            logger.error(f"账号 {phone} 无法在该群组发送消息")
            raise
        except PeerFloodError:
            logger.error(f"账号 {phone} 发送消息过于频繁")
            self._client_status[phone] = 'limited'
            raise
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise
    
    async def check_account_health(self, phone: str) -> tuple:
        """检查账号健康状态"""
        client = self.get_client(phone)
        if not client:
            return False, "客户端不存在"
        
        try:
            me = await client.get_me()
            if me:
                return True, f"账号正常: {me.first_name}"
            return False, "无法获取账号信息"
        except AuthKeyUnregisteredError:
            self._client_status[phone] = 'banned'
            return False, "账号已被封禁"
        except UserDeactivatedBanError:
            self._client_status[phone] = 'banned'
            return False, "账号已被停用"
        except Exception as e:
            return False, f"检查失败: {str(e)}"
    
    async def resolve_username(self, username: str) -> Optional[dict]:
        """解析用户名获取实体信息"""
        client = self._main_client or next(iter(self._clients.values()), None)
        if not client:
            return None
        
        try:
            entity = await client.get_entity(username)
            
            if isinstance(entity, (Chat, Channel)):
                return {
                    "id": entity.id,
                    "title": entity.title,
                    "username": getattr(entity, 'username', None),
                    "type": "channel" if isinstance(entity, Channel) else "chat"
                }
            elif isinstance(entity, User):
                return {
                    "id": entity.id,
                    "first_name": entity.first_name,
                    "last_name": entity.last_name,
                    "username": entity.username,
                    "type": "user"
                }
            return None
        except Exception as e:
            logger.error(f"解析用户名失败: {e}")
            return None
    
    async def get_entity_info(self, entity_id: int) -> Optional[dict]:
        """获取实体信息"""
        client = self._main_client or next(iter(self._clients.values()), None)
        if not client:
            return None
        
        try:
            entity = await client.get_entity(entity_id)
            
            if isinstance(entity, (Chat, Channel)):
                return {
                    "id": entity.id,
                    "title": entity.title,
                    "username": getattr(entity, 'username', None),
                    "type": "channel" if isinstance(entity, Channel) else "chat"
                }
            elif isinstance(entity, User):
                return {
                    "id": entity.id,
                    "first_name": entity.first_name,
                    "last_name": entity.last_name,
                    "username": entity.username,
                    "type": "user"
                }
            return None
        except Exception as e:
            logger.error(f"获取实体信息失败: {e}")
            return None
    
    @property
    def connected_count(self) -> int:
        """获取已连接的客户端数量"""
        return sum(1 for s in self._client_status.values() if s == 'active')
    
    @property
    def active_phones(self) -> List[str]:
        """获取所有活跃的手机号"""
        return [p for p, s in self._client_status.items() if s == 'active']


# 全局客户端管理器实例
client_manager = TelegramClientManager()
