"""
Tezbarakat Telegram Bot - WebSocket API
用于实时推送日志和状态更新
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import List, Set
import asyncio
import json
from datetime import datetime

import sys
sys.path.append('..')
from services.auth_service import decode_token

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message, default=str, ensure_ascii=False)
        
        async with self._lock:
            disconnected = set()
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    disconnected.add(connection)
            
            # 移除断开的连接
            self.active_connections -= disconnected
    
    async def send_log(self, level: str, message: str, module: str = None):
        """发送日志消息"""
        await self.broadcast({
            "type": "log",
            "data": {
                "level": level,
                "message": message,
                "module": module,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def send_alert(self, alert_type: str, title: str, message: str, severity: str = "info"):
        """发送告警消息"""
        await self.broadcast({
            "type": "alert",
            "data": {
                "type": alert_type,
                "title": title,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def send_status_update(self, status: dict):
        """发送状态更新"""
        await self.broadcast({
            "type": "status",
            "data": status
        })
    
    async def send_new_message(self, message_data: dict):
        """发送新消息通知"""
        await self.broadcast({
            "type": "message",
            "data": message_data
        })
    
    @property
    def connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)


# 全局连接管理器实例
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """获取连接管理器"""
    return manager


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    """WebSocket 端点"""
    # 验证 token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await manager.connect(websocket)
    
    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "WebSocket 连接成功",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # 保持连接并处理消息
        while True:
            try:
                # 等待客户端消息（心跳等）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 60秒超时
                )
                
                # 处理心跳
                if data == "ping":
                    await websocket.send_text("pong")
                
            except asyncio.TimeoutError:
                # 发送心跳检测
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass
    finally:
        await manager.disconnect(websocket)


@router.get("/ws/connections")
async def get_ws_connections():
    """获取 WebSocket 连接数"""
    return {"connections": manager.connection_count}
