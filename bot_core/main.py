"""
Tezbarakat Telegram Bot - Bot 核心服务主入口
"""

import sys
import os
import asyncio
from datetime import datetime
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from loguru import logger
import uvicorn

from config import bot_settings
from services.telegram_client import client_manager
from services.dify_service import dify_service
from services.database import db_service
from handlers.message_handler import message_handler


# 配置日志
os.makedirs(bot_settings.log_path, exist_ok=True)
logger.add(
    f"{bot_settings.log_path}/bot_core.log",
    rotation="10 MB",
    retention="7 days",
    level=bot_settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
)


# 全局状态
class BotState:
    running: bool = False
    start_time: Optional[datetime] = None
    health_check_task: Optional[asyncio.Task] = None


bot_state = BotState()


async def start_bot():
    """启动 Bot"""
    if bot_state.running:
        logger.warning("Bot 已经在运行中")
        return
    
    logger.info("正在启动 Bot 核心服务...")
    
    try:
        # 初始化消息处理器
        await message_handler.initialize()
        
        # 加载并连接所有账号
        accounts = await db_service.get_all_accounts()
        
        for account in accounts:
            if account.get('status') in ['active', 'logging_in']:
                try:
                    success = await client_manager.connect_existing(
                        phone=account['phone_number'],
                        session_name=account['session_name']
                    )
                    if success:
                        logger.info(f"账号 {account['phone_number']} 连接成功")
                    else:
                        logger.warning(f"账号 {account['phone_number']} 连接失败")
                        await db_service.update_account_status(
                            account['phone_number'], 'limited'
                        )
                except Exception as e:
                    logger.error(f"连接账号 {account['phone_number']} 时出错: {e}")
        
        # 设置主监听账号（第一个活跃账号）
        active_phones = client_manager.active_phones
        if active_phones:
            client_manager.set_main_client(active_phones[0])
        
        # 启动健康检查任务
        bot_state.health_check_task = asyncio.create_task(health_check_loop())
        
        bot_state.running = True
        bot_state.start_time = datetime.now()
        
        logger.info(f"Bot 核心服务已启动，连接了 {client_manager.connected_count} 个账号")
        
    except Exception as e:
        logger.error(f"启动 Bot 失败: {e}", exc_info=True)
        raise


async def stop_bot():
    """停止 Bot"""
    if not bot_state.running:
        logger.warning("Bot 未在运行")
        return
    
    logger.info("正在停止 Bot 核心服务...")
    
    try:
        # 取消健康检查任务
        if bot_state.health_check_task:
            bot_state.health_check_task.cancel()
            try:
                await bot_state.health_check_task
            except asyncio.CancelledError:
                pass
        
        # 断开所有连接
        await client_manager.disconnect_all()
        
        # 关闭数据库连接
        await db_service.close_session()
        
        bot_state.running = False
        bot_state.start_time = None
        
        logger.info("Bot 核心服务已停止")
        
    except Exception as e:
        logger.error(f"停止 Bot 时出错: {e}", exc_info=True)


async def health_check_loop():
    """健康检查循环"""
    while True:
        try:
            await asyncio.sleep(3600)  # 每小时检查一次
            
            if not bot_state.running:
                break
            
            logger.info("执行账号健康检查...")
            
            for phone in client_manager.active_phones:
                is_healthy, message = await client_manager.check_account_health(phone)
                
                if not is_healthy:
                    logger.warning(f"账号 {phone} 健康检查失败: {message}")
                    await db_service.update_account_status(phone, 'limited')
                    
                    # 创建告警
                    await db_service.create_alert(
                        alert_type='account_health',
                        title=f'账号健康检查失败',
                        message=f'账号 {phone}: {message}',
                        severity='warning'
                    )
                    
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"健康检查出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Bot 核心服务 API 启动中...")
    yield
    logger.info("Bot 核心服务 API 关闭中...")
    await stop_bot()


# 创建 FastAPI 应用
app = FastAPI(
    title="Tezbarakat Bot Core API",
    version="1.0.0",
    description="Bot 核心服务内部 API",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# API 模型
# =====================================================

class LoginStartRequest(BaseModel):
    phone: str
    session_name: str


class LoginCompleteRequest(BaseModel):
    phone: str
    code: Optional[str] = None
    password: Optional[str] = None


class GroupRequest(BaseModel):
    group_id: int


class ReconnectRequest(BaseModel):
    phone: str
    session_name: str


# =====================================================
# API 端点
# =====================================================

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "running": bot_state.running,
        "connected_accounts": client_manager.connected_count
    }


@app.post("/start")
async def api_start_bot(background_tasks: BackgroundTasks):
    """启动 Bot"""
    if bot_state.running:
        return {"status": "already_running"}
    
    background_tasks.add_task(start_bot)
    return {"status": "starting"}


@app.post("/stop")
async def api_stop_bot():
    """停止 Bot"""
    if not bot_state.running:
        return {"status": "not_running"}
    
    await stop_bot()
    return {"status": "stopped"}


@app.get("/status")
async def get_status():
    """获取状态"""
    uptime = None
    if bot_state.start_time and bot_state.running:
        uptime = int((datetime.now() - bot_state.start_time).total_seconds())
    
    return {
        "running": bot_state.running,
        "uptime": uptime,
        "connected_accounts": client_manager.connected_count,
        "monitored_groups": len(message_handler._monitored_groups),
        "keywords_count": len(message_handler._keywords)
    }


# =====================================================
# 账号管理 API
# =====================================================

@app.post("/accounts/login/start")
async def start_login(request: LoginStartRequest):
    """开始登录"""
    try:
        result = await client_manager.start_login(request.phone, request.session_name)
        return result
    except Exception as e:
        logger.error(f"开始登录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/accounts/login/complete")
async def complete_login(request: LoginCompleteRequest):
    """完成登录"""
    try:
        result = await client_manager.complete_login(
            request.phone,
            code=request.code,
            password=request.password
        )
        return result
    except Exception as e:
        logger.error(f"完成登录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/accounts/{phone}")
async def remove_account(phone: str):
    """移除账号"""
    await client_manager.disconnect(phone)
    return {"status": "removed"}


@app.post("/accounts/reconnect")
async def reconnect_account(request: ReconnectRequest):
    """重新连接账号"""
    try:
        success = await client_manager.connect_existing(request.phone, request.session_name)
        if success:
            return {"status": "connected"}
        else:
            raise HTTPException(status_code=400, detail="连接失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accounts/{phone}/health")
async def check_account_health(phone: str):
    """检查账号健康"""
    is_healthy, message = await client_manager.check_account_health(phone)
    return {"healthy": is_healthy, "message": message}


# =====================================================
# 群组管理 API
# =====================================================

@app.get("/groups/resolve")
async def resolve_group(username: str):
    """解析群组"""
    result = await client_manager.resolve_username(username)
    if result:
        return result
    raise HTTPException(status_code=404, detail="未找到群组")


@app.get("/groups/{group_id}/info")
async def get_group_info(group_id: int):
    """获取群组信息"""
    result = await client_manager.get_entity_info(group_id)
    if result:
        return result
    raise HTTPException(status_code=404, detail="未找到群组")


@app.post("/groups/add")
async def add_group(request: GroupRequest):
    """添加群组"""
    message_handler.add_group(request.group_id)
    return {"status": "added"}


@app.post("/groups/remove")
async def remove_group(request: GroupRequest):
    """移除群组"""
    message_handler.remove_group(request.group_id)
    return {"status": "removed"}


# =====================================================
# 关键词和配置 API
# =====================================================

@app.post("/keywords/reload")
async def reload_keywords():
    """重新加载关键词"""
    await message_handler.reload_keywords()
    return {"status": "reloaded", "count": len(message_handler._keywords)}


@app.post("/config/reload")
async def reload_config():
    """重新加载配置"""
    # 重新加载 Dify 配置
    dify_service.reload_config()
    return {"status": "reloaded"}


# =====================================================
# Dify API
# =====================================================

@app.get("/dify/test")
async def test_dify():
    """测试 Dify 连接"""
    success, message = await dify_service.test_connection()
    return {"success": success, "message": message}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=bot_settings.api_host,
        port=bot_settings.api_port,
        reload=False,
        log_level=bot_settings.log_level.lower()
    )
