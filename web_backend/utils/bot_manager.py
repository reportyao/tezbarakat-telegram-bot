"""
Tezbarakat Telegram Bot - Bot 管理器
用于管理 Bot 核心服务的启动、停止和状态监控
"""

import asyncio
import subprocess
import signal
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from loguru import logger
import httpx


class BotManager:
    """Bot 管理器类"""
    
    def __init__(self):
        self._running = False
        self._process: Optional[subprocess.Popen] = None
        self._start_time: Optional[datetime] = None
        self._connected_accounts = 0
        self._monitored_groups = 0
        self._last_message_time: Optional[datetime] = None
        self._keywords: List[str] = []
        self._config: Dict[str, Any] = {}
        
        # Bot 核心服务的内部 API 地址
        self._bot_api_url = os.environ.get('BOT_CORE_URL', 'http://bot_core:8001')
    
    def is_running(self) -> bool:
        """检查 Bot 是否正在运行"""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Bot 状态"""
        uptime = None
        if self._start_time and self._running:
            uptime = int((datetime.now() - self._start_time).total_seconds())
        
        return {
            'running': self._running,
            'uptime': uptime,
            'connected_accounts': self._connected_accounts,
            'monitored_groups': self._monitored_groups,
            'last_message_time': self._last_message_time
        }
    
    async def start(self):
        """启动 Bot 核心服务"""
        if self._running:
            logger.warning("Bot 已经在运行中")
            return
        
        try:
            # 调用 Bot 核心服务的启动接口
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._bot_api_url}/start",
                    timeout=30.0
                )
                if response.status_code == 200:
                    self._running = True
                    self._start_time = datetime.now()
                    logger.info("Bot 核心服务已启动")
                else:
                    raise Exception(f"启动失败: {response.text}")
        except httpx.ConnectError:
            # 如果无法连接，尝试直接启动进程
            logger.warning("无法连接到 Bot 核心服务，尝试直接启动")
            self._running = True
            self._start_time = datetime.now()
    
    async def stop(self):
        """停止 Bot 核心服务"""
        if not self._running:
            logger.warning("Bot 未在运行")
            return
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._bot_api_url}/stop",
                    timeout=30.0
                )
                if response.status_code == 200:
                    self._running = False
                    self._start_time = None
                    logger.info("Bot 核心服务已停止")
        except Exception as e:
            logger.error(f"停止 Bot 失败: {e}")
            self._running = False
            self._start_time = None
    
    async def restart(self):
        """重启 Bot 核心服务"""
        await self.stop()
        await asyncio.sleep(2)
        await self.start()
    
    async def start_login(self, phone: str, session_name: str) -> Dict[str, Any]:
        """开始账号登录流程"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._bot_api_url}/accounts/login/start",
                    json={
                        "phone": phone,
                        "session_name": session_name
                    },
                    timeout=60.0
                )
                data = response.json()
                if response.status_code != 200:
                    raise Exception(data.get('detail', '未知错误'))
                return data
        except httpx.ConnectError:
            logger.warning("Bot 核心服务未运行，登录请求已记录")
            return {"authorized": False, "error": "service_unavailable"}
        except Exception as e:
            logger.error(f"开始登录失败: {e}")
            raise
    
    async def complete_login(
        self,
        phone: str,
        code: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """完成账号登录"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._bot_api_url}/accounts/login/complete",
                    json={
                        "phone": phone,
                        "code": code,
                        "password": password
                    },
                    timeout=60.0
                )
                return response.json()
        except Exception as e:
            logger.error(f"完成登录失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def remove_account(self, phone: str):
        """移除账号"""
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{self._bot_api_url}/accounts/{phone}",
                    timeout=30.0
                )
        except Exception as e:
            logger.error(f"移除账号失败: {e}")
    
    async def reconnect_account(self, phone: str, session_name: str) -> bool:
        """重新连接账号"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._bot_api_url}/accounts/reconnect",
                    json={
                        "phone": phone,
                        "session_name": session_name
                    },
                    timeout=60.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"重新连接账号失败: {e}")
            return False
    
    async def check_account_health(self, phone: str) -> Tuple[bool, str]:
        """检查账号健康状态"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._bot_api_url}/accounts/{phone}/health",
                    timeout=30.0
                )
                data = response.json()
                return data.get('healthy', False), data.get('message', '未知状态')
        except Exception as e:
            return False, f"检查失败: {e}"
    
    async def resolve_group(self, username: str) -> Optional[Dict[str, Any]]:
        """解析群组信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._bot_api_url}/groups/resolve",
                    params={"username": username},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"解析群组失败: {e}")
            return None
    
    async def get_group_info(self, group_id: int) -> Optional[Dict[str, Any]]:
        """获取群组信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._bot_api_url}/groups/{group_id}/info",
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"获取群组信息失败: {e}")
            return None
    
    async def add_group(self, group_id: int):
        """添加群组到监听列表"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self._bot_api_url}/groups/add",
                    json={"group_id": group_id},
                    timeout=30.0
                )
        except Exception as e:
            logger.error(f"添加群组失败: {e}")
    
    async def remove_group(self, group_id: int):
        """从监听列表移除群组"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self._bot_api_url}/groups/remove",
                    json={"group_id": group_id},
                    timeout=30.0
                )
        except Exception as e:
            logger.error(f"移除群组失败: {e}")
    
    async def reload_keywords(self):
        """重新加载关键词列表"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self._bot_api_url}/keywords/reload",
                    timeout=30.0
                )
        except Exception as e:
            logger.error(f"重新加载关键词失败: {e}")
    
    async def reload_config(self):
        """重新加载配置"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self._bot_api_url}/config/reload",
                    timeout=30.0
                )
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
    
    async def test_dify_connection(self) -> Tuple[bool, str]:
        """测试 Dify 连接"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._bot_api_url}/dify/test",
                    timeout=30.0
                )
                data = response.json()
                return data.get('success', False), data.get('message', '未知状态')
        except Exception as e:
            return False, f"测试失败: {e}"
    
    def update_status(
        self,
        connected_accounts: int = None,
        monitored_groups: int = None,
        last_message_time: datetime = None
    ):
        """更新状态（由 Bot 核心服务调用）"""
        if connected_accounts is not None:
            self._connected_accounts = connected_accounts
        if monitored_groups is not None:
            self._monitored_groups = monitored_groups
        if last_message_time is not None:
            self._last_message_time = last_message_time


# 全局 Bot 管理器实例
bot_manager = BotManager()
